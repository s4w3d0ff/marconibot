from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, VotingClassifier

from .. import logging, pd, np, time, pickle, shuffleDataFrame


logger = logging.getLogger(__name__)


def labelByIndicators(candle):
    score = 0
    # close is above top bband (0.5)
    if candle['bbpercent'] > 0.5:
        # overbought, sell
        score += -2
    # close is below bottom bband (-0.5)
    if candle['bbpercent'] < -0.5:
        # oversold, buy
        score += 2
    # rsi indicates overbought
    if candle['rsi'] > 70:
        # sell
        score += -1
    # rsi indicates oversold
    if candle['rsi'] < 30:
        score += 1
    # if next candle close is larger than this close
    if candle['future'] > candle['close']:
        # buy
        score += 1
    # if smaller
    if candle['future'] < candle['close']:
        # sell
        score += -1
    # pos macd
    if candle['macd'] > 0:
        # overbought, sell
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


class Brain(object):

    def __init__(self, lobes=False):
        self._lobes = lobes
        if not self._lobes:
            self._lobes = {'rf': RandomForestClassifier(n_estimators=10,
                                                        random_state=123),
                           'dt': DecisionTreeClassifier()
                           }
        self.leftLobe = VotingClassifier(
            estimators=[(lobe, self._lobes[lobe]) for lobe in self._lobes],
            voting='soft',
            n_jobs=len(self._lobes))

        self.rightLobe = VotingClassifier(
            estimators=[(lobe, self._lobes[lobe]) for lobe in self._lobes],
            voting='hard',
            n_jobs=len(self._lobes))

    def train(self, df,
              featureset=['bbpercent', 'macd', 'rsi',
                          'volume', 'percentChange'],
              labels=True, split=False):
        # make sure we have labels
        if not labels or not 'label' in df:
            logger.info('Generating new labels')
            df['future'] = df['percentChange'].shift(-1)
            df['label'] = df.apply(labelByIndicators, axis=1)
            del df['future']
        # prep df, remove nan
        df = prepDataframe(df)
        # split if needed
        if split:
            df, tdf = splitTrainTestData(df, split)
        # shuffle data for good luck
        df = shuffleDataFrame(df)
        # fit lobes
        logger.info('%d samples to train', len(df[featureset].values))
        logger.info('Training left lobe')
        self.leftLobe.fit(df[featureset].values, df['label'].values)
        logger.info('Training right lobe')
        self.rightLobe.fit(df[featureset].values, df['label'].values)
        if split:
            return tdf
