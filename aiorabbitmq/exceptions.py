class MismatchedMessageCls(Exception):
    def __init__(self, *args, **kwargs):
        super(MismatchedMessageCls, self).__init__(*args, **kwargs)
