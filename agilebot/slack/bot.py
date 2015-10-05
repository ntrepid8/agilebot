__author__ = 'ntrepid8'
import requests
from agilebot import util
import json


class SlackBot(object):

    def __init__(self, conf=None):
        self.conf = util.gen_namedtuple('Slack', self.default_conf(), conf or {})

    @classmethod
    def default_conf(cls):
        return {
            'webhook_url': None,
            'channel': None,
            'icon_emoji': ':ghost:',
            'username': 'agilebot',
            'token': None
        }

    def post_msg(self, text, webhook_url=None, channel=None, icon_emoji=None, username=None):
        data = {
            'text': text,
            'channel': channel or self.conf.channel,
            'icon_emoji': icon_emoji or self.conf.icon_emoji,
            'username': username or self.conf.username,
            'link_names': 1
        }
        for k, v in data.items():
            if not v:
                raise ValueError('invalid {key}: {value}'.format(
                    key=k,
                    value=v
                ))
        webhook_url = webhook_url or self.conf.webhook_url
        if not webhook_url:
            raise ValueError('webhook_url is required')
        resp = requests.post(
            webhook_url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data))
        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        return {'success': True}
