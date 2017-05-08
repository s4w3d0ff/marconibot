import random
import inspect
from datetime import datetime, timedelta
from logging import getLogger

from autobahn.wamp import message
from autobahn.wamp.role import DEFAULT_CLIENT_ROLES
from autobahn.wamp.serializer import JsonSerializer

from . import constants

__author__ = 'andrew.shvv@gmail.com'

logger = getLogger(__name__)


class WAMPClient():

    def __init__(self,
                 url,
                 session,
                 roles=DEFAULT_CLIENT_ROLES,
                 realm='realm1',
                 protocols=('wamp.2.json',),
                 serializer=JsonSerializer()):

        super().__init__()

        self.url = url
        self.session = session
        self.protocols = protocols
        self.realm = realm
        self.roles = roles
        self.serializer = serializer
        self.ws = None
        self.need_stop = False
        self.connected = False
        self.handlers = {
            message.Welcome.MESSAGE_TYPE: self._on_welcome,
            message.Subscribed.MESSAGE_TYPE: self._on_subscribed,
            message.Event.MESSAGE_TYPE: self._on_event,
        }

        self.queue = {}
        self.subscriptions = {}
        self.logger = getLogger(__name__)

    def get_handler(self, message_type):
        handler = self.handlers.get(message_type)
        if handler is None:
            handler = self._on_other
        return handler

    @property
    def subsciptions(self):
        return [self.queue, self.subscriptions]

    async def _on_welcome(self, msg):
        self.connected = True

        for request_id, subscription in self.queue.items():
            topic = subscription['topic']
            subscribe = message.Subscribe(request=request_id, topic=topic)
            self.send(subscribe)

    async def _on_event(self, event):
        subscription_id = event.subscription
        subscription = self.subscriptions[subscription_id]

        handler = subscription['handler']
        await handler(event.args)

    async def _on_subscribed(self, msg):
        request_id = msg.request
        subscription_id = msg.subscription

        subscription = self.queue.pop(request_id)
        subscription['request_id'] = request_id
        self.subscriptions[subscription_id] = subscription

    async def _on_other(self, msg):
        raise NotImplementedError("Unimplemented handler")

    def send(self, msg):
        payload, _ = self.serializer.serialize(msg)
        self.ws.send_str(payload.decode())

    def recv(self, s):
        messages = self.serializer.unserialize(s.encode())
        return messages[0]

    async def start(self):
        async with self.session.ws_connect(url=self.url,
                                           protocols=self.protocols) as ws:
            self.ws = ws

            if self.need_stop:
                await self.stop()
                return

            hello = message.Hello(self.realm, self.roles)
            self.send(hello)

            async for ws_msg in ws:
                wamp_msg = self.recv(ws_msg.data)
                wamp_handler = self.get_handler(wamp_msg.MESSAGE_TYPE)
                await wamp_handler(wamp_msg)

    async def stop(self):
        if self.ws:
            await self.ws.close()
        else:
            self.need_stop = True

    def subscribe(self, handler, topic):
        request_id = random.randint(10 ** 14, 10 ** 15 - 1)
        subscription = {
            'topic': topic,
            'handler': handler
        }

        if self.connected:
            self.send(message.Subscribe(request=request_id, topic=topic))
        else:
            self.queue[request_id] = subscription


def ticker_wrapper(handler):
    async def decorator(data):
        currency_pair = data[0]
        last = data[1]
        lowest_ask = data[2]
        highest_bid = data[3]
        percent_change = data[4]
        base_volume = data[5]
        quote_volume = data[6]
        is_frozen = data[7]
        day_high = data[8]
        day_low = data[9]

        kwargs = {
            "currency_pair": currency_pair,
            "last": last,
            "lowest_ask": lowest_ask,
            "highest_bid": highest_bid,
            "percent_change": percent_change,
            "base_volume": base_volume,
            "quote_volume": quote_volume,
            "is_frozen": is_frozen,
            "day_high": day_high,
            "day_low": day_low
        }

        if inspect.isgeneratorfunction(handler):
            await handler(**kwargs)
        else:
            handler(**kwargs)

    return decorator


def trades_wrapper(topic, handler):
    async def decorator(data):
        for event in data:
            event["currency_pair"] = topic

            if inspect.isgeneratorfunction(handler):
                await handler(**event)
            else:
                handler(**event)

    return decorator


def trollbox_wrapper(handler):
    async def decorator(data):
        if len(data) < 4:
            return
        if len(data) == 4:
            reputation = 0
        else:
            reputation = data[4]
        type_ = data[0]
        message_id = data[1]
        username = data[2]
        text = data[3]

        kwargs = {
            "id": message_id,
            "username": username,
            "type": type_,
            "text": text,
            "reputation": reputation
        }

        if inspect.isgeneratorfunction(handler):
            await handler(**kwargs)
        else:
            handler(**kwargs)

    return decorator


class PushApi:
    url = "wss://api.poloniex.com"

    def __init__(self, session):
        self.wamp = WAMPClient(url=self.url, session=session)

    async def start(self):
        await self.wamp.start()

    async def stop(self, force=True):
        if force or not self.is_subscribed:
            await self.wamp.stop()

    @property
    def is_subscribed(self):
        [queue, subscriptions] = self.wamp.subsciptions
        return len(queue) + len(subscriptions) != 0

    def subscribe(self, topic, handler):
        if topic in constants.CURRENCY_PAIRS:
            handler = trades_wrapper(topic, handler)
            self.wamp.subscribe(topic=topic, handler=handler)

        elif topic is "trollbox":
            handler = trollbox_wrapper(handler)
            self.wamp.subscribe(topic=topic, handler=handler)

        elif topic is "ticker":
            handler = ticker_wrapper(handler)
            self.wamp.subscribe(topic=topic, handler=handler)

        elif topic in constants.AVAILABLE_SUBSCRIPTIONS:
            self.wamp.subscribe(topic=topic, handler=handler)

        else:
            raise NotImplementedError("Topic not available")
