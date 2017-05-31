# core ---------------------------------------------------------------------
import logging
import json
import sys
from math import floor, ceil
from decimal import Decimal
from operator import itemgetter
from time import time, gmtime, strftime, strptime, localtime, mktime, sleep
from calendar import timegm
from multiprocessing import Process
from multiprocessing.dummy import Process as Thread
try:
    from html.parser import HTMLParser
except:
    from HTMLParser import HTMLParser
html = HTMLParser()

# 3rd party ----------------------------------------------------------------
# pip install pandas numpy
import pandas as pd
import numpy as np
# pip install pymongo
from pymongo import MongoClient

# local --------------------------------------------------------------------
from . import indicators as indica
from .poloniex import Poloniex, Coach, PoloniexError
from .poloniex.push import Application
from .daemon import DaemonContext

# constants ----------------------------------------------------------------

# tools logger
logger = logging.getLogger(__name__)

PHI = (1 + 5 ** 0.5) / 2

# smallest coin fraction
SATOSHI = 0.00000001
# smallest loan fraction
LOANTOSHI = 0.000001
# minimum trade amount (btc and usdt)
TRADE_MIN = 0.0001
# scraped from trollbox js var mods (5/8/2017)
TROLL_MODS = {
    "Xoblort": 1,
    "Chickenliver": 1,
    "MobyDick": 1,
    "cybiko123": 1,
    "SweetJohnDee": 1,
    "smallbit": 1,
    "Wizwa": 1,
    "OldManKidd": 1,
    "Quantum": 1,
    "Popcorntime": 1,
    "busoni@poloniex": 1,
    "Thoth": 1,
    "wausboot": 1,
    "Mirai": 1,
    "qubix": 1,
    "Oldgamejunk": 1,
    "Chewpacabra": 1,
    "orio": 1,
    "j33hopper": 1,
    "VenomGhost": 1,
    "ultim8um": 1,
    "TheDjentleman": 1,
    "GambitKnight": 1,
    "Bigolas": 1,
    "Watchtower": 1
}
# Our name in the trollbox
TROLL_NAME = 'PulloutKing'

# console colors
WT = '\033[0m'  # white (normal)
RD = lambda text: '\033[31m' + text + WT  # red
GR = lambda text: '\033[32m' + text + WT  # green
OR = lambda text: '\033[33m' + text + WT  # orange
BL = lambda text: '\033[34m' + text + WT  # blue
PR = lambda text: '\033[35m' + text + WT  # purp
CY = lambda text: '\033[36m' + text + WT  # cyan
GY = lambda text: '\033[37m' + text + WT  # gray


# convertions, misc ------------------------------------------------------
def getMongoDb(db, coll):
    return MongoClient()[db][coll]


def wait(i=10):
    """ wraps 'time.sleep()' with logger output"""
    logger.debug('Waiting %d sec...', i)
    sleep(i)


def addPercent(n, p):
    """ (n * p) + n
    >>> addPercent(8, 0.5)
    8.04
    """
    return (n * percent2float(p)) + n


def float2percent(n):
    return float(n) * 100


def percent2float(n):
    return float(n) / 100


def roundDown(n, d=8):
    """
    n :: float to be rounded
    d :: int munber of decimals to round to
    """
    d = int('1' + ('0' * d))
    return floor(n * d) / d


def roundUp(n, d=8):
    """
    n :: float to be rounded
    d :: int munber of decimals to round to
    """
    d = int('1' + ('0' * d))
    return ceil(n * d) / d


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


def saveJSON(data, filename):
    """ Save data as json to a file """
    with open(filename, 'w') as f:
        return json.dump(data, f, indent=4)


def loadJSON(filename):
    """ Load json file """
    with open(filename, 'r') as f:
        return json.load(f)


def restart_line():
    sys.stdout.write('\r')
    sys.stdout.flush()
# trading ------------------------------------------------------------------


def getAverage(seq):
    """
    Finds the average of <seq>
    >>> getAverage(['3', 9.4, '0.8888', 5, 1.344444, '3', '5', 6, '7'])
    4.033320571428571
    """
    return sum(seq) / len(seq)


def geoProgress(n, r=PHI, size=5):
    """ Creates a Geometric Progression with the Geometric sum of <n>
    >>> geoProgress(42)
    [2.5725461188664465, 4.162467057952537, 6.735013176818984, 10.897480234771521, 17.63249341159051]
    >>> r = geoProgress(42)
    >>> r
    [2.5725461188664465, 4.162467057952537, 6.735013176818984, 10.897480234771521, 17.63249341159051]
    >>> sum(r)
    42.0
    """
    return [(n * (1 - r) / (1 - r ** size)) * r ** i for i in range(size)]


