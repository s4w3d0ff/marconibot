from tools import time, MongoClient, indica, logging, izip

logger = logging.getLogger(__name__)


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
        self.db.drop()
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
            self._lastUpdate = time()
            self.db.update_one(
                {'_id': self.pair},
                {'$set': {
                    "frame": self.frame,
                    "period": self.period,
                    "shortWin": self.shortWin,
                    "midWin": self.midWin,
                    "longWin": self.longWin,
                    "candles": self.extendChart(),
                    "timestamp": self._lastUpdate,
                }}, upsert=True)
            logger.info('%s chart db updated!', self.pair)
        return self.db.find_one({'_id': self.pair})

    def extendChart(self):
        raw = self.api.returnChartData(
            self.pair, self.period, time() - self.frame)
        aves = [i['weightedAverage'] for i in raw]
        for i, data in izip(range(len(raw)), indica.roc(aves, self.midWin).tolist()):
            raw[i]['roc'] = data
        for i, data in izip(range(len(raw)), indica.rsi(aves, self.midWin).tolist()):
            raw[i]['rsi'] = data
        for i, data in izip(range(len(raw)), indica.ma_env(aves, self.midWin, 0.1, 3).tolist()):
            raw[i]['wma'] = data
        for i, data in izip(range(len(raw)), indica.ma_env(aves, self.longWin, 0.1, 4).tolist()):
            raw[i]['sma'] = data
        for i, data in izip(range(len(raw)), indica.ma_env(aves, self.shortWin, 0.1, 0).tolist()):
            raw[i]['ema'] = data
        for i, data in izip(range(len(raw)), indica.ma_env(aves, self.shortWin - 10, 0.1, 1).tolist()):
            raw[i]['ema2'] = data
        for i, data in izip(range(len(raw)), indica.ma_env(aves, self.shortWin + 10, 0.1, 2).tolist()):
            raw[i]['ema3'] = data
        for i, data in izip(range(len(raw)), indica.bb(aves, self.longWin).tolist()):
            raw[i]['bbands'] = data
        return raw
