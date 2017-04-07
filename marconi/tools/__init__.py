# core ---------------------------------------------------------------------
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
# - https://github.com/s4w3d0ff/python-poloniex
from poloniex import Poloniex, Coach
# pip install daemon
from daemon import Daemon

# constants ----------------------------------------------------------------

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

# trading ------------------------------------------------------------------


def getTrend(seq):
    """
    Basic trend calculation by splitting the <seq> data in half, find the
    mean of each half, then subtract the old half from the new half. A
    negitive number represents a down trend, positive number is an up trend.
    >>> trend([1.563, 2.129, 3.213, 4.3425, 5.1986, 5.875644])
    2.866122
    """
    half = len(seq) // 2
    return average(seq[half:]) - average(seq[:-half])


def getAverage(seq):
    """
    Finds the average of <seq>
    >>> average(['3', 9.4, '0.8888', 5, 1.344444, '3', '5', 6, '7'])
    4.033320571428571
    """
    return sum(seq) / len(seq)


def geoProgress(n, r=PHI, size=5):
    """ Creates a Geometric Progression with the Geometric sum of <n> """
    return [(n * (1 - r) / (1 - r ** size)) * r ** i for i in range(size)]


def cancelAllOrders(api, market, arg=False):
    """ Cancels all orders for a market. Can be limited to just buy or sell
        orders using the 'arg' param """
    orders = api.returnOpenOrders(market)
    if market == 'all':
        nOrders = []
        for market in orders:
            for order in orders[market]:
                nOrders.append(order)
        orders = nOrders

    # cancel just buy or sell
    if arg in ('sell', 'buy')
        for o in orders:
            if o['type'] == arg:
                logger.info(api.cancelOrder(o["orderNumber"]))
    # cancel all
    else:
        for o in orders:
            logger.info(api.cancelOrder(o["orderNumber"]))


def cancelAllLoanOffers(api, coin=False):
    """ Cancels all open loan offers, for all coins or a single <coin> """
    loanOrders = api.returnOpenLoanOffers()
    if not coin:
        for c in loanOrders:
            for order in loanOrders[c]:
                logger.info(api.cancelLoanOffer(order['id']))
    else:
        for order in loanOrders[coin]:
            logger.info(api.cancelLoanOffer(order['id']))


def closeAllMargins(api):
    """ Closes all margin positions """
    for m in api.returnTradableBalances():
        logger.info(api.closeMarginPosition(m))


def autoRenewAll(api, toggle=True):
    """ Turns auto-renew on or off for all active loans """
    if toggle:
        toggle = 1
    else:
        toggle = 0
    for loan in api.returnActiveLoans()['provided']:
        if int(loan['autoRenew']) != toggle:
            api.toggleAutoRenew(loan['id'])
