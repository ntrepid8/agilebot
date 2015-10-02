__author__ = 'ntrepid8'
import argparse
import os
import sys
import pytoml as toml
import logging
from colorlog import ColoredFormatter
from agilebot import (
    agilebot,
    cmd_boards
)

CONFIG_PATH = os.path.expanduser('~/.agilebot.toml')
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = ColoredFormatter(
    "%(log_color)s[%(levelname)s (%(asctime)s) %(name)s]%(reset)s %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def cmd_main(args, bot):
    pass


def main():
    # config file
    toml_config = {}
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            toml_config = toml.load(f)

    # logging conf
    logging_conf = toml_config.get('logging') or {}
    if 'level' in logging_conf:
        logger.setLevel(logging_conf['level'])

    # library logging config
    lib_log_level = logging.CRITICAL
    logging.getLogger('oauthlib').setLevel(lib_log_level)
    logging.getLogger('requests').setLevel(lib_log_level)
    logging.getLogger('requests_oauthlib').setLevel(lib_log_level)

    # trello_conf
    trello_conf = toml_config.get('trello') or {}

    # command line args
    parser = argparse.ArgumentParser(description='Automate functions for Agile development sprints.')
    subparsers = parser.add_subparsers(help='sub-command help', dest='subparser_0')
    parser.add_argument('--trello-organization-id', help='organization ID in Trello')
    parser.add_argument('--trello-api-key', help='your Trello API key')
    parser.add_argument('--trello-api-secret', help='your Trello API secret')
    parser.add_argument('--trello-oauth-token', help='your Trello OAuth access token')
    parser.add_argument('--trello-oauth-secret', help='your Trello OAuth access secret')

    # boards sub-command
    sub_commands = {
        'boards': cmd_boards.sub_command(subparsers)
    }

    # set defaults, ENV var first, then config file, then command line args
    parser.set_defaults(
        trello_organization_id=os.environ.get('TRELLO_ORGANIZATION_ID', trello_conf.get('organization_id')),
        trello_api_key=os.environ.get('TRELLO_API_KEY', trello_conf.get('api_key')),
        trello_api_secret=os.environ.get('TRELLO_API_SECRET', trello_conf.get('api_secret')),
        trello_oauth_token=os.environ.get('TRELLO_OAUTH_TOKEN', trello_conf.get('oauth_token')),
        trello_oauth_secret=os.environ.get('TRELLO_OAUTH_SECRET', trello_conf.get('oauth_secret')),
    )

    args = parser.parse_args()
    bot = agilebot.AgileBot(
        trello_api_key=args.trello_api_key,
        trello_api_secret=args.trello_api_secret,
        trello_oauth_token=args.trello_oauth_token,
        trello_oauth_secret=args.trello_oauth_secret,
        trello_organization_id=args.trello_organization_id)

    if not getattr(args, 'func', None):
        if hasattr(args, 'func_help'):
            func_help = args.func_help
        else:
            func_help = parser.print_help
        func_help()
        sys.exit(1)
    args.func(args, bot)


if __name__ == '__main__':
    main()
