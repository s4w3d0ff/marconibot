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
from marconi import tools
from marconi.tools import np, pd
from marconi.tools.chart import Chart
from marconi.tools.poloniex import Poloniex

import matplotlib.pyplot as plt
import matplotlib
matplotlib.style.use('ggplot')
import pickle

from sklearn import svm, preprocessing, cross_validation


class Marconi(object):

    def __init__(self, api, market, **kwarg):
        self.api = api
        self.market = market
        self.chart = Chart(self.api,
                           self.market,
                           frame=kwarg.get('frame', self.api.MONTH * 3))
        self.brain = svm.SVC(kernel=kwarg.get('kernel', 'linear'))

    def preprocessChart(self, df, futureSize):
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df['future'] = df['percentChange'].shift(-futureSize)
        df['label'] = list(map(self.create_labels, df['future']))
        df.dropna(inplace=True)
        features = preprocessing.scale(
            np.array(df.drop(['label', 'future'], 1))
        )
        labels = np.array(df['label'])
        return features, labels

    def train(self, features, labels, testSize=0.2):
        f_train, f_test, l_train, l_test = cross_validation.train_test_split(
            features,
            labels,
            test_size=testSize)
        self.brain.fit(f_train, l_train)
        return self.brain.score(f_test, l_test)

    def create_labels(self, future):
        if future > 10:
            return 'buy'
        if future < -10:
            return 'sell'

with open("brain.pickle", "wb") as f:
    pickle.dump(tickers, f)

if __name__ == '__main__':
    api = Poloniex(jsonNums=float)
    m = Marconi(api, 'USDT_BTC')
    df = m.chart.dataFrame()
    features, labels = m.preprocessChart(df)
    print(m.train(features, labels))
    print(m.brain.predict(df[]))
