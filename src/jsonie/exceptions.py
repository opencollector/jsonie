from .pointer import JSONPointer


class ToJsonicConverterError(Exception):
    _pointer: JSONPointer
    _message: str

    def __init__(self, pointer: JSONPointer, message: str):
        self._pointer = pointer
        self._message = message

    @property
    def pointer(self) -> JSONPointer:
        return self._pointer

    @property
    def message(self) -> str:
        return self._message

    def __str__(self):
        return f"{self._message} at {self._pointer}"
