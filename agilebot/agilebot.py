__author__ = 'ntrepid8'
import requests
import logging
from logging import NullHandler
import json
from fnmatch import fnmatch
from datetime import date
from agilebot import util
from agilebot.trello.bot import TrelloBot
from agilebot.slack.bot import SlackBot
logger = logging.getLogger('agilebot.lib')
logger.addHandler(NullHandler())
TRELLO_API_BASE_URL = 'https://api.trello.com/1'


class AgileBot(object):

    def __init__(self, **kwargs):

        self.conf = util.left_merge(self.default_conf(), kwargs)

        # agile
        self.agile = util.gen_namedtuple('Agile', self.conf['agile'])
        self._boards = None

        # trello
        try:
            self.trello = TrelloBot(kwargs.get('trello'))
        except Exception as e:
            raise ValueError('trello {}'.format(e))

        # slack
        self.slack = SlackBot(kwargs.get('slack'))

    @classmethod
    def default_conf(cls):
        return {
            'agile': {
                'backlogs': [],
                'sprint_lists': ['To Do', 'In Progress', 'Completed', 'Deployed']
            },
            'logging': {
                'level': 'INFO'
            },
            'slack': SlackBot.default_conf(),
            'trello': TrelloBot.default_conf(),
        }

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
        # TODO - move this to trello.bot

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
        # TODO - move this to trello.bot

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
        # TODO - move this to trello.bot

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
        # TODO - move this to trello.bot

        # render the name
        sprint_name = self.format_sprint_name(name or 'Sprint {iso_year}.{iso_week}')

        # check for duplicate names
        duplicates = self.find_boards(name=sprint_name, organization_id=organization_id)
        if duplicates:
            raise ValueError('duplicate board name: "{}"'.format(sprint_name))

        # create the sprint board
        board_url = [TRELLO_API_BASE_URL, '/boards']
        board_data = {
            'name': sprint_name
        }
        org_id = organization_id or self.trello.conf.organization_id
        if org_id:
            board_data['idOrganization'] = org_id
            board_data['prefs_permissionLevel'] = 'org'
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

