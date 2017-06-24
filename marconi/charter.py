from tools import time, getMongoDb, logging, itemgetter
from tools import pd, np, figure
from tools.indicators import ema, macd, bbands, rsi

from bokeh.models import LinearAxis, Range1d

logger = logging.getLogger(__name__)


def plotVolume(p, df, period, color='blue'):
    candleWidth = (period * 900)
    p.extra_y_ranges = {"volume": Range1d(start=min(df['volume'].values),
                                          end=max(df['volume'].values))
                        }
    p.add_layout(LinearAxis(y_range_name="volume"), 'right')
    # Plot volume
    p.vbar(x=df['date'],
           width=candleWidth,
           top=df['volume'],
           bottom=0,
           fill_color=color,
           alpha=0.2,
           y_range_name="volume")


def plotCandlesticks(p, df, period, upcolor='green', downcolor='red'):
    candleWidth = (period * 900)
    # Plot candle 'shadows'/wicks
    p.segment(x0=df.date,
              y0=df.high,
              x1=df.date,
              y1=df.low,
              color="black",
              line_width=4)
    # Plot green candles
    inc = df.close > df.open
    p.vbar(x=df.date[inc],
           width=candleWidth,
           top=df.open[inc],
           bottom=df.close[inc],
           fill_color=upcolor,
           line_color="black")
    # Plot red candles
    dec = df.open > df.close
    p.vbar(x=df.date[dec],
           width=candleWidth,
           top=df.open[dec],
           bottom=df.close[dec],
           fill_color=downcolor,
           line_color="black")


def plotBBands(p, df, color='navy'):
    # Plot bbands
    band_x = np.append(df['date'].values, df['date'].values[::-1])
    band_y = np.append(df['bbbottom'].values, df['bbtop'].values[::-1])
    p.patch(band_x,
            band_y,
            color=color,
            fill_alpha=0.1,
            legend="bband")
    p.line(df['date'], df['sma'], color=color,
           alpha=0.9, legend="sma")


def plotMovingAverages(p, df):
    # Plot moving averages
    p.line(df['date'], df['emaslow'], color='orange',
           alpha=0.9, legend="emaslow")
    p.line(df['date'], df['emafast'], color='red',
           alpha=0.9, legend="emafast")


class Charter(object):
    """ Retrieves chart data for a market and saves it in a mongo db collection
        based on market name and candle period. It also remembers the last
        called market and period when called multiple times. """

    def __init__(self, api, pair='USDT_BTC', **kwargs):
        """
        api = poloniex api object
        pair = market pair
        period = time period of candles (default: 5 Min)
        """
        self.api = api
        self.pair = pair
        self.period = kwargs.get('period', self.api.DAY)

    def __call__(self, pair=False, period=False):
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
        return sorted(list(db.find()), key=itemgetter('_id'))

    def dataFrame(self, pair=False, period=False, size=0, window=120, raw=False):
        """ returns pandas DataFrame from raw db data with indicators """
        data = raw
        # get data from db
        if not raw:
            data = self.__call__(pair, period)
        # make dataframe
        df = pd.DataFrame(data)
        # set date column
        df['date'] = pd.to_datetime(df["_id"], unit='s')
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
        df['bodysize'] = df['close'] - df['open']
        df['shadowsize'] = df['high'] - df['low']
        df['percentChange'] = df['close'].pct_change()
        df.fillna(df.mean(), inplace=True)[-size:]
        return df

    def graph(self, pair=False, period=False, size=0,
              window=120, volume=False, bands=False,
              maves=False, figargs=False):
        df = self.dataFrame(pair, period, size, window)

        if not figargs:
            p = figure(x_axis_type="datetime",
                       x_minor_ticks=1000,
                       y_range=(min(df['low'].values),
                                max(df['high'].values)),
                       tools="pan,wheel_zoom,reset",
                       title=self.pair,
                       plot_width=1500,
                       toolbar_location="above")
        else:
            p = figure(**figargs)

        if volume:
            plotVolume(p, df, self.period)

        plotCandlesticks(p, df, self.period)

        if bands:
            plotBBands(p, df)
        if maves:
            plotMovingAverages(p, df)

        df.set_index('date', inplace=True)
        return p, df


if __name__ == '__main__':
    from tools.poloniex import Poloniex
    from tools import show, PI

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("tools.poloniex").setLevel(logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)

    api = Poloniex(jsonNums=float)

    p, df = Charter(api,
                    'BTC_DOGE',
                    period=api.DAY).graph(bands=True, volume=True, maves=True)

    p.xaxis.major_label_orientation = PI / 4
    p.grid.grid_line_alpha = 0.8

    show(p)
