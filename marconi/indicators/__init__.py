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
from ..tools import pd, np, getLogger

logger = getLogger(__name__)


def rsi(df, window, targetcol='weightedAverage', colname='rsi'):
    """ Calculates the Relative Strength Index (RSI) from a pandas dataframe
    http://stackoverflow.com/a/32346692/3389859

    df = pandas dataframe
    window = number of rows to look back
    targetcol = string name of column to calulate indicator
        default: 'weightedAverage'
    colname = string name of newly generated indicator column returned with df
        default: 'rsi'
    """
    series = df[targetcol]
    delta = series.diff().dropna()
    u = delta * 0
    d = u.copy()
    u[delta > 0] = delta[delta > 0]
    d[delta < 0] = -delta[delta < 0]
    # first value is sum of avg gains
    u[u.index[window - 1]] = np.mean(u[:window])
    u = u.drop(u.index[:(window - 1)])
    # first value is sum of avg losses
    d[d.index[window - 1]] = np.mean(d[:window])
    d = d.drop(d.index[:(window - 1)])
    rs = u.ewm(com=window - 1,
               ignore_na=False,
               min_periods=0,
               adjust=False).mean() / d.ewm(com=window - 1,
                                            ignore_na=False,
                                            min_periods=0,
                                            adjust=False).mean()
    df[colname] = 100 - 100 / (1 + rs)
    df[colname].fillna(df[colname].mean(), inplace=True)
    return df


def sma(df, window, targetcol='close', colname='sma', stddev=2.0):
    """
    Moving average standard dev (Bollinger Bands)

    df = pandas dataframe
    window = number of rows to look back
    targetcol = string name of column to calulate indicators
        default: 'close'
    colname = string name (+ top, bottom, etc) of newly generated indicators
        columns returned with df
            default: 'sma'
    stddev = standard deviation
        default: 2.0
    """
    if colname not in df:
        df[colname] = df[targetcol].rolling(min_periods=1,
                                            window=window,
                                            center=False).mean()
        df[colname].fillna(df[colname].mean())
    df[colname + 'top'] = df[colname] + stddev * df[targetcol].rolling(
        min_periods=1,
        window=window,
        center=False).std()
    df[colname + 'top'].fillna(df[colname + 'top'].mean(), inplace=True)
    df[colname + 'bottom'] = df[colname] - stddev * df[targetcol].rolling(
        min_periods=1,
        window=window,
        center=False).std()
    df[colname + 'bottom'].fillna(df[colname + 'bottom'].mean(), inplace=True)
    df[colname + 'range'] = df[colname + 'top'] - df[colname + 'bottom']
    df[colname + 'percent'] = ((df[targetcol] - df[colname + 'bottom']) /
                               df[colname + 'range']) - 0.5
    return df.round({colname: 8,
                     colname + 'top': 8,
                     colname + 'bottom': 8,
                     colname + 'range': 8,
                     colname + 'percent': 8})


def ema(df, window, targetcol='close', colname='ema', stddev=2.0, **kwargs):
    """ Calculates Expodential Moving Average on a 'targetcol' in a pandas
    dataframe

    df = pandas dataframe
    window = number of rows to look back
    targetcol = string name of column to calulate indicator
        default: 'close'
    colname = string name of newly generated indicator column returned with df
        default: 'ema'
    """
    if colname not in df:
        df[colname] = df[targetcol].ewm(
            span=window,
            min_periods=kwargs.get('min_periods', 1),
            adjust=kwargs.get('adjust', True),
            ignore_na=kwargs.get('ignore_na', False)
        ).mean()
        df[colname].fillna(df[colname].mean(), inplace=True)
    df[colname + 'top'] = df[colname] + stddev * df[targetcol].rolling(
        min_periods=1,
        window=window,
        center=False).std()
    df[colname + 'top'].fillna(df[colname + 'top'].mean(), inplace=True)
    df[colname + 'bottom'] = df[colname] - stddev * df[targetcol].rolling(
        min_periods=1,
        window=window,
        center=False).std()
    df[colname + 'bottom'].fillna(df[colname + 'bottom'].mean(), inplace=True)
    df[colname + 'range'] = df[colname + 'top'] - df[colname + 'bottom']
    df[colname + 'percent'] = ((df[targetcol] - df[colname + 'bottom']) /
                               df[colname + 'range']) - 0.5
    return df.round({colname: 8,
                     colname + 'top': 8,
                     colname + 'bottom': 8,
                     colname + 'range': 8,
                     colname + 'percent': 8})


