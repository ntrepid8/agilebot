__author__ = 'ntrepid8'
from collections import namedtuple, Mapping


def log_request_response(resp, logger):
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
                new_left[k] = right.get(k, left[k])
        return new_left
