import itertools
import typing

JSONPointerComponent = typing.Union[str, int]


def convert_int(c: JSONPointerComponent) -> JSONPointerComponent:
    try:
        return int(c)
    except ValueError:
        pass

    return c


class JSONPointer:
    path: typing.Tuple[JSONPointerComponent, ...]

    def __init__(
        self, arg: typing.Union[JSONPointerComponent, typing.Iterable[JSONPointerComponent]] = ()
    ):
        path: typing.Iterable[JSONPointerComponent]
        if isinstance(arg, str):
            _path = arg.split("/")
            if len(_path) > 0 and _path[0] == "":
                _path = _path[1:]
            if len(_path) > 0 and _path[-1] == "":
                _path = _path[:-1]
            path = _path
        elif isinstance(arg, int):
            path = (arg,)
        else:
            path = arg
        self.path = tuple(convert_int(c) for c in path)

    def __eq__(self, that):
        return isinstance(that, JSONPointer) and self.path == that.path

    def __ne__(self, that):
        return not isinstance(that, JSONPointer) or self.path != that.path

    def __truediv__(
        self, components: typing.Union[JSONPointerComponent, typing.Iterable[JSONPointerComponent]]
    ) -> "JSONPointer":
        _components: typing.Iterable[JSONPointerComponent]
        if isinstance(components, (str, int)):
            _components = (components,)
        else:
            _components = components
        return self.__class__(itertools.chain(self.path, _components))

    def __str__(self) -> str:
        return "/" + "/".join(str(p) for p in self.path)

    def __repr__(self) -> str:
        return f"JSONPointer({repr(str(self))})"

    def __getitem__(self, index: JSONPointerComponent) -> "JSONPointer":
        return self / index

    def __iter__(self) -> typing.Iterator[JSONPointerComponent]:
        return iter(self.path)

    def __hash__(self) -> int:
        return hash(self.path)
