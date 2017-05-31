from . import time, getMongoDb indica, logging, itemgetter
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
        self.pair = pair
        self.db = getMongoDb('poloCharts', self.pair)
        self.api = api
        self.period = kwargs.get('period', self.api.MINUTE * 5)

    def __call__(self):
        last = sorted(list(self.db.find()), key=itemgetter('_id'))[-1]

        # no entrys found
        if not last:
            logger.warning('%s collection is empty!', self.pair)
            raw = self.api.returnChartData(
                self.pair, period=self.period, start=time() - self.api.YEAR)
        else:
            since = time() - int(last['_id'])
            logger.debug(int(last['_id']))
            logger.debug(since)
            # too soon return old candles
            if since < self.period:
                logger.debug('Getting chart data from db')
                return sorted(list(self.db.find()), key=itemgetter('_id'))
            logger.debug('Getting new data')
            raw = self.api.returnChartData(
                self.pair, period=self.period, start=int(last['_id']))
        # add new candles
        updateSize = len(raw)
        logger.info('Updating %s with %s new entrys!',
                    self.pair, str(updateSize))
        for i in range(updateSize):
            date = raw[i]['date']
            del raw[i]['date']
            self.db.update_one({'_id': date}, {"$set": raw[i]}, upsert=True)
        logger.debug('Getting chart data from db')
        # return all
        return sorted(list(self.db.find()), key=itemgetter('_id'))

    def dataFrame(self, window=120):
        # get data from db
        data = self.__call__()
        # make dataframe
        df = pd.DataFrame(data)
        # format dates
        df['date'] = [pd.to_datetime(c['_id'], unit='s') for c in data]
        # del '_id'
        del df['_id']
        # set 'date' col as index
        df.set_index('date', inplace=True)
        # calculate/add sma and bbands
        df = bbands(df, window)
        # add slow ema
        df = ema(df, window // 4, colname='emaslow')
        # add fast ema
        df = ema(df, window // 2, colname='emafast')
        # add macd
        df = macd(df)
        # add rsi
        df = rsi(df, window // 2)
        # add candle body and shadow size
        df['bodysize'] = df['open'] - df['close']
        df['shadowsize'] = df['high'] - df['low']
        df['percentChange'] = df['close'].pct_change()
        return df

if __name__ == '__main__':
    from .poloniex import Poloniex
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("tools.poloniex").setLevel(logging.INFO)

    logging.getLogger('requests').setLevel(logging.ERROR)
    api = Poloniex(jsonNums=float)
    df = Chart(api, 'BTC_LTC').dataFrame()
    df.dropna(inplace=True)
    print(df.tail(30))
