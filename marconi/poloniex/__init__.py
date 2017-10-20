# Poloniex API wrapper tested on Python 2.7.6 & 3.4.3
# https://github.com/s4w3d0ff/python-poloniex
# BTC: 1A7K4kgXLSSzvDRjvoGwomvhrNU4CKezEp
# TODO:
#   [x] PEP8ish
#   [ ] Improve logging output
#   [x] Add Push Api application wrapper
#
#    Copyright (C) 2016  https://github.com/s4w3d0ff
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# python 2
try:
    from urllib import urlencode as _urlencode
    str = unicode
# python 3
except:
    from urllib.parse import urlencode as _urlencode

from threading import Thread as _Thread
from json import loads as _loads
from json import dumps as _dumps
from hmac import new as _new
from hashlib import sha512 as _sha512
from itertools import chain as _chain
from functools import wraps as _wraps
from time import sleep, time

# 3rd party
from requests.exceptions import RequestException
from requests import post as _post
from requests import get as _get
from websocket import WebSocketApp

# local
from .coach import Coach
from ..tools import getLogger

# logger
logger = getLogger(__name__)

retryDelays = (0, 2, 5, 30)

# Possible Commands
PUBLIC_COMMANDS = [
    'returnTicker',
    'return24hVolume',
    'returnOrderBook',
    'marketTradeHist',
    'returnChartData',
    'returnCurrencies',
    'returnLoanOrders']

PRIVATE_COMMANDS = [
    'returnBalances',
    'returnCompleteBalances',
    'returnDepositAddresses',
    'generateNewAddress',
    'returnDepositsWithdrawals',
    'returnOpenOrders',
    'returnTradeHistory',
    'returnAvailableAccountBalances',
    'returnTradableBalances',
    'returnOpenLoanOffers',
    'returnOrderTrades',
    'returnActiveLoans',
    'returnLendingHistory',
    'createLoanOffer',
    'cancelLoanOffer',
    'toggleAutoRenew',
    'buy',
    'sell',
    'cancelOrder',
    'moveOrder',
    'withdraw',
    'returnFeeInfo',
    'transferBalance',
    'returnMarginAccountSummary',
    'marginBuy',
    'marginSell',
    'getMarginPosition',
    'closeMarginPosition']


class PoloniexError(Exception):
    """ Exception for handling poloniex api errors """
    pass


class RetryException(PoloniexError):
    """ Exception for retry decorator """
    pass


