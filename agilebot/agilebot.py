__author__ = 'ntrepid8'
import requests
from requests_oauthlib import OAuth1
import logging
from logging import NullHandler
import collections
from collections import namedtuple
import json
from fnmatch import fnmatch
from datetime import date
from agilebot import util
logger = logging.getLogger('agilebot.lib')
logger.addHandler(NullHandler())
TRELLO_API_BASE_URL = 'https://api.trello.com/1'


class AgileBot(object):

    def __init__(self, **kwargs):

        self.default_conf = {
            'agile': {
                'backlogs': [],
                'sprint_lists': ['To Do', 'In Progress', 'Completed', 'Deployed']
            },
            'logging': {
                'level': 'INFO'
            },
            'slack': {
                'webhook_url': None,
                'channel': None,
                'icon_emoji': ':ghost:',
                'username': 'agilebot'
            },
            'trello': {
                'api_key': None,
                'api_secret': None,
                'oauth_token': None,
                'oauth_secret': None,
                'organization_id': None
            },
        }

        self.conf = self.left_merge(self.default_conf, kwargs)

        # agile
        self.agile = self.gen_namedtuple('Agile', self.conf['agile'])
        self._boards = None

        # trello
        self.trello = self.gen_namedtuple('Trello', self.conf['trello'], dict(
            session=requests.Session()
        ))
        self.trello.session.auth = OAuth1(
            client_key=self.trello.api_key,
            client_secret=self.trello.api_secret,
            resource_owner_key=self.trello.oauth_token,
            resource_owner_secret=self.trello.oauth_secret)
        self.trello.session.headers['Accept'] = 'application/json'

        # slack
        self.slack = self.gen_namedtuple('Slack', self.conf['slack'])

    def left_merge(self, left, right):
        """ Update values in the left dictionary from the values in the right dictionary, if they exist.
        Another way to phrase it would be:

        - copy `left` as a new dictionary called `d`
        - recursively update `d` with the intersection of right & left

        :param left: starting dictionary
        :type left: dict
        :param right: dictionary to be intersected and merged
        :type right: dict
        :return: copy of left, merged with the recursive intersection of left & right
        :rtype: dict
        """
        new_left = {}
        for k, v in left.items():
            if isinstance(v, collections.Mapping):
                new_left[k] = self.left_merge(left[k], right.get(k, {}))
            else:
                new_left[k] = right.get(k, left[k])
        return new_left

    def gen_namedtuple(self, name, *param_dicts):
        nt_param_dict = {}
        for pd in param_dicts:
            nt_param_dict.update(pd)
        nt_class = namedtuple(name, ', '.join(k for k in nt_param_dict.keys()))
        return nt_class(**nt_param_dict)

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
        # build URL
        url = [TRELLO_API_BASE_URL, '/members/me/boards']

        # query_params
        query_params = query_params or {}

        # query_params.filter
        filter_params = filter_params or []
        filter_params.append('open')  # default to only "open" boards
        if filter_params:
            query_params['filter'] = ','.join(filter_params)

        # fetch lists along with board or not
        if include_lists is False and include_cards is True:
            raise ValueError('include_lists must be True if include_cards is True')
        if include_lists is True:
            query_params['lists'] = 'open'

        # fetch the boards from trello
        resp = self.trello.session.get(''.join(url), params=query_params)
        self.log_http(resp)

        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        resp_json = resp.json()

        # filter by organization_id
        if organization_id:
            logger.debug('filter by organization_id: {}'.format(organization_id))
            resp_json = [i for i in resp_json if i['idOrganization'] == organization_id]
        else:
            logger.debug('filter any boards with an organization_id')
            resp_json = [i for i in resp_json if not i['idOrganization']]

        # filter by name
        if name:
            logger.debug('filter by name: {}'.format(name))
            resp_json = [i for i in resp_json if fnmatch(i['name'], name)]

        # fetch cards along with lists
        if include_cards is True:
            for i in resp_json:
                self.add_cards_to_board(i)

        # all done!
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

        # render the name
        sprint_name = self.format_sprint_name(name or 'Sprint {iso_year}.{iso_week}')

        # check for duplicate names
        duplicates = self.find_boards(name=sprint_name, organization_id=organization_id)
        if duplicates:
            raise ValueError('duplicate board name: "{}"'.format(sprint_name))

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
            'username': username or self.slack.username,
            'link_names': 1
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
