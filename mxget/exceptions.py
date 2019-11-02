class ClientError(Exception):
    def __init__(self, *args, **kwargs):
        pass


class RequestError(ClientError):
    def __init__(self, *args, **kwargs):
        pass


class ResponseError(ClientError):
    def __init__(self, *args, **kwargs):
        pass


class DataError(ClientError):
    def __init__(self, *args, **kwargs):
        pass