class Poloniex(object):
    """The Poloniex Object!"""

    def __init__(
            self, key=False, secret=False,
            timeout=None, coach=True, jsonNums=False, loglevel=False):
        """
        key = str api key supplied by Poloniex
        secret = str secret hash supplied by Poloniex
        timeout = int time in sec to wait for an api response
            (otherwise 'requests.exceptions.Timeout' is raised)
        coach = bool to indicate if the api coach should be used
        jsonNums = datatype to use when parsing json ints and floats

        # Time Placeholders: (MONTH == 30*DAYS)
        self.MINUTE, self.HOUR, self.DAY, self.WEEK, self.MONTH, self.YEAR
        """
        if loglevel:
            logger.setLevel(loglevel)
        self.coach = coach
        if self.coach is True:
            self.coach = Coach()
        # create nonce
        self._nonce = int("{:.6f}".format(time()).replace('.', ''))
        # json number datatypes
        self.jsonNums = jsonNums
        # grab keys, set timeout
        self.key, self.secret, self.timeout = key, secret, timeout
        # set time labels
        self.MINUTE, self.HOUR, self.DAY = 60, 60 * 60, 60 * 60 * 24
        self.WEEK, self.MONTH = self.DAY * 7, self.DAY * 30
        self.YEAR = self.DAY * 365

    # -----------------Meat and Potatos---------------------------------------
    def _retry(func):
        """ retry decorator """
        @_wraps(func)
        def retrying(*args, **kwargs):
            problems = []
            for delay in _chain(retryDelays, [None]):
                try:
                    # attempt call
                    return func(*args, **kwargs)

                # we need to try again
                except RequestException as problem:
                    problems.append(problem)
                    if delay is None:
                        logger.debug(problems)
                        raise RetryException(
                            'retryDelays exhausted ' + str(problem))
                    else:
                        # log exception and wait
                        logger.debug(problem)
                        logger.info("-- retrying in %ds", delay)
                        sleep(delay)
        return retrying

    @_retry
    def __call__(self, command, args={}):
        """ Main Api Function
        - encodes and sends <command> with optional [args] to Poloniex api
        - raises 'poloniex.PoloniexError' if an api key or secret is missing
            (and the command is 'private'), if the <command> is not valid, or
            if an error is returned from poloniex.com
        - returns decoded json api message """
        # get command type
        cmdType = self._checkCmd(command)

        # pass the command
        args['command'] = command
        payload = {}
        # add timeout
        payload['timeout'] = self.timeout

        # private?
        if cmdType == 'Private':
            payload['url'] = 'https://poloniex.com/tradingApi'

            # wait for coach
            if self.coach:
                self.coach.wait()

            # set nonce
            args['nonce'] = self.nonce

            # add args to payload
            payload['data'] = args

            # sign data with our Secret
            sign = _new(
                self.secret.encode('utf-8'),
                _urlencode(args).encode('utf-8'),
                _sha512)

            # add headers to payload
            payload['headers'] = {'Sign': sign.hexdigest(),
                                  'Key': self.key}

            # send the call
            ret = _post(**payload)

            # return data
            return self._handleReturned(ret.text)

        # public?
        if cmdType == 'Public':
            # encode url
            payload['url'] = 'https://poloniex.com/public?' + _urlencode(args)

            # wait for coach
            if self.coach:
                self.coach.wait()

            # send the call
            ret = _get(**payload)
            # return data
            return self._handleReturned(ret.text)

    @property
    def nonce(self):
        """ Increments the nonce """
        self._nonce += 42
        return self._nonce

    def _checkCmd(self, command):
        """ Returns if the command is private of public, raises PoloniexError
        if command is not found """
        global PUBLIC_COMMANDS, PRIVATE_COMMANDS
        if command in PRIVATE_COMMANDS:
            # check for keys
            if not self.key or not self.secret:
                raise PoloniexError("An Api Key and Secret needed!")
            return 'Private'
        if command in PUBLIC_COMMANDS:
            return 'Public'

        raise PoloniexError("Invalid Command!: %s" % command)

    def _handleReturned(self, data):
        """ Handles returned data from poloniex"""
        try:
            if not self.jsonNums:
                out = _loads(data, parse_float=str)
            else:
                out = _loads(data,
                             parse_float=self.jsonNums,
                             parse_int=self.jsonNums)
        except:
            logger.error(data)
            raise PoloniexError('Invalid json response returned')

        # check if poloniex returned an error
        if 'error' in out:

            # update nonce if we fell behind
            if "Nonce must be greater" in out['error']:
                self._nonce = int(
                    out['error'].split('.')[0].split()[-1])
                # raise RequestException so we try again
                raise RequestException('PoloniexError ' + out['error'])

            # conncetion timeout from poloniex
            if "please try again" in out['error'].lower():
                # raise RequestException so we try again
                raise RequestException('PoloniexError ' + out['error'])

            # raise other poloniex errors, ending retry loop
            else:
                raise PoloniexError(out['error'])
        return out

    # --PUBLIC COMMANDS-------------------------------------------------------
    def returnTicker(self):
        """ Returns the ticker for all markets. """
        return self.__call__('returnTicker')

    def return24hVolume(self):
        """ Returns the 24-hour volume for all markets,
        plus totals for primary currencies. """
        return self.__call__('return24hVolume')

    def returnOrderBook(self, currencyPair='all', depth=20):
        """ Returns the order book for a given market as well as a sequence
        number for use with the Push API and an indicator specifying whether the
        market is frozen. (defaults to 'all' markets, at a 'depth' of 20 orders)
        """
        return self.__call__('returnOrderBook', {
            'currencyPair': str(currencyPair).upper(),
            'depth': str(depth)
        })

    @_retry
    def marketTradeHist(self, currencyPair, start=False, end=False):
        """ Returns the past 200 trades for a given market, or up to 50,000
        trades between a range specified in UNIX timestamps by the "start" and
        "end" parameters. """
        if self.coach:
            self.coach.wait()
        args = {'command': 'returnTradeHistory',
                'currencyPair': str(currencyPair).upper()}
        if start:
            args['start'] = start
        if end:
            args['end'] = end
        ret = _get(
            'https://poloniex.com/public?' + _urlencode(args),
            timeout=self.timeout)
        # decode json
        return self._handleReturned(ret.text)

    def returnChartData(self, currencyPair, period=False,
                        start=False, end=False):
        """ Returns candlestick chart data. Parameters are "currencyPair",
        "period" (candlestick period in seconds; valid values are 300, 900,
        1800, 7200, 14400, and 86400), "start", and "end". "Start" and "end"
        are given in UNIX timestamp format and used to specify the date range
        for the data returned (default date range is start='1 day ago' to
        end='now') """
        if period not in [300, 900, 1800, 7200, 14400, 86400]:
            raise PoloniexError("%s invalid candle period" % str(period))
        if not start:
            start = time() - self.DAY
        if not end:
            end = time()
        return self.__call__('returnChartData', {
            'currencyPair': str(currencyPair).upper(),
            'period': str(period),
            'start': str(start),
            'end': str(end)
        })

    def returnCurrencies(self):
        """ Returns information about all currencies. """
        return self.__call__('returnCurrencies')

    def returnLoanOrders(self, currency):
        """ Returns the list of loan offers and demands for a given currency,
        specified by the "currency" parameter """
        return self.__call__('returnLoanOrders', {
                             'currency': str(currency).upper()})

    # --PRIVATE COMMANDS------------------------------------------------------
    def returnBalances(self):
        """ Returns all of your available balances."""
        return self.__call__('returnBalances')

    def returnCompleteBalances(self, account='all'):
        """ Returns all of your balances, including available balance, balance
        on orders, and the estimated BTC value of your balance. By default,
        this call is limited to your exchange account; set the "account"
        parameter to "all" to include your margin and lending accounts. """
        return self.__call__('returnCompleteBalances',
                             {'account': str(account)})

    def returnDepositAddresses(self):
        """ Returns all of your deposit addresses. """
        return self.__call__('returnDepositAddresses')

    def generateNewAddress(self, currency):
        """ Generates a new deposit address for the currency specified by the
        "currency" parameter. """
        return self.__call__('generateNewAddress', {
                             'currency': currency})

    def returnDepositsWithdrawals(self, start=False, end=False):
        """ Returns your deposit and withdrawal history within a range,
        specified by the "start" and "end" parameters, both of which should be
        given as UNIX timestamps. (defaults to 1 month)"""
        if not start:
            start = time() - self.MONTH
        if not end:
            end = time()
        args = {'start': str(start), 'end': str(end)}
        return self.__call__('returnDepositsWithdrawals', args)

    def returnOpenOrders(self, currencyPair='all'):
        """ Returns your open orders for a given market, specified by the
        "currencyPair" parameter, e.g. "BTC_XCP". Set "currencyPair" to
        "all" to return open orders for all markets. """
        return self.__call__('returnOpenOrders', {
                             'currencyPair': str(currencyPair).upper()})

    def returnTradeHistory(self, currencyPair='all', start=False, end=False):
        """ Returns your trade history for a given market, specified by the
        "currencyPair" parameter. You may specify "all" as the currencyPair to
        receive your trade history for all markets. You may optionally specify
        a range via "start" and/or "end" POST parameters, given in UNIX
        timestamp format; if you do not specify a range, it will be limited to
        one day. """
        args = {'currencyPair': str(currencyPair).upper()}
        if start:
            args['start'] = start
        if end:
            args['end'] = end
        return self.__call__('returnTradeHistory', args)

    def returnOrderTrades(self, orderNumber):
        """ Returns all trades involving a given order, specified by the
        "orderNumber" parameter. If no trades for the order have occurred
        or you specify an order that does not belong to you, you will receive
        an error. """
        return self.__call__('returnOrderTrades', {
                             'orderNumber': str(orderNumber)})

    def buy(self, currencyPair, rate, amount, orderType=False):
        """ Places a limit buy order in a given market. Required parameters are
        "currencyPair", "rate", and "amount". You may optionally set "orderType"
        to "fillOrKill", "immediateOrCancel" or "postOnly". A fill-or-kill order
        will either fill in its entirety or be completely aborted. An
        immediate-or-cancel order can be partially or completely filled, but
        any portion of the order that cannot be filled immediately will be
        canceled rather than left on the order book. A post-only order will
        only be placed if no portion of it fills immediately; this guarantees
        you will never pay the taker fee on any part of the order that fills.
        If successful, the method will return the order number. """
        args = {
            'currencyPair': str(currencyPair).upper(),
            'rate': str(rate),
            'amount': str(amount),
        }
        # order type specified?
        if orderType:
            possTypes = ['fillOrKill', 'immediateOrCancel', 'postOnly']
            # check type
            if not orderType in possTypes:
                raise PoloniexError('Invalid orderType')
            args[orderType] = 1

        return self.__call__('buy', args)

    def sell(self, currencyPair, rate, amount, orderType=False):
        """ Places a sell order in a given market. Parameters and output are
        the same as for the buy method. """
        args = {
            'currencyPair': str(currencyPair).upper(),
            'rate': str(rate),
            'amount': str(amount),
        }
        # order type specified?
        if orderType:
            possTypes = ['fillOrKill', 'immediateOrCancel', 'postOnly']
            # check type
            if not orderType in possTypes:
                raise PoloniexError('Invalid orderType')
            args[orderType] = 1

        return self.__call__('sell', args)

    def cancelOrder(self, orderNumber):
        """ Cancels an order you have placed in a given market. Required
        parameter is "orderNumber". """
        return self.__call__('cancelOrder', {'orderNumber': str(orderNumber)})

    def moveOrder(self, orderNumber, rate, amount=False, orderType=False):
        """ Cancels an order and places a new one of the same type in a single
        atomic transaction, meaning either both operations will succeed or both
        will fail. Required parameters are "orderNumber" and "rate"; you may
        optionally specify "amount" if you wish to change the amount of the new
        order. "postOnly" or "immediateOrCancel" may be specified as the
        "orderType" param for exchange orders, but will have no effect on
        margin orders. """

        args = {
            'orderNumber': str(orderNumber),
            'rate': str(rate)
        }
        if amount:
            args['amount'] = str(amount)
        # order type specified?
        if orderType:
            possTypes = ['immediateOrCancel', 'postOnly']
            # check type
            if not orderType in possTypes:
                raise PoloniexError('Invalid orderType: %s' % str(orderType))
            args[orderType] = 1

        return self.__call__('moveOrder', args)

    def withdraw(self, currency, amount, address, paymentId=False):
        """ Immediately places a withdrawal for a given currency, with no email
        confirmation. In order to use this method, the withdrawal privilege
        must be enabled for your API key. Required parameters are
        "currency", "amount", and "address". For XMR withdrawals, you may
        optionally specify "paymentId". """
        args = {
            'currency': str(currency).upper(),
            'amount': str(amount),
            'address': str(address)
        }
        if paymentId:
            args['paymentId'] = str(paymentId)
        return self.__call__('withdraw', args)

    def returnFeeInfo(self):
        """ If you are enrolled in the maker-taker fee schedule, returns your
        current trading fees and trailing 30-day volume in BTC. This
        information is updated once every 24 hours. """
        return self.__call__('returnFeeInfo')

    def returnAvailableAccountBalances(self, account=False):
        """ Returns your balances sorted by account. You may optionally specify
        the "account" parameter if you wish to fetch only the balances of
        one account. Please note that balances in your margin account may not
        be accessible if you have any open margin positions or orders. """
        if account:
            return self.__call__('returnAvailableAccountBalances',
                                 {'account': account})
        return self.__call__('returnAvailableAccountBalances')

    def returnTradableBalances(self):
        """ Returns your current tradable balances for each currency in each
        market for which margin trading is enabled. Please note that these
        balances may vary continually with market conditions. """
        return self.__call__('returnTradableBalances')

    def transferBalance(self, currency, amount,
                        fromAccount, toAccount, confirmed=False):
        """ Transfers funds from one account to another (e.g. from your
        exchange account to your margin account). Required parameters are
        "currency", "amount", "fromAccount", and "toAccount" """
        args = {
            'currency': str(currency).upper(),
            'amount': str(amount),
            'fromAccount': str(fromAccount),
            'toAccount': str(toAccount)
        }
        if confirmed:
            args['confirmed'] = 1
        return self.__call__('transferBalance', args)

    def returnMarginAccountSummary(self):
        """ Returns a summary of your entire margin account. This is the same
        information you will find in the Margin Account section of the Margin
        Trading page, under the Markets list """
        return self.__call__('returnMarginAccountSummary')

    def marginBuy(self, currencyPair, rate, amount, lendingRate=2):
        """ Places a margin buy order in a given market. Required parameters are
        "currencyPair", "rate", and "amount". You may optionally specify a
        maximum lending rate using the "lendingRate" parameter (defaults to 2).
        If successful, the method will return the order number and any trades
        immediately resulting from your order. """
        return self.__call__('marginBuy', {
            'currencyPair': str(currencyPair).upper(),
            'rate': str(rate),
            'amount': str(amount),
            'lendingRate': str(lendingRate)
        })

    def marginSell(self, currencyPair, rate, amount, lendingRate=2):
        """ Places a margin sell order in a given market. Parameters and output
        are the same as for the marginBuy method. """
        return self.__call__('marginSell', {
            'currencyPair': str(currencyPair).upper(),
            'rate': str(rate),
            'amount': str(amount),
            'lendingRate': str(lendingRate)
        })

    def getMarginPosition(self, currencyPair='all'):
        """ Returns information about your margin position in a given market,
        specified by the "currencyPair" parameter. You may set
        "currencyPair" to "all" if you wish to fetch all of your margin
        positions at once. If you have no margin position in the specified
        market, "type" will be set to "none". "liquidationPrice" is an
        estimate, and does not necessarily represent the price at which an
        actual forced liquidation will occur. If you have no liquidation price,
        the value will be -1. (defaults to 'all')"""
        return self.__call__('getMarginPosition', {
                             'currencyPair': str(currencyPair).upper()})

    def closeMarginPosition(self, currencyPair):
        """ Closes your margin position in a given market (specified by the
        "currencyPair" parameter) using a market order. This call will also
        return success if you do not have an open position in the specified
        market. """
        return self.__call__(
            'closeMarginPosition', {'currencyPair': str(currencyPair).upper()})

    def createLoanOffer(self, currency, amount,
                        lendingRate, autoRenew=0, duration=2):
        """ Creates a loan offer for a given currency. Required parameters are
        "currency", "amount", "lendingRate", "duration" (num of days, defaults
        to 2), "autoRenew" (0 or 1, defaults to 0 'off'). """
        return self.__call__('createLoanOffer', {
            'currency': str(currency).upper(),
            'amount': str(amount),
            'duration': str(duration),
            'autoRenew': str(autoRenew),
            'lendingRate': str(lendingRate)
        })

    def cancelLoanOffer(self, orderNumber):
        """ Cancels a loan offer specified by the "orderNumber" parameter. """
        return self.__call__(
            'cancelLoanOffer', {'orderNumber': str(orderNumber)})

    def returnOpenLoanOffers(self):
        """ Returns your open loan offers for each currency. """
        return self.__call__('returnOpenLoanOffers')

    def returnActiveLoans(self):
        """ Returns your active loans for each currency."""
        return self.__call__('returnActiveLoans')

    def returnLendingHistory(self, start=False, end=False, limit=False):
        """ Returns your lending history within a time range specified by the
        "start" and "end" parameters as UNIX timestamps. "limit" may also
        be specified to limit the number of rows returned. (defaults to the last
        months history)"""
        if not start:
            start = time() - self.MONTH
        if not end:
            end = time()
        args = {'start': str(start), 'end': str(end)}
        if limit:
            args['limit'] = str(limit)
        return self.__call__('returnLendingHistory', args)

    def toggleAutoRenew(self, orderNumber):
        """ Toggles the autoRenew setting on an active loan, specified by the
        "orderNumber" parameter. If successful, "message" will indicate
        the new autoRenew setting. """
        return self.__call__(
            'toggleAutoRenew', {'orderNumber': str(orderNumber)})


