__author__ = 'ntrepid8'


def log_request_response(resp, logger):
    logger.debug('{method} {code} {url}'.format(
        method=resp.request.method,
        code=resp.status_code,
        url=resp.request.url
    ))