def macd(df, window, fastcol='ema', slowcol='sma'):
    """
    Calculates macd, signal, and divergance from a pandas dataframe

    df = pandas dataframe
    window = number of rows to look back for macd signal
    fastcol = string name of fast moving average column
        default: 'ema'
    slowcol = string name of slow moving average column
        default: 'sma'
    """
    if fastcol not in df and fastcol == 'ema':
        df = ema(df, window, colname='ema')
    if slowcol not in df and slowcol == 'sma':
        df = sma(df, window, colname='sma')
    df['macd'] = df[fastcol] - df[slowcol]
    df['macdSignal'] = df['macd'].ewm(span=window,
                                      min_periods=1,
                                      adjust=True,
                                      ignore_na=False
                                      ).mean()
    df['macdDivergence'] = (df['macd'] - df['macdSignal']) * 10
    return df.round({'macd': 8, 'macdDivergence': 8, 'macdSignal': 8})


def ppsr(df, stddev=2.0):
    """
    Pivot Point, Supports and Resistances

    df = pandas dataframe (expects 'high', 'low', and 'close' columns)
    stddev = standard deviation
        default: 2.0
    """
    df['pivotPoint'] = (df['high'] + df['low'] + df['close']) / 3
    df['resist1'] = stddev * df['pivotPoint'] - df['low']
    df['resist2'] = df['pivotPoint'] + df['high'] - df['low']
    df['resist3'] = df['high'] + stddev * (df['pivotPoint'] - df['low'])
    df['support1'] = stddev * df['pivotPoint'] - df['high']
    df['support2'] = df['pivotPoint'] - df['high'] + df['low']
    df['support3'] = df['low'] - stddev * (df['high'] - df['pivotPoint'])
    return df.round({'pivotPoint': 8,
                     'resist1': 8,
                     'resist2': 8,
                     'resist3': 8,
                     'support1': 8,
                     'support2': 8,
                     'support3': 8})


def cci(df, window):
    """
    Commodity Channel Index

    df = pandas dataframe (expects 'high', 'low', and 'close' columns)
    window = number of rows to look back
    """
    if not 'pivotPoint' in df:
        df['pivotPoint'] = (df['high'] + df['low'] + df['close']) / 3
    df['cci'] = (df['pivotPoint'] - df['pivotPoint'].rolling(
        window=window,
        min_periods=1,
        center=False).mean()) / df['pivotPoint'].rolling(window=window,
                                                         min_periods=1,
                                                         center=False).std()
    return df.round({'pivotPoint': 8,
                     'cci': 8})


def force(df, window, targetcol='close'):
    """
    Force Index

    df = pandas dataframe (expects 'volume' column)
    window = number of rows to look back
    targetcol = string name of column to calulate indicators
        default: 'close'
    """
    df['force'] = df[targetcol].diff(window) * df['volume'].diff(window)
    return df.round({'force': 8})


def copp(df, window, targetCol='close'):
    """
    Coppock Curve

    df = pandas dataframe
    window = number of rows to look back
    targetcol = string name of column to calulate indicators
        default: 'close'
    """
    ROC1 = df[targetCol].diff(int(window * 11 / 10) - 1) / \
        df[targetCol].shift(int(window * 11 / 10) - 1)
    ROC2 = df[targetCol].diff(int(window * 14 / 10) - 1) / \
        df[targetCol].shift(int(window * 14 / 10) - 1)
    T = ROC1 + ROC2
    df['copp'] = T.ewm(ignore_na=False,
                       span=window,
                       min_periods=1,
                       adjust=True).mean()
    return df.round({'copp': 8})


def eom(df, window):
    """
    Ease of Movement

    df = pandas dataframe (expects 'high', 'low', 'volume' columns)
    window = number of rows to look back
    """
    EoM = (df['high'].diff(1) + df['low'].diff(1)) * \
        (df['high'] - df['low']) / (2 * df['volume'])
    df['eom'] = EoM.rolling(window=window, center=False).mean() * 100000
    return df.round({'eom': 8})


def massindex(df, window):
    """
    Mass Index

    df = pandas dataframe (expects 'high', 'low' columns)
    window = number of rows to look back
    """
    Range = df['high'] - df['low']
    EX1 = Range.ewm(ignore_na=False,
                    span=window,
                    min_periods=1,
                    adjust=True).mean()
    EX2 = EX1.ewm(ignore_na=False,
                  span=window,
                  min_periods=1,
                  adjust=True).mean()
    Mass = EX1 / EX2
    df['massindex'] = Mass.rolling(window=window * 3,
                                   center=False,
                                   min_periods=1).sum()
    return df.round({'massindex': 8})
