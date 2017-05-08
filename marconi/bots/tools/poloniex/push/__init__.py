import asyncio
import signal
import sys
from logging import getLogger

import aiohttp

from .wamp import PushApi

__author__ = 'andrew.shvv@gmail.com'


class Application(object):

    def __init__(self):
        super().__init__()
        self.logger = getLogger(__name__)
        self.push = None

    def init_api(self, loop=None, session=None):
        def stop_handler(*args, **kwargs):
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, stop_handler)

        self.push = PushApi(session=session)

        def stop_decorator(main, api):
            async def decorator(*args, **kwargs):
                await main(*args, **kwargs)
                await api.stop(force=False)

            return decorator

        g = asyncio.gather(
            self.push.wamp.start(),
            stop_decorator(self.main, self.push)()
        )

        loop.run_until_complete(g)

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    def run(self, session=None):
        self.loop = asyncio.get_event_loop()

        if not session:
            with aiohttp.ClientSession(loop=self.loop) as session:
                self.init_api(self.loop, session)
        else:
            self.init_api(self.loop, session)

    async def main(self):
        raise NotImplementedError("method 'main' should be overridden!")
