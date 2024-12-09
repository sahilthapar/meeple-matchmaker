<!-- TOC -->
* [meeple-matchmaker](#meeple-matchmaker)
  * [How does it work?](#how-does-it-work)
  * [Example:](#example)
<!-- TOC -->

# meeple-matchmaker
A telegram bot for meeple market which matches 
"in-search-of" and sale posts and notifies users

## How does it work?
    
The bot uses two things from a posted message in the group
  
- a message tag, supported tags are:
  - to search for a game: `#lookingfor, #iso, #looking`
  - to sell a game: `#seekinginterest, #auction, #sale, #sell, #selling`
  - to mark a game as sold: `#sold`
  - to mark a game as found: `#found`
- a game name, the more accurately your name matches the BGG name, the better your chances of success

This game name is then searched against BGG, and converted to a game id
if a successful match is found.

If the bot was able to find a successful match, it will react to the message with a 👍

```
Important note: Keep the first line of your message limited to only these two things
a hashtag and a game name (as seen on BGG)

All other details like condition, price, location should be present only in a new line
```

## Example:

Deepak posts a message
```
#lookingfor Ark Nova
```

Chaitanya posts a message
```
#lookingfor Ark Nova
```

Tanuj posts a message a few days later
```
#seekinginterest Ark Nova
```

The bot will reply to Tanuj's message and tag Deepak and Chaitanya
```
@Deepak @Chaitanya
```

## Supported Commands


| Command                    | Description                                           | Private / Group Support     | Notes                                                                                      |
|----------------------------|-------------------------------------------------------|-----------------------------|--------------------------------------------------------------------------------------------|
| #lookingfor game_name      | Adds game_name to your search list                    | Both Private and Group Chat | Supported tags are #lookingfor, #looking, #iso                                             |
| #sale game_name            | Adds game_name to your sale list                      | Both Private and Group Chat | Supported tags are #sale, #seekinginterest, #selling, #auction                             |
| #sold game_name            | Removes game_name from your sale list                 | Both Private and Group Chat |                                                                                            |
| #found game_name           | Removes game_name from your search list               | Both Private and Group Chat |                                                                                            |
| /start                     | Gives a detailed message explaining what the bot does | Private Only                |                                                                                            |
| /list_all_sales            | Lists all active sales                                | Private Only                |                                                                                            |
| /list_all_searches         | List all active searches                              | Private Only                |                                                                                            |
| /list_my_posts             | List all your active posts - both sales and searches  | Private Only                |                                                                                            |
| /match_me                  | Finds matches for your sales and searches             | Private Only                |                                                                                            |
| /add_bgg_username          | Updates your user profile to add a bgg username       | Private Only                |                                                                                            |
| /import_my_bgg_collection  | Imports your collection                               | Private Only                | Only imports wishlist / want-to-buy as searches and<br/>  for-trade as sales not all games |
| /disable                   | Marks all your posts as inactive                      | Private Only                |                                                                                            |


Have questions?
[Check out this FAQ](faq.md)

Have suggestions?
Use the meeple-market chit chat group
or [Github issues](https://github.com/sahilthapar/meeple-matchmaker/issues).
**Do not post in the main channel.**
