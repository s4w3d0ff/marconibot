from sklearn import svm
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
import matplotlib.pyplot as plt
import matplotlib
matplotlib.style.use('ggplot')
import pickle
from . import getMongoDb, logging, pd, np

logger = logging.getLogger(__name__)


class Brain(object):

    def __init__(self, api):
        self.lobe = VotingClassifier(
            estimators=[
                ('rf', RandomForestClassifier()),
                ('lsvc', svm.SVC(kernel='linear', C=1.0))],
            voting='hard',
            n_jobs=-1)
        self.api = api

    def create_labels(self, future, threshold=0.03):
        if future > threshold:
            return 1
        if future < -threshold:
            return -1
        return 0

    def getTrainingData(self, pcoin='BTC', minvolume=2000, new=False, ignore=[], **kwargs):
        err = True
        if not new:
            try:
                df = pickle.load(open("trainData.pickle", "rb"))
                err = False
            except:
                logging.warn('No trainData.pickle found!')
        if err:
            # get volumes for all markets
            vols = self.api.return24hVolume()
            charts = {}
            first = True
            for market in vols:
                # skip market if specifyed
                if market in ignore:
                    continue
                # only bitcoin markets
                if not pcoin in vols[market]:
                    continue
                # only high vol markets
                if float(vols[market][pcoin]) < minvolume:
                    continue
                logger.info("%s Volume: %s", market, vols[market][pcoin])
                # create chart
                charts[market] = Chart(
                    self.api,
                    market,
                    frame=kwargs.get('frame', self.api.YEAR * 4),
                    period=kwargs.get('period', self.api.MINUTE * 30)
                )
                # create df if none exists
                if first:
                    df = charts[market].dataFrame()
                    df.reset_index(inplace=True)
                    del df['date']
                    df.replace([np.inf, -np.inf], np.nan, inplace=True)
                    # create 'futures'
                    df['future'] = df['percentChange'].shift(-1)
                    # label based on 'futures'
                    df['label'] = list(map(self.create_labels, df['future']))
                    df.dropna(inplace=True)
                    first = False
                # append all charts together
                else:
                    ndf = charts[market].dataFrame()
                    ndf.reset_index(inplace=True)
                    del ndf['date']
                    ndf.replace([np.inf, -np.inf], np.nan, inplace=True)
                    # create 'futures'
                    ndf['future'] = ndf['percentChange'].shift(-1)
                    # label based on 'futures'
                    ndf['label'] = list(map(self.create_labels, ndf['future']))
                    ndf.dropna(inplace=True)
                    df = df.append(ndf)
            pickle.dump(df, open("trainData.pickle", "wb"))
        # remove unwanted cols
        featureSet = df.drop(['label',
                              'future',
                              'high',
                              'low',
                              'open',
                              'close',
                              'bbtop',
                              'bbbottom',
                              'sma',
                              'emaslow',
                              'quoteVolume',
                              'volume'], 1)
        features = np.array(featureSet)
        # return data
        logger.info("Training size: %s", str(len(df)))
        return df, features, np.array(df['label'])

    def processDataFrame(self, df):
        df.reset_index(inplace=True)
        del df['date']
        # handle infinity
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        # create 'futures'
        df['future'] = df['percentChange'].shift(-1)
        # label based on 'futures'
        df['label'] = list(map(self.create_labels, df['future']))
        df.dropna(inplace=True)
        # remove unwanted cols
        featureSet = df.drop(['label',
                              'future',
                              'high',
                              'low',
                              'open',
                              'close',
                              'bbtop',
                              'bbbottom',
                              'sma',
                              'emaslow',
                              'quoteVolume',
                              'volume'], 1)
        # preprocess
        features = np.array(featureSet)
        # return data
        return df, features, np.array(df['label'])

if __name__ == '__main__':
    from .chart import Chart
    from .poloniex import Poloniex
    from matplotlib.pyplot import subplots, draw
    # pip3 install git+https://github.com/s4w3d0ff/mpl_finance.git
    import mpl_finance
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('tools.poloniex').setLevel(logging.INFO)
    api = Poloniex(jsonNums=float)
    b = Brain(api)
    chart = Chart(api, 'BTC_DASH', frame=api.DAY * 2, period=api.MINUTE * 30)
    if True:
        # get training data
        tdf, tX, ty = b.getTrainingData(
            minvolume=9000,
            new=True,
            ignore=['BTC_DASH'],
            frame=api.MONTH * 5,
            period=api.MINUTE * 30
        )
        # train
        b.lobe.fit(tX, ty)
        pickle.dump(b.lobe, open("brain.pickle", "wb"))
    else:
        b.lobe = pickle.load(open("brain.pickle", "rb"))

    # get tesing data
    df = chart.dataFrame()
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)
    logger.info(df.tail())

    ndf, X, y = b.processDataFrame(df)
    logger.info('Testing Confidence: %s', str(b.lobe.score(X, y)))
    df['predict'] = b.lobe.predict(X)
    logger.info(df[
        ['label',
         'predict',
         'weightedAverage',
         'bbpercent',
         'percentChange']
    ])
    ohlc = [tuple(x) for x in df[['date', 'open', 'close',
                                  'high', 'low']].to_records(index=False)]
    fig = plt.figure()
    ax1 = plt.subplot(1, 1, 1)
    mpl_finance.candlestick_ochl(
        ax1, ohlc, width=0.6, colorup='g', colordown='r')
    plt.show()
