import asyncio
from aiorabbitmq.consumers import BaseConsumer
from aiorabbitmq.connection import connection
from aiorabbitmq.exchanges import BaseExchange, EXCHANGE_TYPES
from aiorabbitmq.producers import BaseProducer
from aiorabbitmq.queues import BaseQueue
from aiorabbitmq.messages import BaseMessage


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


class TestProducer(BaseProducer):
    CONSUMER = TestConsumer
    EXCHANGE = TestConsumer.EXCHANGE


async def produce():
    async with connection("localhost", 5672, "guest", "guest") as conn:
        prod = TestProducer(conn)
        for x in range(0, 100):
            message = TestMessage("Testing the producer, this is message {}".format(x))
            await prod.publish(message)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(produce())