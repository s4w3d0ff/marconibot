from tools import time, getMongoDb, logging, itemgetter
from tools import pd, np, figure, output_file, PI
from tools.indicators import ema, macd, bbands, rsi
from bokeh.models import LinearAxis, Range1d
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
        """ returns pandas DataFrame from raw db data with indicators"""
        # get data from db
        data = self.__call__(size)
        # make dataframe
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df["_id"], unit='s')
        df.set_index('_id', inplace=True)
        # calculate/add sma and bbands
        df = bbands(df, window)
        # add slow ema
        slowWin = window // 2
        df = ema(df, slowWin, colname='emaslow')
        # add fast ema
        df = ema(df, slowWin // 4, colname='emafast')
        # add macd
        df = macd(df)
        # add rsi
        df = rsi(df, window // 5)
        # add candle body and shadow size
        df['bodysize'] = df['open'] - df['close']
        df['shadowsize'] = df['high'] - df['low']
        df['percentChange'] = df['close'].pct_change()
        return df

    def graph(self, size=0, window=120):
        df = self.dataFrame(size, window)
        df.dropna(inplace=True)

        output_file("%s.html" % self.pair,
                    title="%s-Poloniex" % self.pair)

        p = figure(x_axis_type="datetime",
                   y_range=(min(df['low'].values),
                            max(df['high'].values)),
                   tools="pan,wheel_zoom,box_zoom,reset,save",
                   plot_width=1500,
                   title=self.pair)

        p.extra_y_ranges = {
            "volume": Range1d(start=1,
                              end=max(df['volume'].values))
        }

        candleWidth = (self.period * 1000) - self.period * 100

        p.xaxis.major_label_orientation = PI / 4
        p.grid.grid_line_alpha = 0.8

        # Plot volume
        p.vbar(x=df['date'],
               width=candleWidth,
               top=df['volume'],
               bottom=0,
               fill_color="blue",
               alpha=0.2,
               y_range_name="volume")

        #p.add_layout(LinearAxis(y_range_name="volume"), 'left')

        # Plot candle 'shadows'/wicks
        p.segment(x0=df.date,
                  y0=df.high,
                  x1=df.date,
                  y1=df.low,
                  color="black",
                  line_width=1)

        # Plot green candles
        inc = df.close > df.open
        p.vbar(x=df.date[inc],
               width=candleWidth,
               top=df.open[inc],
               bottom=df.close[inc],
               fill_color="green",
               line_color="black"
               )

        # Plot red candles
        dec = df.open > df.close
        p.vbar(x=df.date[dec],
               width=candleWidth,
               top=df.open[dec],
               bottom=df.close[dec],
               fill_color="red",
               line_color="black")

        # Plot bbands
        band_x = np.append(df['date'].values, df['date'].values[::-1])
        band_y = np.append(df['bbbottom'].values, df['bbtop'].values[::-1])
        p.patch(band_x,
                band_y,
                color='navy',
                fill_alpha=0.1)

        # Plot moving averages
        p.line(df['date'], df['sma'], color='navy',
               alpha=0.9)
        p.line(df['date'], df['emaslow'], color='orange',
               alpha=0.9)
        p.line(df['date'], df['emafast'], color='red',
               alpha=0.9)

        return p

if __name__ == '__main__':
    from tools.poloniex import Poloniex
    from tools import show

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("tools.poloniex").setLevel(logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)

    period = 60 * 60 * 24

    api = Poloniex(jsonNums=float)
    p = Chart(api, 'BTC_ETH', period=period).graph(window=120)
    show(p)
