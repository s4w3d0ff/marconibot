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
from marconi.tools import np, pd, logging, Poloniex, shuffleDataFrame, time
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
        self.charter = Charter(self.api)
        self.brain = Brain({'rf': RandomForestClassifier(n_estimators=10,
                                                         random_state=123),
                            'dt': DecisionTreeClassifier()})
        self.ticker = Ticker(self.api)
        # self.loaner = Loaner(self.api, coins=lendCoins})


if __name__ == '__main__':
    from marconi.tools import localstr2epoch
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('poloniex').setLevel(logging.INFO)

    marconi = Marconi()

    markets = {
        'BTC_LTC': {
            'start': localstr2epoch('2017-03', fmat="%Y-%m"),
            'zoom': '1H',
            'window': 70
        },
        'ETH_ETC': {
            'start': localstr2epoch('2016-09', fmat="%Y-%m"),
            'zoom': '2H',
            'window': 80
        },
        'BTC_DOGE': {
            'start': localstr2epoch('2017-03', fmat="%Y-%m"),
            'zoom': '2H',
            'window': 60
        },
        'BTC_XRP': {
            'start': localstr2epoch('2017-03', fmat="%Y-%m"),
            'zoom': '1H',
            'window': 60
        },
        'USDT_BTC': {
            'start': localstr2epoch('2017-01', fmat="%Y-%m"),
            'zoom': '1H',
            'window': 70
        },
        'USDT_LTC': {
            'start': localstr2epoch('2017-04', fmat="%Y-%m"),
            'zoom': '1H',
            'window': 70
        },
        'BTC_DASH': {
            'start': localstr2epoch('2017-02', fmat="%Y-%m"),
            'zoom': '1H',
            'window': 60
        },
        'USDT_DASH': {
            'start': localstr2epoch('2017-02', fmat="%Y-%m"),
            'zoom': '1H',
            'window': 70
        },
        'BTC_ETH': {
            'start': localstr2epoch('2017-03', fmat="%Y-%m"),
            'zoom': '1H',
            'window': 70
        },
        'BTC_ETC': {
            'start': localstr2epoch('2017-03', fmat="%Y-%m"),
            'zoom': '1H',
            'window': 70
        }
    }

    featureset = ['shadowsize', 'rsi', 'bbpercent', 'bbrange', 'volume']

    first = True
    for market in markets:
        df = marconi.charter.dataFrame(
            pair=market,
            start=markets[market]['start'],
            zoom=markets[market]['zoom'],
            window=markets[market]['window']
        )
        df['label'] = df['percentChange'].shift(-1) > 0
        df = marconi.brain.prepDataframe(df)

        if first:
            first = False
            tempDF = df
        else:
            tempDF.append(df)
    tempDF = shuffleDataFrame(tempDF)
    f = tempDF[featureset].values
    l = tempDF['label'].values
    logger.info('Fitting %d samples...', len(f))
    marconi.brain.leftLobe.fit(f, l)

    testDF = marconi.charter.dataFrame('USDT_ETH',
                                       start=time() - 60 * 60 * 24,
                                       zoom='10T',
                                       window=30
                                       )
    testDF['label'] = testDF['percentChange'].shift(-1) > 0

    testDF['predict'] = marconi.brain.leftLobe.predict(
        testDF[featureset].values)

    print(testDF[['percentChange', 'predict']].tail(50))
    print(marconi.brain.leftLobe.score(
        testDF[featureset].values, testDF['label'].values))
