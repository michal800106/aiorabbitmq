import asyncio

from aiorabbitmq.connection import connection


class BaseQueue:
    QUEUE_NAME = 'base'
    PASSIVE = False
    DURABLE = False
    EXCLUSIVE = False
    AUTO_DELETE = False
    NO_WAIT = False

    def __init__(self, conn: connection):
        self.connection = conn
        self.declared = False

    async def declare(self):
        channel = await self.connection.channel()
        await channel.queue_declare(**self.kwargs)
        self.declared = True

    @property
    def kwargs(self, arguments=None, **extras):
        kwargs = {
            "queue_name": self.QUEUE_NAME,
            "passive": self.PASSIVE,
            "durable": self.DURABLE,
            "exclusive": self.EXCLUSIVE,
            "auto_delete": self.AUTO_DELETE,
            "no_wait": self.NO_WAIT,
            "arguments": arguments
        }
        kwargs.update(extras)
        return kwargs
