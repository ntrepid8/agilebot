__author__ = 'ntrepid8'
import logging
from logging import NullHandler
import sys
import json
logger = logging.getLogger('agilebot.sprint')
logger.addHandler(NullHandler())
ACTIVE_PATTERN = '*(active)'


def find_sprints(args, bot):
    search_args = ['open']
    board_name = None
    if args.name and args.active and ACTIVE_PATTERN in args.name:
        logger.error('you have specified active flag and included the pattern "{active}" in the name')
    if args.name:
        board_name = args.name
    if args.active:
        if board_name is None:
            board_name = ACTIVE_PATTERN
        else:
            board_name += '*(active)'
    try:
        resp = bot.find_boards(
            filter_params=search_args,
            organization_id=args.organization_id,
            name=board_name,
            include_cards=True,
            include_lists=True,
            query_params={
                'lists': 'open'
            }
        )
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    else:
        return resp


def cmd_sprint_info(args, bot):
    logger.debug('CMD sprint.info')
    resp = find_sprints(args, bot)
    print(json.dumps(resp))


def sub_command(main_subparsers):

    # sprint command
    sprint_parser = main_subparsers.add_parser('sprint', help='manage sprints')
    sprint_subparsers = sprint_parser.add_subparsers(help='sub-commands', dest='subparser_1')
    sprint_parser.set_defaults(func_help=sprint_parser.print_help)

    # info command
    parser_info = sprint_subparsers.add_parser('info', help='show info about sprints')
    parser_info.add_argument('--active', action='store_true', help='info about the active sprint')
    parser_info.add_argument('--organization-id', default=None, help='organization id')
    parser_info.add_argument('--name', default='Sprint*', help='sprint board name (supports *patterns*)')
    parser_info.set_defaults(func=cmd_sprint_info)
