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
from . import tools
from .tools.chart import Chart
from .pushy import Pushy
from .loaner import Loaner
import matplotlib.pyplot as plt
import matplotlib
matplotlib.style.use('ggplot')


class Marconi(object):
    """
    Watches loanable markets
    Buy and sell using just macd and bbands (for now)
    Scrape profits into lending account
    """

    def __init__(self, key, secret, **kwargs):
        """ """
        self.api = tools.Poloniex(key, secret, jsonNums=float)
        self.push = Pushy()
        self.push.api = self.api
        self.coins = kwargs.get(
            'coins',
            {'BTC': 0.01,
             'LTC': 0.1,
             'DOGE': 1000,
             'ETH': 0.1,
             'DASH': 0.1}
        )
        self.tickDb = tools.getMongoDb('markets')
        self.loaner = Loaner(
            api=self.api,
            coins=self.coins,
            maxage=kwargs.get('maxage', 60 * 15),  # 15 min
            offset=kwargs.get('offset', 6),  # 6 loantoshi
            delay=kwargs.get('delay', 60 * 5)  # 5 min
        )
        self.charts = {coin: Chart(self.api, coin, **kwargs)
                       for coin in self.coins}

    def stop(self):
        self.push.stop()
        self.loaner.stop()

    def run(self):
        self.push.run()
        self.loaner.start()
        while True:
            for coin in self.charts:
                df = self.charts[coin].withIndicators()
                df = df[['weightedAverage',
                         'bodysize',
                         'shadowsize',
                         'macd',
                         'bbpercent',
                         'rsi',
                         'roc']]
                # larger the body size, stronger the trend
                #
                df['trend'] = df['bodysize'] + df['bbpercent'] + df['macd']
