from . import time, getMongoDb, indica, logging
from . import pd, np
from .indicators import ema, macd, bbands, rsi

logger = logging.getLogger(__name__)


class Chart(object):
    """ Saves and retrieves chart data for a market """

    def __init__(self, api, pair, **kwargs):
        """
        pair = market pair
        api = poloniex api object
        frame = time frame of chart (default: 1 Day)
        period = time period of candles (default: 5 Min)
        window = number of candles to use for roc, rsi, wma (default: 60)
        """
        self.db = getMongoDb('markets')
        self.pair = pair
        self.api = api
        self.frame = kwargs.get('frame', self.api.DAY * 3)
        self.period = kwargs.get('period', self.api.MINUTE * 5)
        self.window = kwargs.get('window', 80)

    def __call__(self):
        try:  # look for old timestamp
            timestamp = self.db.find_one({
                '_id': self.pair})['chart']['timestamp']
        except:  # not found
            timestamp = 0
        if time() - timestamp > 60:
            logger.info('%s chart db updating...', self.pair)
            raw = self.api.returnChartData(
                self.pair, self.period, time() - self.frame)
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

    def dataFrame(self):
        data = self.__call__()['candles']
        df = pd.DataFrame(data)
        df['date'] = [pd.to_datetime(c['date'], unit='s') for c in data]
        df.set_index('date', inplace=True)
        dfsize = len(list(df['open']))
        df = bbands(df, self.window)
        df = ema(df, self.window, colname='emaslow')
        df = ema(df, self.window // 2, colname='emafast')
        df = macd(df)
        df = rsi(df, self.window // 2)
        df['bodysize'] = df['open'] - df['close']
        df['shadowsize'] = df['high'] - df['low']
        return df.dropna()

if __name__ == '__main__':
    from .poloniex import Poloniex
    logging.basicConfig(level=logging.DEBUG)
    api = Poloniex(jsonNums=float)
    chart = Chart(api, 'BTC_LTC')
    df = chart.dataFrame()
    print(df[['weightedAverage', 'macd', 'bbpercent', 'rsi']].tail(50))
