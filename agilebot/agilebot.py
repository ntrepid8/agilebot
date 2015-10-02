__author__ = 'ntrepid8'
import requests
from requests_oauthlib import OAuth1
import logging
from logging import NullHandler
from collections import namedtuple
import json
logger = logging.getLogger('agilebot.lib')
logger.addHandler(NullHandler())
TRELLO_API_BASE_URL = 'https://api.trello.com/1'


class AgileBot(object):

    def __init__(self,
                 trello_api_key,
                 trello_api_secret,
                 trello_oauth_token,
                 trello_oauth_secret,
                 trello_organization_id=None,
                 slack_webhook_url=None,
                 slack_channel=None,
                 slack_icon_emoji=None,
                 slack_username=None):

        # agile
        self._boards = None

        # trello
        trello_conf_class = namedtuple('TrelloConf', 'organization_id, session')
        self.trello = trello_conf_class(
            organization_id=trello_organization_id,
            session=requests.Session())
        self.trello.session.auth = OAuth1(
            client_key=trello_api_key,
            client_secret=trello_api_secret,
            resource_owner_key=trello_oauth_token,
            resource_owner_secret=trello_oauth_secret)
        self.trello.session.headers['Accept'] = 'application/json'

        # slack
        slack_class = namedtuple('SlackConf', 'webhook_url, channel, icon_emoji, username')
        self.slack = slack_class(
            webhook_url=slack_webhook_url,
            channel=slack_channel,
            icon_emoji=slack_icon_emoji,
            username=slack_username
        )

    @property
    def boards(self):
        if self._boards:
            return self._boards
        else:
            boards = self.find_boards()
            self._boards = [b for b in boards if b.get('idOrganization') is None]
        return self._boards

    def find_boards(self, filter_params=None, organization=False):
        url = [TRELLO_API_BASE_URL, '/members/me/boards']
        query_params = {
            'organization': 'true' if organization is True else 'false'
        }
        if filter_params:
            query_params['filter'] = ','.join(filter_params)
        resp = self.trello.session.get(''.join(url), params=query_params)
        logger.debug('{method} {code} {url}'.format(
            method=resp.request.method,
            code=resp.status_code,
            url=resp.request.url
        ))
        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        return resp.json()

    def post_slack_msg(self, text, webhook_url=None, channel=None, icon_emoji=None, username=None):
        data = {
            'text': text,
            'channel': channel or self.slack.channel,
            'icon_emoji': icon_emoji or self.slack.icon_emoji,
            'username': username or self.slack.username
        }
        for k, v in data.items():
            if not v:
                raise ValueError('invalid {key}: {value}'.format(
                    key=k,
                    value=v
                ))
        webhook_url = webhook_url or self.slack.webhook_url
        if not webhook_url:
            raise ValueError('webhook_url is required')
        resp = requests.post(
            webhook_url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data))
        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        return True
