import asyncio
import json
import unittest

from pyrabbit.http import NetworkError

from aiorabbitmq.connection import connection
from aiorabbitmq.consumers import BaseConsumer
from aiorabbitmq.exchanges import BaseExchange
from aiorabbitmq.exchanges import EXCHANGE_TYPES
from aiorabbitmq.messages import BaseMessage, ProtocolMessage
from aiorabbitmq.producers import BaseProducer
from aiorabbitmq.queues import BaseQueue
from aiorabbitmq.tests import testcase


class ProducerTestCase(testcase.RabbitTestCase, unittest.TestCase):
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

            @asyncio.coroutine
            def callback(self, message: ProtocolMessage):
                self.future.set_result(True)

        class TestProducer(BaseProducer):
            CONSUMER = TestConsumer
            EXCHANGE = TestConsumer.EXCHANGE

        self.TestProducer = TestProducer
        self.TestConsumer = TestConsumer
        self.TestExchange = TestExchange
        self.TestMessage = TestMessage
        self.TestQueue = TestQueue

    def tearDown(self):
        self.http_client.delete_exchange(self.VHOST, self.TestExchange.EXCHANGE_NAME)
        self.http_client.delete_queue(self.VHOST, self.TestQueue.QUEUE_NAME)
        super().tearDown()

    @testcase.coroutine
    async def test_publish(self):
        async with connection(self.host, self.port, "guest", "guest", vhost=self.VHOST) as conn:
            producer = self.TestProducer(conn)
            message = self.TestMessage('testing consumer')
            await producer.publish(message)
            try:
                rmessage = self.http_client.get_messages(self.VHOST, self.TestQueue.QUEUE_NAME)
                self.assertEqual(rmessage[0]['payload'], json.dumps(message))
            except (BrokenPipeError, NetworkError):
                future = asyncio.Future()
                consumer = self.TestConsumer(conn)
                consumer.future = future
                await consumer.run()
                await future
                self.assertTrue(future.result())

    @testcase.coroutine
    async def test_declare(self):
        async with connection(self.host, self.port, "guest", "guest", vhost=self.VHOST) as conn:
            producer = self.TestProducer(conn)
            await producer.declare()
            self.assertTrue(producer.declared)
            await self.assertExchangeExists(producer.CONSUMER.EXCHANGE.EXCHANGE_NAME)
            await self.assertQueueExists(producer.CONSUMER.QUEUE.QUEUE_NAME)
