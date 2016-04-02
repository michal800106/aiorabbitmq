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

    def __enter__(self):
        if not self.connected:
            self.connect()
        return self

    def __exit__(self, *err):
        self.close()

    @property
    def connected(self):
        return self.transport and self.protocol

    @asyncio.coroutine
    def channel(self):
        if not self.connected:
            yield from self.connect()
        if not self._channel:
            self._channel = yield from self.protocol.channel()
        return self._channel

    @asyncio.coroutine
    def connect(self, **kwargs):
        self.transport, self.protocol = yield from connect(
            host=self.host,
            port=self.port,
            login=self.login,
            password=self.password,
            virtualhost=self.vhost,
            ssl=self.ssl,
            verify_ssl=self.verify_ssl,
            **kwargs
        )

    @asyncio.coroutine
    def close(self):
        if not self.connected:
            return True
        if self.channel:
            self._channel.close()
        yield from self.protocol.close()
        self.protocol = None
        self.transport.close()
        self.transport = None

