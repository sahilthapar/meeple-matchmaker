# meeple-matchmaker
A telegram bot for meeple market which matches 
"in-search-of" and sale posts and notifies users

# How it works?

- Users can post messages with one of the following two tags, followed by a game name to trigger the bot
  - **#lookingfor, #iso**
  - **#seekinginterest, #selling, #sale**
- The bot then parses the message using bgg-python-api
  - it tries an exact match and then a fuzzy match to find the game id on bgg

A typical flow will look something like this
- user posts a looking for message
  - this logs an entry into the database
- another user posts a selling or seekinginterest message
  - the bot queries the database to find all users who have previously posted a looking for message
  - and then tags them to a reply

