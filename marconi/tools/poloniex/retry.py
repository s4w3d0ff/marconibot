# http://code.activestate.com/recipes/580745-retry-decorator-in-python/
from itertools import chain
from time import sleep
import logging
logger = logging.getLogger(__name__)


class RetryExhausted(Exception):
    pass


def retry(delays=(0, 1, 2, 3, 4, 5), exception=Exception):
    def wrapper(function):
        def wrapped(*args, **kwargs):
            for delay in chain(delays, [None]):
                try:
                    return function(*args, **kwargs)
                except exception as problem:
                    logger.debug(problem)
                    if delay is None:
                        raise RetryExhausted('Could not execute')
                    logger.debug(problem)
                    logger.info(" -- delaying for %ds", delay)
                    sleep(delay)
        return wrapped
    return wrapper
