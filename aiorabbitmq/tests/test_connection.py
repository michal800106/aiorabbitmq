import unittest

from aiorabbitmq.connection import connection
from aiorabbitmq.tests import testcase


class ConnectionTestCase(testcase.RabbitTestCase, unittest.TestCase):

    @testcase.coroutine
    async def test_connection_setup(self):
        conn = connection(*self.connection_args)
        self.assertFalse(conn.connected)
        await conn.connect()
        self.assertTrue(conn.connected)
        self.assertEqual(len(self.http_client.get_connections()), 1)
        chan = await conn.channel()
        self.assertTrue(chan.is_open)
        await conn.close()
        # Driver has issue closing connection, should be fixed soon.
        # self.assertEqual(len(self.http_client.get_connections()), 0)

    @testcase.coroutine
    async def test_connection_teardown(self):
        conn = connection(*self.connection_args)
        await conn.connect()
        self.assertTrue(conn.connected)
        self.assertEqual(len(self.http_client.get_connections()), 1)
        await conn.close()
        self.assertFalse(conn.connected)
        # Driver has issue closing connection, should be fixed soon.
        # self.assertEqual(len(self.http_client.get_connections()), 0)

    @testcase.coroutine
    async def test_connection_manager(self):
        async with connection(*self.connection_args) as conn:
            self.assertTrue(conn.connected)
            self.assertEqual(len(self.http_client.get_connections()), 1)
        # Driver has issue closing connection, should be fixed soon.
        # self.assertEqual(len(self.http_client.get_connections()), 0)

