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
from .. import Thread, logging

logger = logging.getLogger(__name__)


class Minion(object):
    """ Minions control child processes that do the Daemon's bidding. """

    def start(self):
        """ Start Minion.run Process """
        self.__thread = Thread(target=self.run)
        self.__thread.daemon = True
        self._running = True
        self.__thread.start()

    def stop(self):
        """ Force the Minion to stop """
        self._running = False
        try:
            self.__thread.join()
        except Exception as e:
            logger.exception(e)

    def run(self):
        """ Method ran in a child process. It should be over written when
        subclassed """
        self.stop()
