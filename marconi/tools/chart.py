from . import time, getMongoDb, indica, logging, addDoji, pd, np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.style.use('ggplot')

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
        self.frame = kwargs.get('frame', self.api.DAY * 7)
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

    def getDataFrame(self):
        data = self.__call__()['candles']
        df = pd.DataFrame(data)
        df['date'] = [pd.to_datetime(c['date'], unit='s') for c in data]
        df.set_index('date', inplace=True)
        return df

    def withIndicators(self):
        df = self.getDataFrame()
        # get raw data
        dfsize = len(list(df['open']))
        df['bodysize'] = df['open'] - df['close']
        # candle shadow/wick size
        df['shadowsize'] = df['high'] - df['low']
        df['sma'] = df['weightedAverage'].rolling(
            window=self.window, center=False).mean()
        df['emaslow'] = df['weightedAverage'].ewm(
            span=self.window,
            min_periods=1,
            adjust=True,
            ignore_na=False).mean()
        df['emafast'] = df['weightedAverage'].ewm(
            span=self.window // 2,
            min_periods=1,
            adjust=True,
            ignore_na=False).mean()
        df['macd'] = df['emafast'] - df['emaslow']
        # get roc
        roc = indica.roc(list(df['weightedAverage']), 1).tolist()
        df['roc'] = roc + [np.nan for i in range(dfsize - len(roc))]
        # get rsi
        rsi = indica.rsi(list(df['weightedAverage']), 5).tolist()
        df['rsi'] = [np.nan for i in range(dfsize - len(rsi))] + rsi
        # get bbands
        df['bbtop'] = df['sma'] + 2.0 * \
            df['weightedAverage'].rolling(
                min_periods=self.window, window=self.window, center=False).std()
        df['bbbottom'] = df['sma'] - 2.0 * \
            df['weightedAverage'].rolling(
                min_periods=self.window, window=self.window, center=False).std()
        df['bbrange'] = df['bbtop'] - df['bbbottom']
        df['bbpercent'] = ((df['weightedAverage'] -
                            df['bbbottom']) / df['bbrange']) - 0.5
        return df

if __name__ == '__main__':
    from .poloniex import Poloniex
    logging.basicConfig(level=logging.DEBUG)
    api = Poloniex(jsonNums=float)
    chart = Chart(api, 'BTC_LTC')
    df = chart.withIndicators()
    print(df[['sma', 'emafast', 'rsi', 'macd', 'bbpercent']].tail(20))
    print(df[['sma', 'emafast', 'rsi', 'macd', 'bbpercent']].head(20))
