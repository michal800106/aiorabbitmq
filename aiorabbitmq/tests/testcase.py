import os
from functools import wraps
import logging

import asyncio

import pyrabbit
import time

logger = logging.getLogger(__name__)


class AsyncioErrors(AssertionError):
    def __repr__(self):
        return "<AsyncioErrors: Got asyncio errors: %r" % self.args[0]


class Handler(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.messages = []

    def emit(self, record):
        message = record.msg % record.args
        print(message)
        self.messages.append(message)


asyncio_logger = logging.getLogger('aiorabbit')
handler = Handler()
asyncio_logger.addHandler(handler)


def timeout(t):
    def wrapper(func):
        setattr(func, '__timeout__', t)
        return func
    return wrapper

def coroutine(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        handler.messages = []
        coro = asyncio.coroutine(func)
        timeout_ = getattr(func, '__timeout__', self.__timeout__)
        self.loop.run_until_complete(asyncio.wait_for(coro(self, *args, **kwargs), timeout=timeout_, loop=self.loop))
        if len(handler.messages) != 0:
            raise AsyncioErrors(handler.messages)
    return wrapper


class AsyncioTestCaseMixin:
    __timeout__ = 10

    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        super().tearDown()
        self.loop.close()


class AsyncioTestCaseMixin:
    __timeout__ = 10

    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        super().tearDown()
        self.loop.close()


class RabbitTestCase(AsyncioTestCaseMixin):
    """TestCase with a rabbit running in background"""

    RABBIT_TIMEOUT = 1.0
    VHOST = 'aiorabbit'

    def setUp(self):
        super().setUp()
        self.host = os.environ.get('AMQP_HOST', 'rabbit')
        self.port = os.environ.get('AMQP_PORT', 5672)
        self.vhost = os.environ.get('AMQP_VHOST', self.VHOST)
        self.http_client = pyrabbit.api.Client('localhost:15672/', 'guest', 'guest')

        self.amqps = []
        self.channels = []
        self.exchanges = {}
        self.queues = {}
        self.transports = []

        # self.reset_vhost()

    @property
    def connection_args(self):
        return [self.host, self.port, "guest", "guest", self.VHOST]

    def reset_vhost(self):
        try:
            self.http_client.delete_vhost(self.vhost)
        except Exception:  # pylint: disable=broad-except
            pass

        self.http_client.create_vhost(self.vhost)
        self.http_client.set_vhost_permissions(
            vname=self.vhost, username='guest', config='.*', rd='.*', wr='.*',
        )

        @asyncio.coroutine
        def go():
            transport, protocol = yield from self.create_amqp()
            channel = yield from self.create_channel(amqp=protocol)
            self.channels.append(channel)
        self.loop.run_until_complete(go())

    def tearDown(self):
        @asyncio.coroutine
        def go():
            for queue_name, channel in self.queues.values():
                logger.debug('Delete queue %s', self.full_name(queue_name))
                yield from self.safe_queue_delete(queue_name, channel)
            for exchange_name, channel in self.exchanges.values():
                logger.debug('Delete exchange %s', self.full_name(exchange_name))
                yield from self.safe_exchange_delete(exchange_name, channel)
            for channel in self.channels:
                logger.debug('Delete channel %s', channel)
                yield from channel.close(no_wait=True)
                del channel
            for amqp in self.amqps:
                logger.debug('Delete amqp %s', amqp)
                yield from amqp.close()
                del amqp
            for transport in self.transports:
                self.transport.close()
        self.loop.run_until_complete(go())
        super().tearDown()

    @property
    def amqp(self):
        return self.amqps[0]

    @property
    def transport(self):
        return self.transports[0]

    @property
    def channel(self):
        return self.channels[0]

    def server_version(self, amqp=None):
        if amqp is None:
            amqp = self.amqp

        server_version = tuple(int(x) for x in amqp.server_properties['version'].split('.'))
        return server_version

    @asyncio.coroutine
    def check_exchange_exists(self, exchange_name):
        """Check if the exchange exist"""
        try:
            yield from self.exchange_declare(exchange_name, passive=True)
        except asyncio.exceptions.ChannelClosed:
            return False
        exchange = self.http_client.get_exchange(self.VHOST, exchange_name)
        return exchange is not None

    @asyncio.coroutine
    def assertExchangeExists(self, exchange_name):
        """Check if the exchange exists"""
        exchange = self.http_client.get_exchange(self.VHOST, exchange_name)
        if not exchange or not self.check_exchange_exists(exchange_name):
            self.fail("Exchange {} does not exists".format(exchange_name))

    @asyncio.coroutine
    def check_queue_exists(self, queue_name):
        """Check if the queue exist"""
        try:
            yield from self.queue_declare(queue_name, passive=True)
        except asyncio.exceptions.ChannelClosed:
            return False
        return True

    @asyncio.coroutine
    def assertQueueExists(self, queue_name):
        if not self.check_queue_exists(queue_name):
            self.fail("Queue {} does not exists".format(queue_name))

    def list_queues(self, vhost=None, fully_qualified_name=False):
        # wait for the http client to get the correct state of the queue
        time.sleep(int(os.environ.get('AMQP_REFRESH_TIME', 3)))
        queues_list = self.http_client.get_queues(vhost=vhost or self.vhost)
        queues = {}
        for queue_info in queues_list:
            queue_name = queue_info['name']
            if fully_qualified_name is False:
                queue_name = self.local_name(queue_info['name'])
                queue_info['name'] = queue_name

            queues[queue_name] = queue_info
        return queues

    def list_exchanges(self, vhost=None, name=None):
        """Return the list of the exchanges"""
        return self.http_client.get_exchanges(vhost, name)

    @asyncio.coroutine
    def safe_queue_delete(self, queue_name, channel=None):
        """Delete the queue but does not raise any exception if it fails
        The operation has a timeout as well.
        """
        channel = channel or self.channel
        full_queue_name = self.full_name(queue_name)
        try:
            yield from channel.queue_delete(full_queue_name, no_wait=False, timeout=1.0)
        except asyncio.TimeoutError:
            logger.warning('Timeout on queue %s deletion', full_queue_name, exc_info=True)
        except Exception:
            logger.error('Unexpected error on queue %s deletion', full_queue_name, exc_info=True)

    @asyncio.coroutine
    def safe_exchange_delete(self, exchange_name, channel=None):
        """Delete the exchange but does not raise any exception if it fails
        The operation has a timeout as well.
        """
        channel = channel or self.channel
        full_exchange_name = self.full_name(exchange_name)
        try:
            yield from channel.exchange_delete(full_exchange_name, no_wait=False, timeout=1.0)
        except asyncio.TimeoutError:
            logger.warning('Timeout on exchange %s deletion', full_exchange_name, exc_info=True)
        except Exception:
            logger.error('Unexpected error on exchange %s deletion', full_exchange_name, exc_info=True)

    def full_name(self, name):
        if self.is_full_name(name):
            return name
        else:
            return self.id() + '.' + name

    def local_name(self, name):
        if self.is_full_name(name):
            return name[len(self.id()) + 1:]  # +1 because of the '.'
        else:
            return name

    def is_full_name(self, name):
        return name.startswith(self.id())

    @asyncio.coroutine
    def queue_declare(self, queue_name, *args, channel=None, safe_delete_before=True, **kw):
        channel = channel or self.channel
        if safe_delete_before:
            yield from self.safe_queue_delete(queue_name, channel=channel)
        # prefix queue_name with the test name
        full_queue_name = self.full_name(queue_name)
        try:
            rep = yield from channel.queue_declare(full_queue_name, *args, **kw)

        finally:
            self.queues[queue_name] = (queue_name, channel)
        return rep

    @asyncio.coroutine
    def exchange_declare(self, exchange_name, *args, channel=None, safe_delete_before=True, **kw):
        channel = channel or self.channel
        if safe_delete_before:
            yield from self.safe_exchange_delete(exchange_name, channel=channel)
        # prefix exchange name
        full_exchange_name = self.full_name(exchange_name)
        try:
            rep = yield from channel.exchange_declare(full_exchange_name, *args, **kw)
        finally:
            self.exchanges[exchange_name] = (exchange_name, channel)
        return rep

    def register_channel(self, channel):
        self.channels.append(channel)

    @asyncio.coroutine
    def create_channel(self, amqp=None):
        amqp = amqp or self.amqp
        channel = yield from amqp.channel()
        return channel
