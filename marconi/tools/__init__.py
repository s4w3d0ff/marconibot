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
import sys
import logging
import json
import pickle
from functools import wraps
from math import floor, ceil
from math import pi as PI
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


# constants ----------------------------------------------------------------

PHI = (1 + 5 ** 0.5) / 2

# smallest coin fraction
SATOSHI = 0.00000001
# smallest loan fraction
LOANTOSHI = 0.000001
# minimum trade amount (btc and usdt)
TRADE_MIN = 0.0001


def getLogger(name, fmt="[%(asctime)s]%(name)s<%(levelname)s>%(message)s"):
    logger = logging.getLogger(name)
    cHandle = logging.StreamHandler()
    cHandle.setFormatter(logging.Formatter(fmt=fmt, datefmt="%H:%M:%S"))
    logger.addHandler(cHandle)
    return logger


def getRLogger(name, fmt="[%(asctime)s]%(name)s<%(levelname)s>%(message)s"):
    logger = logging.getLogger(name)
    cHandle = logging.StreamHandler()
    cHandle.terminator = "\r"
    cHandle.setFormatter(logging.Formatter(fmt=fmt, datefmt="%H:%M:%S"))
    logger.addHandler(cHandle)
    return logger


# tools logger
logger = getLogger(__name__)

# console colors ---------------------------------------------------------
WT = '\033[0m'  # white (normal)


def RD(text):
    """ Red """
    return '\033[31m%s%s' % (str(text), WT)


def GR(text):
    """ Green """
    return '\033[32m%s%s' % (str(text), WT)


def OR(text):
    """ Orange """
    return '\033[33m%s%s' % (str(text), WT)


def BL(text):
    """ Blue """
    return '\033[34m%s%s' % (str(text), WT)


def PR(text):
    """ Purple """
    return '\033[35m%s%s' % (str(text), WT)


def CY(text):
    """ Cyan """
    return '\033[36m%s%s' % (str(text), WT)


def GY(text):
    """ Gray """
    return '\033[37m%s%s' % (str(text), WT)


# convertions, misc ------------------------------------------------------

def isString(obj):
    return isinstance(obj, str if sys.version_info[0] >= 3 else basestring)


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
