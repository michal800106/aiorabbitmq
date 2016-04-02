import asyncio

from aiorabbit.connection import connection
from aiorabbit.producers import BaseProducer
from tests.consumer import TestConsumer, TestMessage


class TestProducer(BaseProducer):
    CONSUMER = TestConsumer
    EXCHANGE = TestConsumer.EXCHANGE


@asyncio.coroutine
def test_producer(conn):
    producer = TestProducer(conn)
    while True:
        message = TestMessage('testing consumer')
        yield from producer.publish(message)

if __name__ == '__main__':
    conn = connection("192.168.99.100", 5672, "testuser", "testpass")
    loop = asyncio.get_event_loop().run_until_complete(test_producer(conn))
