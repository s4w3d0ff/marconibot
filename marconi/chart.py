from tools import time, getMongoDb, logging, itemgetter
from tools import pd, np
from tools.indicators import ema, macd, bbands, rsi
logger = logging.getLogger(__name__)


class Chart(object):
    """ Saves and retrieves chart data for a market """

    def __init__(self, api, pair, **kwargs):
        """
        pair = market pair
        api = poloniex api object
        period = time period of candles (default: 5 Min)
        """
        self.pair = pair
        self.api = api
        self.period = kwargs.get('period', self.api.MINUTE * 5)
        self.db = getMongoDb('poloCharts', self.pair + '-' + str(self.period))

    def __call__(self, size=0):
        old = sorted(list(self.db.find()), key=itemgetter('_id'))
        try:
            last = old[-1]
        except:
            last = False
        # no entrys found
        if not last:
            logger.warning('%s collection is empty!',
                           self.pair + str(self.period))
            new = self.api.returnChartData(self.pair,
                                           period=self.period,
                                           start=time() - self.api.YEAR)
        else:
            since = time() - int(last['_id'])
            logger.debug(int(last['_id']))
            logger.debug(since)
            # too soon return old candles
            if since < self.period:
                logger.debug('Too soon to update candles')
                return old[-size:]
            logger.debug('Getting new data')
            new = self.api.returnChartData(self.pair,
                                           period=self.period,
                                           start=int(last['_id']) + self.period)
        # add new candles
        updateSize = len(new)
        logger.info('Updating %s with %s new entrys!',
                    self.pair + str(self.period), str(updateSize))
        for i in range(updateSize):
            print("\r%s/%s" % (str(i + 1), str(updateSize)), end=" complete ")
            date = new[i]['date']
            del new[i]['date']
            self.db.update_one({'_id': date}, {"$set": new[i]}, upsert=True)
        print('')
        logger.debug('Getting chart data from db')
        # return data from db
        return sorted(list(self.db.find()), key=itemgetter('_id'))[-size:]

    def dataFrame(self, size=0, window=120):
        # get data from db
        data = self.__call__(size)
        # make dataframe
        df = pd.DataFrame(data)
        print(df.tail())
        df['date'] = pd.to_datetime(df["_id"], unit='s')
        df.set_index('_id', inplace=True)
        # calculate/add sma and bbands
        df = bbands(df, window)
        # add slow ema
        df = ema(df, window // 2, colname='emaslow')
        # add fast ema
        df = ema(df, window // 4, colname='emafast')
        # add macd
        df = macd(df)
        # add rsi
        df = rsi(df, window // 5)
        # add candle body and shadow size
        df['bodysize'] = df['open'] - df['close']
        df['shadowsize'] = df['high'] - df['low']
        df['percentChange'] = df['close'].pct_change()
        return df

if __name__ == '__main__':
    from tools.poloniex import Poloniex
    from tools import PI, figure, output_file, show

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("tools.poloniex").setLevel(logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)

    period = 60 * 60 * 4
    w = (period * 1000) - 5000
    TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
    output_file("BTC_ETH.html", title="BTC_ETH-Poloniex")

    api = Poloniex(jsonNums=float)
    df = Chart(api, 'BTC_ETH', period=period).dataFrame(250, window=80)

    df.dropna(inplace=True)
    print(df.tail())

    inc = df.close > df.open
    dec = df.open > df.close

    p = figure(x_axis_type="datetime", tools=TOOLS,
               plot_width=1500, title="BTC_ETH")

    p.xaxis.major_label_orientation = PI / 4
    p.grid.grid_line_alpha = 0.7

    p.segment(df.date, df.high, df.date, df.low, color="black")

    p.vbar(df.date[inc], w, df.open[inc], df.close[inc],
           fill_color="green", line_color="black")
    p.vbar(df.date[dec], w, df.open[dec], df.close[dec],
           fill_color="red", line_color="black")

    p.line(df['date'], df['sma'], color='navy', alpha=0.5)
    p.line(df['date'], df['bbtop'], color='red', alpha=0.9)
    p.line(df['date'], df['bbbottom'], color='red', alpha=0.9)

    show(p)
