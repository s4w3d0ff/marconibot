# core
from time import time, sleep
from operator import itemgetter
# local
from . import MongoClient, logger
from . import indica


class Chart(object):
    """ Saves and retrieves chart data for a market """

    def __init__(self, pair, api, **kwargs):
        """
        pair = market pair
        api = poloniex api object
        frame = time frame of chart (default: 7 Days)
        period = time period of candles (default: 30 Min)
        shortWin = number of candles to use for ema(s) (default: 30)
        midWin = number of candles to use for roc, rsi, wma (default: 60)
        longWin = number of candles to use for sma, bbands (default: 120)
        """
        self.db = MongoClient().poloniex['charts']
        self.pair = pair
        self.api = api
        self.frame = kwargs.get('frame', self.api.DAY * 7)
        self.period = kwargs.get('period', self.api.MINUTE * 30)
        self.shortWin = kwargs.get('shortWin', 30)
        self.midWin = kwargs.get('midWin', 60)
        self.longWin = kwargs.get('longWin', 120)
        self._lastUpdate = 0

    def __call__(self):
        if time() - self._lastUpdate > 60:
            logger.info('%s chart db updating...', self.pair)
            raw = self.api.returnChartData(
                self.pair, self.period, time() - self.frame)
            aves = [i['weightedAverage'] for i in raw]
            self._lastUpdate = time()
            self.db.update_one(
                {'_id': self.pair},
                {'$set': {
                    "frame": self.frame,
                    "period": self.period,
                    "shortWin": self.shortWin,
                    "midWin": self.midWin,
                    "longWin": self.longWin,
                    "raw": raw,
                    "timestamp": self._lastUpdate,
                    "weightedAvs": aves,
                    "dates": [i['date'] for i in raw],
                    "highs": [i['high'] for i in raw],
                    "lows": [i['low'] for i in raw],
                    "opens": [i['open'] for i in raw],
                    "closes": [i['close'] for i in raw],
                    "quoteVolumes": [i['quoteVolume'] for i in raw],
                    "volumes": [i['volume'] for i in raw],
                    "roc": indica.roc(aves, self.midWin).tolist(),
                    "rsi": indica.rsi(aves, self.midWin).tolist(),
                    "wma": indica.ma_env(aves, self.midWin, 0.1, 3).tolist(),
                    "sma": indica.ma_env(aves, self.longWin, 0.1, 4).tolist(),
                    "ema": indica.ma_env(aves, self.shortWin, 0.1, 0).tolist(),
                    "ema2": indica.ma_env(aves, self.shortWin - 10, 0.1, 1).tolist(),
                    "ema3": indica.ma_env(aves, self.shortWin + 10, 0.1, 2).tolist(),
                    "bbands": indica.bb(aves, self.longWin).tolist()},
                 }, upsert=True)
            logger.info('%s chart db updated!', self.pair)
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
        book = self.orderBook['asks']
        book.sort(key=itemgetter(1), reverse=True)
        return book[:7]

    @property
    def buywalls(self):
        book = self.orderBook['bids']
        book.sort(key=itemgetter(1), reverse=True)
        return book[:7]

    @property
    def lowestask(self):
        return self.api.returnTicker()[self.pair]['lowestAsk']

    @property
    def highestbid(self):
        return self.api.returnTicker()[self.pair]['highestBid']

    @property
    def last(self):
        return self.api.returnTicker()[self.pair]['last']

    @property
    def percentChange(self):
        return self.api.returnTicker()[self.pair]['percentChange']

    @property
    def baseVolume(self):
        return self.api.returnTicker()[self.pair]['baseVolume']

    @property
    def quoteVolume(self):
        return self.api.returnTicker()[self.pair]['quoteVolume']

    @property
    def volume24(self):
        return self.api.return24hVolume()[self.pair]


if __name__ == '__main__':
    # python -m bots.tools.data
    from poloniex import Poloniex
    market = Market(pair="usdt_btc", api=Poloniex(jsonNums=float))
    print(market.chart())
