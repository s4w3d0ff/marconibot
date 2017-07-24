#!/usr/bin/python
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
from .tools import time, UTCstr2epoch, logging, pymongo

logger = logging.getLogger(__name__)


class Bookie(object):

    def __init__(self, api):
        self.api = api
        self.db = pymongo.MongoClient().poloniex

    def updateTradeHistory(self, market):
        try:
            old = list(self.db[market + 'tradeHistory'].find().sort(
                'timestamp', pymongo.ASCENDING))[-1]
        except:
            logger.warning('No %s trades found in database', market)
            old = {'timestamp': time() - self.api.YEAR * 10}
        start = old['timestamp'] + 1
        hist = self.api.returnTradeHistory(market, start=start)
        if len(hist) > 0:
            logger.info('%d new trade database entries' % len(hist))

            for trade in hist:
                _id = trade['globalTradeID']
                del trade['globalTradeID']
                trade['timestamp'] = UTCstr2epoch(trade['date'])
                trade['amount'] = float(trade['amount'])
                trade['total'] = float(trade['total'])
                trade['tradeID'] = int(trade['tradeID'])
                trade['orderNumber'] = int(trade['orderNumber'])
                trade['rate'] = float(trade['rate'])
                trade['fee'] = float(trade['fee'])
                self.db[market + 'tradeHistory'].update_one(
                    {"_id": _id}, {"$set": trade}, upsert=True)

    def myTradeHistory(self, market, query=None):
        self.updateTradeHistory(market)
        return list(self.db[market + 'tradeHistory'].find(query).sort(
            'timestamp', pymongo.ASCENDING))

if __name__ == '__main__':
    from .tools import Poloniex
    from sys import argv
    from pprint import pprint
    logging.basicConfig(level=logging.INFO)
    key, secret = argv[1:3]
    api = Poloniex(key, secret, jsonNums=float)
    bookie = Bookie(api)
    pprint(bookie.myTradeHistory('BTC_DASH')[-6:])
