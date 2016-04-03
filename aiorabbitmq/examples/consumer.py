import asyncio
import signal
from aiorabbitmq.consumers import BaseConsumer
from aiorabbitmq.connection import connection
from aiorabbitmq.exchanges import BaseExchange, EXCHANGE_TYPES
from aiorabbitmq.queues import BaseQueue
from aiorabbitmq.messages import BaseMessage, ProtocolMessage


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

    async def callback(self, message: ProtocolMessage):
        test_message = message.body
        print(test_message.value)


async def test_consumer():
    async with connection("localhost", 5672, "guest", "guest", vhost='/') as conn:
        consumer = TestConsumer(conn)
        await consumer.run()
        await stop_future
    loop.stop()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    stop_future = asyncio.Future(loop=loop)
    loop.create_task(test_consumer())
    loop.add_signal_handler(signal.SIGHUP, lambda: stop_future.set_result(None))
    loop.run_forever()
