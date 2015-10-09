__author__ = 'ntrepid8'
import argparse
import os
import sys
import pytoml as toml
import logging
from copy import copy
from colorlog import ColoredFormatter
from agilebot import (
    agilebot,
    cmd_slack,
    cmd_sprint,
    cmd_trello,
    util
)

CONFIG_PATH = os.path.expanduser('~/.agilebot.toml')
root_logger = logging.getLogger()
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
root_logger.addHandler(handler)
logger = logging.getLogger('agilebot')


def get_first_value(*args):
    return next((i for i in args if i is not None), None)


def main():
    # config
    default_conf = agilebot.AgileBot.default_conf()
    conf = copy(default_conf)

    # config file
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            toml_config = toml.load(f)
            conf = util.left_merge(default_conf, toml_config)

    # logging conf
    log_level = os.environ.get('AGILEBOT_LOG_LEVEL') or conf['logging']['level']
    logger.setLevel(log_level)
    logger.info('log level: {}'.format(log_level))

    # library logging config
    lib_log_level = logging.CRITICAL
    logging.getLogger('oauthlib').setLevel(lib_log_level)
    logging.getLogger('requests').setLevel(lib_log_level)
    logging.getLogger('requests_oauthlib').setLevel(lib_log_level)

    # command line args
    parser = argparse.ArgumentParser(
        description='Automate functions for Agile development sprints.')
    subparsers = parser.add_subparsers(help='sub-command help', dest='subparser_0')
    parser.add_argument('--conf', action='store_true', default=False, help='print current configuration')

    # boards sub-command
    sub_commands = {
        'slack': cmd_slack.sub_command(subparsers),
        'sprint': cmd_sprint.sub_command(subparsers),
        'trello': cmd_trello.sub_command(subparsers)
    }

    # set defaults, ENV var first, then config file, then command line args
    parser.set_defaults(
        func=None,
        func_help=parser.print_help,
        agile_sprint_lists=get_first_value(
            os.environ.get('AGILE_SPRINT_LISTS'),
            conf['agile']['sprint_lists']
        ),
    )

    # parse the arguments
    args = parser.parse_args()
    sc_0 = getattr(args, 'subparser_0', '')
    sc_1 = getattr(args, 'subparser_1', '')
    logger.debug('subparser_0: {}'.format(sc_0))
    logger.debug('subparser_1: {}'.format(sc_1))

    # agile
    conf['agile']['sprint_lists'] = args.agile_sprint_lists

    if not len(sys.argv) > 1:
        # no arguments given, show help
        logger.debug('sys.argv: {}'.format(len(sys.argv)))
        parser.print_help()
    elif args.conf:
        # show current config
        logger.debug('printing current configuration')
        print(toml.dumps(conf, sort_keys=True))
    elif not getattr(args, 'func', None):
        # if the sub-command function is not set, show help
        logger.debug('sub-command function not found')
        if hasattr(args, 'func_help'):
            logger.debug('show sub-command specific help')
            func_help = args.func_help
        else:
            logger.debug('show general help')
            func_help = parser.print_help
        func_help()
        sys.exit(1)
    else:
        # run the sub-command
        logger.debug('executing: agilebot {} {}'.format(sc_0, sc_1))
        args.func(args, conf)


if __name__ == '__main__':
    main()
