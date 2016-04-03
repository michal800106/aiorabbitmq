class MismatchedMessageCls(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NotDeclared(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)