__author__ = 'ntrepid8'
import requests
from requests_oauthlib import OAuth1
import logging
from logging import NullHandler
logger = logging.getLogger('agilebot.lib')
logger.addHandler(NullHandler())
TRELLO_API_BASE_URL = 'https://api.trello.com/1'


class AgileBot(object):

    def __init__(self,
                 trello_api_key,
                 trello_api_secret,
                 trello_oauth_token,
                 trello_oauth_secret,
                 trello_organization_id=None):
        self._boards = None
        self.trello_oauth = OAuth1(
            client_key=trello_api_key,
            client_secret=trello_api_secret,
            resource_owner_key=trello_oauth_token,
            resource_owner_secret=trello_oauth_secret)
        self.trello_session = requests.session()
        self.trello_session.auth = self.trello_oauth
        self.trello_session.headers['Accept'] = 'application/json'
        self.trello_organization_id = trello_organization_id

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
        resp = self.trello_session.get(''.join(url), params=query_params)
        logger.debug('{method} {code} {url}'.format(
            method=resp.request.method,
            code=resp.status_code,
            url=resp.request.url
        ))
        if resp.status_code != requests.codes.ok:
            raise ValueError('http error: {}'.format(resp.status_code))
        return resp.json()
