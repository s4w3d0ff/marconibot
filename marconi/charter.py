from tools import time, getMongoDb, logging, itemgetter
from tools import pd, np, figure
from tools.indicators import ema, macd, bbands, rsi

from bokeh.models import NumeralTickFormatter
from bokeh.models import LinearAxis, Range1d

logger = logging.getLogger(__name__)


def plotRSI(p, df, period, upcolor='green', downcolor='red'):
    # create y axis for rsi
    p.extra_y_ranges = {"rsi": Range1d(start=0, end=100)}
    p.add_layout(LinearAxis(y_range_name="rsi"), 'right')

    # create rsi 'zone' (30-70)
    p.patch(np.append(df['date'].values, df['date'].values[::-1]),
            np.append([30 for i in df['rsi'].values],
                      [70 for i in df['rsi'].values[::-1]]),
            color='olive',
            fill_alpha=0.2,
            legend="rsi",
            y_range_name="rsi")

    candleWidth = (period * 800)
    # plot green bars
    inc = df.rsi >= 50
    p.vbar(x=df.date[inc],
           width=candleWidth,
           top=df.rsi[inc],
           bottom=50,
           fill_color=upcolor,
           line_color=upcolor,
           alpha=0.5,
           y_range_name="rsi")
    # Plot red bars
    dec = df.rsi <= 50
    p.vbar(x=df.date[dec],
           width=candleWidth,
           top=50,
           bottom=df.rsi[dec],
           fill_color=downcolor,
           line_color=downcolor,
           alpha=0.5,
           y_range_name="rsi")


def plotMACD(p, df, color='blue'):
    # plot macd
    p.line(df['date'], df['macd'], line_width=4,
           color=color, alpha=0.8, legend="macd")
    p.yaxis[0].formatter = NumeralTickFormatter(format='0.00000000')


def plotCandlesticks(p, df, period, upcolor='green', downcolor='red'):
    candleWidth = (period * 750)
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
    # format price labels
    p.yaxis[0].formatter = NumeralTickFormatter(format='0.00000000')


def plotVolume(p, df, period, color='blue'):
    candleWidth = (period * 800)
    # create new y axis for volume
    p.extra_y_ranges = {"volume": Range1d(start=min(df['volume'].values),
                                          end=max(df['volume'].values))}
    p.add_layout(LinearAxis(y_range_name="volume"), 'right')
    # Plot volume
    p.vbar(x=df['date'],
           width=candleWidth,
           top=df['volume'],
           bottom=0,
           fill_color=color,
           alpha=0.2,
           y_range_name="volume")


def plotBBands(p, df, color='navy'):
    # Plot bbands
    p.patch(np.append(df['date'].values, df['date'].values[::-1]),
            np.append(df['bbbottom'].values, df['bbtop'].values[::-1]),
            color=color,
            fill_alpha=0.1,
            legend="bband")
    # plot sma
    p.line(df['date'], df['sma'], color=color, alpha=0.9, legend="sma")


def plotMovingAverages(p, df):
    # Plot moving averages
    p.line(df['date'], df['emaslow'],
           color='orange', alpha=0.9, legend="emaslow")
    p.line(df['date'], df['emafast'],
           color='red', alpha=0.9, legend="emafast")


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
            frame = self.api.YEAR
        # get db connection
        dbcolName = pair + '-' + str(period)
        db = getMongoDb('poloniexCharts', dbcolName)
        # get last candle
        try:
            last = sorted(
                list(db.find({"_id": {"$gt": time() - frame}})),
                key=itemgetter('_id'))[-1]
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
        df = ema(df, int(window // 3.5), colname='emafast')
        # add macd
        df = macd(df)
        # add rsi
        df = rsi(df, window // 5)
        # add candle body and shadow size
        df['bodysize'] = df['close'] - df['open']
        df['shadowsize'] = df['high'] - df['low']
        df['percentChange'] = df['close'].pct_change()
        df.dropna(inplace=True)
        return df

    def graph(self, pair=False, period=False, frame=False,
              window=120, plotWidth=1000):
        df = self.dataFrame(pair, period, frame, window)
        #
        # Start Candlestick Plot -------------------------------------------
        # create figure
        candlePlot = figure(
            x_axis_type=None,
            y_range=(min(df['low'].values) - (min(df['low'].values) * 0.2),
                     max(df['high'].values) * 1.2),
            x_range=(df.tail(int(len(df) // 10)).date.min().timestamp() * 1000,
                     df.date.max().timestamp() * 1000),
            tools="pan,wheel_zoom,reset",
            title=self.pair + '-' + str(self.period),
            plot_width=plotWidth,
            plot_height=int(plotWidth // 2.7),
            toolbar_location="above")
        # add plots
        # plot volume
        plotVolume(candlePlot, df, self.period)
        # plot candlesticks
        plotCandlesticks(candlePlot, df, self.period)
        # plot bbands
        plotBBands(candlePlot, df)
        # plot moving aves
        plotMovingAverages(candlePlot, df)
        # set legend location
        candlePlot.legend.location = "top_left"
        # set background color
        candlePlot.background_fill_color = "white"
        candlePlot.background_fill_alpha = 0.4
        # set border color and size
        candlePlot.border_fill_color = "whitesmoke"
        candlePlot.min_border_left = 40
        candlePlot.min_border_right = 40
        #
        # Start RSI/MACD Plot -------------------------------------------
        # create a new plot and share x range with candlestick plot
        rsiPlot = figure(plot_height=150,
                         x_axis_type="datetime",
                         y_range=(-(max(df['macd'].values) * 2),
                                  max(df['macd'].values) * 2),
                         x_range=candlePlot.x_range,
                         plot_width=candlePlot.plot_width,
                         title=None,
                         toolbar_location=None)
        # plot macd
        plotMACD(rsiPlot, df)
        # plot rsi
        plotRSI(rsiPlot, df, self.period)
        # set background color
        rsiPlot.background_fill_color = "white"
        rsiPlot.background_fill_alpha = 0.4
        # set border color and size
        rsiPlot.border_fill_color = "whitesmoke"
        rsiPlot.min_border_left = 40
        rsiPlot.min_border_right = 40
        rsiPlot.min_border_bottom = 20
        # orient x labels
        rsiPlot.xaxis.major_label_orientation = PI / 4
        # set legend
        rsiPlot.legend.location = "top_left"
        # set dataframe 'date' as index
        df.set_index('date', inplace=True)
        # return layout and df
        return [[candlePlot], [rsiPlot]], df


if __name__ == '__main__':
    from tools import Poloniex
    from tools import show, PI, gridplot

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("tools.poloniex").setLevel(logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)

    api = Poloniex(jsonNums=float)

    layout, df = Charter(api,
                         'BTC_DASH',
                         period=api.DAY).graph(window=90, frame=api.YEAR * 12)
    p = gridplot(layout)
    show(p)
