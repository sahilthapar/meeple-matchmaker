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
        update = mocker.Mock()
        update.to_dict.return_value = {"message": {"text": "hello"}}
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
        context.bot.send_message.assert_awaited_once()
        context.bot.send_message.assert_awaited_once_with(
            chat_id=ERROR_GROUP_CHAT_ID,
            text=mocker.ANY,
            parse_mode=ParseMode.HTML,
        )

        sent_message = context.bot.send_message.await_args.kwargs["text"]
        assert "An exception was raised while handling an update" in sent_message
        assert "boom" in sent_message
        assert "<pre>update =" in sent_message

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
        context.bot.send_message.assert_awaited_once()

        sent_message = context.bot.send_message.await_args.kwargs["text"]
        assert "not-an-update" in sent_message
        assert "bad payload" in sent_message
