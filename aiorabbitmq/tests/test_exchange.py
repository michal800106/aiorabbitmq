import unittest

from aiorabbitmq.connection import connection
from aiorabbitmq.exchanges import BaseExchange, EXCHANGE_TYPES
from aiorabbitmq.tests import testcase


class ExchangeTestCase(testcase.RabbitTestCase, unittest.TestCase):
    def setUp(self):
        super().setUp()

        class TestExchange(BaseExchange):
            EXCHANGE_NAME = self.get_random_name()
            TYPE_NAME = EXCHANGE_TYPES.DIRECT

        self.TestExchange = TestExchange

    def tearDown(self):
        self.http_client.delete_exchange(self.VHOST, self.TestExchange.EXCHANGE_NAME)
        super().tearDown()

    def validate_exchange(self, exch):
        exch_results = self.http_client.get_exchange(self.VHOST, exch.EXCHANGE_NAME)
        for key in ['durable', 'auto_delete', 'type']:
            value = getattr(exch, key.upper())
            self.assertEqual(exch_results[key], value)

    @testcase.coroutine
    async def test_declare(self):
        async with connection(*self.connection_args) as conn:
            exch = self.TestExchange(conn)

            await exch.declare()
            self.validate_exchange(exch)
            self.http_client.delete_exchange(self.VHOST, self.TestExchange.EXCHANGE_NAME)

            exch.AUTO_DELETE = True
            await exch.declare()
            self.validate_exchange(exch)
            self.http_client.delete_exchange(self.VHOST, self.TestExchange.EXCHANGE_NAME)
            exch.AUTO_DELETE = False

            exch.DURABLE = True
            await exch.declare()
            self.validate_exchange(exch)
            self.http_client.delete_exchange(self.VHOST, self.TestExchange.EXCHANGE_NAME)
            exch.DURABLE = False

            exch.TYPE = EXCHANGE_TYPES.FANOUT
            await exch.declare()
            self.validate_exchange(exch)
            self.http_client.delete_exchange(self.VHOST, self.TestExchange.EXCHANGE_NAME)

            exch.TYPE = EXCHANGE_TYPES.HEADERS
            await exch.declare()
            self.validate_exchange(exch)
