from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier, VotingClassifier

from .. import logging, pd, np, time, pickle


logger = logging.getLogger(__name__)


class Brain(object):

    def __init__(self, lobes=False):
        self._lobes = lobes
        if not self._lobes:
            self._lobes = {'svc': LinearSVC(),
                           'kn': KNeighborsClassifier(n_neighbors=3),
                           'rf': RandomForestClassifier(n_estimators=10,
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

    def prepDataframe(self, df):
        # make infinity nan
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        # drop nan
        df.dropna(inplace=True)
        return df

    def splitTrainTestData(self, df, size=1):
        # split db
        return df.iloc[:-size], df.tail(size)

    def getFeatures(self, df, featureset):
        return df[featureset].values

    def getLabels(self, df, new=False):
        if 'label' in df and not new:
            return df['label'].values
        if new == 'auto_close':
            for i in range(len(df)):
                # skip first row
                if i == 0:
                    df.iloc[i]['label'] = 0
                    continue
                # if last 'close' was less than this 'close'
                if df.iloc[i]['close'] > df.iloc[i - 1]['close']:
                    # label last candle as buy
                    df.iloc[i - 1]['label'] = 1
                    continue
                # if last 'close' was greater than this 'close'
                if df.iloc[i]['close'] < df.iloc[i - 1]['close']:
                    # label last candle as sell
                    df.iloc[i - 1]['label'] = -1
                    continue
                # else hold
                df.iloc[i - 1]['label'] = 0
            return df['label'].values

    def trainLeft(self, df,
                  featureset=['bbpercent', 'macd', 'rsi',
                              'volume', 'percentChange'],
                  newLabels=False, split=False):
        df = self.prepDataframe(df)
        if split:
            df, tdf = self.splitTrainTestData(df, split)
        f = self.getFeatures(df, featureset)
        l = self.getLabels(df, newLabels)
        self.leftLobe.fit(f, l)
        if split:
            return tdf

    def trainRight(self, df,
                   featureset=['bbpercent', 'macd', 'rsi',
                               'volume', 'percentChange'],
                   newLabels=False, split=False):
        df = self.prepDataframe(df)
        if split:
            df, tdf = self.splitTrainTestData(df, split)
        f = self.getFeatures(df, featureset)
        l = self.getLabels(df, newLabels)
        self.rightLobe.fit(f, l)
        if split:
            return tdf
