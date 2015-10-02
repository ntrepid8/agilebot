__author__ = 'ntrepid8'
import argparse
import os
import sys
import pytoml as toml
import logging
import collections
from colorlog import ColoredFormatter
from agilebot import (
    agilebot,
    cmd_boards,
    cmd_slack,
    cmd_sprint
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


def merge(dict_0, dict_1):
    for d1_key, d1_val in dict_1.items():
        if isinstance(d1_val, collections.Mapping):
            r = merge(dict_0.get(d1_key, {}), d1_val)
            dict_0[d1_key] = r
        else:
            dict_0[d1_key] = dict_1[d1_key]
    return dict_0


def get_first_value(*args):
    return next((i for i in args if i is not None), None)


def cmd_main(args, bot):
    pass


def main():
    # config
    conf = {
        'trello': {
            'api_key': None,
            'api_secret': None,
            'oauth_token': None,
            'oauth_secret': None,
            'organization_id': None
        },
        'agile': {
            'backlogs': []
        },
        'slack': {
            'webhook_url': None,
            'channel': None,
            'icon_emoji': ':ghost:',
            'username': 'agilebot'
        },
        'logging': {
            'level': 'INFO'
        }
    }

    # config file
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            toml_config = toml.load(f)
            conf = merge(conf, toml_config)

    # logging conf
    logger.setLevel(conf['logging']['level'])

    # library logging config
    lib_log_level = logging.CRITICAL
    logging.getLogger('oauthlib').setLevel(lib_log_level)
    logging.getLogger('requests').setLevel(lib_log_level)
    logging.getLogger('requests_oauthlib').setLevel(lib_log_level)

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
        'boards': cmd_boards.sub_command(subparsers),
        'slack': cmd_slack.sub_command(subparsers),
        'sprint': cmd_sprint.sub_command(subparsers)
    }

    # set defaults, ENV var first, then config file, then command line args
    parser.set_defaults(
        trello_api_key=get_first_value(
            os.environ.get('TRELLO_API_KEY'),
            conf['trello']['api_key']
        ),
        trello_api_secret=get_first_value(
            os.environ.get('TRELLO_API_SECRET'),
            conf['trello']['api_secret']
        ),
        trello_oauth_token=get_first_value(
            os.environ.get('TRELLO_OAUTH_TOKEN'),
            conf['trello']['oauth_token']
        ),
        trello_oauth_secret=get_first_value(
            os.environ.get('TRELLO_OAUTH_SECRET'),
            conf['trello']['oauth_secret']
        ),
        trello_organization_id=get_first_value(
            os.environ.get('TRELLO_ORGANIZATION_ID`'),
            conf['trello']['organization_id']
        ),
        slack_webhook_url=get_first_value(
            os.environ.get('SLACK_WEBHOOK_URL'),
            conf['slack']['webhook_url']
        ),
        slack_channel=get_first_value(
            os.environ.get('SLACK_CHANNEL'),
            conf['slack']['channel']
        ),
        slack_icon_emoji=get_first_value(
            os.environ.get('SLACK_ICON_EMOJI'),
            conf['slack']['icon_emoji']
        ),
        slack_username=get_first_value(
            os.environ.get('SLACK_USERNAME'),
            conf['slack']['username']
        ),
    )

    args = parser.parse_args()
    bot = agilebot.AgileBot(
        trello_api_key=args.trello_api_key,
        trello_api_secret=args.trello_api_secret,
        trello_oauth_token=args.trello_oauth_token,
        trello_oauth_secret=args.trello_oauth_secret,
        trello_organization_id=args.trello_organization_id,
        slack_webhook_url=args.slack_webhook_url,
        slack_channel=args.slack_channel,
        slack_icon_emoji=args.slack_icon_emoji,
        slack_username=args.slack_username,
    )

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