class wsPoloniex(Poloniex):
    # websocket stuff --------------------------------------------------
    def _on_message(self, ws, message):
        message = _loads(message)
        if 'error' in message:
            return logger.error(message['error'])

        if message[0] == 1002:
            if message[1] == 1:
                return logger.debug('Subscribed to ticker')

            if message[1] == 0:
                return logger.debug('Unsubscribed to ticker')

            data = message[2]
            data = [float(dat) for dat in data]
            self._tick[data[0]] = {'id': data[0],
                                   'last': data[1],
                                   'lowestAsk': data[2],
                                   'highestBid': data[3],
                                   'percentChange': data[4],
                                   'baseVolume': data[5],
                                   'quoteVolume': data[6],
                                   'isFrozen': data[7],
                                   'high24hr': data[8],
                                   'low24hr': data[9]
                                   }

    def _on_error(self, ws, error):
        logger.error(error)

    def _on_close(self, ws):
        if self._t._running:
            try:
                self.stop()
            except Exception as e:
                logger.exception(e)
            try:
                self.start()
            except Exception as e:
                logger.exception(e)
                self.stop()
        else:
            logger.info("Websocket closed!")

    def _on_open(self, ws):
        self._ws.send(_dumps({'command': 'subscribe', 'channel': 1002}))

    @property
    def tickerStatus(self):
        """
        Returns True if the websocket thread is running, False if not.
        """
        try:
            return self._t._running
        except:
            return False

    def startWebsocket(self):
        """ Run the websocket in a thread """
        self._tick = {}
        iniTick = self.returnTicker()
        self._ids = {market: iniTick[market]['id'] for market in iniTick}
        for market in iniTick:
            self._tick[self._ids[market]] = iniTick[market]

        self._ws = WebSocketApp("wss://api2.poloniex.com/",
                                on_open=self._on_open,
                                on_message=self._on_message,
                                on_error=self._on_error,
                                on_close=self._on_close)
        self._t = _Thread(target=self._ws.run_forever)
        self._t.daemon = True
        self._t._running = True
        self._t.start()
        logger.info('Websocket thread started')

    def stopWebsocket(self):
        """ Stop/join the websocket thread """
        self._t._running = False
        self._ws.close()
        self._t.join()
        logger.info('Websocket thread stopped/joined')

    def marketTick(self, market=None):
        """ returns ticker from websocket if running/connected, else
        'self.returnTicker is used'"""
        if self.tickerStatus:
            if market:
                return self._tick[self._ids[market]]
            return self._tick
        logger.warning('Ticker is not running!')
        if market:
            return self.returnTicker()[market]
        return self.returnTicker()
