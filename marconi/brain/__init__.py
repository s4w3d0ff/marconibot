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
from sklearn import preprocessing
from sklearn.metrics import accuracy_score
from sklearn.externals import joblib

from ..market import Market
from ..tools import logging, pd, np, time, shuffleDataFrame, json


logger = logging.getLogger(__name__)


def customLabels(df, bbLimit=False, rsiLimit=False, pchLimit=False,
                 cciLimit=False, macdLimit=False, forceLimit=False,
                 eomLimit=False):
    """
    Creates labels from a dataframe
    """
    logger.debug('Adding labels')

    def _bbrsiLabels(candle, bbLimit, rsiLimit, pchLimit,
                     cciLimit, macdLimit, forceLimit, eomLimit):
        score = 0
        if bbLimit:
            smabb = candle['smapercent']
            if smabb > bbLimit:
                score += -1
            if smabb < -bbLimit:
                score += 1

            emabb = candle['emapercent']
            if emabb > bbLimit:
                score += -1
            if emabb < -bbLimit:
                score += 1

        if rsiLimit:
            rsi = candle['rsi'] - 50
            if rsi > rsiLimit:
                score += -1
            if rsi < -rsiLimit:
                score += 1

        if cciLimit:
            ccindex = candle['cci']
            if ccindex > cciLimit:
                score += -1
            if ccindex < -cciLimit:
                score += 1

        if macdLimit:
            macdd = candle['macdDivergence']
            if macdd > macdLimit:
                score += 1
            if macdd < -macdLimit:
                score += -1

        if forceLimit:
            force = candle['force']
            if force > forceLimit:
                score += -1
            if force < -forceLimit:
                score += 1

        if eomLimit:
            eom = candle['eom']
            if eom > eomLimit:
                score += -1
            if eom < -eomLimit:
                score += 1

        return score

    return df.apply(_bbrsiLabels, axis=1, bbLimit=bbLimit,
                    rsiLimit=rsiLimit, pchLimit=pchLimit,
                    cciLimit=cciLimit, macdLimit=macdLimit,
                    forceLimit=forceLimit, eomLimit=eomLimit)


def prepDataframe(df):
    """ Preps a dataframe for sklearn, removing infinity and droping nan """
    # make infinity nan
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    # drop nan
    return df.dropna()


def splitTrainTestData(df, size=1):
    """ Splits a dataframe by <size> starting from the rear """
    # split db
    return df.iloc[:-size], df.tail(size)


class Brain(object):
    """
    The Brain object

    Holds sklrean classifiers and makes it simpler to train using a dataframe
    """

    def __init__(self, lobes=False):
        """
        lobes = a dict of classifiers to use in the VotingClassifier
            defaults to RandomForestClassifier and DecisionTreeClassifier
        """
        if not lobes:
            lobes = {'rf': RandomForestClassifier(n_estimators=7,
                                                  random_state=666),
                     'dt': DecisionTreeClassifier()
                     }
        self.lobe = VotingClassifier(
            estimators=[(lobe, lobes[lobe]) for lobe in lobes],
            voting='hard',
            n_jobs=-1)
        self._trained = False

    def train(markets=False, featureset=False, labelFunc=customLabels,
              labelArgs={}, shuffle=True, preprocess=False):
        if not markets or not featureset:
            return logger.error(
                'Need both a markets and featureset param to train')
        if self._trained:
            logger.warning('Overwriting an already trained brain!')
            self._trained = False
        self.markets = markets
        self.featureset = featureset
        self.labelFunc = labelFunc
        self.labelArgs = labelArgs
        self.shuffle = shuffle
        self.preprocess = preprocess

        first = True
        logger.info('Building training dataset')
        for market in markets:
            # append each df with labels
            df = Market(self.api, market).chart(**markets[market]).dropna()
            df['label'] = self.labelFunc(df, **self.labelArgs)
            if first:
                first = False
                trainDF = df[self.featureset + ['label']]
            else:
                trainDF = pd.concat([trainDF, df[self.featureset + ['label']]])
        # prep df, remove nan
        df = prepDataframe(trainDF)
        # shuffle data for good luck
        if shuffle:
            df = shuffleDataFrame(df)
        # scale train data and fit lobe
        x = df.drop('label', axis=1).values
        y = df['label'].values
        del df
        if preprocess:
            x = preprocessing.scale(x)
        logger.info('%d samples to train', len(x))
        self.lobe.fit(x, y)
        self._trained = True

    def predict(self, df):
        """ Get a prediction from the votingLobe """
        df = prepDataframe(df)
        return self.lobe.predict(df[self.featureset].values)

    def score(self, df, x='label', y='predict'):
        """ Get a prediction score from the votingLobe """
        df = prepDataframe(df)
        return accuracy_score(df[x].values, df[y].values)

    def save(self, fname="brain"):
        """ Pickle and save brain with config """
        if self._trained:
            joblib.dump(self.lobe, fname + ".pickle")
            json.dump({"markets": self.markets,
                       "featureset": self.featureset,
                       "labelArgs": self.labelArgs,
                       "labelFunc": self.labelFunc.__name__,
                       "shuffle": self.shuffle,
                       "preprocess": self.preprocess},
                      open(fname + ".json", "w"))
        else:
            return logging.error('Brain is not trained yet! Nothing to save...')

    def load(self, fname="brain"):
        """ Loads a brain pickle and config """
        self.lobe = joblib.load(fname + ".pickle")
        config = json.load(open(fname + ".json", "w"))
        self.featureset = config['featureset']
        self.labelArgs = config['labelArgs']
        self.markets = config['markets']
        self.shuffle = config['shuffle']
        self.preprocess = config['preprocess']
        exec("self.labelFunc = " + config['labelFunc'])
