# core
from time import time
from operator import itemgetter
from decimal import Decimal
# 3rd party
from pymongo import MongoClient
# local
from __init__.indica import roc, rsi, ma_env, bb


class Chart(object):

    def __init__(self, **kwargs):
        self.db = MongoClient().poloniex['charts']
        self.pair = kwargs.get('pair')
        self.api = kwargs.get('api')
        self.frame = kwargs.get('frame', self.api.DAY * 7)
        self.period = kwargs.get('period', self.api.MINUTE * 30)
        self.window = kwargs.get('window', 30)
        self._lastUpdate = 0
        self.updateDb()

    def updateDb(self):
        raw = self.api.returnChartData(
            self.pair, self.period, time() - self.frame)
        aves = [i['weightedAverage'] for i in raw]
        self._lastUpdate = time()
        self.db.update_one(
            {'_id': self.pair},
            {'$set': {
                "frame": self.frame,
                "period": self.period,
                "window": self.window,
                "raw": raw,
                "timestamp": self._lastUpdate,
                "weightedAvs": aves,
                "dates": [i['date'] for i in raw],
                "highs": [i['high'] for i in raw],
                "lows": [i['low'] for i in raw],
                "opens": [i['open'] for i in raw],
                "closes": [i['close'] for i in raw],
                "quoteVolumes": [i['quoteVolume'] for i in raw],
                "volumes", [i['volume'] for i in raw],
                "roc": roc(aves, self.window),
                "rsi": rsi(aves, self.window),
                "wma": ma_env(aves, self.window, 0.1, 3),
                "sma": ma_env(aves, self.window, 0.1, 4),
                "ema": ma_env(aves, self.window, 0.1, 0),
                "ema2": ma_env(aves, self.window, 0.1, 1),
                "ema3": ma_env(aves, self.window, 0.1, 2),
                "bbands": bb(aves, self.window)},
             }, upsert=True)

    def __call__(self):
        if time() - self._lastUpdate > 60:
            self.updateDb()
        return self.db.find_one({'_id': self.pair})


class Market(object):
    """ Holds data for a market <pair> """

    def __init__(self, pair, **kwargs):
        self.pair = pair.upper()
        kwargs['pair'] = pair.upper()
        self.api = kwargs.get('api')
        self.chart = Chart(**kwargs)

    @property
    def balances(self):
        coins = self.pair.split('_')
        bals = self.api.returnCompleteBalances()
        return [bals[coins[0]], bals[coins[1]]]

    @property
    def openOrders(self):
        return self.api.returnOpenOrders(self.pair)

    @property
    def orderBook(self):
        return self.api.returnOrderBook(self.pair, 50)

    @property
    def sellwalls(self):
        return self.orderBook['asks'].sort(key=itemgetter(1), reverse=True)[:10]

    @property
    def buywalls(self):
        return self.orderBook['bids'].sort(key=itemgetter(1), reverse=True)[:10]

    @property
    def lowestask(self):
        return float(self.api.returnTicker()[self.pair]['lowestAsk'])

    @property
    def highestbid(self):
        return float(self.api.returnTicker()[self.pair]['highestBid'])

    @property
    def last(self):
        return float(self.api.returnTicker()[self.pair]['last'])

    @property
    def percentChange(self):
        return float(self.api.returnTicker()[self.pair]['percentChange)'])

    @property
    def baseVolume(self):
        return float(self.api.returnTicker()[self.pair]['baseVolume'])

    @property
    def quoteVolume(self):
        return float(self.api.returnTicker()[self.pair]['quoteVolume'])

    @property
    def volume24(self):
        return self.api.return24hVolume()[self.pair]

    def updateChart(self, **kwargs):
        """
        Updates the chart data, if no aguments are passed, the old chart
        params are used but with updated data.
        """
        for i in ['frame', 'period', 'window', 'pair', 'api']:
            if i not in kwargs:
                kwargs[i] = getattr(self.chart, i)
        self.chart = Chart(**kwargs)

    def getScore(self):
