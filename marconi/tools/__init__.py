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
# core ---------------------------------------------------------------------
import logging
import json
import pickle
try:
    from Queue import Queue
except:
    from queue import Queue
from functools import wraps
from copy import copy
from operator import itemgetter
from math import floor, ceil
from math import pi as PI
from decimal import Decimal
from time import time, gmtime, strftime, strptime, localtime, mktime, sleep
from calendar import timegm
from multiprocessing.dummy import Process, Pool
from threading import Thread

# 3rd party ----------------------------------------------------------------
# pip install pandas numpy
import pandas as pd
import numpy as np
# pip install pymongo
import pymongo
# pip install scikit-learn
import sklearn
# pip install bokeh
import bokeh
# pip install websocket-client
import websocket

# local --------------------------------------------------------------------
from .poloniex import Poloniex, Coach, PoloniexError


# constants ----------------------------------------------------------------

# tools logger
logger = logging.getLogger(__name__)

PHI = (1 + 5 ** 0.5) / 2

# smallest coin fraction
SATOSHI = 0.00000001
# smallest loan fraction
LOANTOSHI = 0.000001
# minimum trade amount (btc and usdt)
TRADE_MIN = 0.0001

# console colors
WT = '\033[0m'  # white (normal)
RD = lambda text: '\033[31m' + str(text) + WT  # red
GR = lambda text: '\033[32m' + str(text) + WT  # green
OR = lambda text: '\033[33m' + str(text) + WT  # orange
BL = lambda text: '\033[34m' + str(text) + WT  # blue
PR = lambda text: '\033[35m' + str(text) + WT  # purp
CY = lambda text: '\033[36m' + str(text) + WT  # cyan
GY = lambda text: '\033[37m' + str(text) + WT  # gray


# convertions, misc ------------------------------------------------------

def shuffleDataFrame(df):
    """ Shuffles the rows of a dataframe """
    df.reset_index(inplace=True)
    del df['index']
    return df.reindex(np.random.permutation(df.index))


def getMongoColl(db, coll):
    """ Returns a mongodb collection """
    return pymongo.MongoClient()[db][coll]


def wait(i=10):
    """ Wraps 'time.sleep()' with logger output """
    logger.debug('Waiting %d sec... (%.2fmin)', i, i / 60.0)
    sleep(i)


def epoch2UTCstr(timestamp=False, fmat="%Y-%m-%d %H:%M:%S"):
    """
    - takes epoch timestamp
    - returns UTC formated string
    """
    if not timestamp:
        timestamp = time()
    return strftime(fmat, gmtime(timestamp))


def UTCstr2epoch(datestr=False, fmat="%Y-%m-%d %H:%M:%S"):
    """
    - takes UTC date string
    - returns epoch
    """
    if not datestr:
        datestr = epoch2UTCstr()
    return timegm(strptime(datestr, fmat))


def epoch2localstr(timestamp=False, fmat="%Y-%m-%d %H:%M:%S"):
    """
    - takes epoch timestamp
    - returns localtimezone formated string
    """
    if not timestamp:
        timestamp = time()
    return strftime(fmat, localtime(timestamp))


def localstr2epoch(datestr=False, fmat="%Y-%m-%d %H:%M:%S"):
    """
    - takes localtimezone date string,
    - returns epoch
    """
    if not datestr:
        datestr = epoch2localstr()
    return mktime(strptime(datestr, fmat))


def saveJSON(data, filename):
    """ Save data as json to a file """
    with open(filename, 'w') as f:
        return json.dump(data, f, indent=4)


def loadJSON(filename):
    """ Load json file """
    with open(filename, 'r') as f:
        return json.load(f)


def addPercent(n, p):
    """ (n * p) + n
    >>> addPercent(8, 0.5)
    8.04
    """
    return (n * percent2float(p)) + n


def float2percent(n):
    """ n * 100 """
    return float(n) * 100


def percent2float(n):
    """ n / 100 """
    return float(n) / 100


def roundDown(n, d=8):
    """
    n :: float to be rounded
    d :: int munber of decimals to round to
    """
    d = int('1' + ('0' * d))
    return floor(float(n) * d) / d


def roundUp(n, d=8):
    """
    n :: float to be rounded
    d :: int munber of decimals to round to
    """
    d = int('1' + ('0' * d))
    return ceil(float(n) * d) / d


def getAverage(seq):
    """
    Finds the average of <seq>
    >>> getAverage(['3', 9.4, '0.8888', 5, 1.344444, '3', '5', 6, '7'])
    4.033320571428571
    """
    return sum(seq) / len(seq)


def geoProgress(n, r=PHI, size=5):
    """ Creates a Geometric Progression with the Geometric sum of <n>
    >>> l = geoProgress(42)
    >>> l
    [2.5725461188664465, 4.162467057952537, 6.735013176818984,
    10.897480234771521, 17.63249341159051]
    >>> sum(l)
    42.0
    """
    return [(n * (1 - r) / (1 - r ** size)) * r ** i for i in range(size)]
