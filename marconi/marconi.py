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
    """
    The Marconi object

    Holds an instance of marconi.Charter(), maronic.Brain(), and
        marconi.Ticker()

    'self.charter' handles saving, updating and retrieving of chart data
        from mongodb

    'self.brain' is an object that handles scikit-learn classifiers

    'self.ticker' is an object that captures ticker websocket messages and saves
        them to mongodb

    """

    def __init__(self, api=False, trainMarkets=False, featureset=False):
        """
        api = an instance of the Poloniex class (default is a new instance)
        trainMarkets = optional dict of markets to train the brain with as
            the default
        featureset = optional list of features to use to train the brain with
            as the default
        """
        self.api = api
        if not self.api:
            self.api = Poloniex(jsonNums=float)

        self.charter = Charter(self.api)
        self.brain = Brain()
        self.ticker = Ticker(self.api)

        self.trainMarkets = trainMarkets
        self.featureset = featureset

    @property
    def tickerStatus(self):
        """
        Returns True if the websocket ticker is running, False if not
        """
        return self.ticker.t._running

    def getTick(self, market):
        """
        Get a market 'tick'

        If the websocket ticker is running the data is returned from mongodb.
        Else data is returned from self.api.returnTicker()
        """
        if self.tickerStatus:
            return self.ticker(market)
        return self.api.returnTicker()[market]

    def learn(self, markets=False, featureset=False,
              labelFunc=customLabels, labelArgs={}):
        """
        Train/fit self.brain with <markets> useing <featureset> as features,
        <labelFunc> as the function to create the training labels,
        use <labelArgs> to pass a dict of keyword args to the <labelFunc>

        if markets = False self.trainMarkets is used
        if featureset = False self.featureset is used
        """
        if not markets:
            markets = self.trainMarkets
            if not markets:
                raise TypeError('Found no markets to train with!')
        if not featureset:
            featureset = self.featureset
            if not featureset:
                raise TypeError('Found no featureset to train with!')

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
                trainDF = df[featureset + ['label']]
            else:
                trainDF = pd.concat([trainDF, df[featureset + ['label']]])
        self.brain.train(trainDF)
        self._learning = False

    def plotMarkets(self, markets, show=False):
        """
        Plot a list of markets
        markets example format:
        {
            'BTC_DASH': {
                'start': localstr2epoch('2017-02', fmat="%Y-%m"),
                'zoom': '30T',
                'slowWindow': 42,
                'fastWindow': 15
            },
            'BTC_LTC': {
                'start': localstr2epoch('2017-02', fmat="%Y-%m"),
                'zoom': '25T',
                'slowWindow': 69,
                'fastWindow': 24
            },
        }
        set <show> to True to open a browser window and show the plots
        returns the gridplot plot
        """
        grid = []
        for market in markets:
            plots, df = self.charter.graph(pair=market,
                                           plot_width=1500,
                                           **markets[market])
            grid.append([plots[0]])
            grid.append([plots[1]])
        plot = gridplot(grid)
        if show:
            show(plot)
        return plot

    def getMarketPrediction(self, market, zoom='15T', slowWindow=36,
                            fastWindow=28, labelFunc=customLabels,
                            labelArgs={}):
        """
        Gets a fresh dataframe for <market>, and uses the self.brain to
        make a prediction. Returns the dataFrame with new column named 'predict'
        """
        df = self.charter.dataFrame(market,
                                    start=time() - (self.api.WEEK * 7),
                                    zoom=zoom,
                                    slowWindow=slowWindow,
                                    fastWindow=fastWindow)
        # add predictions to df
        df['predict'] = self.brain.predict(df[self.featureset].values)

        # get prediction score
        logger.info('%s Brain Score: %.8f',
                    market,
                    self.brain.score(
                        df[self.featureset].values,
                        labelFunc(df, **labelArgs).values
                    ))
        return df

    def getBalances(self, market):
        """
        Uses self.api to get balances for parentCoin and childCoin of a market
        """
        parentCoin, childCoin = market.split('_')
        bals = self.api.returnCompleteBalances('exchange')
        childBal = float(bals[childCoin]['available'])
        parentBal = float(bals[parentCoin]['available'])
        logger.debug('%s [%s] %.8f [%s] %.8f',
                     market, parentCoin, parentBal, childCoin, childBal)
        return parentBal, childBal
