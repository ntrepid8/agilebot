import sys
from agilebot import agilebot

__author__ = 'ntrepid8'


def create_bot(conf, logger):
    try:
        bot = agilebot.AgileBot(**conf)
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    else:
        logger.debug('AgileBot created successfully')

    return bot