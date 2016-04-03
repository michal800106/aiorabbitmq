# About

aiorabbitmq is based off of aioampqp project and just adds class based functionality to rabbitmq in an asyncio fashion. All the lower level AMQP functionality is done in there. This project may work for other AMQP services but is mainly designed for rabbitmq.

If you have any questions or find a bug please open an issue.


# Installation

Working this out, along with the naming

# Basic usage

### Queue
```python
from aiorabbitmq.queues import BaseQueue

class Queue(BaseQueue):
    QUEUE_NAME = 'my_queue'
    DURABLE = True
```

### Exchange
```python
from aiorabbitmq.exchanges import BaseExchange, EXCHANGE_TYPES

class Exchange(BaseExchange):
    EXCHANGE_NAME = 'my_exchange'
    DURABLE = True
    TYPE_NAME = EXCHANGE_TYPES.DIRECT
```

### Message
Messages, at this point in time, must be JSON serializable.

```python
from aiorabbitmq.messages import BaseMessage

class Message(BaseMessage):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
```

### Consumer
```python
import asyncio
from aiorabbitmq.connection import connection
from aiorabbitmq.consumers import BaseConsumer, ProtocolMessage

class Consumer(BaseConsumer):
    EXCHANGE = Exchange  # From above
    QUEUE = Queue  # From above
    MESSAGE_CLS = Message # From above
    PREFETCH_COUNT = 10  # Limit the number of messages pulled in at one time.

    @asyncio.coroutine
    def callback(self, message: ProtocolMessage):
        my_message = message.body
        print("Value 1 {}".format(my_message.value1))
        print("Value 2 {}".format(my_message.value2))
        yield from work_on_message(my_message)

@asyncio.coroutine
def consume():
    with connection("192.168.99.100", 5672, "testuser", "testpass") as conn:
        consumer = Consumer(conn)
        yield from consumer.run()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(consume())
    loop.run_forever()
```

### Producer
```python
import asyncio
from aiorabbitmq.connection import connection
from aiorabbitmq.producers import BaseProducer

class Producer(BaseProducer):
    CONSUMER = Consumer # From above
    EXCHANGE = Consumer.EXCHANGE # From Above

@asyncio.coroutine
def publish(value1, value2):
    with connection("192.168.99.100", 5672, "testuser", "testpass") as conn:
        prod = Producer(conn)
        message = prod.CONSUMER.MESSAGE_CLS(value1, value2)
        prod.publish(message)

if __name__ == '__main__':
    value1 = "test value 1"
    value2 = "test value 2"
    asyncio.get_event_loop().run_until_complete(publish(value1, value2))
```