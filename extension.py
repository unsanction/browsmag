from abc import ABCMeta


class BaseExtension(metaclass=ABCMeta):
    def __init__(self):
        ...

    @property
    def dir(self):
        return self._dir
