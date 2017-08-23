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
from .tools import logging, pd, np, SATOSHI, TRADE_MIN, wait, roundDown
from .tools import time, UTCstr2epoch, pymongo, getMongoColl
from .tools import BL, OR, RD, GY, GR, float2percent, Thread


logger = logging.getLogger(__name__)


def stopLimit(api, market, amount, stop, limit, interval=2, ticker=False):
    """
    Simple stop limit, waits until <stop> has been triggered then attempts to
        create an order for <amount> at <limit>

    Use <interval> to throttle the rate it checks for price changes

    Pass <ticker> an instance of 'marconi.ticker.Ticker' to use that instance to
        retrieve ticker data, defaults to api.returnTicker()
    """
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
    logger.debug('%s stop limit triggered!', market)
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
                            rate=hBid - (SATOSHI * 1000),
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
    # get open orders for 'market'
    orders = api.returnOpenOrders(market)
    # if market is set to 'all' we will cancel all open orders
    if market == 'all':
        # iterate through each market
        for market in orders:
            # iterate through each market order
            for order in orders[market]:
                # if arg = 'sell' or 'buy' skip the orders not labeled as such
                if arg in ('sell', 'buy') and order['type'] != arg:
                    continue
                # show results as we cancel each order
                logger.debug(api.cancelOrder(order["orderNumber"]))
    else:
        # just an individial market
        for order in orders:
            # if arg = 'sell' or 'buy' skip the orders not labeled as such
            if arg in ('sell', 'buy') and order['type'] != arg:
                continue
            # show output
            logger.debug(api.cancelOrder(order["orderNumber"]))


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


def backtester(df, parentBal, childBal, moveOn='predict', tradeSize=TRADE_MIN):
    """
    df = requires a 'close' column for the closing price and the <moveOn> column
    parentBal = starting parent coin balance to backtest with
    childBal = starting child coin balance to backtest with
    moveOn = name of column to direct trades; expects a whole number, positive
        for buy trades, negative for sell trades, defaults to 'predict'
    tradesSize = the minimum trade size, actual trades are
        tradesSize * df[moveOn]

    returns same dataframe with backtesting results
    """
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

    df = df.merge(df.apply(_backtest, axis=1,
                           moveOn=moveOn, tradeSize=tradeSize),
                  left_index=True, right_index=True)
    df['btTotal'] = df['btParent'] + (df['btChild'] * df['close'])
    df['btStart'] = bals['pstart'] + (bals['cstart'] * df['close'])
    df['btProfit'] = df['btTotal'] - df['btStart']
    df['btProfit'] = df['btProfit'].apply(roundDown, d=8)
    return df


class Bookie(object):

    def __init__(self, api):
        self.api = api
        self.db = pymongo.MongoClient().poloniex

    def updateTradeHistory(self, market):
        try:
            old = list(self.db[market + 'tradeHistory'].find().sort(
                'timestamp', pymongo.ASCENDING))[-1]
        except:
            logger.warning('No %s trades found in database', market)
            old = {'timestamp': time() - self.api.YEAR * 10}
        start = old['timestamp'] + 1
        hist = self.api.returnTradeHistory(market, start=start)
        if len(hist) > 0:
            logger.info('%d new trade database entries' % len(hist))

            for trade in hist:
                _id = trade['globalTradeID']
                del trade['globalTradeID']
                trade['timestamp'] = UTCstr2epoch(trade['date'])
                trade['amount'] = float(trade['amount'])
                trade['total'] = float(trade['total'])
                trade['tradeID'] = int(trade['tradeID'])
                trade['orderNumber'] = int(trade['orderNumber'])
                trade['rate'] = float(trade['rate'])
                trade['fee'] = float(trade['fee'])
                self.db[market + 'tradeHistory'].update_one(
                    {"_id": _id}, {"$set": trade}, upsert=True)

    def myTradeHistory(self, market, query=None):
        self.updateTradeHistory(market)
        return list(self.db[market + 'tradeHistory'].find(query).sort(
            'timestamp', pymongo.ASCENDING))


