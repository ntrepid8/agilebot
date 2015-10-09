__author__ = 'ntrepid8'
from collections import namedtuple, Mapping
import os
import requests
import calendar
import time
import sys
from agilebot import agilebot
DUMP_PATH = '/tmp/agilebot_dumps'


def log_request_response(resp, logger):
    if resp.status_code != requests.codes.ok:
        if not os.path.exists(DUMP_PATH):
            os.makedirs(DUMP_PATH)
        dp_kwargs = dict(dump_path=DUMP_PATH, code=resp.status_code, time_stamp=calendar.timegm(time.gmtime()))
        with open('{dump_path}/{method}_{code}_{time_stamp}.log'.format(**dp_kwargs), 'w') as f:
            f.write(vars(resp))
    # TODO - sometimes 'method' is not available, handle this condition
    logger.debug('{method} {code} {url}'.format(
        method=resp.request.method,
        code=resp.status_code,
        url=resp.request.url
    ))


def gen_namedtuple(name, *param_dicts):
        nt_param_dict = {}
        for pd in param_dicts:
            nt_param_dict.update(pd)
        nt_class = namedtuple(name, ', '.join(k for k in nt_param_dict.keys()))
        return nt_class(**nt_param_dict)


def left_merge(left, right):
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
            if isinstance(v, Mapping):
                new_left[k] = left_merge(left[k], right.get(k, {}))
            else:
                new_left[k] = right.get(k) or left[k]
        return new_left


def get_first_value(*args):
    return next((i for i in args if i is not None), None)


def update_config_group(group_name, args, conf):
    for k, v in conf[group_name].items():
        val = getattr(args, k, None)
        if val is not None:
            conf[group_name][k] = val
    return conf


def create_bot(conf, logger):
    try:
        bot = agilebot.AgileBot(**conf)
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    else:
        logger.debug('AgileBot created successfully')

    return bot
