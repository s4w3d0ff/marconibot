from sklearn import svm
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
import matplotlib.pyplot as plt
import matplotlib
matplotlib.style.use('ggplot')
import pickle
from . import getMongoDb, logging, pd, np, time

logger = logging.getLogger(__name__)


class Brain(object):

    def __init__(self, api):
        """
        self.lobe = VotingClassifier(
            estimators=[
                ('rf', RandomForestClassifier()),
                ('lsvc', svm.SVC(kernel='linear', C=1.0))],
            voting='hard',
            n_jobs=-1)"""
        self.lobe = RandomForestClassifier()
        self.api = api

    def getInput(self):
        # get user input
        raw = input('Buy(+), Sell(-), or Hold(0)?: ')
        rec = str(raw).strip()
        if rec == '+':
            rec = 1
        elif rec == '-':
            rec = -1
        else:
            rec = 0
        return rec

    def getLabels(self, df, save=False, auto=False, threshold=0.01):
        """ Go row by row, plot 10 rows on either side and ask for user input """
        end = len(df)
        if not auto:
            logger.warn('There are %s rows to review!',
                        str(end))
            for index, row in df.iterrows():
                logger.info('Index: %s', str(index))
                rec = self.getInput()
                df.set_value(index, 'label', rec)
        else:
            df['future'] = df['percentChange'].shift(-1)
            # label based on 'futures'
            df['label'] = list(map(self.autoLabels, df['future']))

        df.fillna(0, inplace=True)
        labels = np.array(df['label'])

        return df, labels

    def autoLabels(self, future, threshold=0.003):
        if future > threshold:
            return 1
        if future < -threshold:
            return -1
        return 0

    def train(self, markets=['BTC_ZEC', 'BTC_ETH', 'USDT_BTC', 'USDT_LTC'],
              save=False, autoL=False, **kwargs):
        for market in markets:
            # create chart
            chart = Chart(
                self.api,
                market,
                frame=kwargs.get('frame', self.api.DAY * 300),
                period=kwargs.get('period', self.api.MINUTE * 15)
            )
            # create df if none exists
            df = chart.dataFrame()
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df.dropna(inplace=True)
            df.reset_index(inplace=True)
            features = np.array(df[['close',
                                    'bbpercent',
                                    'bodysize',
                                    'shadowsize',
                                    'sma',
                                    'macd',
                                    'bbrange']])
            df, labels = self.getLabels(df, auto=autoL, save=save)

            # train
            logger.info("Training size: %s", str(len(features)))
            self.lobe.fit(features, labels)
            if save:
                pickle.dump(self.lobe, open("brain.pickle", "wb"))
        return df

    def predict(self, market, **kwargs):
        chart = Chart(api,
                      market,
                      frame=api.DAY * 5,
                      period=api.MINUTE * 15)

        df = chart.dataFrame()
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        df.reset_index(inplace=True)
        features = np.array(df[['close',
                                'bbpercent',
                                'bodysize',
                                'shadowsize',
                                'sma',
                                'macd',
                                'bbrange']])
        return df, self.lobe.predict(features)


if __name__ == '__main__':
    from .chart import Chart
    from .poloniex import Poloniex
    from matplotlib.pyplot import subplots, draw
    # pip3 install git+https://github.com/s4w3d0ff/mpl_finance.git
    import mpl_finance
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('tools.poloniex').setLevel(logging.INFO)
    api = Poloniex(jsonNums=float)
    b = Brain(api)
    ldf = b.train(save=True, autoL=True).tail(20)
    pdf, predictions = b.predict('BTC_DASH')
    pdf['predict'] = predictions
    df = pdf.tail(20)
    print(df[['close', 'percentChange', 'predict']])
