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
from ..tools import (getLogger, pd, np, time, shuffleDataFrame,
                     json, isString, TRADE_MIN)


logger = getLogger(__name__)


def customLabels(df, *args, **kwargs):
    """
    Creates labels from a dataframe
    """
    logger.debug('Adding labels')

    def _labels(candle, bbLimit=False, rsiLimit=False, pchLimit=False,
                cciLimit=False, macdLimit=False, forceLimit=False,
                eomLimit=False):
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

    return df.apply(_labels, axis=1, *args, **kwargs)


def prepDataframe(df):
    """ Preps a dataframe for sklearn, removing infinity and droping nan """
    # make infinity nan and drop nan
    return df.replace([np.inf, -np.inf], np.nan).dropna()


def splitTrainTestData(df, size=1):
    """ Splits a dataframe by <size> starting from the rear """
    # split db
    return df.iloc[:-size], df.tail(size)


class Brain(object):
    """
    The Brain object

    Holds sklrean classifiers and makes it simpler to train using a dataframe
    """

    def __init__(self, api, lobes=False):
        """
        lobes = a dict of classifiers to use in the VotingClassifier
            defaults to RandomForestClassifier and DecisionTreeClassifier
        """
        self.api = api
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
        self.split = splitTrainTestData
        self.prep = prepDataframe

    def train(self, df, shuffle=True, preprocess=False, *args, **kwargs):
        """
        Takes a dataframe of features + a 'label' column and trains the lobe
        """
        if self._trained:
            logger.warning('Overwriting an already trained brain!')
            self._trained = False

        # shuffle data for good luck
        if shuffle:
            df = shuffleDataFrame(df)
        # scale train data and fit lobe
        x = df.drop('label', axis=1).values
        y = df['label'].values
        del df
        if preprocess:
            x = preprocessing.scale(x)
        logger.info('Training with %d samples', len(x))
        self.lobe.fit(x, y)
        self._trained = True

    def predict(self, df):
        """ Get a prediction from the votingLobe """
        return self.lobe.predict(self.prep(df).values)

    def score(self, df, test='predict'):
        """ Get a prediction score from the votingLobe """
        df = self.prep(df)
        return accuracy_score(df[test].values, df['label'].values)

    def save(self, location="brain"):
        """ Pickle the brain """
        if self._trained:
            joblib.dump(self.lobe, location + ".pickle")
            logger.info('Brain %s saved', location + '.pickle')
        else:
            return logging.error('Brain is not trained yet! Nothing to save...')

    def load(self, location="brain"):
        """ Loads a brain pickle """
        logger.info('Loading saved brain %s', location + '.pickle')
        self.lobe = joblib.load(location + ".pickle")
        self._trained = True


class SmartMarket(Market):
    """ A child class of 'Market' with an instance of 'Brain' """

    def __init__(self, brain=False, *args, **kwargs):
        super(SmartMarket, self).__init__(*args, **kwargs)
        if isString(brain):
            self.brain = Brain(self.api)
            try:
                self.brain.load(brain.split('.pickle')[0])
            except Exception as e:
                logger.exception(e)
        if not brain:
            self.brain = Brain(self.api)

    def backtest(self, df, parent, child, *args, **kwargs):
        logger.info('Backtesting %s...', self.pair)
        bals = {
            'pstart': float(parent),
            'cstart': float(child),
            'ptotal': float(parent),
            'ctotal': float(child),
        }

        def _backtest(row, moveOn='predict', tradeMin=TRADE_MIN, moveMin=0):
            # get move and rate
            move = row[moveOn]
            rate = row['close']

            # if buy
            if move > moveMin:
                parentAmt = tradeMin * move
                childAmt = parentAmt / rate
                if parentAmt < TRADE_MIN:
                    logger.debug('Parent trade amount is below the minimum!')
                elif bals['ptotal'] - parentAmt < 0:
                    logger.debug('Not enough parentCoin!')
                else:
                    bals['ctotal'] = bals['ctotal'] + childAmt
                    bals['ptotal'] = bals['ptotal'] - parentAmt

            # if sell
            if move < -moveMin:
                parentAmt = abs(tradeMin * move)
                childAmt = parentAmt / rate
                if parentAmt < TRADE_MIN:
                    logger.debug('Parent trade amount is below the minimum!')
                elif bals['ctotal'] - childAmt < 0:
                    logger.debug('Not enough childCoin!')
                else:
                    bals['ptotal'] = bals['ptotal'] + parentAmt
                    bals['ctotal'] = bals['ctotal'] - childAmt

            return pd.Series({'btParent': bals['ptotal'],
                              'btChild': bals['ctotal']})

        df = df.merge(df.apply(_backtest, axis=1, *args, **kwargs),
                      left_index=True, right_index=True)
        df['btTotal'] = df['btParent'] + (df['btChild'] * df['close'])
        df['btStart'] = bals['pstart'] + (bals['cstart'] * df['close'])
        df['btProfit'] = df['btTotal'] - df['btStart']
        df['btProfit'] = df['btProfit'].round(8)
        return df
