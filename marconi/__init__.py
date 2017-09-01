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
from marconi.market import RunningMarket, Market
from marconi.brain import Brain, SmartMarket
from marconi.poloniex import Poloniex
from marconi.tools import *

__version__ = '0.1.2'

logger = getLogger(__name__)


class SRMarket(SmartMarket, RunningMarket):
    """ A Smart Running Market """

    def __init__(self, *args, **kwargs):
        super(SRMarket, self).__init__(*args, **kwargs)


class Marconi(object):
    def __init__(self, config):

        self.config = config
        if isString(self.config):
            self.config = json.load(fp=open(self.config))

        self.trainConfig = self.config['trainConfig']
        self.tradeConfig = self.config['tradeConfig']

        self.api = Poloniex(self.config['key'], self.config['secret'],
                            jsonNums=float)
        self.brain = Brain(self.api)
        # should we load a brain?
        if 'brain' in self.config:
            try:
                self.brain.load(self.config['brain'], self.trainConfig)
            except Exception as e:
                logger.exception(e)
                logger.warning(
                    "Brain could not be loaded! %s", self.config['brain'])

    def trade(self, config=False, marketClass=Market, start=False):
        if config:
            self.tradeConfig = config
        # create a Market instance for each market in tradeConfig
        self.markets = {}
        for market in self.tradeConfig:
            self.markets[market] = marketClass(
                api=self.api,
                pair=market,
                brain=self.brain)
            if start:
                # start the market thread
                self.markets[market].start(**self.tradeConfig[market])

    def stopMarkets(self):
        logger.info('Stopping all markets')
        for market in self.markets:
            self.markets[market].stop()
        self.markets = {}
        logger.info('Markets stopped')

    @property
    def brainStatus(self):
        """ Returns True if the brain is trained """
        return self.brain._trained

    def train(self, config=False):
        """ trains self.brain using a dict of kwargs  """
        logger.info('Training Brain')
        if config:
            self.trainConfig = config
        self.brain.train(**self.trainConfig)

    def save(self, name='marconi'):
        """ Saves current configuration in a json file '<name>.json' """
        json.dump(obj={"key": self.api.key,
                       "secret": self.api.secret,
                       "tradeConfig": self.tradeConfig,
                       "trainConfig": self.trainConfig,
                       "brain": name},
                  fp=open(name + ".json", 'w'),
                  indent=4)
        logger.info('%s.json saved', name)
        self.brain.save(name)