class Loaner(object):
    """ Loanbot class [API REQUIRES KEY AND SECRET!]"""

    def __init__(self,
                 api,
                 coins={'BTC': 0.01},
                 maxage=60 * 5,
                 delay=60 * 3):
        self.api, self.delay = api, delay
        self.coins, self.maxage = coins, maxage
        self.db = getMongoColl('poloniex', 'lendingHistory')

    def getLoanOfferAge(self, order):
        return time() - UTCstr2epoch(order['date'])

    def cancelOldOffers(self):
        logger.info(GR("Checking Open Loan Offers:----------------"))
        offers = self.api.returnOpenLoanOffers()
        if len(offers) < 1:
            return logger.info(RD('No open loan offers found'))
        for coin in self.coins:
            if coin not in offers:
                continue
            for offer in offers[coin]:
                logger.info("%s|%s:%s-[rate:%s]",
                            BL(offer['date']),
                            OR(coin),
                            RD(offer['amount']),
                            GY(float2percent(offer['rate'])) + '%'
                            )
                if self.getLoanOfferAge(offer) > self.maxage:
                    logger.info("Canceling %s offer %s",
                                OR(coin), GY(offer['id']))
                    r = self.api.cancelLoanOffer(offer['id'])
                    logger.info(r['message'])

    def createLoanOffers(self):
        logger.info(GR("Checking for coins to lend:---------------"))
        bals = self.api.returnAvailableAccountBalances()
        if not 'lending' in bals:
            return logger.info(RD("No coins found in lending account"))
        for coin in self.coins:
            if coin not in bals['lending']:
                continue
            amount = bals['lending'][coin]
            if float(amount) < self.coins[coin]:
                logger.info("Not enough %s:%s, below set minimum: %s",
                            OR(coin),
                            RD(amount),
                            BL(self.coins[coin]))
                continue
            else:
                logging.info("%s:%s", OR(coin), GR(amount))
            orders = self.api.returnLoanOrders(coin)['offers']
            price = sum([float(o['rate']) for o in orders]) / len(orders)
            logger.info('Creating %s %s loan offer at %s',
                        RD(amount), OR(coin), GR(float2percent(price)) + '%')
            r = self.api.createLoanOffer(coin, amount, price, autoRenew=0)
            logger.info('%s', GR(r["message"]))

    def updateLendingHistory(self):
        try:
            old = list(self.db.find().sort('timestamp', pymongo.ASCENDING))[-1]
        except IndexError:
            logger.warning(RD('No loan history found in database'))
            old = {'timestamp': time() - self.api.YEAR * 10}
        start = old['timestamp'] + 1
        new = self.api.returnLendingHistory(start=start)
        if len(new) > 0:
            logger.info(GR('%d new lending database entries' % len(new)))
            for loan in new:
                _id = loan['id']
                del loan['id']
                loan['timestamp'] = UTCstr2epoch(loan['close'])
                loan['rate'] = float(loan['rate'])
                loan['duration'] = float(loan['duration'])
                loan['interest'] = float(loan['interest'])
                loan['fee'] = float(loan['fee'])
                loan['earned'] = float(loan['earned'])
                self.db.update_one({'_id': _id}, {'$set': loan}, upsert=True)

    def myLendingHistory(self):
        self.updateLendingHistory()
        for coin in self.coins:
            earned = 0
            duration = 0
            rates = []
            hist = list(self.db.find({'currency': coin}))
            if len(hist) > 0:
                logger.debug('%s past loan orders found for %s',
                             GR(len(hist)), OR(coin))
                for loan in hist:
                    earned += loan['earned']
                    duration += loan['duration']
                    rates.append(loan['rate'])

            logger.info(
                "Total %s earned lending: [earnings: %s] [average rate: %s]",
                OR(coin), GR(roundDown(earned)),
                BL(roundDown(sum(rates) / len(rates)))
            )

    def showActiveLoans(self):
        active = self.api.returnActiveLoans()['provided']
        logger.info(GR('Active Loans:-----------------------------'))
        for i in active:
            logger.info('%s|%s:%s-[rate:%s]-[fees:%s]',
                        BL(i['date']),
                        OR(i['currency']),
                        RD(i['amount']),
                        GY(roundDown(float2percent(i['rate']))) + '%',
                        GR(i['fees'])
                        )

    def run(self):
        """ Main loop, cancels 'stale' loan offers, turns auto - renew off on
        active loans, and creates new loan offers at optimum price """
        # Check auto renew is not enabled for current loans
        autoRenewAll(self.api, toggle=False)
        while self._running:
            try:
                # Check for old offers
                self.cancelOldOffers()
                # Create new offer (if can)
                self.createLoanOffers()
                # show active
                self.showActiveLoans()
                # show history
                self.myLendingHistory()

            except Exception as e:
                logger.exception(e)

            finally:
                # sleep with one eye open...
                for i in range(int(self.delay)):
                    if not self._running:
                        break
                    wait(1)

    def start(self):
        """ Run the Loaner in a thread """
        self._t = Thread(target=self.run)
        self._t.daemon = True
        self._running = True
        self._t.start()
        logger.info('Loaner thread started')

    def stop(self):
        """ Stop/join the Loaner thread """
        self._running = False
        self._t.join()
        logger.info('Loaner thread stopped/joined')


class Liquidator(object):

    def __init__(self, api, **kwargs):
        self.api = api
        self.coin = kwargs.get('coin', 'BTC')
        self.address = kwargs.get('address', False)

    def run(self, coin, address=False):
        """
        Move all assets into <coin> and withdraw to external coin
        address (api withdrawing needs to be enabled on poloniex in order to
        withdraw)
        """
        # turn off auto-renew on active loans
        autoRenewAll(self.api, False)
        # cancel loan offers
        cancelAllLoanOffers(self.api)
        # cancel all open orders
        cancelAllOrders(self.api, market='all')
        # close margins
        closeAllMargins(self.api)
        # transfer all funds to 'exchange' account
        # 'dump' all coins at highestBid and buy <coin>
        # withdraw to external <coin> address (if specifiyed)
        return

    def start(self):
        """ Start 'run' in a thread """
        self._t = Thread(target=self.run)
        self._t.daemon = True
        self._running = True
        self._t.start()
        logger.info('Liquidator thread started')

    def stop(self):
        """ Stop/join the thread """
        self._running = False
        self._t.join()
        logger.info('Liquidator thread stopped/joined')


if __name__ == '__main__':
    from .tools.poloniex import Poloniex
    from sys import argv
    from pprint import pprint
    logging.basicConfig(level=logging.INFO)
    key, secret = argv[1:3]
    api = Poloniex(key, secret, jsonNums=float)
    bookie = Bookie(api)
    pprint(bookie.myTradeHistory('BTC_DASH')[-6:])
