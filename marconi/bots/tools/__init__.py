# core ---------------------------------------------------------------------
import logging
from math import floor, ceil
#from decimal import Decimal
from operator import itemgetter
from itertools import izip
from time import time, gmtime, strftime, strptime, localtime, mktime, sleep
from calendar import timegm
from multiprocessing import Process
from multiprocessing.dummy import Process as Thread
try:
    from html.parser import HTMLParser
except:
    from HTMLParser import HTMLParser
# 3rd party ----------------------------------------------------------------
# pip install autobahn[twisted]
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
# - pip install pymongo
from pymongo import MongoClient
# - https://github.com/s4w3d0ff/trade_indica
import trade_indica as indica
# - https://github.com/s4w3d0ff/python-poloniex
from poloniex import Poloniex, Coach, PoloniexError

# constants ----------------------------------------------------------------

logger = logging.getLogger(__name__)

PHI = (1 + 5 ** 0.5) / 2
# smallest coin fraction
satoshi = 0.00000001
# smallest loan fraction
loantoshi = 0.000001
# minimum trade amount (btc and usdt)
tradeMin = 0.0001


# convertions, misc ------------------------------------------------------


def wait(i=10):
    logger.debug('Waiting %d sec...', i)
    sleep(i)


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
    >>> getTrend([1.563, 2.129, 3.213, 4.3425, 5.1986, 5.875644])
    2.866122
    """
    half = len(seq) // 2
    return getAverage(seq[half:]) - getAverage(seq[:-half])


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
            logging.info('Toggling autorenew for offer %s', loan['id'])
            api.toggleAutoRenew(loan['id'])


def frontSell(api, market, amount=False):
    """ Creates a sell order for <market> using all coins in balance at
    the 'front' of markete. Keeps pushing the order to 'front' until the order
    is filled. """
    parentCoin, childCoin = market.split('_')
    if not amount:
        amount = getAvailCoin(api, childCoin)
    price = getFront(api, market, 'sell')
    if amount * sellPrice < tradeMin:
        return 'Total %s is below tradeMin: %s.' % (str(amount), str(tradeMin))
    # create sell order
    trades = []
    initOrder = api.sell(market, price, amount, orderType='postOnly')
    orderNums = [int(initOrder['orderNumber'])]
    for trade in initOrder["resultingTrades"]:
        trades.append(trade)
    while 1:
        for order in api.returnOpenOrders(market):
            if int(order['orderNumber']) != int(orderNums[-1]):
                continue
            logging.debug(order)
            price = getFront(api, market, 'sell')
            if float(order['rate']) > price:
                logger.debug('Moving %s order %s', market, orderNums[-1])
                norder = api.moveOrder(
                    orderNums[-1], price, orderType='postOnly')
                if 'success' in norder and int(norder['success']) == 1:
                    orderNums.append(int(norder['orderNumber']))
                    for trade in norder["resultingTrades"]:
                        trades.append(trade)
                else:
                    logger.error(norder)
                    break
            wait()
            break
        else:
            return orderNums


def frontBuy(api, market, allowance=tradeMin + satoshi):
    """ Creates a buy order for <market> using <allowance> as the
    amount and the 'front' of market as the bid rate. Keeps pushing the
    order to 'front' until the order is filled. returns a list of trades """
    logging.info('Creating "front buy" order in %s', market)
    parentCoin, childCoin = market.split('_')
    if getAvailCoin(api, parentCoin) < allowance or allowance < tradeMin:
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
            logging.debug(order)
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
    logger.info('Checking order %s for trades', str(orderNumber))
    try:
        result = api.returnOrderTrades(orderNumber)
        return result
    # no trades yet
    except PoloniexError:
        return False


def getFront(api, market, arg):
    tick = api.returnTicker()[market]
    hbid = float(tick['highestBid'])
    lask = float(tick['lowestAsk'])
    if arg is 'buy':
        if hbid + satoshi == lask:
            return hbid
        else:
            return hbid + satoshi
    if arg is 'sell':
        if lask - satoshi == hbid:
            return lask
        else:
            return lask - satoshi


def getAvailCoin(api, coin):
    """ Returns available <coin> in exchange account """
    bals = api.returnAvailableAccountBalances('exchange')['exchange']
    logger.debug(bals)
    if not coin in bals:
        return 0.0
    return float(bals[coin])
