import logging
log = logging.getLogger("meeple-matchmaker")

async def reaction_handler(update, context) -> None:
    log.info('received reaction')
    log.info(update)