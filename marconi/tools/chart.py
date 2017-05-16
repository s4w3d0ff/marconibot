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
        frame = time frame of chart (default: 3 Days)
        period = time period of candles (default: 5 Min)
        window = period for moving averages (default: 120)
        """
        self.db = getMongoDb('markets')
        self.pair = pair
        self.api = api
        self.frame = kwargs.get('frame', self.api.DAY * 3)
        self.period = kwargs.get('period', self.api.MINUTE * 5)
        self.window = kwargs.get('window', 120)

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
        # get data from db
        data = self.__call__()['candles']
        # make dataframe
        df = pd.DataFrame(data)
        # format dates
        df['date'] = [pd.to_datetime(c['date'], unit='s') for c in data]
        # set 'date' col as index
        df.set_index('date', inplace=True)
        # calculate/add sma and bbands
        df = bbands(df, self.window)
        # add slow ema
        df = ema(df, self.window // 4, colname='emaslow')
        # add fast ema
        df = ema(df, self.window // 2, colname='emafast')
        # add macd
        df = macd(df)
        # add rsi
        df = rsi(df, self.window // 2)
        # add candle body and shadow size
        df['bodysize'] = df['open'] - df['close']
        df['shadowsize'] = df['high'] - df['low']
        return df.dropna()

if __name__ == '__main__':
    from .poloniex import Poloniex
    logging.basicConfig(level=logging.DEBUG)
    api = Poloniex(jsonNums=float)
    chart = Chart(api, 'BTC_LTC')
    df = chart.dataFrame()
    print(df[['shadowsize', 'macd', 'bbpercent', 'rsi']].head(30))
    print(df[['shadowsize', 'macd', 'bbpercent', 'rsi']].tail(30))
