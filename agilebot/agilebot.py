__author__ = 'ntrepid8'
import requests
from requests_oauthlib import OAuth1
import logging
from logging import NullHandler
from collections import namedtuple
import json
from fnmatch import fnmatch
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

    def find_boards(self,
                    filter_params=None,
                    organization_id=None,
                    name=None,
                    query_params=None,
                    include_lists=False,
                    include_cards=False):
        url = [TRELLO_API_BASE_URL, '/members/me/boards']
        query_params = query_params or {}
        if filter_params:
            query_params['filter'] = ','.join(filter_params)
        if include_lists is False and include_cards is True:
            raise ValueError('include_lists must be True if include_cards is True')
        if include_lists is True:
            query_params['lists'] = 'open'
        resp = self.trello.session.get(''.join(url), params=query_params)
        logger.debug('{method} {code} {url}'.format(
            method=resp.request.method,
            code=resp.status_code,
            url=resp.request.url
        ))
        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        resp_json = resp.json()
        if organization_id:
            logger.debug('filter by organization_id: {}'.format(organization_id))
            resp_json = [i for i in resp_json if i['idOrganization'] == organization_id]
        else:
            logger.debug('filter any boards with an organization_id')
            resp_json = [i for i in resp_json if not i['idOrganization']]
        if name:
            logger.debug('filter by name: {}'.format(name))
            resp_json = [i for i in resp_json if fnmatch(i['name'], name)]
        if include_cards is True:
            for i in resp_json:
                self.add_cards_to_board(i)
        return resp_json

    def add_cards_to_board(self, board):
        cards = self.find_cards(board['id'])
        for c in cards:
            for l in board['lists']:
                if l['id'] != c['idList']:
                    continue
                if 'cards' not in l:
                    l['cards'] = []
                l['cards'].append(c)
        return board

    def find_cards(self, board_id):
        url = [TRELLO_API_BASE_URL, '/boards/{board_id}/cards'.format(board_id=board_id)]
        resp = self.trello.session.get(''.join(url))
        logger.debug('{method} {code} {url}'.format(
            method=resp.request.method,
            code=resp.status_code,
            url=resp.request.url
        ))
        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        resp_json = resp.json()
        return resp_json

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
        return {'success': True}
