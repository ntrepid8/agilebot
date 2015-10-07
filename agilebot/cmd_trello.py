__author__ = 'ntrepid8'
import logging
from logging import NullHandler
import sys
import json
logger = logging.getLogger('agilebot.trello')
logger.addHandler(NullHandler())


def cmd_trello(args, bot):
    logger.debug('CMD trello')


def find_trello(args, bot):
    # search args
    search_args = []
    if args.closed:
        search_args.append('closed')
    else:
        search_args.append('open')

    try:
        resp = bot.find_trello(search_args, organization_id=args.organization_id, name=args.name)
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    else:
        return resp


def cmd_trello_get_board(args, bot):
    logger.debug('CMD trello get-board')
    board = bot.trello.get_board(args.board_id)
    print(json.dumps(board))


def cmd_trello_find(args, bot):
    logger.debug('CMD trello find')
    print(json.dumps(find_trello(args, bot)))


def sub_command(main_subparsers):
    # trello command
    trello_parser = main_subparsers.add_parser('trello', help='interact with trello')
    board_subparsers = trello_parser.add_subparsers(help='sub-commands', dest='subparser_1')
    trello_parser.set_defaults(func_help=trello_parser.print_help)

    # get_board command
    parser_list = board_subparsers.add_parser('get-board', help='get a board by Id')
    parser_list.add_argument('--board-id', default=None, help='list organization trello')
    parser_list.set_defaults(func=cmd_trello_get_board)

    return trello_parser
