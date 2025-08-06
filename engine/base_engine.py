from abc import abstractmethod


class Engine:
    def __init__(self):
        pass

    @staticmethod
    def add_parser_args(parser):
        pass

    @abstractmethod
    def get_response(self, memories):
        pass
    