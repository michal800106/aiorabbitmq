import asyncio
import unittest

from aiorabbitmq.connection import connection
from aiorabbitmq.consumers import BaseConsumer
from aiorabbitmq.exchanges import BaseExchange
from aiorabbitmq.exchanges import EXCHANGE_TYPES
from aiorabbitmq.messages import BaseMessage, ProtocolMessage
from aiorabbitmq.producers import BaseProducer
from aiorabbitmq.queues import BaseQueue
from aiorabbitmq.tests import testcase


class ConsumerTestCase(testcase.RabbitTestCase, unittest.TestCase):
    def setUp(self):
        super().setUp()

        class TestQueue(BaseQueue):
            QUEUE_NAME = self.get_random_name()

        class TestMessage(BaseMessage):
            def __init__(self, value):
                self.value = value

        class TestExchange(BaseExchange):
            EXCHANGE_NAME = self.get_random_name()
            TYPE_NAME = EXCHANGE_TYPES.DIRECT

        class TestConsumer(BaseConsumer):
            QUEUE = TestQueue
            EXCHANGE = TestExchange
            MESSAGE_CLS = TestMessage

            async def callback(self, message: ProtocolMessage):
                assert message.body.value == self.current_test_value, "wrong value from producer"

        class TestProducer(BaseProducer):
            CONSUMER = TestConsumer
            EXCHANGE = TestConsumer.EXCHANGE

        self.TestQueue = TestQueue
        self.TestExchange = TestExchange
        self.TestMessage = TestMessage
        self.TestConsumer = TestConsumer
        self.TestProducer = TestProducer

    def tearDown(self):
        self.http_client.delete_exchange(self.VHOST, self.TestExchange.EXCHANGE_NAME)
        self.http_client.delete_queue(self.VHOST, self.TestQueue.QUEUE_NAME)
        super().tearDown()

    @testcase.coroutine
    async def test_declare(self):
        async with connection(*self.connection_args) as conn:
            consumer = self.TestConsumer(conn)
            await consumer.declare()
            exch = self.http_client.get_exchange(self.VHOST, self.TestExchange.EXCHANGE_NAME)
            self.assertEqual(exch['name'], consumer.EXCHANGE.EXCHANGE_NAME)
            queue = self.http_client.get_queue(self.VHOST, self.TestQueue.QUEUE_NAME)
            self.assertEqual(queue['name'], consumer.QUEUE.QUEUE_NAME)

    @testcase.coroutine
    async def test_consume(self):
        async with connection(*self.connection_args) as conn:
            producer = self.TestProducer(conn)
            consumer = self.TestConsumer(conn)
            message = self.TestMessage(self.get_random_name())
            consumer.current_test_value = message.value
            await producer.publish(message)
            await consumer.run()


