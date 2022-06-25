import logging

logger = logging.getLogger("discord_bot")

logger.setLevel(logging.DEBUG)

fh = logging.FileHandler("errorLog.log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
