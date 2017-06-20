from tools import time, getMongoDb, logging, itemgetter
from tools import pd, np, figure, output_file, PI
from tools.indicators import ema, macd, bbands, rsi
from bokeh.models import LinearAxis, Range1d
logger = logging.getLogger(__name__)


class Charter(object):
    """ Retrieves chart data for a market and saves it in a mongo db collection
        based on market name and candle period. It also remembers the last
        called market and period when called multiple times. """

    def __init__(self, api, pair, **kwargs):
        """
        api = poloniex api object
        pair = market pair
        period = time period of candles (default: 5 Min)
        """
        self.pair = pair
        self.api = api
        self.period = kwargs.get('period', self.api.MINUTE * 5)

    def __call__(self, pair=False, period=False, size=0):
        """ returns raw chart data from the mongo database, updates/fills the
        data if needed, the date column is the '_id' of each candle entry, and
        the date column has been removed """
        # use last pair and period if not specified
        if not pair:
            pair = self.pair
        if not period:
            period = self.period
        # 'remember' the last period, pair
        self.period = period
        self.pair = pair
        # get db connection
        dbcolName = pair + '-' + str(period)
        db = getMongoDb('poloCharts', dbcolName)
        # get old candles from db
        old = sorted(list(db.find()), key=itemgetter('_id'))
        # get last candle
        try:
            last = old[-1]
        except:
            last = False
        # no entrys found, get all data
        if not last:
            logger.warning('%s collection is empty!', dbcolName)
            new = self.api.returnChartData(pair,
                                           period=period,
                                           start=time() - self.api.YEAR * 6)

        else:
            since = time() - int(last['_id'])
            # too soon return old candles
            if since < period:
                logger.debug('Too soon to update candles')
                return old[-size:]
            logger.debug('Getting new data')
            # get just what we need to add to the db
            new = self.api.returnChartData(pair,
                                           period=period,
                                           start=int(last['_id']) + period)
        # add new candles
        updateSize = len(new)
        logger.info('Updating %s with %s new entrys!',
                    dbcolName, str(updateSize))

        # show the progess
        for i in range(updateSize):
            print("\r%s/%s" % (str(i + 1), str(updateSize)), end=" complete ")
            date = new[i]['date']
            del new[i]['date']
            db.update_one({'_id': date}, {"$set": new[i]}, upsert=True)
        print('')

        logger.debug('Getting chart data from db')
        # return data from db (sorted just in case...)
        return sorted(list(db.find()), key=itemgetter('_id'))[-size:]

    def dataFrame(self, pair=False, period=False, size=0, window=120):
        """ returns pandas DataFrame from raw db data with indicators """
        # get data from db
        data = self.__call__(pair, period, size)
        # make dataframe
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df["_id"], unit='s')
        df.set_index('_id', inplace=True)
        # calculate/add sma and bbands
        df = bbands(df, window)
        # add slow ema
        df = ema(df, window, colname='emaslow')
        # add fast ema
        df = ema(df, window // 3, colname='emafast')
        # add macd
        df = macd(df)
        # add rsi
        df = rsi(df, window // 7)
        # add candle body and shadow size
        df['bodysize'] = df['open'] - df['close']
        df['shadowsize'] = df['high'] - df['low']
        df['percentChange'] = df['close'].pct_change()
        df.fillna(df.mean(), inplace=True)
        return df

    def graph(self, pair=False, period=False, size=0, window=120):
        df = self.dataFrame(pair, period, size, window)
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
            "volume": Range1d(start=0,
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

    api = Poloniex(jsonNums=float)
    p = Charter(api, 'BTC_ETH', period=api.DAY).graph(size=365 * 2, window=120)
    show(p)
