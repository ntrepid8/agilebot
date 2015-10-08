__author__ = 'ntrepid8'
import logging
from logging import NullHandler
import sys
import json
import argparse
import os
from agilebot import util
logger = logging.getLogger('agilebot.trello')
logger.addHandler(NullHandler())


def create_bot(args, conf):
    # update trello arguments
    conf = util.update_config_group('trello', args, conf)
    # create the bot
    return util.create_bot(conf, logger)


def cmd_trello_get_board(args, conf):
    logger.debug('CMD trello get-board')
    bot = create_bot(args, conf)
    try:
        board = bot.trello.get_board(board_id=args.board_id)
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    else:
        print(json.dumps(board))


def cmd_trello_find_boards(args, conf):
    logger.debug('CMD trello find-boards')
    bot = create_bot(args, conf)
    try:
        boards = bot.trello.find_boards(
            board_name=args.board_name,
            organization_id=args.organization_id
        )
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    else:
        print(json.dumps(boards))


def cmd_trello_create_board(args, conf):
    logger.debug('CMD trello create-board')
    bot = create_bot(args, conf)
    try:
        board = bot.trello.create_board(
            board_name=args.board_name,
            list_names=args.list_names,
            organization_id=args.organization_id
        )
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    else:
        print(json.dumps(board))


def sub_command(main_subparsers):
    # trello sub-command
    trello_parser = main_subparsers.add_parser('trello', help='interact with trello')
    trello_subparsers = trello_parser.add_subparsers(help='sub-commands', dest='subparser_1')
    trello_parser.set_defaults(func_help=trello_parser.print_help)
    
    # common arguments parser
    trello_common_parser = argparse.ArgumentParser(description='trello common arguments', add_help=False)
    trello_common_parser.add_argument('--organization-id', type=str, help='organization ID in Trello')
    trello_common_parser.set_defaults(
        organization_id=os.environ.get('TRELLO_ORGANIZATION_ID'),
    )

    # trello auth argument group
    trello_auth_group = trello_common_parser.add_argument_group(
        'auth arguments',
        'These are required but may be supplied with arguments, by environment variable, or by conf file.')
    trello_auth_group.add_argument('--api-key', type=str, help='Trello API key')
    trello_auth_group.add_argument('--api-secret', type=str, help='Trello API secret')
    trello_auth_group.add_argument('--oauth-token', type=str, help='Trello OAuth access token')
    trello_auth_group.add_argument('--oauth-secret', type=str, help='Trello OAuth access secret')
    trello_auth_group.set_defaults(
        api_key=os.environ.get('TRELLO_API_KEY'),
        api_secret=os.environ.get('TRELLO_API_SECRET'),
        oauth_token=os.environ.get('TRELLO_OAUTH_TOKEN'),
        oauth_secret=os.environ.get('TRELLO_OAUTH_SECRET'),
    )

    # SUB-COMMAND: get_board (gb)
    gb_desc = 'get a trello board by id'
    gb_parser = trello_subparsers.add_parser(
        'get-board',
        aliases=['gb'],
        description=gb_desc,
        parents=[trello_common_parser],
        formatter_class=argparse.MetavarTypeHelpFormatter,
        help=gb_desc)
    # required arguments
    gb_req_group = gb_parser.add_argument_group('required arguments')
    gb_req_group.add_argument('--board-id', required=True, type=str, help='board Id')
    # set defaults
    gb_parser.set_defaults(func=cmd_trello_get_board, func_help=gb_parser.print_help)
    
    # SUB-COMMAND: find_boards (fb)
    fb_desc = 'find trello boards by name or pattern, if not pattern is give all boards are returned'
    fb_parser = trello_subparsers.add_parser(
        'find-boards',
        aliases=['fb'],
        description=fb_desc,
        parents=[trello_common_parser],
        formatter_class=argparse.MetavarTypeHelpFormatter,
        help=fb_desc)
    # fb optional arguments
    fb_parser.add_argument(
        '--board-name', type=str, help='board name (supports Unix style pattern matching)')
    # fb set defaults
    fb_parser.set_defaults(func=cmd_trello_find_boards, func_help=fb_parser.print_help)

    # SUB-COMMAND: create-board (cb)
    cb_desc = 'create a new trello board'
    cb_parser = trello_subparsers.add_parser(
        'create-board',
        aliases=['cb'],
        description=cb_desc,
        parents=[trello_common_parser],
        formatter_class=argparse.MetavarTypeHelpFormatter,
        help=cb_desc)
    # cb required arguments
    cb_req_group = cb_parser.add_argument_group('required arguments')
    cb_req_group.add_argument('--board-name', required=True, type=str, help='board name')
    # cb optional arguments
    cb_parser.add_argument(
        '--list-name',
        dest='list_names',
        action='append',
        type=str,
        help='name of list to add to the board (multiple allowed)')
    # cb set defaults
    cb_parser.set_defaults(func=cmd_trello_create_board, func_help=cb_parser.print_help)

    return trello_parser
