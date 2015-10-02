__author__ = 'ntrepid8'
import logging
from logging import NullHandler
import sys
import json
logger = logging.getLogger('agilebot.boards')
logger.addHandler(NullHandler())


def cmd_boards(args, bot):
    logger.debug('boards command')


def cmd_boards_list(args, bot):
    logger.debug('list boards')
    try:
        resp = bot.boards
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    else:
        print(json.dumps(resp))


def cmd_boards_find(args, bot):
    logger = logging.getLogger('agilebot.boards.find')
    logger.debug('CMD boards find')

    # search args
    search_args = []
    if args.open:
        search_args.append('open')
    if args.closed:
        search_args.append('closed')

    try:
        resp = bot.find_boards(search_args, organization=args.organization)
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    else:
        print(json.dumps(resp))


def sub_command(main_subparsers):
    # boards command
    board_parser = main_subparsers.add_parser('boards', help='interact with boards')
    board_subparsers = board_parser.add_subparsers(help='sub-commands', dest='subparser_1')
    board_parser.set_defaults(func_help=board_parser.print_help)

    # list command
    parser_list = board_subparsers.add_parser('list', help='list boards')
    parser_list.set_defaults(func=cmd_boards_list)

    # find command
    parser_find = board_subparsers.add_parser('find', help='find boards')
    parser_find.add_argument('--open', action='store_true', help='find open boards')
    parser_find.add_argument('--closed', action='store_true', help='find closed boards')
    parser_find.add_argument('--organization_id', default=None, help='find organization boards')
    parser_find.set_defaults(func=cmd_boards_find)

    return board_parser
