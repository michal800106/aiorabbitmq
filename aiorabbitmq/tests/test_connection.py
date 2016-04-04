import unittest

from aiorabbitmq.connection import connection
from aiorabbitmq.tests import testcase


class ConnectionTestCase(testcase.RabbitTestCase, unittest.TestCase):
    async def find_conn(self, conn):
        rabbit_conn = None
        connections = self.http_client.get_connections()
        for c in connections:
            if c['client_properties']['uuid'] == str(conn.uuid):
                rabbit_conn = c
                break
        return rabbit_conn

    @testcase.coroutine
    async def test_connection_setup(self):
        conn = connection(*self.connection_args)
        self.assertFalse(conn.connected)
        await conn.connect()
        self.assertTrue(conn.connected)
        self.assertIsNotNone(await self.find_conn(conn))
        chan = await conn.channel()
        self.assertTrue(chan.is_open)
        await conn.close()
        # Driver has issue closing connection, should be fixed soon.
        # self.assertIsNone(await self.find_conn(conn))

    @testcase.coroutine
    async def test_connection_teardown(self):
        conn = connection(*self.connection_args)
        await conn.connect()
        self.assertTrue(conn.connected)
        self.assertIsNotNone(await self.find_conn(conn))
        await conn.close()
        self.assertFalse(conn.connected)
        # Driver has issue closing connection, should be fixed soon.
        # self.assertIsNone(await self.find_conn(conn))

    @testcase.coroutine
    async def test_connection_manager(self):
        async with connection(*self.connection_args) as conn:
            self.assertTrue(conn.connected)
            self.assertIsNotNone(await self.find_conn(conn))
        # Driver has issue closing connection, should be fixed soon.
        # self.assertIsNone(await self.find_conn(conn))

