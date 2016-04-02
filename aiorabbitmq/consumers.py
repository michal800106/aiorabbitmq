import asyncio
import json

from aiorabbitmq.connection import connection
from aiorabbitmq.exceptions import MismatchedMessageCls
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
            self.exchange = self.EXCHANGE(self.connection, auto_declare=auto_declare)
        else:
            self.exchange = None
        self.queue = self.QUEUE(self.connection, auto_declare=auto_declare)
        self.declared = False
        if auto_declare:
            self.declare()

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

    @asyncio.coroutine
    def declare(self):
        try:
            if not self.queue.declared:
                yield from self.queue.declare()
        except Exception:
            print("Exception during queue declaration")
            raise
        if self.exchange and not self.exchange.declared:
            try:
                yield from self.exchange.declare()
                yield from self.exchange.bind_queue(self.QUEUE.QUEUE_NAME)
            except Exception:
                print("Exception during exchange declaration")
                raise
        self.declared = True

    @asyncio.coroutine
    def _callback(self, channel, body, envelope, properties):
        if type(body) == bytes:
            body = body.decode(self.CHAR_SET)
        protocol_message = ProtocolMessage(channel, body, envelope, properties)
        protocol_message.body = yield from self.clean(protocol_message)
        try:
            yield from self.callback(protocol_message)
        except Exception:
            if self.nack_on_error:
                print("Exception during callback, nacking")
                yield from channel.basic_client_nack(envelope.delivery_tag)
            elif not self.NO_ACK:
                yield from channel.basic_client_ack(envelope.delivery_tag)
        else:
            if not self.NO_ACK:
                yield from channel.basic_client_ack(envelope.delivery_tag)

    @asyncio.coroutine
    def clean(self, message):
        value = json.loads(message.body)
        if self.MESSAGE_CLS:
            try:
                value = self.MESSAGE_CLS(**value)
            except Exception:
                raise MismatchedMessageCls
        return value

    @asyncio.coroutine
    def callback(self, message: ProtocolMessage):
        raise NotImplementedError

    @asyncio.coroutine
    def run(self):
        channel = yield from self.connection.channel()
        if not self.declared:
            yield from self.declare()
        if self.PREFETCH_COUNT:
            yield from channel.basic_qos(prefetch_count=self.PREFETCH_COUNT)
        yield from channel.basic_consume(self._callback, **self.kwargs)
