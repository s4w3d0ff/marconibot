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
from marconi.tools import np, pd, logging, getMongoDb
from marconi.tools.chart import Chart
from marconi.tools.poloniex import Poloniex
from marconi.tools.brain import Brain


logger = logging.getLogger(__name__)


class Marconi(object):

    def __init__(self, api, market, **kwarg):
        self.api = api
        self.market = market
        self.brain = Brain(self.api)
        self.chart = Chart(api, self.market)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('marconi.tools.poloniex').setLevel(logging.INFO)
    api = Poloniex(jsonNums=float)
    m = Marconi(api, 'USDT_BTC')
