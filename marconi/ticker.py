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
from .tools import getMongoColl, websocket
from .tools import Poloniex, Thread
from .tools import logging, json

logger = logging.getLogger(__name__)


class Ticker(object):

    def __init__(self, api=None):
        self.api = api
        if not self.api:
            self.api = Poloniex(jsonNums=float)
        self.db = getMongoColl('poloniex', 'ticker')
        self._ws = websocket.WebSocketApp("wss://api2.poloniex.com/",
                                          on_open=self.on_open,
                                          on_message=self.on_message,
                                          on_error=self.on_error,
                                          on_close=self.on_close)

    def on_message(self, ws, message):
        message = json.loads(message)
        if 'error' in message:
            return logger.error(message['error'])

        if message[0] == 1002:
            if message[1] == 1:
                return logger.info('Subscribed to ticker')

            if message[1] == 0:
                return logger.info('Unsubscribed to ticker')

            data = message[2]
            data = [float(dat) for dat in data]
            self.db.update_one(
                {"id": data[0]},
                {"$set": {'last': data[1],
                          'lowestAsk': data[2],
                          'highestBid': data[3],
                          'percentChange': data[4],
                          'baseVolume': data[5],
                          'quoteVolume': data[6],
                          'isFrozen': data[7],
                          'high24hr': data[8],
                          'low24hr': data[9]
                          }},
                upsert=True)

    def on_error(self, ws, error):
        logger.error(error)

    def on_close(self, ws):
        if self._t._running:
            try:
                self.stop()
            except Exception as e:
                logger.exception(e)
            try:
                self.start()
            except Exception as e:
                logger.exception(e)
                self.stop()
        else:
            logger.info("Websocket closed!")

    def on_open(self, ws):
        tick = self.api.returnTicker()
        for market in tick:
            self.db.update_one(
                {'_id': market},
                {'$set': tick[market]},
                upsert=True)
        logger.info('Populated markets database with ticker data')
        self._ws.send(json.dumps({'command': 'subscribe', 'channel': 1002}))

    @property
    def status(self):
        """
        Returns True if the websocket is running, False if not
        """
        try:
            return self._t._running
        except:
            return False

    def start(self):
        """ Run the websocket in a thread """
        self._t = Thread(target=self._ws.run_forever)
        self._t.daemon = True
        self._t._running = True
        self._t.start()
        logger.info('Websocket thread started')

    def stop(self):
        """ Stop/join the websocket thread """
        self._t._running = False
        self._ws.close()
        self._t.join()
        logger.info('Websocket thread stopped/joined')

    def __call__(self, market=None):
        """ returns ticker from mongodb """
        if market:
            return self.db.find_one({'_id': market})
        return list(self.db.find())


if __name__ == "__main__":
    import pprint
    from .tools import sleep
    logging.basicConfig(level=logging.DEBUG)
    # websocket.enableTrace(True)
    ticker = Ticker()
    try:
        ticker.start()
        for i in range(3):
            sleep(5)
            pprint.pprint(ticker('USDT_BTC'))
    except Exception as e:
        logger.exception(e)
    ticker.stop()
