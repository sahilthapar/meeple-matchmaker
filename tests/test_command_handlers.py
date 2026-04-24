"""Test file for all command handlers"""
import textwrap
import pytest
from src.command_handlers import format_list_of_posts, format_post, start_command, disable_command, list_all_active_sales, list_all_active_searches, list_my_active_posts, add_bgg_username, get_status_from_bgg_game, import_my_bgg_collection, match_me, disable_user
from tests.helpers import initialize_post

class TestCommandHandlers:
    """Class containing all test cases to be executed for command handlers"""

    @pytest.mark.parametrize(
        argnames="posts,expected_reply",
        argvalues=[
            (   # post_type, game_id, user_id, user_name, game_name
                [
                    ('sale', 167791, '101', 'Jacob', "Terraforming Mars", 1),
                    ('sale', 167791, '103', 'Vikrant', "Terraforming Mars", 1),
                    ('sale', 342942, '101', 'Jacob', 'Ark Nova', 1),
                ],
                "\nActive sales:"
                "\nTerraforming Mars: [Jacob](tg://user?id=101)"
                "\nTerraforming Mars: [Vikrant](tg://user?id=103)"
                "\nArk Nova: [Jacob](tg://user?id=101)\n"
            ),
            (
                [
                    ('search', 167791, '102', 'Henry', "Terraforming Mars", 1),
                    ('search', 1406, '101', 'Jacob', "Monopoly", 1),
                    ('search', 1406, '102', 'Henry', "Monopoly", 1),
                ],
                "\n\nActive searches:"
                "\nTerraforming Mars: [Henry](tg://user?id=102)"
                "\nMonopoly: [Jacob](tg://user?id=101)"
                "\nMonopoly: [Henry](tg://user?id=102)"
            ),
            (
                [
                    ('sale', 167791, '101', 'Jacob', "Terraforming Mars", 1),
                    ('sale', 167791, '103', 'Vikrant', "Terraforming Mars", 1),
                    ('sale', 342942, '101', 'Jacob', "Ark Nova", 1),
                    ('search', 167791, '102', 'Henry', "Terraforming Mars", 1),
                    ('search', 1406, '101', 'Jacob', 'Monopoly', 1),
                    ('search', 1406, '102', 'Henry', "Monopoly", 1),
                ],
                "\nActive sales:"
                "\nTerraforming Mars: [Jacob](tg://user?id=101)"
                "\nTerraforming Mars: [Vikrant](tg://user?id=103)"
                "\nArk Nova: [Jacob](tg://user?id=101)"
                "\n"
                "\nActive searches:"
                "\nTerraforming Mars: [Henry](tg://user?id=102)"
                "\nMonopoly: [Jacob](tg://user?id=101)"
                "\nMonopoly: [Henry](tg://user?id=102)"
            ),
        ],
        ids=[
            "list_active_sales",
            "list_active_searches",
            "list_all_posts",
        ]

    )
    def test_format_list_of_posts(self, database, posts, expected_reply):
        """Tests whether the formatted list of posts is as expected"""
        posts_orm = []
        for post_type, game_id, user_id, user_name, game_name, active in posts:
            posts_orm.append(
                initialize_post(
                    post_type=post_type, text='', active=active,
                    user_id=user_id, user_name=user_name,
                    game_id=game_id, game_name=game_name
                )
            )
        assert list(format_list_of_posts(posts_orm))[0] == textwrap.dedent(expected_reply)

    @pytest.mark.parametrize(
        argnames="post,expected_response",
        argvalues=[
            (
                # post_type, game_id, user_id, user_name, game_name, active
                ('sale', 167791, '101', 'Jacob', "Terraforming Mars", 1),
                "Terraforming Mars: [Jacob](tg://user?id=101)"
            ),
            (
                ('sale', 167791, '1012', 'Jacob', "", 1),
                ": [Jacob](tg://user?id=1012)" 
                )
        ],
        ids=[
            "format_single_post",
            "error_format_single_post_without_game_name"
        ]

    )
    def test_format_post(self, bgg_client, database, post, expected_response):
        """Tests the individual format post function"""
        post_type, game_id, user_id, user_name, game_name, active = post
        post = initialize_post(
                post_type=post_type, text='', active=active,
                user_id=user_id, user_name=user_name,
                game_id=game_id, game_name=game_name
            )
        assert format_post(post, bgg_client) == textwrap.dedent(expected_response)
   
    @pytest.mark.parametrize(
            "chat_type",
            ("private","group")
    )
    async def test_start_command(self, mock_update, chat_type):
        mock_update.effective_chat.type=chat_type
        await start_command(mock_update, None)
        if chat_type!="private":
            mock_update.message.set_reaction.assert_called_once_with("👎")
        else:
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.parametrize("update_details",
                            [
                                {"chat_type":"group", "user_id":"101"},
                                {"chat_type":"private", "user_id":"101"}
                            ]
                            )
    async def test_disable_command(self, mock_update, update_details, mocker):
        mock_update.effective_chat.type=update_details["chat_type"]
        mock_update.message.from_user.id=update_details["user_id"]
        mock_disable_posts = mocker.patch("src.command_handlers.disable_posts")
        await disable_command(mock_update, None)
        if update_details["chat_type"]!="private":
            mock_update.message.set_reaction.assert_called_once_with("👎")
        else:
            mock_disable_posts.assert_called_once_with(user_id=update_details["user_id"])
    
    @pytest.mark.parametrize(
            "chat_type",
            ("private","group")
    )
    async def test_list_all_active_sales(self, mock_update, chat_type, mocker, database):
        mock_update.effective_chat.type=chat_type
        # Create test posts
        posts_orm = [
            initialize_post(
                post_type="sale", text='', active=1,
                user_id="101", user_name="Jacob",
                game_id=167791, game_name="Terraforming Mars"
            ),
            initialize_post(
                post_type="sale", text='', active=1,
                user_id="102", user_name="Henry",
                game_id=342942, game_name="Ark Nova"
            ),
        ]

        # Mock read_posts to return test data
        mock_read_posts = mocker.patch("src.command_handlers.read_posts", return_value=posts_orm)
        await list_all_active_sales(mock_update, None)
        if chat_type!="private":
            mock_update.message.set_reaction.assert_called_once_with("👎")
        else:
            mock_read_posts.assert_called_once_with(post_type="sale")
            mock_update.message.reply_text.assert_called()
    
    @pytest.mark.parametrize(
            "chat_type",
            ("private","group")
    )
    async def test_list_all_active_searches(self, mock_update, chat_type, mocker, database):
        mock_update.effective_chat.type=chat_type
        # Create test posts
        posts_orm = [
            initialize_post(
                post_type="search", text='', active=1,
                user_id="101", user_name="Jacob",
                game_id=167791, game_name="Terraforming Mars"
            ),
            initialize_post(
                post_type="search", text='', active=1,
                user_id="102", user_name="Henry",
                game_id=342942, game_name="Ark Nova"
            ),
        ]

        # Mock read_posts to return test data
        mock_read_posts = mocker.patch("src.command_handlers.read_posts", return_value=posts_orm)
        await list_all_active_searches(mock_update, None)
        if chat_type!="private":
            mock_update.message.set_reaction.assert_called_once_with("👎")
        else:
            mock_read_posts.assert_called_once_with(post_type="search")
            mock_update.message.reply_text.assert_called()
    
    @pytest.mark.parametrize("update_details",
                            [
                                {"chat_type":"group", "user_id":"101"},
                                {"chat_type":"private", "user_id":"101"}
                            ]
                            )
    async def test_list_my_active_posts(self, mock_update, update_details, mocker, database):
        mock_update.effective_chat.type=update_details["chat_type"]
        mock_update.message.from_user.id=update_details["user_id"]
        # Create test posts
        posts_orm = [
            initialize_post(
                post_type="search", text='', active=1,
                user_id="101", user_name="Jacob",
                game_id=167791, game_name="Terraforming Mars"
            ),
            initialize_post(
                post_type="sale", text='', active=1,
                user_id="101", user_name="Jacob",
                game_id=342942, game_name="Ark Nova"
            ),
        ]

        # Mock read_posts to return test data
        mock_read_posts = mocker.patch("src.command_handlers.read_posts", return_value=posts_orm)
        await list_my_active_posts(mock_update, None)
        if update_details["chat_type"]!="private":
            mock_update.message.set_reaction.assert_called_once_with("👎")
        else:
            mock_read_posts.assert_called_once_with(user_id=update_details["user_id"])
            mock_update.message.reply_text.assert_called()

