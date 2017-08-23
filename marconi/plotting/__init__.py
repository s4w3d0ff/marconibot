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
from bokeh.models import LinearAxis, Range1d, Span

from ..tools import pd, np


def plotCCI(p, df, plotwidth=800, upcolor='orange', downcolor='yellow'):
    # create y axis for rsi
    p.extra_y_ranges = {"cci": Range1d(start=min(df['cci'].values),
                                       end=max(df['cci'].values))}
    p.add_layout(LinearAxis(y_range_name="cci"), 'right')
    candleWidth = (df.iloc[2]['date'].timestamp() -
                   df.iloc[1]['date'].timestamp()) * plotwidth
    # plot green bars
    inc = df.cci >= 0
    p.vbar(x=df.date[inc],
           width=candleWidth,
           top=df.cci[inc],
           bottom=0,
           fill_color=upcolor,
           line_color=upcolor,
           alpha=0.5,
           y_range_name="cci",
           legend='cci')
    # Plot red bars
    dec = df.cci < 0
    p.vbar(x=df.date[dec],
           width=candleWidth,
           top=0,
           bottom=df.cci[dec],
           fill_color=downcolor,
           line_color=downcolor,
           alpha=0.5,
           y_range_name="cci",
           legend='cci')


def plotRSI(p, df, plotwidth=800, upcolor='green',
            downcolor='red', yloc='right', limits=(30, 70)):
    # create y axis for rsi
    p.extra_y_ranges = {"rsi": Range1d(start=0, end=100)}
    p.add_layout(LinearAxis(y_range_name="rsi"), yloc)

    p.add_layout(Span(location=limits[0],
                      dimension='width',
                      line_color=upcolor,
                      line_dash='dashed',
                      line_width=2,
                      y_range_name="rsi"))

    p.add_layout(Span(location=limits[1],
                      dimension='width',
                      line_color=downcolor,
                      line_dash='dashed',
                      line_width=2,
                      y_range_name="rsi"))

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


def plotMACD(p, df, plotwidth=800, upcolor='teal', downcolor='navy'):
    candleWidth = (df.iloc[2]['date'].timestamp() -
                   df.iloc[1]['date'].timestamp()) * plotwidth
    # plot green bars
    inc = df['macdDivergence'] >= 0
    p.vbar(x=df.date[inc],
           width=candleWidth,
           top=df['macdDivergence'][inc],
           bottom=0,
           fill_color=upcolor,
           line_color=upcolor,
           alpha=0.5,
           legend='macdDivergence',
           # y_range_name="macd"
           )
    # Plot red bars
    dec = df['macdDivergence'] < 0
    p.vbar(x=df.date[dec],
           width=candleWidth,
           top=0,
           bottom=df['macdDivergence'][dec],
           fill_color=downcolor,
           line_color=downcolor,
           alpha=0.5,
           legend='macdDivergence',
           # y_range_name="macd"
           )
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


def plotVolume(p, df, plotwidth=800, upcolor='green',
               downcolor='red', colname='volume'):
    candleWidth = (df.iloc[2]['date'].timestamp() -
                   df.iloc[1]['date'].timestamp()) * plotwidth
    # create new y axis for volume
    p.extra_y_ranges = {colname: Range1d(start=min(df[colname].values),
                                         end=max(df[colname].values))}
    p.add_layout(LinearAxis(y_range_name=colname), 'right')
    # Plot green candles
    inc = df.close > df.open
    p.vbar(x=df.date[inc],
           width=candleWidth,
           top=df[colname][inc],
           bottom=0,
           alpha=0.1,
           fill_color=upcolor,
           line_color=upcolor,
           y_range_name=colname)

    # Plot red candles
    dec = df.open > df.close
    p.vbar(x=df.date[dec],
           width=candleWidth,
           top=df[colname][dec],
           bottom=0,
           alpha=0.1,
           fill_color=downcolor,
           line_color=downcolor,
           y_range_name=colname)


def plotMABands(p, df, color='navy', colname='sma'):
    # Plot bbands
    p.patch(np.append(df['date'].values, df['date'].values[::-1]),
            np.append(df[colname + 'bottom'].values,
                      df[colname + 'top'].values[::-1]),
            color=color,
            fill_alpha=0.1,
            legend=colname)
    # plot sma
    p.line(df['date'], df[colname], color=color, alpha=0.9, legend=colname)
