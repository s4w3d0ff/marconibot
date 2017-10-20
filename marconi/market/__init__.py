#!/usr/bin/python3
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
from ..tools import (getMongoColl, time, pd,
                     pymongo, RD, GR, sleep, Thread, SATOSHI,
                     TRADE_MIN, getLogger, UTCstr2epoch)
from ..poloniex import PoloniexError, wsPoloniex
from ..trading import StopLimit
from .. import indicators

logger = getLogger(__name__)


class Market(object):
    """
    Market object

    Maintains/Returns database entries for a market, as well as provides
    convienance methods for common functions done on markets.
    """

    def __init__(self, pair, api=False):
        """
        pair = str market currencyPair. example: 'BTC_LTC'
        api = an instance of 'poloniex.Poloniex'
        """
        self.api = api
        if not self.api:
            self.api = wsPoloniex(jsonNums=float)
        self.pair = pair
        self.parent, self.child = self.pair.split('_')
        self.stopOrders = []

    @property
    def tick(self):
        """
        Get a market 'tick'
        """
        return self.api.marketTick(self.pair)

    @property
    def availBalances(self):
        """
        Get available balances from poloniex
        """
        bals = self.api.returnCompleteBalances('exchange')
        childBal = float(bals[self.child]['available'])
        parentBal = float(bals[self.parent]['available'])
        logger.debug('Balances: %s [%s] %.8f [%s] %.8f',
                     self.pair, self.parent, parentBal, self.child, childBal)
        return parentBal, childBal

    @property
    def openOrders(self):
        """ Get open orders from poloniex """
        return self.api.returnOpenOrders(self.pair)

    def chart(self, start=False, zoom=False, indica=False):
        """ returns chart data in a dataframe from mongodb, updates/fills the
        data, the date column is the '_id' of each candle entry, and
        the date column has been removed. Use 'start' to restrict the amount
        of data returned.
        Example: 'start=time() - api.YEAR' will return last years data
        """
        if not start:
            start = time() - self.api.YEAR * 1
        dbcolName = self.pair + '-chart'
        # get db connection
        db = getMongoColl('poloniex', dbcolName)
        # get last candle
        try:
            last = list(db.find({"_id": {
                "$gt": time() - self.api.WEEK * 2
            }}).sort('timestamp', pymongo.ASCENDING))[-1]
        except:
            last = False
        # no entrys found, get all 5min data from poloniex
        if not last:
            logger.warning('%s collection is empty!', dbcolName)
            logger.debug('Getting new %s candles from Poloniex...', self.pair)
            new = self.api.returnChartData(self.pair,
                                           period=60 * 5,
                                           start=time() - self.api.YEAR * 13)
        else:
            logger.debug('Getting new %s candles from Poloniex...', self.pair)
            new = self.api.returnChartData(self.pair,
                                           period=60 * 5,
                                           start=int(last['_id']))
        # add new candles
        updateSize = len(new)

        if updateSize > 10000:
            logger.info('Updating %s with %s new entrys!... This could take some time...',
                        dbcolName, str(updateSize))
        for i in range(updateSize):
            db.update_one({'_id': new[i]['date']}, {
                          "$set": new[i]}, upsert=True)

        logger.debug('Getting %s chart data from db', self.pair)
        # make dataframe
        df = pd.DataFrame(list(db.find({"_id": {"$gt": start}}
                                       ).sort('timestamp', pymongo.ASCENDING)))
        # set date column to datetime
        df['date'] = pd.to_datetime(df["_id"], unit='s')
        # adjust candle period 'zoom'
        if zoom:
            logger.debug('Zooming %s dataframe...', self.pair)
            df.set_index('date', inplace=True)
            df = df.resample(rule=zoom,
                             closed='left',
                             label='left').apply({'open': 'first',
                                                  'high': 'max',
                                                  'low': 'min',
                                                  'close': 'last',
                                                  'quoteVolume': 'sum',
                                                  'volume': 'sum',
                                                  'weightedAverage': 'mean'})
            df.reset_index(inplace=True)
        if indica:
            df = self.addIndicators(df, indica)
        return df

    def addIndicators(self, df, indica={}):
        # add indicators
        logger.debug('Adding indicators to %s dataframe', self.pair)
        # save macd for last if it is defined
        macdC = False
        if 'macd' in indica:
            macdC = indica.pop('macd')
        # fill df with indicators
        availInd = dir(indicators)
        for ind in indica:
            if ind in availInd:
                df = getattr(indicators, ind)(df, **indica[ind])
        # do macd last if it is defined
        if macdC:
            df = getattr(indicators, 'macd')(df, **macdC)
            indica['macd'] = macdC
        df['percentChange'] = df['close'].pct_change().round(8) * 100
        return df

    def myTradeHistory(self, query=None):
        """
        Retrives and saves trade history in "poloniex.'self.pair'-tradeHistory"
        """
        dbcolName = self.pair + '-tradeHistory'
        db = getMongoColl('poloniex', dbcolName)
        # get last trade
        old = {'date': time() - self.api.YEAR * 10}
        try:
            old = list(db.find().sort('date', pymongo.ASCENDING))[-1]
        except:
            logger.warning('No %s trades found in database', self.pair)
        # get new data from poloniex
        hist = self.api.returnTradeHistory(self.pair, start=old['date'] - 1)

        if len(hist) > 0:
            logger.debug('%d new %s trade database entries',
                         len(hist), self.pair)

            for trade in hist:
                _id = trade['globalTradeID']
                del trade['globalTradeID']
                trade['date'] = UTCstr2epoch(trade['date'])
                trade['amount'] = float(trade['amount'])
                trade['total'] = float(trade['total'])
                trade['tradeID'] = int(trade['tradeID'])
                trade['orderNumber'] = int(trade['orderNumber'])
                trade['rate'] = float(trade['rate'])
                trade['fee'] = float(trade['fee'])
                db.update_one({"_id": _id}, {"$set": trade}, upsert=True)

        df = pd.DataFrame(list(db.find(query).sort('date',
                                                   pymongo.ASCENDING)))
        if 'date' in df:
            df['date'] = pd.to_datetime(df["date"], unit='s')
            df.set_index('date', inplace=True)
        return df

    def myLendingHistory(self, coin=False, query=False):
        """
        Retrives and saves lendingHistory in 'poloniex.lendingHistory' database
        coin = coin to get history for (defaults to self.child)
        query = pymongo query for .find() (defaults to last 24 hours)
        """
        if not query:
            query = {'currency': coin, '_id': {'$gt': time() - self.api.DAY}}
        if not coin:
            coin = self.child
        db = getMongoColl('poloniex', 'lendingHistory')
        # get last entry timestamp
        old = {'open': time() - self.api.YEAR * 10}
        try:
            old = list(db.find({"currency": coin}).sort('open',
                                                        pymongo.ASCENDING))[-1]
        except:
            logger.warning(RD('No %s loan history found in database!'), coin)
        # get new entries
        new = self.api.returnLendingHistory(start=old['open'] - 1)
        nLoans = [loan for loan in new if loan['currency'] == coin]
        if len(nLoans) > 0:
            logger.info(GR('%d new lending database entries'), len(new))
            for loan in nLoans:
                _id = loan['id']
                del loan['id']
                loan['close'] = UTCstr2epoch(loan['close'])
                loan['open'] = UTCstr2epoch(loan['open'])
                loan['rate'] = float(loan['rate'])
                loan['duration'] = float(loan['duration'])
                loan['interest'] = float(loan['interest'])
                loan['fee'] = float(loan['fee'])
                loan['earned'] = float(loan['earned'])
                db.update_one({'_id': _id}, {'$set': loan}, upsert=True)
        return pd.DataFrame(list(db.find(query).sort('open',
                                                     pymongo.ASCENDING)))

    def cancelOrders(self, arg=False):
        """
        Generator method that cancels all orders for self.pair. Can be
        limited to just buy or sell orders using the 'arg' param,
        yields results from 'self.api.cancelOrder'
        """
        # get open orders for 'market'
        for order in self.openOrders:
            # if arg = 'sell' or 'buy' skip the orders not labeled as such
            if arg in ('sell', 'buy') and order['type'] != arg:
                continue
            # show output
            yield self.api.cancelOrder(order["orderNumber"])

    def addStopOrder(self, amount, stop, limit):
        """ adds a stop order to 'self.stops' and starts its thread """
        self.stops.append(StopLimit(self.api, self.pair)(amount, stop, limit))

    def cancelStopOrder(self, indx=False):
        """ cancels all stop orders within 'self.stops', or just <indx> """
        if indx:
            self.stops[indx].cancel()
        else:
            for stop in self.stops:
                stop.cancel()

    def dump(self, amount):
        """ Dumps childcoin <amount> at highestBid """
        if amount == 'all':
            amount = self.api.returnCompleteBalances(
                'exchange')[self.child]['available']
        while True:
            rate = self.tick['highestBid'] - (SATOSHI * 1000)
            try:
                if amount * rate < TRADE_MIN:
                    return logger.warning('Amount is below min')
                return self.api.sell(currencyPair=self.pair,
                                     rate=rate,
                                     amount=amount,
                                     orderType='fillOrKill')
            except PoloniexError as e:
                # log exceptions and keep trying
                logger.exception(e)
                continue

    def pump(self, amount):
        """ Pumps parentCoin <amount> at lowestAsk """
        if amount == 'all':
            amount = api.returnCompleteBalances(
                'exchange')[self.parent]['available']
        while True:
            rate = self.tick['lowestAsk'] + (SATOSHI * 1000)
            try:
                if amount < TRADE_MIN:
                    return logger.warning('Amount is below min')
                childAmt = amount / rate
                return api.sell(currencyPair=self.pair,
                                rate=rate,
                                amount=childAmt,
                                orderType='fillOrKill')
            except Exception as e:
                # log exceptions and keep trying
                logger.exception(e)
                continue

    def getOrder(self, orderNum):
        # is the order open?
        for order in self.openOrders:
            if int(order['orderNumber']) == int(orderNum):
                return order
        # else see if it made trades
        return self.myTradeHistory(query={'orderNumber': int(orderNum)})

    def moveToFront(self, orderNumber, offset=SATOSHI):
        order = self.getOrder(orderNumber)
        # if a dataframe is returned, the order is no longer open
        if isinstance(order, pd.DataFrame):
            try:
                logger.info('Order %d is no longer open...',
                            int(order.iloc[0]['orderNumber']))
                return order
            except IndexError:
                logger.warning('Not a known orderNumber for this market: %d',
                               int(orderNumber))
                return None
        # order is still open, move it
        if order['type'] == 'sell':
            rate = float(self.tick['lowestAsk'])
            # our order is already the front
            if rate == order['rate']:
                # move rate higher by offset
                rate += offset
            # order is not in front
            else:
                # move rate lower by offset
                rate += -offset
        if order['type'] == 'buy':
            rate = float(self.tick['highestBid'])
            # our order is already the front
            if rate == order['rate']:
                # move rate lower by offset
                rate += -offset
            # order is not in front
            else:
                # move rate higher by offset
                rate += offset
        logger.debug('Moving %s order %s', self.pair, str(orderNumber))
        return self.api.moveOrder(orderNumber, rate)


