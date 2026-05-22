"""Contains message constants for use across the project"""


# Command handler messages
INVALID_DISABLE_POST_FOR_USER = "Please follow this format:\n /disable_post_for_user <user_id> <game_id> (sale|search)"
INVALID_DISABLE_USER = "Please enter a valid user id and post type (sale|search|all)"
INVALID_NOT_AN_ADMIN = "Sorry this command is only available to the admin!"
INVALID_ADD_BGG_USERNAME_ERROR = "Invalid username! Add username after the command. Copy the example below."
INVALID_ADD_BGG_USERNAME_NOT_FOUND = "No BGG username found! Please attach a BGG User using the command /add_bgg_username <your-username>"
INVALID_ADD_BGG_USERNAME_SHOW_FORMAT = "/add_bgg_username my-username"
MEEPLE_MATCHMAKER_START = """
Hi! I'm Meeple Matchmaker Bot.

I help match buyers and sellers in the Meeple Market Telegram channel.

*How to use:*
- Start your message with a hashtag and the game name (as listed on BGG).
  - To buy: #lookingfor, #iso, #looking
  - To sell: #sale, #sell, #selling, #auction (Not allowed in DMs)
- The bot will check the game name on BGG and react with 👍 if it finds a match.

*Tip:*
Keep the first line to just the hashtag and game name. Add details (condition, price, location) on new lines.

[Full guide & features](https://github.com/sahilthapar/meeple-matchmaker/blob/main/README.md)
[FAQ](https://github.com/sahilthapar/meeple-matchmaker/blob/main/faq.md)
Suggestions? Use the chit chat group or [GitHub issues](https://github.com/sahilthapar/meeple-matchmaker/issues).
**Don't post suggestions in the main channel.**
"""