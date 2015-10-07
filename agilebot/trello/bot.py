__author__ = 'ntrepid8'
from requests_oauthlib import OAuth1
import requests
from agilebot import util
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

    def get_board(self, board_id, lists=None, cards=None):

        lists = lists or 'open'
        cards = cards or 'open'

        resp = self.session.get(
            '{base_url}/boards/{board_id}'.format(base_url=TRELLO_API_BASE_URL, board_id=board_id),
            params={
                'lists': lists,
                'cards': cards
            }
        )

        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        board = resp.json()
        return board
