__author__ = 'ntrepid8'
import requests
from requests_oauthlib import OAuth1
import logging
from logging import NullHandler
from collections import namedtuple
import json
from fnmatch import fnmatch
from datetime import date
from agilebot import util
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
                 slack_username=None,
                 agile_sprint_lists=None):

        # agile
        agile_conf_class = namedtuple('AgileConf', 'sprint_lists')
        self.agile = agile_conf_class(
            sprint_lists=agile_sprint_lists
        )
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

    def log_http(self, resp):
        util.log_request_response(resp, logger)

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
        self.log_http(resp)

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
        self.log_http(resp)

        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        resp_json = resp.json()
        return resp_json

    def format_sprint_name(self, sprint_name, iso_year=None, iso_week=None):
        iso_date = date.today().isocalendar()
        sn_kwargs = dict(
            iso_year=iso_year or iso_date[0],
            iso_week=iso_week or iso_date[1]
        )
        return sprint_name.format(**sn_kwargs)

    def create_sprint(self, name=None, sprint_list_names=None, organization_id=None):

        # create the board
        sprint_name = self.format_sprint_name(name or 'Sprint {iso_year}.{iso_week}')
        board_url = [TRELLO_API_BASE_URL, '/boards']
        board_data = {
            'name': sprint_name
        }
        org_id = organization_id or self.trello.organization_id
        if org_id:
            board_data['idOrganization'] = org_id
        board_resp = self.trello.session.post(
            ''.join(board_url),
            headers={'Content-Type': 'application/json'},
            data=json.dumps(board_data)
        )
        self.log_http(board_resp)

        if board_resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(board_resp.status_code))
        board_json = board_resp.json()

        # close the default lists
        default_lists_resp = self.trello.session.get(
            ''.join([TRELLO_API_BASE_URL, '/boards/{board_id}/lists'.format(board_id=board_json['id'])])
        )

        self.log_http(default_lists_resp)
        if default_lists_resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(default_lists_resp.status_code))
        for l in default_lists_resp.json():
            l_resp = self.trello.session.put(
                ''.join([TRELLO_API_BASE_URL, '/lists/{list_id}/closed'.format(list_id=l['id'])]),
                headers={'Content-Type': 'application/json'},
                data=json.dumps({'value': True})
            )
            self.log_http(l_resp)

        # add the lists
        lists_url = [TRELLO_API_BASE_URL, '/boards/{board_id}/lists'.format(board_id=board_json['id'])]
        sprint_list_names = sprint_list_names or self.agile.sprint_lists
        sprint_list_resps = []
        for index, sln in enumerate(sprint_list_names):
            sprint_list_resps.append(self.trello.session.post(
                ''.join(lists_url),
                headers={'Content-Type': 'application/json'},
                data=json.dumps({
                    'name': sln,
                    'pos': index + 1
                })
            ))
            self.log_http(sprint_list_resps[-1])

        return {'success': True, 'id': board_json['id'], 'name': board_json['name']}

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
