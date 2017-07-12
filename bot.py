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
from marconi.tools import np, pd, logging, show, Poloniex, shuffleDataFrame
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
        self.parentCoin, self.childCoin = self.market.split('_')
        self.charter = Charter(self.api)
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

    markets = {
        'BTC_LTC': {
            'frame': 1337,
            'zoom': '1D',
            'window': 70
        },
        'ETH_ETC': {
            'frame': 1337,
            'zoom': '1D',
            'window': 70
        },
        'BTC_DOGE': {
            'frame': 1337,
            'zoom': '1D',
            'window': 70
        },
        'BTC_XRP': {
            'frame': 1337,
            'zoom': '1D',
            'window': 70
        },
        'USDT_BTC': {
            'frame': 1337,
            'zoom': '1D',
            'window': 70
        },
        'USDT_LTC': {
            'frame': 1337,
            'zoom': '1D',
            'window': 70
        },
        'BTC_DASH': {
            'frame': 1337,
            'zoom': '1D',
            'window': 70
        },
        'USDT_DASH': {
            'frame': 1337,
            'zoom': '1D',
            'window': 70
        },
        'BTC_FCT': {
            'frame': 1337,
            'zoom': '1D',
            'window': 70
        },
        'BTC_ETC': {
            'frame': 1337,
            'zoom': '1D',
            'window': 70
        }
    }

    featureset = ['shadowsize', 'rsi', 'bbpercent', 'bbrange']

    traindf = False
    for market in markets:
        df = marconi.charter.dataFrame(
            pair=market,
            frame=markets[market]['frame']
            zoom=markets[market]['zoom']
            window=markets[market]['window']
        )

        df['label'] =

        df = shuffleDataFrame(df[featureset])

        if not traindf:
            traindf = df
        else:
            traindf.append(df)

    """
    test['prediction'] = m.brain.votinglobe.predict(test[featureset].values)
    print(test[['close', 'bbpercent', 'prediction']])
    """
