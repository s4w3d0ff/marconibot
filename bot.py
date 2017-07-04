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
from marconi.tools import np, pd, logging, getMongoDb, show, Poloniex
from marconi.tools.brain import Brain
from marconi.tools.brain import RandomForestClassifier, DecisionTreeClassifier
from marconi.charter import Charter
from marconi.ticker import Ticker
from marconi.loaner import Loaner


logger = logging.getLogger(__name__)


class Marconi(object):

    def __init__(self, api=False):
        self.api = api
        if not self.api:
            self.api = Poloniex(jsonNums=float)
        self.market = market
        self.parentCoin, self.child = self.market.split('_')
        self.charter = Charter(Charter(self.api))
        self.brain = Brain({'rf': RandomForestClassifier(n_estimators=10,
                                                         random_state=123),
                            'dt': DecisionTreeClassifier()})
        self.ticker = Ticker(self.api)
        # self.loaner = Loaner(self.api, coins=lendCoins})


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('poloniex').setLevel(logging.INFO)

    marconi = Marconi()
    marconi.charter.dataFrame()

    """
    markets = ['BTC_LTC',
               'ETH_ETC',
               'BTC_DOGE',
               'BTC_XRP',
               'USDT_BTC',
               'USDT_LTC',
               'BTC_DASH',
               'USDT_DASH',
               'BTC_FCT',
               'BTC_ETC']
    window = 120
    featureset = ['sma', 'macd', 'rsi', 'close']

    for market in markets:
        train = m.chart.dataFrame(market, period, window=window)
        train.replace([np.inf, -np.inf], np.nan, inplace=True)
        # make nan the mean
        train.fillna(train.mean(), inplace=True)

        features = train[featureset].values
        logger.info("%s training size: %s", market, str(len(features)))

        if 'label' in train:
            labels = train['label'].values
        # get labels
        labels = []

        m.brain.train(features, labels)

    p, test = m.chart.graph('BTC_ETH',
                            period,
                            window=window,
                            volume=True,
                            bands=True,
                            maves=True)
    show(p)

    test['prediction'] = m.brain.votinglobe.predict(test[featureset].values)
    print(test[['close', 'bbpercent', 'prediction']])
    """
