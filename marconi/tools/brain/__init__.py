from sklearn import svm
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.cluster import KMeans

from .. import logging, pd, np, time, pickle


logger = logging.getLogger(__name__)


class Brain(object):

    def __init__(self):
        self._lobes = {'svc': svm.SVC(gamma=0.001),
                       'sgd': SGDClassifier(),
                       'lsvc': svm.LinearSVC(),
                       'kn': KNeighborsClassifier(n_neighbors=3),
                       'rf': RandomForestClassifier(n_estimators=10, random_state=123),
                       'kmeans': KMeans(n_clusters=3, random_state=1)
                       }
        self.votinglobe = VotingClassifier(
            estimators=[(lobe, self._lobes[lobe]) for lobe in self._lobes],
            voting='hard',
            n_jobs=4,
        )

    def splitData(self, df, size=1):
        # make infinity nan
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        # make nan the mean
        df.fillna(df.mean(), inplace=True)
        # split db
        return df.iloc[:-size], df.tail(size)

    def train(self, f, l):
        self.votinglobe.fit(f, l)
