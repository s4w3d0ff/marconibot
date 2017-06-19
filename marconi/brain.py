from sklearn import svm
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
import pickle
from tools import getMongoDb, logging, pd, np, time

logger = logging.getLogger(__name__)


def autoLabels(df, target='close'):
    # create future
    df['future'] = df['close'].shift(-1)
    df.fillna(0, inplace=True)
    # label sells
    df.loc[df['future'] < df['close'], 'label'] = -1
    # label buys
    df.loc[df['future'] > df['close'], 'label'] = 1
    # label holds
    df.loc[df['future'] == df['close'], 'label'] = 0
    df.fillna(0, inplace=True)
    return df


class Brain(object):

    def __init__(self):
        self.lobe = svm.SVC(gamma=0.001, C=100.)


if __name__ == '__main__':
    from chart import Chart
    from poloniex import Poloniex
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('tools.poloniex').setLevel(logging.INFO)
    market = 'BTC_LTC'
    brain = Brain()
    df = Chart(Poloniex(jsonNums=float),
               pair=market,
               period=60 * 60 * 4).dataFrame(window=120)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(0, inplace=True)

    testDf, trainDf = df.tail(1), df.iloc[:-1]
    print(testDf)
    print(trainDf)

    trainDf = autoLabels(trainDf)
    labels = trainDf['label'].values

    features = trainDf[['bbpercent',
                        'bodysize',
                        'macd',
                        'bbrange',
                        'rsi']].values

    logger.info("Training size: %s", str(len(features)))

    brain.lobe.fit(features, labels)

    print(brain.lobe.predict(testDf[['bbpercent',
                                     'bodysize',
                                     'macd',
                                     'bbrange',
                                     'rsi']].values))
