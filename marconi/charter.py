from __future__ import print_function

from .tools import time, getMongoColl, logging, itemgetter
from .tools import pd, np, PI
from .tools.plotting import (figure, plotBBands, plotRSI,
                             plotMACD, plotVolume, plotCandlesticks,
                             plotMovingAverages)
from .tools.indicators import ema, macd, bbands, rsi


logger = logging.getLogger(__name__)


class Charter(object):
    """ Retrieves 5min candlestick data for a market and saves it in a mongo
    db collection. Can display data in a dataframe or bokeh plot."""

    def __init__(self, api):
        """
        api = poloniex api object
        """
        self.api = api

    def __call__(self, pair, frame=False):
        """ returns raw chart data from the mongo database, updates/fills the
        data if needed, the date column is the '_id' of each candle entry, and
        the date column has been removed. Use 'frame' to restrict the amount
        of data returned.
        Example: 'frame=api.YEAR' will return last years data
        """
        # use last pair and period if not specified
        if not frame:
            frame = self.api.YEAR * 10
        dbcolName = pair + 'chart'
        # get db connection
        db = getMongoColl('poloniex', dbcolName)
        # get last candle
        try:
            last = sorted(
                list(db.find({"_id": {"$gt": time() - 60 * 20}})),
                key=itemgetter('_id'))[-1]
        except Exception as e:
            logger.exception(e)
            last = False
        # no entrys found, get all 5min data from poloniex
        if not last:
            logger.warning('%s collection is empty!', dbcolName)
            new = self.api.returnChartData(pair,
                                           period=60 * 5,
                                           start=time() - self.api.YEAR * 13)
        else:
            new = self.api.returnChartData(pair,
                                           period=60 * 5,
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

    def dataFrame(self, pair, frame=False, zoom=False, window=120):
        """ returns pandas DataFrame from raw db data with indicators.
        zoom = passed as the resample(rule) argument to 'merge' candles into a
            different timeframe
        window = number of candles to use when calculating indicators
        """
        data = self.__call__(pair, frame)
        # make dataframe
        df = pd.DataFrame(data)
        # set date column
        df['date'] = pd.to_datetime(df["_id"], unit='s')
        if zoom:
            df.set_index('date', inplace=True)
            df = df.resample(rule=zoom,
                             closed='left',
                             label='left').apply({'open': 'first',
                                                  'high': 'max',
                                                  'low': 'min',
                                                  'close': 'last',
                                                  'quoteVolume': 'sum',
                                                  'volume': 'sum',
                                                  'weightedAverage': 'mean'})
            df.reset_index(inplace=True)

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

    def graph(self, pair, frame=False, zoom=False,
              window=120, plot_width=1000, min_y_border=40,
              border_color="whitesmoke", background_color="white",
              background_alpha=0.4, legend_location="top_left",
              tools="pan,wheel_zoom,reset"):
        """
        Plots market data using bokeh and returns a 2D array for gridplot
        """
        df = self.dataFrame(pair, frame, zoom, window)
        #
        # Start Candlestick Plot -------------------------------------------
        # create figure
        candlePlot = figure(
            x_axis_type=None,
            y_range=(min(df['low'].values) - (min(df['low'].values) * 0.2),
                     max(df['high'].values) * 1.2),
            x_range=(df.tail(int(len(df) // 10)).date.min().timestamp() * 1000,
                     df.date.max().timestamp() * 1000),
            tools=tools,
            title=pair,
            plot_width=plot_width,
            plot_height=int(plot_width // 2.7),
            toolbar_location="above")
        # add plots
        # plot volume
        plotVolume(candlePlot, df)
        # plot candlesticks
        plotCandlesticks(candlePlot, df)
        # plot bbands
        plotBBands(candlePlot, df)
        # plot moving aves
        plotMovingAverages(candlePlot, df)
        # set legend location
        candlePlot.legend.location = legend_location
        # set background color
        candlePlot.background_fill_color = background_color
        candlePlot.background_fill_alpha = background_alpha
        # set border color and size
        candlePlot.border_fill_color = border_color
        candlePlot.min_border_left = min_y_border
        candlePlot.min_border_right = candlePlot.min_border_left
        #
        # Start RSI/MACD Plot -------------------------------------------
        # create a new plot and share x range with candlestick plot
        rsiPlot = figure(plot_height=int(candlePlot.plot_height // 2.5),
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
        plotRSI(rsiPlot, df)
        # set background color
        rsiPlot.background_fill_color = candlePlot.background_fill_color
        rsiPlot.background_fill_alpha = candlePlot.background_fill_alpha
        # set border color and size
        rsiPlot.border_fill_color = candlePlot.border_fill_color
        rsiPlot.min_border_left = candlePlot.min_border_left
        rsiPlot.min_border_right = candlePlot.min_border_right
        rsiPlot.min_border_bottom = 20
        # orient x labels
        rsiPlot.xaxis.major_label_orientation = PI / 4
        # set legend
        rsiPlot.legend.location = legend_location
        # set dataframe 'date' as index
        df.set_index('date', inplace=True)
        # return layout and df
        return [[candlePlot], [rsiPlot]], df


if __name__ == '__main__':
    from .tools import Poloniex
    from .tools.plotting import show, gridplot

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("poloniex").setLevel(logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)

    api = Poloniex(jsonNums=float)

    layout, df = Charter(api).graph('USDT_DASH', window=50,
                                    frame=api.YEAR * 12, zoom='12H')
    p = gridplot(layout)
    show(p)
