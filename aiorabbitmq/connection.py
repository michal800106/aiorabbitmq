import asyncio

from aioamqp import connect


class connection:
    def __init__(self, host, port, login, password, vhost='/', ssl=False, verify_ssl=True, *args, **kwargs):
        self.host = host
        self.port = port
        self.login = login
        self.password = password
        self.vhost = vhost
        self.ssl = ssl
        self.verify_ssl = verify_ssl

        self.transport = None
        self.protocol = None
        self._channel = None

    async def __aenter__(self):
        if not self.connected:
            await self.connect()
        return self

    async def __aexit__(self, *err):
        if any(err):
            import traceback
            map(lambda x: print(traceback.format_exc(x)), err)
        await self.close()

    @property
    def connected(self):
        return self.transport and self.protocol

    async def channel(self):
        if not self.connected:
            await self.connect()
        if not self._channel:
            self._channel = await self.protocol.channel()
        return self._channel

    async def connect(self, **kwargs):
        self.transport, self.protocol = await connect(
            host=self.host,
            port=self.port,
            login=self.login,
            password=self.password,
            virtualhost=self.vhost,
            ssl=self.ssl,
            verify_ssl=self.verify_ssl,
            **kwargs
        )

    async def close(self):
        await self.protocol.close()
        self.transport.close()
        self.protocol = None
        self.transport = None

