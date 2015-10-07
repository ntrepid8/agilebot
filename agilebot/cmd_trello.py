__author__ = 'ntrepid8'
import logging
from logging import NullHandler
import sys
import json
logger = logging.getLogger('agilebot.trello')
logger.addHandler(NullHandler())


def cmd_trello_get_board(args, bot):
    logger.debug('CMD trello get-board')
    try:
        board = bot.trello.get_board(board_id=args.board_id)
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    else:
        print(json.dumps(board))


def cmd_trello_find_boards(args, bot):
    logger.debug('CMD trello find')
    try:
        boards = bot.trello.find_boards(name=args.board_name)
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    else:
        print(json.dumps(boards))


def sub_command(main_subparsers):
    # trello command
    trello_parser = main_subparsers.add_parser('trello', help='interact with trello')
    board_subparsers = trello_parser.add_subparsers(help='sub-commands', dest='subparser_1')
    trello_parser.set_defaults(func_help=trello_parser.print_help)

    # get_board command
    parser_get_board = board_subparsers.add_parser('get-board', help='get a board by Id')
    parser_get_board.add_argument('--board-id', default=None, help='board Id')
    parser_get_board.set_defaults(func=cmd_trello_get_board)
    
    # find_boards command
    parser_find_boards = board_subparsers.add_parser('find-boards', help='search for boards')
    parser_find_boards.add_argument(
        '--board-name', default=None, help='board name (supports Unix style pattern matching)')
    parser_find_boards.set_defaults(func=cmd_trello_find_boards)

    return trello_parser
