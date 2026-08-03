"""Tests for the Telegram error handler."""

import pytest
from unittest.mock import AsyncMock

from telegram.constants import ParseMode

from src.constants import ERROR_GROUP_CHAT_ID
from src.error_handler import error_handler_cb


class TestErrorHandler:
    """Covers error reporting behavior for the bot."""

    @pytest.mark.asyncio
    async def test_error_handler_reports_exception_to_error_group(self, mocker):
        """The handler should log the failure and forward a report to the error chat."""

        class FakeUpdate:
            def __init__(self, payload):
                self._payload = payload

            def to_dict(self):
                return self._payload

        mocker.patch("src.error_handler.Update", FakeUpdate)

        update = FakeUpdate({"message": {"text": "hello"}})
        error = None
        try:
            raise RuntimeError("boom")
        except RuntimeError as exc:
            error = exc

        context = mocker.Mock()
        context.error = error
        context.bot.send_message = AsyncMock()

        mocked_logger = mocker.patch("src.error_handler.log")

        await error_handler_cb(update, context)

        mocked_logger.error.assert_called_once()
        mocked_logger.info.assert_called_once()
        assert context.bot.send_message.await_count == 2

        first_call, second_call = context.bot.send_message.await_args_list

        assert first_call.kwargs["chat_id"] == ERROR_GROUP_CHAT_ID
        assert first_call.kwargs["parse_mode"] == ParseMode.HTML
        assert (
            "An exception was raised while handling an update"
            in first_call.kwargs["text"]
        )
        assert "<pre>update =" in first_call.kwargs["text"]
        assert "hello" in first_call.kwargs["text"]

        assert second_call.kwargs["chat_id"] == ERROR_GROUP_CHAT_ID
        assert second_call.kwargs["parse_mode"] == ParseMode.HTML
        assert "<pre>" in second_call.kwargs["text"]
        assert "RuntimeError: boom" in second_call.kwargs["text"]

    @pytest.mark.asyncio
    async def test_error_handler_handles_non_update_objects(self, mocker):
        """The handler should still report a string-based update payload safely."""
        context = mocker.Mock()
        try:
            raise ValueError("bad payload")
        except ValueError as exc:
            context.error = exc
        context.bot.send_message = AsyncMock()

        mocked_logger = mocker.patch("src.error_handler.log")

        await error_handler_cb("not-an-update", context)

        mocked_logger.error.assert_called_once()
        assert context.bot.send_message.await_count == 2

        first_call, second_call = context.bot.send_message.await_args_list
        assert "not-an-update" in first_call.kwargs["text"]
        assert second_call.kwargs["parse_mode"] == ParseMode.HTML
        assert "ValueError: bad payload" in second_call.kwargs["text"]
