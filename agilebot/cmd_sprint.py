__author__ = 'ntrepid8'
import logging
from logging import NullHandler
import sys
import json
import argparse
from agilebot import util
logger = logging.getLogger('agilebot.sprint')
logger.addHandler(NullHandler())
ACTIVE_PATTERN = '*(active)'


def find_sprints(args, conf):
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
        conf = util.update_config_group('sprint', args, conf)
        bot = util.create_bot(conf, logger)
        resp = bot.trello.find_boards(
            board_name=board_name,
            organization_id=args.organization_id
        )

    except Exception as e:
        util.log_generic_error(e, sys.exc_info(), logger)
        sys.exit(1)
    else:
        return resp


def cmd_sprint_info(args, bot):
    logger.debug('CMD sprint.info')
    resp = find_sprints(args, bot)
    print(json.dumps(resp))


def cmd_sprint_start_new(args, conf):
    logger.debug('CMD sprint render-name')
    try:
        conf = util.update_config_group('sprint', args, conf)
        bot = util.create_bot(conf, logger)
        resp = bot.start_new_sprint(
            sprint_name=args.new_sprint_name,
            closing_sprint_name=args.closing_sprint_name,
            organization_id=args.organization_id)
    except Exception as e:
        util.log_generic_error(e, sys.exc_info(), logger)
        sys.exit(1)
    else:
        print(json.dumps(resp))


def cmd_render_name(args, conf):
    logger.debug('CMD sprint render-name')
    try:
        conf = util.update_config_group('sprint', args, conf)
        bot = util.create_bot(conf, logger)
        rendered_name = bot.format_sprint_name(args.sprint_name)
    except Exception as e:
        util.log_generic_error(e, sys.exc_info(), logger)
        sys.exit(1)
    else:
        print(rendered_name)


def cmd_sprint_get_active(args, conf):
    logger.debug('CMD sprint get-active')
    try:
        conf = util.update_config_group('sprint', args, conf)
        bot = util.create_bot(conf, logger)
        resp = bot.get_active_sprint()
    except Exception as e:
        util.log_generic_error(e, sys.exc_info(), logger)
        sys.exit(1)
    else:
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
    parser_info.set_defaults(func=cmd_sprint_info, func_help=parser_info.print_help)

    #
    # SUB-COMMAND: start-new (sn)
    sn_desc = 'start a new sprint and optionally migrate cards from the prior sprint'
    parser_create = sprint_subparsers.add_parser(
        'start-new',
        aliases=['sn'],
        description=sn_desc,
        formatter_class=argparse.MetavarTypeHelpFormatter,
        help=sn_desc
    )
    parser_create.add_argument('--organization-id', type=str, help='organization id')
    parser_create.add_argument(
        '--new-sprint-name',
        type=str,
        default='Sprint {iso_year}.{iso_week}',
        help='new sprint name (supports templates: {iso_year}, {iso_week})')
    parser_create.add_argument(
        '--closing-sprint-name',
        type=str,
        help='closing sprint name (supports * patterns)')
    parser_create.set_defaults(func=cmd_sprint_start_new, func_help=parser_create.print_help)

    #
    # SUB-COMMAND: render-name (rn)
    rn_desc = 'render a sprint board name'
    rn_parser = sprint_subparsers.add_parser(
        'render-name',
        aliases=['rn'],
        description=rn_desc,
        formatter_class=argparse.MetavarTypeHelpFormatter,
        help=rn_desc)
    # rn optional arguments
    rn_parser.add_argument('--sprint-name', type=str, help='sprint name')
    # rn defaults
    rn_parser.set_defaults(func=cmd_render_name, func_help=rn_parser.print_help)
    
    #
    # SUB-COMMAND: get-active (ga)
    ga_desc = 'get the active sprint'
    ga_parser = sprint_subparsers.add_parser(
        'get-active',
        aliases=['ga'],
        description=ga_desc,
        formatter_class=argparse.MetavarTypeHelpFormatter,
        help=ga_desc)
    # ga defaults
    ga_parser.set_defaults(func=cmd_sprint_get_active, func_help=ga_parser.print_help)
