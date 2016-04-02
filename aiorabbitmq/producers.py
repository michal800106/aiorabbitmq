import asyncio

from aiorabbitmq.connection import connection
from aiorabbitmq.consumers import BaseConsumer
from aiorabbitmq.exceptions import MismatchedMessageCls
from aiorabbitmq.exchanges import BaseExchange


class BaseProducer:
    CONSUMER = BaseConsumer
    EXCHANGE = BaseExchange

    def __init__(self, conn: connection, auto_declare=True):
        self.connection = conn
        self.consumer = self.CONSUMER(self.connection, auto_declare=auto_declare)
        self.exchange = self.consumer.exchange if self.CONSUMER.EXCHANGE == self.EXCHANGE else self.EXCHANGE(conn)
        if auto_declare:
            self.declare()

    @asyncio.coroutine
    def declare(self):
        if not self.consumer.declared:
            yield from self.consumer.declare()

    @asyncio.coroutine
    def publish(self, message: CONSUMER.MESSAGE_CLS, properties=None, **extras):
        if not isinstance(message, self.consumer.MESSAGE_CLS):
            raise MismatchedMessageCls
        kwargs = {
            'payload': message.json
        }
        if self.exchange:
            kwargs['exchange_name'] = self.exchange.EXCHANGE_NAME
            kwargs['routing_key'] = self.exchange.ROUTING_KEY
        else:
            kwargs['exchange_name'] = ''
            kwargs['routing_key'] = ''
        if properties:
            kwargs['properties'] = properties
        kwargs.update(extras)
        channel = yield from self.connection.channel()
        yield from channel.basic_publish(**kwargs)
