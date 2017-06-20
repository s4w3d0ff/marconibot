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

    def getLabels(self, df, threshold=0.0057):
        # label sells
        futures = df['percentChange'].shift(-1).fillna(0).values

        labels = []
        for i in range(len(futures)):
            future = futures[i]
            if abs(future) > threshold:
                if future < 0:
                    labels.append(-1)
                else:
                    labels.append(1)
            else:
                labels.append(0)
        df['label'] = labels
        return df

    def train(self, f, l):
        self.lobe.fit(f, l)


if __name__ == '__main__':
    from chart import Charter
    from poloniex import Poloniex
    from tools import show
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('poloniex').setLevel(logging.INFO)
    markets = ['BTC_LTC',
               'BTC_ETH',
               'USDT_BTC',
               'USDT_LTC',
               'USDT_ETH',
               'BTC_DASH',
               'USDT_DASH']
    periods = [60 * 60 * 4, 60 * 60 * 24]
    windows = [120, 80]
    brain = Brain()
    charter = Charter(Poloniex(jsonNums=float))

    for market in markets:
        for period in periods:
            for window in windows:
                train = charter.dataFrame(market, period, window=window)
                train.replace([np.inf, -np.inf], np.nan, inplace=True)
                # make nan the mean
                train.fillna(train.mean(), inplace=True)

                train = brain.getLabels(train)

                labels = train['label'].values
                features = train[['bbpercent',
                                  #'bodysize',
                                  'macd',
                                  'rsi',
                                  'close']].values

                logger.info("%s training size: %s", market, str(len(features)))
                brain.train(features, labels)

    test = charter.dataFrame('BTC_XRP', window=120)
    test['prediction'] = brain.lobe.predict(test[[
        'bbpercent',
        #'bodysize',
        'macd',
        #'bbrange',
        'rsi',
        'close']].values)
    test = brain.getLabels(test)
    print(test[['close', 'date', 'percentChange', 'label', 'prediction']].tail(
        50).set_index('date'))

    #show(charter.graph('BTC_XRP', window=120))
    print(brain.lobe.score(test[[
        'bbpercent',
        #'bodysize',
        'macd',
        #'bbrange',
        'rsi',
        'close']].values,
        test['label'].values))
