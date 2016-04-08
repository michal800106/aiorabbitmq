import asyncio
import json
import traceback

from aiorabbitmq.connection import connection
from aiorabbitmq.exceptions import MismatchedMessageCls, NotDeclared
from aiorabbitmq.queues import BaseQueue
from aiorabbitmq.messages import BaseMessage, ProtocolMessage


class BaseConsumer:
    NO_LOCAL = False
    NO_ACK = False
    NO_WAIT = False
    CONSUMER_TAG = ""
    QUEUE = BaseQueue
    MESSAGE_CLS = BaseMessage
    EXCHANGE = None
    PREFETCH_COUNT = None
    EXCLUSIVE = False

    CHAR_SET = 'utf-8'

    def __init__(self, conn: connection, auto_declare=True, nack_on_error=True):
        self.connection = conn
        self.nack_on_error = nack_on_error
        if self.EXCHANGE:
            self.exchange = self.EXCHANGE(self.connection)
        else:
            self.exchange = None
        self.queue = self.QUEUE(self.connection)
        self.auto_declare = auto_declare

    @property
    def declared(self):
        return self.queue.declared and self.exchange.declared

    @property
    def kwargs(self):
        return {
            "queue_name": self.QUEUE.QUEUE_NAME,
            "no_local": self.NO_LOCAL,
            "no_ack": self.NO_ACK,
            "exclusive": self.EXCLUSIVE,
            "no_wait": self.NO_WAIT,
            "consumer_tag": self.CONSUMER_TAG
        }

    async def declare(self):
        try:
            if not self.queue.declared:
                await self.queue.declare()
        except Exception:
            print("Exception during queue declaration")
            print(traceback.format_exc())
            raise
        if self.exchange and not self.exchange.declared:
            try:
                await self.exchange.declare()
                await self.exchange.bind_queue(self.QUEUE.QUEUE_NAME)
            except Exception:
                print("Exception during exchange declaration")
                print(traceback.format_exc())
                raise

    async def _callback(self, channel, body, envelope, properties):
        if type(body) == bytes:
            body = body.decode(self.CHAR_SET)
        protocol_message = ProtocolMessage(channel, body, envelope, properties)
        protocol_message.body = await self.clean(protocol_message)
        try:
            await self.callback(protocol_message)
        except Exception:
            print("Exception during callback")
            print(traceback.format_exc())
            if self.nack_on_error:
                await channel.basic_client_nack(envelope.delivery_tag)
            elif not self.NO_ACK:
                await channel.basic_client_ack(envelope.delivery_tag)
            raise
        else:
            if not self.NO_ACK:
                await channel.basic_client_ack(envelope.delivery_tag)

    async def clean(self, message):
        value = json.loads(message.body)
        if self.MESSAGE_CLS:
            try:
                value = self.MESSAGE_CLS(**value)
            except Exception:
                raise MismatchedMessageCls
        return value

    async def callback(self, message: ProtocolMessage):
        raise NotImplementedError

    async def run(self):
        channel = await self.connection.channel()
        if not self.declared:
            if self.auto_declare:
                await self.declare()
            else:
                raise NotDeclared
        if self.PREFETCH_COUNT:
            await channel.basic_qos(prefetch_count=self.PREFETCH_COUNT)
        await channel.basic_consume(self._callback, **self.kwargs)
