import json

from attrdict import AttrDict


class ProtocolMessage:
    def __init__(self, channel, body, envelope, properties):
        self.channel = channel
        self.body = body
        self.envelope = envelope
        self.properties = properties


class BaseMessage(AttrDict):
    def __init__(self, *args, **kwargs):
        super(BaseMessage, self).__init__(*args, **kwargs)

    @property
    def json(self):
        return json.dumps(self)
