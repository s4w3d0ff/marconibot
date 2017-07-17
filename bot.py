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
from marconi.tools import logging, Poloniex, shuffleDataFrame, time
from marconi.tools.brain import Brain, labelByIndicators, prepDataframe
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
        self.brain = Brain()
        self.ticker = Ticker(self.api)
        # self.loaner = Loaner(self.api, coins=lendCoins})

    def run(self):
        pass

if __name__ == '__main__':
    from marconi.tools import localstr2epoch
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('poloniex').setLevel(logging.INFO)

    bot = Marconi()

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
            'zoom': '30T',
            'window': 70
        },
        'USDT_LTC': {
            'start': localstr2epoch('2017-04', fmat="%Y-%m"),
            'zoom': '30T',
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
        # append each df with labels
        df = bot.charter.dataFrame(
            pair=market,
            start=markets[market]['start'],
            zoom=markets[market]['zoom'],
            window=markets[market]['window']
        )
        df['future'] = df['close'].shift(-1)
        df['label'] = df.apply(labelByIndicators, axis=1)
        if first:
            first = False
            trainDF = df
        else:
            trainDF.append(df)

    # train brain with dataFrame
    bot.brain.train(trainDF, featureset, labels=True)

    # get test dataframe
    testDF = bot.charter.dataFrame('USDT_BTC',
                                   start=time() - 60 * 60 * 24 * 365,
                                   zoom='1H',
                                   window=120
                                   )
    # get labels
    testDF['future'] = df['close'].shift(-1)
    testDF['label'] = testDF.apply(labelByIndicators, axis=1)
    # get predictions
    testDF['leftpredict'] = bot.brain.leftLobe.predict(
        testDF[featureset].values)
    testDF['rightpredict'] = bot.brain.leftLobe.predict(
        testDF[featureset].values)

    # show results and scores
    print(testDF[['bbpercent', 'close', 'label',
                  'leftpredict', 'rightpredict']].tail(40))
    print(bot.brain.leftLobe.score(testDF[featureset].values,
                                   testDF['label'].values))
    print(bot.brain.rightLobe.score(testDF[featureset].values,
                                    testDF['label'].values))
