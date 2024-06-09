import textwrap


async def start_command(update, context):
    """Send a message when the command /start is issued."""
    reply = """
    
    Hi, this is the meeple matchmaker bot.
    
    I'm here to help match buyers and sellers in the Meeple Market Telegram Channel
        
    ## How do I work?
    
    I use two things from a posted message in the group
    
    - a message tag, supported tags are: #lookingfor, #sale, #selling, #seekinginterest, #sell
    - a game name, the more accurately your name matches the BGG name, the better your chances of success
        
    Example:
    
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
    
    """
    await update.message.reply_text(textwrap.dedent(reply), parse_mode="Markdown")