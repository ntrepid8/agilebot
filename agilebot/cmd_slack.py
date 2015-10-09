__author__ = 'ntrepid8'
import agilebot.cmd_util
import logging
from logging import NullHandler
import json
import sys
import argparse
from agilebot import util
from functools import partial
import os
logger = logging.getLogger('agilebot.slack')
logger.addHandler(NullHandler())


def create_bot(args, conf):
    # update trello arguments
    conf = util.update_config_group('slack', args, conf)
    # create the bot
    return agilebot.cmd_util.create_bot(conf, logger)


def cmd_slack_post(args, conf):
    bot = create_bot(args, conf)
    try:
        resp = bot.slack.post_msg(
            text=args.text,
            webhook_url=args.webhook_url,
            channel=args.channel,
            icon_emoji=args.icon_emoji,
            username=args.username
        )
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    else:
        print(json.dumps(resp))


def cmd_slack_help(parser, text=None):
    t = text or 'slack'
    logger.debug('show {} help'.format(t))
    parser.print_help()


def sub_command(main_subparsers):
    # slack sub-command
    slack_parser = main_subparsers.add_parser('slack', help='slack interaction')
    subparsers = slack_parser.add_subparsers(help='sub-commands', dest='subparser_1')
    slack_parser.set_defaults(func_help=partial(cmd_slack_help, slack_parser, 'slack'))

    # SUB-COMMAND: post (p)
    p_desc = 'Post a message to a slack channel.'
    p_parser = subparsers.add_parser(
        'post',
        aliases=['p'],
        description=p_desc,
        formatter_class=argparse.MetavarTypeHelpFormatter,
        help=p_desc)
    
    # p required arguments
    p_req_group = p_parser.add_argument_group(
        'required arguments',
    )
    p_req_group.add_argument('--text', '-t', required=True, type=str, help='text content of the message')

    # p additional required arguments
    p_add_group = p_parser.add_argument_group(
        'additional required arguments',
        'Required and may be specified here or in the configuration file.'
    )
    p_add_group.add_argument('--channel', type=str, help='Slack channel name')
    p_add_group.add_argument('--username', type=str, help='username of the bot')
    p_add_group.add_argument('--webhook-url', type=str, help='Slack url to POST the message to')
    p_add_group.set_defaults(
        channel=os.environ.get('SLACK_CHANNEL'),
        username=os.environ.get('SLACK_USERNAME'),
        webhook_url=os.environ.get('SLACK_WEBHOOK_URL'),
    )

    # p optional arguments
    p_opt_group = p_parser.add_argument_group(
        'additional optional arguments',
        'Optional and may be specified here or in the configuration file.'
    )
    p_opt_group.add_argument('--icon-emoji', default=':ghost:', type=str, help='emoji to use for the bot icon')
    p_opt_group.set_defaults(
        icon_emoji=os.environ.get('SLACK_ICON_EMOJI'),
    )
    
    # p defaults
    p_parser.set_defaults(func=cmd_slack_post)

    return slack_parser
