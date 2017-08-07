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
from .. import logging, pd, np, time, SATOSHI, PoloniexError, TRADE_MIN, wait

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


def getAvailCoin(api, coin):
    """ Returns available <coin> in exchange account """
    bals = api.returnAvailableAccountBalances('exchange')['exchange']
    logger.debug(bals)
    if not coin in bals:
        return 0.0
    return float(bals[coin])


class Backtester(object):

    def __init__(self, parentBal=0.1, childBal=1):
        self.parentBal = parentBal
        self.childBal = childBal

    def _backtest(self, row, moveOn='predict', minX=10):
        # get move and rate
        move = row[moveOn]
        rate = row['close']

        # if buy
        if move > 0:
            parentAmt = self.parentBal * (move / 100)
            childAmt = parentAmt / rate
            if parentAmt < TRADE_MIN:
                logger.warning('Parent trade amount is below the minimum!')

            elif self.parentBal - parentAmt < 0:
                logger.warning(
                    'This trade would make parentBal below 0!')
            else:
                self.childBal = self.childBal + childAmt
                self.parentBal = self.parentBal - parentAmt

        # if sell
        if move < 0:
            childAmt = abs(self.childBal * (move / 100))
            parentAmt = childAmt * rate
            if parentAmt < TRADE_MIN:
                logger.warning('Parent trade amount is below the minimum!')

            elif self.childBal - childAmt < 0:
                logger.warning(
                    'This trade would make childBal below 0!')
            else:
                self.parentBal = self.parentBal + parentAmt
                self.childBal = self.childBal - childAmt

        return pd.Series({'btParent': self.parentBal,
                          'btChild': self.childBal})

    def __call__(self, df, parentBal=False, childBal=False, minX=10, moveOn='predict'):
        if parentBal:
            self.parentBal = parentBal
        if childBal:
            self.childBal = childBal

        pstart = float(self.parentBal)
        cstart = float(self.childBal)
        df = df.merge(df.apply(self._backtest, axis=1, moveOn=moveOn, minX=minX),
                      left_index=True,
                      right_index=True)
        df['btTotal'] = df['btParent'] + (df['btChild'] * df['close'])
        df['btStart'] = pstart + (cstart * df['close'])
        df['btProfit'] = df['btTotal'] - df['btStart']
        return df