def cancelAllOrders(api, market='all', arg=False):
    """ Cancels all orders for a market or all markets. Can be limited to just
    buy or sell orders using the 'arg' param """

    orders = api.returnOpenOrders(market)

    if market == 'all':
        for market in orders:
            for order in orders[market]:
                if arg in ('sell', 'buy') and o['type'] != arg:
                    continue
                logger.debug(api.cancelOrder(order["orderNumber"]))
        return True

    for order in orders:
        if arg in ('sell', 'buy') and order['type'] != arg:
            continue
        logger.debug(api.cancelOrder(order["orderNumber"]))
    return True


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
            logger.info('Toggling autorenew for offer %s', loan['id'])
            api.toggleAutoRenew(loan['id'])


def frontSell(api, market, amount=False):
    """ Creates a sell order for <market> using all coins in balance at
    the 'front' of market. Keeps pushing the order to 'front' until the order
    is filled. """
    parentCoin, childCoin = market.split('_')
    if not amount:
        amount = getAvailCoin(api, childCoin)
    price = getFront(api, market, 'sell')
    if amount * sellPrice < TRADE_MIN:
        return 'Total %s is below TRADE_MIN: %s.' % (str(amount), str(TRADE_MIN))
    # create sell order
    initOrder = api.sell(market, price, amount, orderType='postOnly')
    orderNums = [int(initOrder['orderNumber'])]
    while 1:
        for order in api.returnOpenOrders(market):
            if int(order['orderNumber']) != int(orderNums[-1]):
                continue
            logger.debug(order)
            price = getFront(api, market, 'sell')
            if float(order['rate']) > price:
                logger.debug('Moving %s order %s', market, orderNums[-1])
                norder = api.moveOrder(
                    orderNums[-1], price, orderType='postOnly')
                if 'success' in norder and int(norder['success']) == 1:
                    orderNums.append(int(norder['orderNumber']))
                else:
                    logger.error(norder)
                    break
            wait()
            break
        else:
            return orderNums


def frontBuy(api, market, allowance=TRADE_MIN + SATOSHI):
    """ Creates a buy order for <market> using <allowance> as the
    amount and the 'front' of market as the bid rate. Keeps pushing the
    order to 'front' until the order is filled. returns a list of ordernumbers
    """
    logger.info('Creating "front buy" order in %s', market)
    parentCoin, childCoin = market.split('_')
    if getAvailCoin(api, parentCoin) < allowance or allowance < TRADE_MIN:
        return "%s balance or allowance too low!" % parentCoin
    # get 'front'
    price = getFront(api, market, 'buy')
    # amount is in child coins so we need to do the math...
    amount = roundUp(allowance / price)
    # create buy order
    orderNums = [int(
        api.buy(market, price, amount, orderType='postOnly')['orderNumber']
    )]
    while 1:
        for order in api.returnOpenOrders(market):
            if int(order['orderNumber']) != int(orderNums[-1]):
                continue
            logger.debug(order)
            price = getFront(api, market, 'buy')
            if float(order['rate']) < price:
                logger.debug('Moving %s order %s', market, orderNums[-1])
                norder = api.moveOrder(
                    orderNums[-1], price, orderType='postOnly')
                if 'success' in norder and int(norder['success']) == 1:
                    orderNums.append(int(norder['orderNumber']))
                else:
                    logger.error(norder)
                    break
            wait()
            break
        else:
            return orderNums


def checkOrderTrades(api, orderNumber):
    """ Returns False if no trades (or bad order) or returns the trades """
    logger.info('Checking order %s for trades', str(orderNumber))
    try:
        result = api.returnOrderTrades(orderNumber)
        return result
    # no trades yet
    except PoloniexError:
        return False


def getFront(api, market, arg):
    """ Gets 'front' of market and adds/subtracts 1 SATOSHI, if front+SATOSHI
    fills an order, match the front """
    tick = api.returnTicker()[market]
    hbid = float(tick['highestBid'])
    lask = float(tick['lowestAsk'])
    if arg is 'buy':
        if hbid + SATOSHI == lask:
            return hbid
        return hbid + SATOSHI
    if arg is 'sell':
        if lask - SATOSHI == hbid:
            return lask
        return lask - SATOSHI


def getAvailCoin(api, coin):
    """ Returns available <coin> in exchange account """
    bals = api.returnAvailableAccountBalances('exchange')['exchange']
    logger.debug(bals)
    if not coin in bals:
        return 0.0
    return float(bals[coin])


def getLastPoss(api, market, otype, span=5):
    hist = api.returnTradeHistory(market, start=api.DAY * 20)
    rates = []
    for trade in hist:
        if trade['category'] != 'exchange' or trade['type'] != otype:
            continue
        rates.append(float(trade['rate']))
        if len(rates) == span:
            break
    return sum(rates) / len(rates)
