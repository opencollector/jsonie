import datetime
import typing

from .types import JsonicType

Tex = typing.TypeVar("Tex", bound=Exception)


def cause(ex: Tex, cause: Exception) -> Tex:
    ex.__cause__ = cause
    return ex


class DateConstructorProtocol(typing.Protocol):
    def __call__(self, year: int, month: int, day: int):
        ...  # pragma: nocover


Td = typing.TypeVar("Td")  # Td implements DateConstructorProtocol


def date_clone(typ: typing.Type[Td], orig: datetime.datetime) -> Td:
    return typing.cast(DateConstructorProtocol, typ)(
        year=orig.year,
        month=orig.month,
        day=orig.day,
    )


class DateTimeConstructorProtocol(typing.Protocol):
    def __call__(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        second: int,
        microsecond: int,
        tzinfo: typing.Optional[datetime.tzinfo],
    ):
        ...


Tdt = typing.TypeVar("Tdt")  # Tdt implements DateTimeConstructorProtocol


def datetime_clone(typ: typing.Type[Tdt], orig: datetime.datetime) -> Tdt:
    return typing.cast(DateTimeConstructorProtocol, typ)(
        year=orig.year,
        month=orig.month,
        day=orig.day,
        hour=orig.hour,
        minute=orig.minute,
        second=orig.second,
        microsecond=orig.microsecond,
        tzinfo=orig.tzinfo,
    )


def english_enumerate(items: typing.Iterable[str], conj: str = ", and ") -> str:
    buf = []

    i = iter(items)
    try:
        x = next(i)
    except StopIteration:
        return ""
    buf.append(x)

    lx: typing.Optional[str] = None

    for x in i:
        if lx is not None:
            buf.append(", ")
            buf.append(lx)
        lx = x
    if lx is not None:
        buf.append(conj)
        buf.append(lx)
    return "".join(buf)


def is_optional(typ: JsonicType) -> bool:
    return isinstance(typ, typing._GenericAlias) and isinstance(typing.get_origin(typ), typing._SpecialForm) and typing.get_origin(typ)._name == "Union" and type(None) in typ.__args__  # type: ignore
