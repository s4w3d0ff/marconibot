from tools import time, getMongoDb, logging, itemgetter
from tools import pd, np, figure, ColumnDataSource
from tools.indicators import ema, macd, bbands, rsi

from bokeh.layouts import gridplot
from bokeh.models import NumeralTickFormatter
from bokeh.models import HoverTool
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


def plotRSI(p, df, period, upcolor='green', downcolor='red'):
    p.extra_y_ranges = {"rsi": Range1d(start=0,
                                       end=100)
                        }
    p.add_layout(LinearAxis(y_range_name="rsi"), 'right')
    band_x = np.append(df['date'].values, df['date'].values[::-1])
    band_y = np.append([30 for i in df['rsi'].values],
                       [70 for i in df['rsi'].values[::-1]])
    p.patch(band_x,
            band_y,
            color='olive',
            fill_alpha=0.1,
            legend="rsi",
            y_range_name="rsi")
    candleWidth = (period * 900)
    # plot green bars
    inc = df.rsi >= 50
    p.vbar(x=df.date[inc],
           width=candleWidth,
           top=df.rsi[inc],
           bottom=50,
           fill_color=upcolor,
           line_color=upcolor,
           alpha=0.2,
           y_range_name="rsi")
    # Plot red bars
    dec = df.rsi <= 50
    p.vbar(x=df.date[dec],
           width=candleWidth,
           top=50,
           bottom=df.rsi[dec],
           fill_color=downcolor,
           line_color=downcolor,
           alpha=0.2,
           y_range_name="rsi")


def plotMACD(p, df):
    p.line(df['date'], df['macd'], color='blue',
           alpha=0.9, legend="macd")


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

    def __call__(self, pair=False, period=False, frame=False):
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
        if not frame:
            frame = period * 50
        # get db connection
        dbcolName = pair + '-' + str(period)
        db = getMongoDb('poloniexCharts', dbcolName)
        # get old candles from db
        old = sorted(
            list(db.find({"_id": {"$gt": time() - frame}})),
            key=itemgetter('_id'))
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
                                           start=time() - self.api.YEAR * 13)
        else:
            new = self.api.returnChartData(pair,
                                           period=period,
                                           start=int(last['_id']))
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
        return sorted(
            list(db.find({"_id": {"$gt": time() - frame}})),
            key=itemgetter('_id'))

    def dataFrame(self, pair=False, period=False,
                  frame=False, window=120, raw=False):
        """ returns pandas DataFrame from raw db data with indicators """
        data = raw
        # get data from db
        if not raw:
            data = self.__call__(pair, period, frame)
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
        df.dropna(inplace=True)
        return df

    def graph(self, pair=False, period=False, frame=False,
              window=120, volume=False, bands=False,
              maves=False, plotWidth=1300):
        df = self.dataFrame(pair, period, frame, window)
        # create candlestick plot
        candlePlot = figure(x_axis_type="datetime",
                            # x_minor_ticks=1000,
                            y_range=(min(df['low'].values) - (min(df['low'].values) * 0.2),
                                     max(df['high'].values) * 1.2),
                            tools="pan,wheel_zoom,reset",
                            title=self.pair + '-' + str(self.period),
                            plot_width=plotWidth,
                            plot_height=int(plotWidth // 2),
                            toolbar_location="above")

        candlePlot.background_fill_color = "black"
        candlePlot.background_fill_alpha = 0.15
        candlePlot.border_fill_color = "whitesmoke"
        candlePlot.min_border_left = 40
        candlePlot.min_border_right = 40
        if volume:
            plotVolume(candlePlot, df, self.period)
        plotCandlesticks(candlePlot, df, self.period)
        if bands:
            plotBBands(candlePlot, df)
        if maves:
            plotMovingAverages(candlePlot, df)
        candlePlot.xaxis.major_label_orientation = PI / 4
        candlePlot.yaxis[0].formatter = NumeralTickFormatter(
            format='0.00000000')
        candlePlot.legend.location = "top_left"

        # create a new plot and share x range
        rsiPlot = figure(plot_height=200,
                         x_axis_type=None,
                         y_range=(-(max(df['macd'].values) * 2),
                                  max(df['macd'].values) * 2),
                         x_range=candlePlot.x_range,
                         plot_width=candlePlot.plot_width,
                         title=None,
                         toolbar_location=None)

        rsiPlot.background_fill_color = "black"
        rsiPlot.background_fill_alpha = 0.15
        rsiPlot.border_fill_color = "whitesmoke"
        rsiPlot.min_border_left = 40
        rsiPlot.min_border_right = 40
        rsiPlot.min_border_bottom = 20
        plotMACD(rsiPlot, df)
        plotRSI(rsiPlot, df, self.period)
        rsiPlot.yaxis[0].formatter = NumeralTickFormatter(
            format='0.00000000')
        rsiPlot.legend.location = "top_left"

        p = gridplot([[candlePlot], [rsiPlot]])

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
                    'BTC_LTC',
                    period=api.DAY).graph(window=60,
                                          bands=True,
                                          volume=True,
                                          maves=True,
                                          frame=api.MONTH * 12)

    show(p)
