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


def labelByIndicators(candle, bbHLMulti=(10, 10),
                      rsiHL=(60, 35), futureCol='close'):
    score = 0
    # close is above sma
    if candle['bbpercent'] > 0:
        # sell
        score += -int(candle['bbpercent'] * bbHLMulti[0])
    # close is below sma
    if candle['bbpercent'] < 0:
        # buy
        score += int(abs(candle['bbpercent']) * bbHLMulti[1])
    # rsi indicates overbought
    if candle['rsi'] > rsiHL[0]:
        # sell
        score += -1
    # rsi indicates oversold
    if candle['rsi'] < rsiHL[1]:
        score += 1
    # if next candle close is larger than this close
    if candle['future'] > candle[futureCol]:
        # buy
        score += 1
    # if smaller
    if candle['future'] < candle[futureCol]:
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
                                                        random_state=666),
                           'dt': DecisionTreeClassifier()
                           }
        self.votingLobe = VotingClassifier(
            estimators=[(lobe, self._lobes[lobe]) for lobe in self._lobes],
            voting='hard',
            n_jobs=len(self._lobes))

    def train(self, df, labels='label', split=False):
        # make sure we have labels
        if not labels in df:
            logger.info('Generating new labels')
            df['future'] = df['percentChange'].shift(-1)
            df[labels] = df.apply(labelByIndicators, axis=1)
            del df['future']
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
