import asyncio
import traceback

from aiorabbitmq.connection import connection


class EXCHANGE_TYPES:
    FANOUT = 'fanout'
    DIRECT = 'direct'
    TOPIC = 'topic'
    HEADERS = 'headers'


class BaseExchange:
    EXCHANGE_NAME = 'base_exchange'
    TYPE = EXCHANGE_TYPES.FANOUT
    PASSIVE = False
    DURABLE = False
    AUTO_DELETE = False
    NO_WAIT = False
    ROUTING_KEY = ''

    def __init__(self, conn: connection):
        self.connection = conn
        self.declared = False

    @property
    def exchange_kwargs(self):
        return {
            "exchange_name": self.EXCHANGE_NAME,
            "type_name": self.TYPE,
            "passive": self.PASSIVE,
            "durable": self.DURABLE,
            "auto_delete": self.AUTO_DELETE,
            "no_wait": self.NO_WAIT
        }

    async def declare(self):
        channel = await self.connection.channel()
        try:
            await channel.exchange_declare(**self.exchange_kwargs)
        except Exception:
            print("Exception during declaring exchange")
            print(traceback.format_exc())
            raise
        else:
            self.declared = True

    async def bind_queue(self, queue_name: str):
        channel = await self.connection.channel()
        await channel.queue_bind(exchange_name=self.EXCHANGE_NAME,
                                 queue_name=queue_name,
                                 routing_key=self.ROUTING_KEY)
