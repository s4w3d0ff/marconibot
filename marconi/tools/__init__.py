import logging
from operator import itemgetter
from time import time, gmtime, strftime, strptime, localtime, mktime, sleep
from calendar import timegm
from multiprocessing import Process
try:
    from html.parser import HTMLParser
except:
    from HTMLParser import HTMLParser
# 3rd party ----------------------------------------------------------------
# - pip install pymongo
from pymongo import MongoClient
# - https://github.com/s4w3d0ff/trade_indica
import trade_indica as indica

# constants ----------------------------------------------------------------
# tools.logger
logger = logging.getLogger(__name__)

PHI = (1 + 5 ** 0.5) / 2

# convertions --------------------------------------------------------------


def epoch2UTCstr(timestamp=False, fmat="%Y-%m-%d %H:%M:%S"):
    """
    - takes epoch timestamp
    - returns UTC formated string
    """
    if not timestamp:
        timestamp = time()
    return strftime(fmat, gmtime(timestamp))


def UTCstr2epoch(datestr=False, fmat="%Y-%m-%d %H:%M:%S"):
    """
    - takes UTC date string
    - returns epoch
    """
    if not datestr:
        datestr = epoch2UTCstr()
    return timegm(strptime(datestr, fmat))


def epoch2localstr(timestamp=False, fmat="%Y-%m-%d %H:%M:%S"):
    """
    - takes epoch timestamp
    - returns localtimezone formated string
    """
    if not timestamp:
        timestamp = time()
    return strftime(fmat, localtime(timestamp))


def localstr2epoch(datestr=False, fmat="%Y-%m-%d %H:%M:%S"):
    """
    - takes localtimezone date string,
    - returns epoch
    """
    if not datestr:
        datestr = epoch2localstr()
    return mktime(strptime(datestr, fmat))


def float2roundPercent(floatN, decimalP=2):
    """
    - takes float
    - returns percent(*100) rounded to the Nth decimal place as a string
    """
    return str(round(float(floatN) * 100, decimalP)) + "%"
