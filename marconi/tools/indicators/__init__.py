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
from .. import pd, np, addPercent


def rsi(df, window, targetcol='weightedAverage', colname='rsi'):
    """ Calculates the Relative Strength Index (RSI) from a pandas dataframe
    http://stackoverflow.com/a/32346692/3389859
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


def sma(df, window, targetcol='close', colname='sma'):
    """ Calculates Simple Moving Average on a 'targetcol' in a pandas dataframe
    """
    df[colname] = df[targetcol].rolling(
        min_periods=1, window=window, center=False).mean()
    return df


def ema(df, window, targetcol='close', colname='ema', **kwargs):
    """ Calculates Expodential Moving Average on a 'targetcol' in a pandas
    dataframe """
    df[colname] = df[targetcol].ewm(
        span=window,
        min_periods=kwargs.get('min_periods', 1),
        adjust=kwargs.get('adjust', True),
        ignore_na=kwargs.get('ignore_na', False)
    ).mean()
    df[colname].fillna(df[colname].mean(), inplace=True)
    return df


def macd(df, fastWindow=13, slowWindow=36):
    """ Calculates macd, signal, and divergance from a pandas dataframe """
    df = ema(df, fastWindow, colname='emafast')
    df = ema(df, slowWindow, colname='emaslow')
    df['macd'] = df['emafast'] - df['emaslow']
    df = ema(df, (slowWindow + fastWindow) // 2,
             targetcol='macd', colname='macdSignal')
    df['macdDivergence'] = df['macd'] - df['macdSignal']
    return df


def bbands(df, window, targetcol='close', stddev=2.0):
    """ Calculates Bollinger Bands for 'targetcol' of a pandas dataframe """
    if not 'sma' in df:
        df = sma(df, window, targetcol)
    df['sma'].fillna(df['sma'].mean(), inplace=True)
    df['bbtop'] = df['sma'] + stddev * df[targetcol].rolling(
        min_periods=1,
        window=window,
        center=False).std()
    df['bbtop'].fillna(df['bbtop'].mean(), inplace=True)
    df['bbbottom'] = df['sma'] - stddev * df[targetcol].rolling(
        min_periods=1,
        window=window,
        center=False).std()
    df['bbbottom'].fillna(df['bbbottom'].mean(), inplace=True)
    df['bbrange'] = df['bbtop'] - df['bbbottom']
    df['bbpercent'] = ((df[targetcol] - df['bbbottom']) / df['bbrange']) - 0.5
    return df


def getCandleLabel(c):
    """
     |
     | ---- topWick
    _|_ /-- bodytop
    |_| -- body
     |  \-- bodybottom
     | ---- bottomWick
     |
    """
    body = c['bodysize']
    shadow = c['shadowsize']
    # no shadow
    if shadow == abs(body):
        # no body
        if abs(body) == 0:
            return 'other'
        return 'maru'

    # body is bearish
    if body <= 0:
        bodytop = c['high']
        bodybottom = c['low']
    # body is bullish
    else:
        bodytop = c['low']
        bodybottom = c['high']

    topWick = c['high'] - bodytop
    bottomWick = bodybottom - c['low']

    # short wicks
    if topWick + bottomWick < abs(body):
        return 'other'

    # shadow is 75% larger than body
    if shadow > addPercent(abs(body), 75):
        # hammers have large top wicks and big bodies
        if topWick > abs(body) / 2:
            return 'hammer'
        # hanging have large bottom wicks and big bodies
        if bottomWick > abs(body) / 2:
            return 'hanging'
        return 'bdoji'

    # shadow is 50% larger than body
    if shadow > addPercent(abs(body), 50):
        # graves have large top wicks and small bodies
        if topWick > abs(body) / 2:
            return 'grave'
        # dragons have large bottom wicks and small bodies
        if bottomWick > abs(body) / 2:
            return 'dragon'
        return 'ldoji'

    return 'doji'
