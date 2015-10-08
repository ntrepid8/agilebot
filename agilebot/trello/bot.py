__author__ = 'ntrepid8'
from requests_oauthlib import OAuth1
import requests
from agilebot import util
import logging
from logging import NullHandler
from fnmatch import fnmatch
import json
logger = logging.getLogger('agilebot.lib.trello')
logger.addHandler(NullHandler())
TRELLO_API_BASE_URL = 'https://api.trello.com/1'


class TrelloBot(object):

    def __init__(self, conf=None):
        self.conf = util.gen_namedtuple('Trello', self.default_conf(), conf or {})
        self.session = requests.session()
        self.session.headers['Accept'] = 'application/json'

        self.session.auth = OAuth1(
            client_key=self.conf.api_key,
            client_secret=self.conf.api_secret,
            resource_owner_key=self.conf.oauth_token,
            resource_owner_secret=self.conf.oauth_secret)
        
    @classmethod
    def default_conf(cls):
        return {
            'api_key': None,
            'api_secret': None,
            'oauth_token': None,
            'oauth_secret': None,
            'organization_id': None
        }

    @classmethod
    def required_conf(cls):
        return [
            'api_key',
            'api_secret',
            'oauth_token',
            'oauth_secret'
        ]

    def check_required_conf(self, **kwargs):
        # ensure we have the required configuration values
        for c in self.required_conf():
            c_ok = any([
                getattr(self.conf, c, None) is not None,
                kwargs.get(c) is not None
            ])
            if not c_ok:
                raise ValueError('{} is required'.format(c))

    def get_board(self, board_id, lists=None, cards=None):

        # ensure we have all the configuration required to make a request
        self.check_required_conf()

        lists = lists or 'open'
        cards = cards or 'open'

        resp = self.session.get(
            '{base_url}/boards/{board_id}'.format(base_url=TRELLO_API_BASE_URL, board_id=board_id),
            params={
                'lists': lists,
                'cards': cards
            }
        )
        util.log_request_response(resp, logger)
        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        board = resp.json()
        return board

    def find_boards(self, board_name=None, lists=None, cards=None, organization_id=None):

        # ensure we have all the configuration required to make a request
        self.check_required_conf()

        # param setup
        p_name = board_name or '*'
        p_filters = ['open']
        p_lists = lists or 'open'
        p_cards = cards or 'open'
        p_organization_id = organization_id or self.conf.organization_id

        resp = self.session.get(
            '{base_url}/members/me/boards'.format(base_url=TRELLO_API_BASE_URL),
            params={
                'lists': p_lists,
                'filter': ', '.join(p_filters)
            }
        )
        util.log_request_response(resp, logger)
        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        boards = resp.json()

        # filter by organization_id
        boards = [b for b in boards if b['idOrganization'] == p_organization_id]

        # filter by name
        boards = [b for b in boards if fnmatch(b['name'], p_name)]

        # deal with cards
        boards = [self.get_board(b['id'], lists=p_lists, cards=p_cards) for b in boards]

        # return the list of boards
        return boards

    def create_board(self, board_name, list_names=None, organization_id=None):

        # validate board name
        if board_name is None:
            raise ValueError('board_name is required')

        # ensure we have all the configuration required to make a request
        self.check_required_conf()

        # param setup
        p_board_name = board_name
        p_organization_id = organization_id or self.conf.organization_id
        p_list_names = list_names or []

        # check for duplicate names among open boards
        dups = self.find_boards(board_name=p_board_name, organization_id=p_organization_id)
        if dups:
            raise ValueError('duplicate board_name: {}'.format(p_board_name))

        # create the board
        req_body = {
            'name': p_board_name
        }
        if p_organization_id:
            req_body['idOrganization'] = p_organization_id
            req_body['prefs_permissionLevel'] = 'org'
        resp = self.session.post(
            '{base_url}/boards'.format(TRELLO_API_BASE_URL),
            headers={'Content-Type': 'application/json'},
            data=json.dumps(req_body)
        )
        util.log_request_response(resp, logger)
        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        board = resp.json()

        # if lists are specified, purge the default lists
        if list_names is not None:
            resp = self.session.get(
                '{base_url}/boards/{board_id}/lists'.format(base_url=TRELLO_API_BASE_URL, board_id=board['id'])
            )
            util.log_request_response(resp, logger)
            if resp.status_code != requests.codes.ok:
                raise ValueError('http error: {}'.format(resp.status_code))
            default_lists = resp.json()
            for l in default_lists:
                resp = self.session.put(
                    '{base_url}/lists/{list_id}/closed'.format(base_url=TRELLO_API_BASE_URL, list_id=l['id']),
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps({'value': True})
                )
                util.log_request_response(resp, logger)
                if resp.status_code != requests.codes.ok:
                    raise ValueError('http error: {}'.format(resp.status_code))

        # add any lists specified
        for i, l in enumerate(p_list_names):
            resp = self.session.post(
                '{base_url}/boards/{board_id}/lists'.format(base_url=TRELLO_API_BASE_URL, board_id=board['id']),
                headers={'Content-Type': 'application/json'},
                data=json.dumps({'name': l, 'pos': i + 1})
            )
            util.log_request_response(resp, logger)
            if resp.status_code != requests.codes.ok:
                raise ValueError('http error: {}'.format(resp.status_code))

        # get the full board
        board = self.get_board(board_id=board['id'])

        # success
        return board

    def close_board(self, board_id):
        # ensure we have all the configuration required to make a request
        self.check_required_conf()

        # close the board
        resp = self.session.put(
            '{base_url}/boards/{board_id}/closed'.format(base_url=TRELLO_API_BASE_URL, board_id=board_id),
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'value': True})
        )
        util.log_request_response(resp, logger)
        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        return resp.json()

