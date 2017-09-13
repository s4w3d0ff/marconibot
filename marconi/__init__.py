#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    BTC: 13MXa7EdMYaXaQK6cDHqd4dwr2stBK3ESE
#    LTC: LfxwJHNCjDh2qyJdfu22rBFi2Eu8BjQdxj
#
#    https://github.com/s4w3d0ff/marconibot
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
from marconi.market import RunningMarket
from marconi.brain import Brain, SmartMarket
from marconi.poloniex import Poloniex, wsPoloniex, Coach, PoloniexError
from marconi.trading import StopLimit, Loaner, Liquidator
from marconi.tools import *

__version__ = '0.1.3'

logger = getLogger(__name__)


class SRMarket(SmartMarket, RunningMarket):
    def __init__(self, pair='_', key='', secret='', tradeConfig=False,
                 trainConfig=False, coach=True, *args, **kwargs):
        """
        Self contained single market trader with its own brain and thread
        """
        self.coach = coach
        super(SRMarket, self).__init__(pair=pair,
                                       api=wsPoloniex(key, secret,
                                                      jsonNums=float,
                                                      coach=self.coach),
                                       *args, **kwargs)
        self.tradeConfig = tradeConfig
        self.trainConfig = trainConfig

    @property
    def brainStatus(self):
        """ Returns True if the brain is trained """
        return self.brain._trained

    def addLabels(self, df, *args, **kwargs):
        logger.info('Adding %s labels', self.pair)
        if 'pchLimit' in kwargs:
            df['future'] = df['percentChange'].shift(-1)
            df = self.brain.prep(df)

        def _labels(candle, pchLimit=False, *args, **kwargs):
            score = 0
            if pchLimit:
                pch = candle['future']
                if pch > pchLimit:
                    score += 1
                if pch < -pchLimit:
                    score += -1
            return int(score)

        return df.apply(_labels, axis=1, *args, **kwargs)

    def getPredictions(self, df, backtest=False):
        df = self.brain.prep(df).set_index('date')
        df['predict'] = self.brain.predict(df[self.trainConfig['featureset']])
        if backtest:
            df = self.backtest(df, **backtest)
            logger.info("%s\n%s", self.pair,
                        df[['close', 'predict', 'btStart',
                            'btTotal', 'btProfit']].tail(3))
            logger.info("%s Backtest Profit High: %.8f Low: %.8f",
                        self.pair, df['btProfit'].max(),
                        df['btProfit'].min())
        df['label'] = self.addLabels(df, **self.trainConfig['labelArgs'])
        logger.info('%s brain score: %s', self.pair, self.brain.score(df))
        logger.info("%s\n%s", self.pair,
                    df[['close', 'predict']].tail(10))
        logger.info('%s\n%s', self.pair, df['predict'].value_counts())
        return df

    def train(self):
        # build training df based on self.pair and configs
        first = True
        logger.info('Building training dataset')
        wr = [self.trainConfig.get('weightStep', 3) * i
              for i in range(self.trainConfig.get('weightRange', 3) + 1)]
        weights = wr[1:] + [-i for i in wr[1:]]
        bdf = self.chart(start=time() - self.api.MONTH,
                         zoom=str(self.tradeConfig['interval']) + 'T'
                         ).dropna()
        for i in weights:
            # please work...
            wIndica = {
                ind: {
                    'window': self.tradeConfig['indica'][ind]['window'] + i
                } for ind in self.tradeConfig['indica']
            }
            for ind in wIndica:
                if wIndica[ind]['window'] <= 0:
                    wIndica[ind]['window'] = 3
            df = self.addIndicators(bdf, wIndica).copy()
            # append each df with labels
            df['label'] = self.addLabels(df, **self.trainConfig['labelArgs'])
            if first:
                first = False
                trainDF = df[self.trainConfig['featureset'] + ['label']]
            else:
                trainDF = pd.concat([
                    trainDF,
                    df[self.trainConfig['featureset'] + ['label']]
                ])
        self.brain.train(self.brain.prep(trainDF), **self.trainConfig)

    def save(self, location='.marconi'):
        json.dump(obj={"pair": self.pair,
                       "key": self.api.key,
                       "secret": self.api.secret,
                       "tradeConfig": self.tradeConfig,
                       "trainConfig": self.trainConfig,
                       "brain": location + ".pickle"},
                  fp=open(location + ".json", 'w'),
                  indent=4)
        logger.info('%s.json saved', location)
        self.brain.save(location)

    def load(self, location='.marconi'):
        config = json.load(fp=open(location + '.json'))
        self.api.key, self.api.secret = config['key'], config['secret']
        self.pair = config['pair']
        if 'brain' in config:
            self.brain.load(config['brain'].split('.pickle')[0])
        self.brain.labelFunc = self.addLabels
        self.tradeConfig = config['tradeConfig']
        self.trainConfig = config['trainConfig']

    def run(self):
        pass


class Marconi(object):
    def __init__(self, configDir=".marconi", marketClass=SRMarket):
        self.configDir = os.path.join(getHomeDir(), '%s' % configDir)
        if not os.path.isdir(self.configDir):
            os.makedirs(self.configDir)
            raise RuntimeError(
                "'MARKET_PAIR.json' files need to be created in %s" % self.configDir)
        self.coach = Coach()
        self._running = False
        self.markets = {}
        for f in os.listdir(self.configDir):
            if '.json' in f:
                marketConfig = json.load(
                    fp=open(os.path.join(self.configDir, f)))
                self.markets[marketConfig['pair']] = marketClass(coach=self.coach,
                                                                 **marketConfig)

    def train(self):
        logger.info('Training all markets')
        for m in self.markets:
            self.markets[m].train()

    def save(self):
        logger.info('Saving all markets')
        for m in self.markets:
            self.markets[m].save(location=os.path.join(self.configDir,
                                                       m))

    def load(self):
        logger.info('Loading all markets')
        for m in self.markets:
            self.markets[m].load(location=os.path.join(self.configDir,
                                                       m))

    def run(self, train=False):
        self._running = True
        for m in self.markets:
            if train:
                self.markets[m].train()
            self.markets[m].api.startWebsocket()
            self.markets[m].start()

    def stop(self):
        for m in self.markets:
            self.markets[m].api.stopWebsocket()
            self.markets[m].stop()

    def start(self, train=False):
        self.run(train)
        while self._running:
            try:
                sleep(2)
            except:
                self._running = False
                break
        self.stop()
        self.save()
