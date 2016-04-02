import asyncio

from aiorabbit.consumers import BaseConsumer
from aiorabbit.connection import connection
from aiorabbit.exchanges import BaseExchange, EXCHANGE_TYPES
from aiorabbit.queues import BaseQueue
from aiorabbit.messages import BaseMessage


class TestQueue(BaseQueue):
    QUEUE_NAME = 'testqueue'
    DURABLE = False


class TestMessage(BaseMessage):
    def __init__(self, value):
        self.value = value


class TestExchange(BaseExchange):
    EXCHANGE_NAME = 'testexchange'
    TYPE_NAME = EXCHANGE_TYPES.DIRECT


class TestConsumer(BaseConsumer):
    QUEUE = TestQueue
    EXCHANGE = TestExchange
    MESSAGE_CLS = TestMessage

    @asyncio.coroutine
    def callback(self, message: TestMessage):
        return


@asyncio.coroutine
def test_consumer():
    with connection("192.168.99.100", 5672, "testuser", "testpass") as conn:
        consumer = TestConsumer(conn)
        yield from consumer.run()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_consumer())
    loop.run_forever()
