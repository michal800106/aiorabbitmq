import asyncio

from aiorabbitmq.connection import connection


class EXCHANGE_TYPES:
    FANOUT = 'fanout'
    DIRECT = 'direct'
    TOPIC = 'topic'
    HEADERS = 'headers'


class BaseExchange:
    EXCHANGE_NAME = 'base_exchange'
    TYPE_NAME = EXCHANGE_TYPES.FANOUT
    PASSIVE = False
    DURABLE = False
    AUTO_DELETE = False
    NO_WAIT = False
    ROUTING_KEY = ''

    def __init__(self, conn: connection, auto_declare=True):
        self.connection = conn
        self.declared = False
        if auto_declare:
            self.declare()

    @property
    def exchange_kwargs(self):
        return {
            "exchange_name": self.EXCHANGE_NAME,
            "type_name": self.TYPE_NAME,
            "passive": self.PASSIVE,
            "durable": self.DURABLE,
            "auto_delete": self.AUTO_DELETE,
            "no_wait": self.NO_WAIT
        }

    @asyncio.coroutine
    def declare(self):
        channel = yield from self.connection.channel()
        yield from channel.exchange_declare(**self.exchange_kwargs)
        self.declared = True

    @asyncio.coroutine
    def bind_queue(self, queue_name: str):
        channel = yield from self.connection.channel()
        yield from channel.queue_bind(exchange_name=self.EXCHANGE_NAME,
                                      queue_name=queue_name,
                                      routing_key=self.ROUTING_KEY)
