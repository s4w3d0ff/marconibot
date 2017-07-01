from .. import pd, np


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


def macd(df, fastcol='emafast', slowcol='sma', colname='macd'):
    """ Calculates the differance between 'fastcol' and 'slowcol' in a pandas
    dataframe """
    df[colname] = df[fastcol] - df[slowcol]
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
    body = c['body']
    shadow = c['shadow']
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
    # no shadow
    if shadow <= SATOSHI:
        # decent sized body
        if abs(body) > SATOSHI * 5:
            return 'maru'
        # no body
        if abs(body) < SATOSHI * 2:
            return 'doji'
    # large shadow
    if shadow > abs(body) * 2:
        # decent sized body
        if abs(body) > SATOSHI * 5:
            # no topwick
            if topWick <= SATOSHI:
                return 'hanging'
            # no bottomWick
            if bottomWick <= SATOSHI:
                return 'hammer'
        # no body
        if abs(body) < SATOSHI * 2:
            # no topWick
            if topWick <= SATOSHI:
                return 'dragon'
            # no bottomWick
            if bottomWick <= SATOSHI:
                return 'grave'
            return 'doji'
    return False
