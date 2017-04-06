from . import time, MongoClient, indica, logger


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
