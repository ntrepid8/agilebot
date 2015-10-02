__author__ = 'ntrepid8'
import logging
from logging import NullHandler
import sys
import json
logger = logging.getLogger('agilebot.slack')
logger.addHandler(NullHandler())


def cmd_slack_post(args, bot):
    bot.post_slack_msg(
        text=args.text,
        webhook_url=args.webhook_url,
        channel=args.channel,
        icon_emoji=args.icon_emoji,
        username=args.username
    )


def sub_command(main_subparsers):
    # boards command
    slack_parser = main_subparsers.add_parser('slack', help='slack interaction')
    subparsers = slack_parser.add_subparsers(help='sub-commands', dest='subparser_1')
    slack_parser.set_defaults(func_help=slack_parser.print_help)

    # post command
    parser_post = subparsers.add_parser('post', help='post a message to a channel')
    parser_post.add_argument('--channel', help='Slack channel name')
    parser_post.add_argument('--icon-emoji', default=':ghost:', help='emoji to use for the bot icon')
    parser_post.add_argument('--text', help='text content of the message')
    parser_post.add_argument('--username', help='username of the bot')
    parser_post.add_argument('--webhook-url', help='Slack url to POST the message to')
    parser_post.set_defaults(func=cmd_slack_post)

    return slack_parser
