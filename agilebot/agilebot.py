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
import os
logger = logging.getLogger('agilebot.lib')
logger.addHandler(NullHandler())
TRELLO_API_BASE_URL = 'https://api.trello.com/1'
DEFAULT_SPRINT_NAME_TPL = 'Sprint {iso_year}.{iso_week}'


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
        # Agilebot environment variables
        ab_base_path = os.environ.get(
            'AB_BASE_PATH',
            '~/.agilebot.d'
        )
        ab_base_path = os.path.expanduser(ab_base_path)
        ab_active_sprint_path = os.environ.get(
            'AB_ACTIVE_SPRINT_PATH',
            '{base_path}/sprint_active.json'.format(
                base_path=ab_base_path)
        )
        ab_closing_sprint_path = os.environ.get(
            'AB_CLOSING_SPRINT_PATH',
            '{base_path}/sprint_closing.json'.format(
                base_path=ab_base_path)
        )

        return {
            'agile': {
                'backlogs': [],
                'sprint_lists': ['To Do', 'In Progress', 'Completed', 'Deployed'],
                'sprint_lists_forward': ['To Do', 'In Progress']
            },
            'logging': {
                'level': 'INFO'
            },
            'sprint': {
                'name_tpl': DEFAULT_SPRINT_NAME_TPL,
                'active_sprint_path': ab_active_sprint_path,
                'closing_sprint_path': ab_closing_sprint_path,
            },
            'slack': SlackBot.default_conf(),
            'trello': TrelloBot.default_conf(),
        }

    def log_http(self, resp):
        util.log_request_response(resp, logger)

    def format_sprint_name(self, sprint_name=None, iso_year=None, iso_week=None):
        sprint_name = sprint_name or DEFAULT_SPRINT_NAME_TPL
        iso_date = date.today().isocalendar()
        sn_kwargs = dict(
            iso_year=iso_year or iso_date[0],
            iso_week=iso_week or iso_date[1]
        )
        return sprint_name.format(**sn_kwargs)

    def get_active_sprint(self):
        if not os.path.exists(self.conf['sprint']['active_sprint_path']):
            raise ValueError('active sprint not found at: {}'.format(self.conf['sprint']['active_sprint_path']))
        with open(self.conf['sprint']['active_sprint_path']) as f:
            active_sprint = json.load(f)

        # update the trello board
        active_sprint['trello_board'] = self.trello.get_board(active_sprint['trello_board']['id'])
        return active_sprint

    def get_closing_sprint(self):
        if not os.path.exists(self.conf['sprint']['closing_sprint_path']):
            raise ValueError('closing sprint not found at: {}'.format(self.conf['sprint']['closing_sprint_path']))
        with open(self.conf['sprint']['closing_sprint_path']) as f:
            closing_sprint = json.load(f)

        # update the trello board
        closing_sprint['trello_board'] = self.trello.get_board(closing_sprint['trello_board']['id'])
        return closing_sprint

    def start_new_sprint(self,
                         sprint_name=None,
                         sprint_list_names=None,
                         organization_id=None,
                         close_active_sprint=True,
                         closing_sprint_name=None):
        #
        # create a new sprint
        new_sprint = {
            'name': self.format_sprint_name(sprint_name or DEFAULT_SPRINT_NAME_TPL),
            'lists': sprint_list_names or self.agile.sprint_lists,
            'trello_board': None
        }

        # mark the new sprint as the active sprint
        if 'active' not in new_sprint['name']:
            new_sprint['name'] += ' (active)'

        # load the currently active sprint (to become the closing sprint)
        if close_active_sprint is True:
            if os.path.exists(self.conf['sprint']['active_sprint_path']):
                with open(self.conf['sprint']['active_sprint_path']) as f:
                    closing_sprint = json.load(f)
                closing_sprint['trello_board'] = self.trello.get_board(closing_sprint['trello_board']['id'])
            else:
                closing_sprint = None
        elif closing_sprint_name is not None:
            resp = self.trello.find_boards(board_name=closing_sprint_name, organization_id=organization_id)
            if len(resp) == 0:
                raise ValueError('nothing migrated: closing_sprint_name not found: {}'.format(closing_sprint_name))
            elif len(resp) > 1:
                raise ValueError('nothing migrated: ambiguous closing_sprint_name: {}, found {} boards matching'.format(
                    closing_sprint_name, len(resp)
                ))
            else:
                closing_sprint_board = resp[0]
                closing_sprint = {
                    'name': closing_sprint_board['name'],
                    'lists': [l['name'] for l in closing_sprint_board['lists']],
                    'trello_board': closing_sprint_board
                }
        else:
            closing_sprint = None

        # compute members
        if closing_sprint and closing_sprint.get('trello_board'):
            members = closing_sprint['trello_board'].get('members') or []
        else:
            members = []

        # create a trello board for the sprint
        try:
            trello_board = self.trello.create_board(
                board_name=new_sprint['name'],
                list_names=new_sprint['lists'],
                organization_id=organization_id,
                members=members
            )
        except Exception as e:
            logger.debug('while running trello.create_board agilebot.create_sprint caught: {}({})'.format(
                type(e).__name__, e
            ))
            raise e
        else:
            new_sprint['trello_board'] = trello_board
        logger.debug('created new sprint board: {}'.format(trello_board['name']))

        # update the name of the closing sprint
        if closing_sprint is not None:
            csn = closing_sprint['name']
            if 'active' in csn:
                csn = csn.replace('active', 'closing')
            if 'closing' not in csn:
                csn += ' (closing)'
            closing_sprint_board = self.trello.update_board(
                board_id=closing_sprint['trello_board']['id'],
                data={'name': csn}
            )
            logger.debug('updated closing sprint name to: {}'.format(closing_sprint_board['name']))

            # save the old (closing) sprint
            closing_sprint = {
                'name': csn,
                'lists': [l['name'] for l in closing_sprint_board['lists']],
                'trello_board': closing_sprint_board
            }
            with open(self.conf['sprint']['closing_sprint_path'], 'w') as f:
                json.dump(closing_sprint, f, indent=4, sort_keys=True)

        # save the new (active) sprint
        with open(self.conf['sprint']['active_sprint_path'], 'w') as f:
            json.dump(new_sprint, f, indent=4, sort_keys=True)

        # if not migrating from a sprint that is closing, we are all done
        if closing_sprint is None:
            return new_sprint

        #
        # migrate from the closing sprint

        # lists to forward
        closing_lists = closing_sprint['trello_board']['lists']
        lists_forward = [l for l in closing_lists if l['name'] in self.agile.sprint_lists_forward]
        lists_forward = {l['id']: l for l in lists_forward}
        lists_forward_targets = {l['name']: l for l in new_sprint['trello_board']['lists']}

        # migrate cards
        migrated_cards = []
        for c in closing_sprint['trello_board']['cards']:
            if c['idList'] in lists_forward:
                old_list_id = c['idList']
                list_name = lists_forward[old_list_id]['name']
                new_list_id = lists_forward_targets[list_name]['id']
                update_c = {
                    'idList': new_list_id,
                    'idBoard': new_sprint['trello_board']['id']
                }
                updated_c = self.trello.update_card(c['id'], update_c)
                migrated_cards.append(updated_c)
        logger.debug('migrated cards: {}'.format(len(migrated_cards)))

        # get the updated trello board
        new_sprint['trello_board'] = self.trello.get_board(new_sprint['trello_board']['id'])

        # save the new sprint (since we may have added cards)
        with open(self.conf['sprint']['active_sprint_path'], 'w') as f:
            json.dump(new_sprint, f, indent=4, sort_keys=True)

        # log it
        logger.info('successfully started new sprint: {}'.format(new_sprint['trello_board']['name']))

        # all done!
        return new_sprint
