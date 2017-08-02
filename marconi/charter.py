#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    BTC: 13MXa7EdMYaXaQK6cDHqd4dwr2stBK3ESE
#    LTC: LfxwJHNCjDh2qyJdfu22rBFi2Eu8BjQdxj
#
#    https://github.com/s4w3d0ff/marconibot
#
#    Copyright (C) 2017  https://github.com/s4w3d0ff
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import print_function

from .tools import time, getMongoColl, logging, itemgetter, epoch2localstr
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
        self.api.jsonNums = float

    def __call__(self, pair, start=False):
        """ returns raw chart data from the mongo database, updates/fills the
        data if needed, the date column is the '_id' of each candle entry, and
        the date column has been removed. Use 'start' to restrict the amount
        of data returned.
        Example: 'start=time() - api.YEAR' will return last years data
        """
        if not start:
            start = time() - self.api.YEAR * 3
        dbcolName = pair + 'chart'
        # get db connection
        db = getMongoColl('poloniex', dbcolName)
        # get last candle
        try:
            last = sorted(list(db.find()), key=itemgetter('_id'))[-1]
        except IndexError:
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
            list(db.find({"_id": {"$gt": start}})),
            key=itemgetter('_id'))

    def dataFrame(self, pair, start=False,
                  zoom=False, slowWindow=50, fastWindow=20):
        """ returns pandas DataFrame from raw db data with indicators.
        zoom = passed as the resample(rule) argument to 'merge' candles into a
            different timeframe
        window = number of candles to use when calculating indicators
        """
        data = self.__call__(pair, start)
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
        df = bbands(df, (slowWindow + fastWindow) // 2)
        # add slow ema
        df = ema(df, slowWindow, colname='emaslow')
        # add fast ema
        df = ema(df, fastWindow, colname='emafast')
        # add macd
        df = macd(df)
        # add rsi
        df = rsi(df, fastWindow)
        # add candle body and shadow size
        df['bodysize'] = df['close'] - df['open']
        df['shadowsize'] = df['high'] - df['low']
        df['percentChange'] = df['close'].pct_change()
        df.dropna(inplace=True)
        return df

    def graph(self, pair, start=False, zoom=False,
              slowWindow=50, fastWindow=20, plot_width=1000, min_y_border=40,
              border_color="whitesmoke", background_color="white",
              background_alpha=0.4, legend_location="top_left",
              tools="pan,wheel_zoom,reset"):
        """
        Plots market data using bokeh and returns a 2D array for gridplot
        """
        df = self.dataFrame(pair, start, zoom, slowWindow, fastWindow)
        #
        # Start Candlestick Plot -------------------------------------------
        # create figure
        if not zoom:
            zoom = '5T'
        candlePlot = figure(
            x_axis_type=None,
            y_range=(min(df['low'].values) - (min(df['low'].values) * 0.2),
                     max(df['high'].values) * 1.2),
            x_range=(df.tail(int(len(df) // 10)).date.min().timestamp() * 1000,
                     df.date.max().timestamp() * 1000),
            tools=tools,
            title=pair + ' ' + zoom + ' from ' + epoch2localstr(start),
            plot_width=plot_width,
            plot_height=int(plot_width // 3),
            toolbar_location="above")
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
        rsiPlot = figure(plot_height=int(candlePlot.plot_height // 3),
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
        return [candlePlot, rsiPlot], df


if __name__ == '__main__':
    from .tools import Poloniex, localstr2epoch
    from .tools.plotting import show, gridplot

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("poloniex").setLevel(logging.INFO)
    logging.getLogger('requests').setLevel(logging.ERROR)

    api = Poloniex(jsonNums=float)

    layout, df = Charter(api).graph('ETH_ETC',
                                    window=70,
                                    start=localstr2epoch(
                                        '2016-01', fmat="%Y-%m"),
                                    zoom='1H')

    print(df.tail(40))
    p = gridplot(layout)
    show(p)
