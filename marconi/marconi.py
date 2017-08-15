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
from marconi.tools import logging, pd
from marconi.tools.poloniex import Poloniex
from marconi.tools.plotting import show, gridplot
from marconi.tools.brain import Brain, customLabels
from marconi.charter import Charter
from marconi.ticker import Ticker


logger = logging.getLogger(__name__)


class Marconi(object):

    def __init__(self, api=False, trainMarkets={}, featureset=[]):
        self.api = api
        if not self.api:
            self.api = Poloniex(jsonNums=float)
        self.charter = Charter(self.api)
        self.brain = Brain()
        self.ticker = Ticker(self.api)
        self.trainMarkets = trainMarkets
        self.featureset = featureset

    def learn(self, markets=False, featureset=False,
              labelFunc=customLabels, labelArgs={}):
        if not markets:
            markets = self.trainMarkets
        if not featureset:
            featureset = self.featureset

        self.trainMarkets = markets
        self._learning = True
        first = True
        for market in markets:
            # append each df with labels
            df = self.charter.dataFrame(
                pair=market,
                **markets[market]
            )
            df['label'] = labelFunc(df, **labelArgs)
            if first:
                first = False
                trainDF = df[self.featureset + ['label']]
            else:
                trainDF = pd.concat([trainDF, df[self.featureset + ['label']]])
        self.brain.train(trainDF)
        self._learning = False

    @property
    def tickerStatus(self):
        return self.ticker.t._running

    def plotMarkets(self, markets):
        grid = []
        for market in markets:
            plots, df = self.charter.graph(pair=market,
                                           plot_width=1500,
                                           **markets[market])
            grid.append([plots[0]])
            grid.append([plots[1]])
        show(gridplot(grid))

    def getTick(self, market):
        if self.tickerStatus:
            return self.ticker(market)
        return self.api.returnTicker()[market]