class RunningMarket(Market):
    """
    Subclass of Market that includes a thread and a start and stop method.
    Users should overwrite the 'self.run' method to use.
    """

    def __init__(self, *args, **kwargs):
        super(RunningMarket, self).__init__(*args, **kwargs)
        self.startTime = None

    @property
    def tradeHistory(self):
        if not self.startTime:
            return logger.error("%s doesn't seem to be running", self.pair)
        return self.myTradeHistory(query={"date": {"$gt": self.startTime}})

    def run(self):
        while self._running:
            sleep(5)

    def start(self, *args, **kwargs):
        """
        starts the 'self.run' method in a thread ('self._t'). Users need to
        overwrite 'self.run' with a loop of some kind. Use the 'self._running'
        flag to utilize the 'self.stop' method to break free from the loop.
        'self._running' is set to 'True' when 'self.start' is called.
        """
        self._t = Thread(target=self.run,
                         name=self.pair,
                         args=tuple(args),
                         kwargs=kwargs)
        self._t.daemon = True
        self._running = True
        self._t.start()
        self.startTime = time()
        logger.info('%s thread started', self.pair)

    def stop(self):
        """
        sets 'self._running' flag to 'False' and joins 'self._t' (the running
        thread)
        """
        self._running = False
        self._t.join()
        logger.info('%s thread joined', self.pair)
