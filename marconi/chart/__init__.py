from tools import time, MongoClient, indica, logging, izip

logger = logging.getLogger(__name__)


class Chart(object):
    """ Saves and retrieves chart data for a market """

    def __init__(self, pair, api, **kwargs):
        """
        pair = market pair
        api = poloniex api object
        frame = time frame of chart (default: 1 Day)
        period = time period of candles (default: 5 Min)
        window = number of candles to use for roc, rsi, wma (default: 60)
        """
        self.db = MongoClient().poloniex['markets']
        self.pair = pair
        self.api = api
        self.frame = kwargs.get('frame', self.api.DAY)
        self.period = kwargs.get('period', self.api.MINUTE * 5)
        self.window = kwargs.get('window', 60)

    def __call__(self):
        try:  # look for old timestamp
            timestamp = self.db.find_one({
                '_id': self.pair})['chart']['timestamp']
        except Exception as e:  # not found
            logger.exception(e)
            timestamp = 0

        if time() - timestamp > 60 * 2:
            logger.info('%s chart db updating...', self.pair)
            raw = self.api.returnChartData(
                self.pair, self.period, time() - self.frame)
            aves = [i['weightedAverage'] for i in raw]
            # bbands is the shortest list (why??)
            # so slice the base data by bbands size (from rear)
            bbands = indica.bb(aves, self.window * 2).tolist()
            raw = raw[:len(bbands)]
            for i, data in izip(range(len(raw)), bbands):
                raw[i]['bbands'] = data
            for i, data in izip(
                    range(len(raw)), indica.roc(aves, self.window).tolist()):
                raw[i]['roc'] = data
            for i, data in izip(
                    range(len(raw)), indica.rsi(aves, self.window).tolist()):
                raw[i]['rsi'] = data
            for i, data in izip(
                    range(len(raw)),
                    indica.ma_env(aves, self.window, 0.1, 3).tolist()):
                raw[i]['wma'] = data
            for i, data in izip(
                    range(len(raw)),
                    indica.ma_env(aves, self.window * 2, 0.1, 4).tolist()):
                raw[i]['sma'] = data
            for i, data in izip(
                    range(len(raw)),
                    indica.ma_env(aves, self.window // 2, 0.1, 0).tolist()):
                raw[i]['ema'] = data
            for i, data in izip(
                    range(len(raw)),
                    indica.ma_env(aves, (self.window // 2) - 10, 0.1, 1).tolist()):
                raw[i]['ema2'] = data
            for i, data in izip(
                    range(len(raw)),
                    indica.ma_env(aves, (self.window // 2) + 10, 0.1, 2).tolist()):
                raw[i]['ema3'] = data

            self.db.update_one(
                {'_id': self.pair},
                {'$set': {
                    "chart": {
                        "frame": self.frame,
                        "period": self.period,
                        "window": self.window,
                        "candles": raw,
                        "timestamp": time()}}
                 },
                upsert=True)
            logger.info('%s chart db updated!', self.pair)
        return self.db.find_one({'_id': self.pair})['chart']
