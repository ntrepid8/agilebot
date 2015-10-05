__author__ = 'ntrepid8'
from collections import namedtuple
from requests_oauthlib import OAuth1
import requests
from agilebot import util


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
