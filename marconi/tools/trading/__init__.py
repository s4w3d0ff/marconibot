# -*- coding: utf-8 -*-
#
#    BTC: 13MXa7EdMYaXaQK6cDHqd4dwr2stBK3ESE
#    LTC: LfxwJHNCjDh2qyJdfu22rBFi2Eu8BjQdxj
#
#    https://github.com/s4w3d0ff/marconibot
#
#    Copyright (C) 2017  https://github.com/s4w3d0ff
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from .. import (logging, pd, np, time, SATOSHI,
                PoloniexError, TRADE_MIN, wait, roundDown)

logger = logging.getLogger(__name__)


def stopLimit(api, market, amount, stop, limit, interval=2, ticker=False):
    # no order yet
    order = False
    logger.debug('%s stop limit set: [Amount]%.8f [Stop]%.8f [Limit]%.8f',
                 market, amount, stop, limit)
    while not order:
        # get new tick
        if not ticker:
            # use returnTicker
            tick = api.returnTicker()[market]
        else:
            # use external ticker
            tick = ticker(market)
        # sell
        if amount < 0 and stop >= tick['highestbid']:
            # sell amount at limit
            order = api.sell(market, limit, abs(amount))
            continue
        # buy
        if amount > 0 and stop <= tick['lowestAsk']:
            # buy amount at limit
            order = api.buy(market, limit, amount)
            continue
        wait(interval)
    logger.debug('%s stop order triggered!', market)
    return order


def dump(api, market, amount, ticker=False):
    """ Dumps childcoin <amount> on <market> at highestBid """
    parentCoin, childCoin = market.split('_')
    if amount == 'all':
        amount = api.returnCompleteBalances('exchange')[childCoin]['available']
    while True:
        if not ticker:
            hbid = api.returnTicker()[market]['highestBid']
        else:
            hBid = ticker(market)['highestBid']
        try:
            return api.sell(currencyPair=market,
                            rate=hBid + (SATOSHI * 1000),
                            amount=amount,
                            orderType='fillOrKill')
        except Exception as e:
            # log exceptions and keep trying
            logger.exception(e)
            continue


def pump(api, market, amount, ticker=False):
    """ Pumps parentCoin <amount> of <market> at lowestAsk """
    parentCoin, childCoin = market.split('_')
    if amount == 'all':
        amount = api.returnCompleteBalances(
            'exchange')[parentCoin]['available']
    while True:
        if not ticker:
            lAsk = api.returnTicker()[market]['lowestAsk']
        else:
            lAsk = ticker(market)['lowestAsk']
        try:
            return api.sell(currencyPair=market,
                            rate=lAsk + (SATOSHI * 1000),
                            amount=amount,
                            orderType='fillOrKill')
        except Exception as e:
            # log exceptions and keep trying
            logger.exception(e)
            continue


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
    for loan in api.returnActiveLoans()['provided']:
        if int(loan['autoRenew']) != int(toggle):
            logger.info('Toggling autorenew for offer %s', loan['id'])
            api.toggleAutoRenew(loan['id'])


def getAvailCoin(api, coin):
    """ Returns available <coin> in exchange account """
    bals = api.returnAvailableAccountBalances('exchange')['exchange']
    logger.debug(bals)
    if not coin in bals:
        return 0.0
    return float(bals[coin])


class Maker(object):
    """ Fills the market gap with 'makerfee-only' orders """

    def __init__(self, api, ticker):
        self.api = api
        self.ticker = ticker
        self.orderList = []
        self._running = False

    def handleOrders(self):
        if len(self.orderList) > 0:
            for order in orderList:
                order

    def run(self, market, move, amount):
        self._running = True
        while self._running:
            self.handleOrders()


def backtester(df, parentBal, childBal, moveOn='predict', tradeSize=TRADE_MIN):
    bals = {
        'pstart': float(parentBal),
        'cstart': float(childBal),
        'ptotal': float(parentBal),
        'ctotal': float(childBal),
    }

    def _backtest(row, moveOn, tradeSize):
        # get move and rate
        move = row[moveOn]
        rate = row['close']

        # if buy
        if move > 0:
            parentAmt = tradeSize * move
            childAmt = parentAmt / rate
            if parentAmt < TRADE_MIN:
                logger.debug('Parent trade amount is below the minimum!')
            elif bals['ptotal'] - parentAmt < 0:
                logger.debug('Not enough parentCoin!')
            else:
                bals['ctotal'] = bals['ctotal'] + childAmt
                bals['ptotal'] = bals['ptotal'] - parentAmt

        # if sell
        if move < 0:
            parentAmt = abs(tradeSize * move)
            childAmt = parentAmt / rate
            if parentAmt < TRADE_MIN:
                logger.debug('Parent trade amount is below the minimum!')
            elif bals['ctotal'] - childAmt < 0:
                logger.debug('Not enough childCoin!')
            else:
                bals['ptotal'] = bals['ptotal'] + parentAmt
                bals['ctotal'] = bals['ctotal'] - childAmt

        return pd.Series({'btParent': bals['ptotal'],
                          'btChild': bals['ctotal']})

    df = df.merge(df.apply(_backtest, axis=1, moveOn=moveOn, tradeSize=tradeSize),
                  left_index=True, right_index=True)
    df['btTotal'] = df['btParent'] + (df['btChild'] * df['close'])
    df['btStart'] = bals['pstart'] + (bals['cstart'] * df['close'])
    df['btProfit'] = df['btTotal'] - df['btStart']
    df['btProfit'] = df['btProfit'].apply(roundDown, d=8)
    return df
