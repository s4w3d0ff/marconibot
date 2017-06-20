from sklearn import svm
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
import pickle
from tools import getMongoDb, logging, pd, np, time

logger = logging.getLogger(__name__)


class Brain(object):

    def __init__(self, lobe=False):
        if isinstance(lobe, str):
            self.lobe = pickle.load(open(lobe, 'rb'))
        else:
            self.lobe = svm.SVC(gamma=0.001, C=100.)

    def pickle(self, name='lobe.pickle'):
        pickle.dump(self.lobe, open(name, wb))

    def splitData(self, df, size=1):
        # make infinity nan
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        # make nan the mean
        df.fillna(df.mean(), inplace=True)
        # split db
        return df.tail(size), df.iloc[:-size]

    def getLabels(self, df, target='close'):
        # create future
        df['future'] = df[target].shift(-1)
        df.fillna(df.mean(), inplace=True)
        # label sells
        df.loc[df['future'] < df[target], 'label'] = -1
        # label buys
        df.loc[df['future'] > df[target], 'label'] = 1
        # label holds
        df.loc[df['future'] == df[target], 'label'] = 0
        df.fillna(df.mean(), inplace=True)
        return df

    def train(self, f, l):
        self.lobe.fit(f, l)


if __name__ == '__main__':
    from chart import Charter
    from poloniex import Poloniex
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('poloniex').setLevel(logging.INFO)
    markets = ['BTC_LTC',
               'BTC_ETH',
               'USDT_BTC',
               'USDT_LTC',
               'USDT_ETH',
               'BTC_DASH',
               'USDT_DASH']
    brain = Brain()
    charter = Charter(Poloniex(jsonNums=float),
                      pair=markets[0],
                      period=60 * 60 * 4)
    testDFs = {}
    for market in markets:

        df = charter.dataFrame(market, window=120)
        testDFs[market], train = brain.splitData(df, size=2)

        train = brain.getLabels(train)

        labels = train['label'].values
        features = train[['bbpercent',
                          'bodysize',
                          'macd',
                          'bbrange',
                          'rsi',
                          'percentChange']].values

        logger.info("%s training size: %s", market, str(len(features)))
        brain.train(features, labels)

    for market in testDFs:
        print(market)
        print(brain.lobe.predict(testDFs[market][['bbpercent',
                                                  'bodysize',
                                                  'macd',
                                                  'bbrange',
                                                  'rsi',
                                                  'percentChange']].values))
