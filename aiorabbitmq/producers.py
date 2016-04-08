import asyncio

from aiorabbitmq.connection import connection
from aiorabbitmq.consumers import BaseConsumer
from aiorabbitmq.exceptions import MismatchedMessageCls, NotDeclared
from aiorabbitmq.exchanges import BaseExchange


class BaseProducer:
    CONSUMER = BaseConsumer
    EXCHANGE = BaseExchange

    def __init__(self, conn: connection, auto_declare=True):
        self.connection = conn
        self.auto_declare = auto_declare
        self.consumer = self.CONSUMER(self.connection, auto_declare=auto_declare)
        self.exchange = self.consumer.exchange if self.CONSUMER.EXCHANGE == self.EXCHANGE else self.EXCHANGE(conn)

    @property
    def declared(self):
        return self.consumer.declared

    async def declare(self):
        if not self.consumer.declared:
            await self.consumer.declare()

    async def publish(self, message: CONSUMER.MESSAGE_CLS, properties=None, **extras):
        if not self.declared:
            if self.auto_declare:
                await self.declare()
            else:
                raise NotDeclared
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
        channel = await  self.connection.channel()
        await  channel.basic_publish(**kwargs)
