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
from marconi.tools import logging, Poloniex, pd
from marconi.tools.brain import Brain, labelByIndicators
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

    def learn(self, markets={},
              featureset=['macd', 'rsi', 'bbpercent', 'bbrange'],
              labels='indica', slowWindow=60, fastWindow=20):
        first = True
        for market in markets:
            # append each df with labels
            df = self.charter.dataFrame(
                pair=market,
                # start=markets[market]['start'],
                # zoom=markets[market]['zoom'],
                slowWindow=slowWindow,
                fastWindow=fastWindow,
                **markets[market]
            )
            if labels == 'indica':
                df['future'] = df['close'].shift(-1)
                df[labels] = df.apply(labelByIndicators, axis=1)
            if first:
                first = False
                trainDF = df[featureset + [labels]]
            else:
                trainDF = pd.concat([trainDF, df[featureset + [labels]]])
            logger.debug(trainDF.shape)
        self.brain.train(trainDF, labels=labels)
