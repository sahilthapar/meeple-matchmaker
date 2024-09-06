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

Have questions?
[Check out this FAQ](faq.md)

Have suggestions?
Use the meeple-market chit chat group
or [Github issues](https://github.com/sahilthapar/meeple-matchmaker/issues).
**Do not post in the main channel.**
