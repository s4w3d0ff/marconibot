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
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, VotingClassifier

from .. import logging, pd, np, time, pickle, shuffleDataFrame


logger = logging.getLogger(__name__)


def labelByPercent(candle, threshold=0.1, futureCol='percentChange'):
    # percentchange is greater than threshold
    if candle[futureCol] > threshold:
        # buy
        return -1
    # percentchange is less than -threshold
    if candle[futureCol] < -threshold:
        # sell
        return 1
    return 0


def labelByIndicators(candle, threshold=0.01, rsiHL=(60, 40)):
    score = 0
    # close is above sma: sell
    if candle['bbpercent'] > 0:
        if candle['bbpercent'] > 0.5:
            score += -int(candle['bbpercent'])
        else:
            score += -1
    # close is below sma: buy
    if candle['bbpercent'] < 0:
        if candle['bbpercent'] < -0.5:
            score += int(abs(candle['bbpercent']))
        else:
            score += 1

    # rsi indicates overbought
    if candle['rsi'] > rsiHL[0]:
        score += -1
    # rsi indicates oversold
    if candle['rsi'] < rsiHL[0]:
        score += 1

    # future percentchange is greater than threshold
    if candle['future'] > threshold:
        # buy
        score += 1
    # future percentchange is less than -threshold
    if candle['future'] < -threshold:
        # sell
        score += -1

    # pos macd
    if candle['macd'] > 0:
        # sell
        score += -1
    # neg macd
    if candle['macd'] < 0:
        # buy
        score += 1

    return score


def prepDataframe(df):
    # make infinity nan
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    # drop nan
    return df.dropna()


def splitTrainTestData(df, size=1):
    # split db
    return df.iloc[:-size], df.tail(size)


def getLabels(df, kind='indica', future='percentChange'):
    if kind == 'indica':
        df['future'] = df[future].shift(-1)
        return df.apply(labelByIndicators, axis=1)


class Brain(object):

    def __init__(self, lobes=False):
        self._lobes = lobes
        if not self._lobes:
            self._lobes = {'rf': RandomForestClassifier(n_estimators=7,
                                                        random_state=666),
                           'dt': DecisionTreeClassifier()
                           }
        self.votingLobe = VotingClassifier(
            estimators=[(lobe, self._lobes[lobe]) for lobe in self._lobes],
            voting='hard',
            n_jobs=-1)

    def train(self, df, labels='label', split=False):
        # make sure we have labels
        if not labels in df:
            logger.info('Generating new labels')
            df[labels] = getLabels(df)
        # prep df, remove nan
        df = prepDataframe(df)
        # split if needed
        if split:
            df, tdf = splitTrainTestData(df, split)
        # shuffle data for good luck
        df = shuffleDataFrame(df)
        # fit lobes
        logger.info('%d samples to train', len(df))
        self.votingLobe.fit(df.drop(labels, axis=1).values, df[labels].values)
        if split:
            return tdf

    def predict(self, X):
        return self.votingLobe.predict(X)

    def score(self, X, y):
        return self.votingLobe.score(X, y)
