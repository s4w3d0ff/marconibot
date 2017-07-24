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
from bokeh.plotting import figure, output_file, show, ColumnDataSource
from bokeh.layouts import gridplot
from bokeh.models import NumeralTickFormatter
from bokeh.models import LinearAxis, Range1d

from .. import pd, np


def plotRSI(p, df, plotwidth=800, upcolor='green', downcolor='red'):
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

    candleWidth = (df.iloc[2]['date'].timestamp() -
                   df.iloc[1]['date'].timestamp()) * plotwidth
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


def plotCandlesticks(p, df, plotwidth=750, upcolor='green', downcolor='red'):
    candleWidth = (df.iloc[2]['date'].timestamp() -
                   df.iloc[1]['date'].timestamp()) * plotwidth
    # Plot candle 'shadows'/wicks
    p.segment(x0=df.date,
              y0=df.high,
              x1=df.date,
              y1=df.low,
              color="black",
              line_width=2)
    # Plot green candles
    inc = df.close > df.open
    p.vbar(x=df.date[inc],
           width=candleWidth,
           top=df.open[inc],
           bottom=df.close[inc],
           fill_color=upcolor,
           line_width=0.5,
           line_color='black')
    # Plot red candles
    dec = df.open > df.close
    p.vbar(x=df.date[dec],
           width=candleWidth,
           top=df.open[dec],
           bottom=df.close[dec],
           fill_color=downcolor,
           line_width=0.5,
           line_color='black')
    # format price labels
    p.yaxis[0].formatter = NumeralTickFormatter(format='0.00000000')


def plotVolume(p, df, plotwidth=800, upcolor='green', downcolor='red'):
    candleWidth = (df.iloc[2]['date'].timestamp() -
                   df.iloc[1]['date'].timestamp()) * plotwidth
    # create new y axis for volume
    p.extra_y_ranges = {"volume": Range1d(start=min(df['volume'].values),
                                          end=max(df['volume'].values))}
    p.add_layout(LinearAxis(y_range_name="volume"), 'right')
    # Plot green candles
    inc = df.close > df.open
    p.vbar(x=df.date[inc],
           width=candleWidth,
           top=df.volume[inc],
           bottom=0,
           alpha=0.1,
           fill_color=upcolor,
           line_color=upcolor,
           y_range_name="volume")

    # Plot red candles
    dec = df.open > df.close
    p.vbar(x=df.date[dec],
           width=candleWidth,
           top=df.volume[dec],
           bottom=0,
           alpha=0.1,
           fill_color=downcolor,
           line_color=downcolor,
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
