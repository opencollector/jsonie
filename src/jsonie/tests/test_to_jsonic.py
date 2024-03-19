import collections.abc
import dataclasses
import datetime
import decimal
import sys
import types
import typing
from collections import namedtuple

import pytest

from ..exceptions import ToJsonicConverterError


@pytest.mark.parametrize(
    ("expected", "input"),
    [
        (
            1,
            (int, 1),
        ),
        (
            1,
            (int, 1.0),
        ),
        (
            1.0,
            (float, 1),
        ),
        (
            1.0,
            (float, 1.0),
        ),
        (
            "test",
            (str, "test"),
        ),
        (
            b"test",
            (bytes, "dGVzdA=="),
        ),
        (
            True,
            (bool, True),
        ),
        (
            decimal.Decimal("123"),
            (decimal.Decimal, 123),
        ),
        (
            decimal.Decimal("123.456"),
            (decimal.Decimal, "123.456"),
        ),
        (
            decimal.Decimal("123"),
            (decimal.Decimal, 123.0),
        ),
        (
            datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
            (datetime.datetime, "1970-01-01T00:00:00+00:00"),
        ),
        (
            datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
            (datetime.datetime, "1970-01-01T00:00:00Z"),
        ),
        (
            datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
            (datetime.datetime, 0),
        ),
        (
            datetime.date(1970, 1, 1),
            (datetime.date, "1970-01-01"),
        ),
        (
            datetime.date(1970, 1, 1),
            (datetime.date, "1970-01-01T00:00:00+00:00"),
        ),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_scalars(expected, input):
    from ..to_jsonic import ToJsonicConverter

    assert ToJsonicConverter()(input[0], input[1]) == expected


@pytest.mark.parametrize(
    ("expected", "input"),
    [
        (
            1.2,
            (typing.Union[int, float], 1.2),
        ),
        (
            1.2,
            (typing.Union[float, int], 1.2),
        ),
        (
            1,
            (typing.Union[int, str], 1),
        ),
        (
            "1",
            (typing.Union[int, str], "1"),
        ),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_scalar_unions(expected, input):
    from ..to_jsonic import ToJsonicConverter

    assert ToJsonicConverter()(input[0], input[1]) == expected


@pytest.mark.parametrize(
    ("prefer_immutable_types_for_nonmutable_sequence", "expected", "input"),
    [
        (
            False,
            [1, 2],
            (typing.Sequence[int], [1, 2]),
        ),
        (
            False,
            [1, 2],
            (typing.Sequence[int], [1.5, 2.3]),
        ),
        (
            False,
            [1.0, 2.0],
            (typing.Sequence[float], [1, 2]),
        ),
        (
            False,
            [1.5, 2.3],
            (typing.Sequence[typing.Any], [1.5, 2.3]),
        ),
        (
            False,
            [datetime.datetime(1970, 1, 1, 0, 0, 1, tzinfo=datetime.timezone.utc)],
            (typing.Sequence[datetime.datetime], [1]),
        ),
        (
            True,
            (1, 2),
            (typing.Sequence[int], [1, 2]),
        ),
        (
            True,
            (1, 2),
            (typing.Sequence[int], [1.5, 2.3]),
        ),
        (
            True,
            (1.0, 2.0),
            (typing.Sequence[float], [1, 2]),
        ),
        (
            True,
            (1.5, 2.3),
            (typing.Sequence[typing.Any], [1.5, 2.3]),
        ),
        (
            True,
            (datetime.datetime(1970, 1, 1, 0, 0, 1, tzinfo=datetime.timezone.utc),),
            (typing.Sequence[datetime.datetime], [1]),
        ),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_array(
    prefer_immutable_types_for_nonmutable_sequence, expected, input
):
    from ..to_jsonic import ToJsonicConverter

    typ_ = input[0]
    if isinstance(typ_, types.FunctionType):
        typ_ = typ_()

    assert (
        ToJsonicConverter(
            prefer_immutable_types_for_nonmutable_sequence=prefer_immutable_types_for_nonmutable_sequence
        )(typ_, input[1])
        == expected
    )


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python 3.9 or higher")
@pytest.mark.parametrize(
    ("prefer_immutable_types_for_nonmutable_sequence", "expected", "input"),
    [
        (
            False,
            [1, 2],
            (lambda: collections.abc.Sequence[int], [1, 2]),
        ),
        (
            False,
            [1, 2],
            (lambda: collections.abc.Sequence[int], [1.5, 2.3]),
        ),
        (
            False,
            [1.0, 2.0],
            (lambda: collections.abc.Sequence[float], [1, 2]),
        ),
        (
            False,
            [1.5, 2.3],
            (lambda: collections.abc.Sequence[typing.Any], [1.5, 2.3]),
        ),
        (
            False,
            [datetime.datetime(1970, 1, 1, 0, 0, 1, tzinfo=datetime.timezone.utc)],
            (lambda: collections.abc.Sequence[datetime.datetime], [1]),
        ),
        (
            True,
            (1, 2),
            (lambda: collections.abc.Sequence[int], [1, 2]),
        ),
        (
            True,
            (1, 2),
            (lambda: collections.abc.Sequence[int], [1.5, 2.3]),
        ),
        (
            True,
            (1.0, 2.0),
            (lambda: collections.abc.Sequence[float], [1, 2]),
        ),
        (
            True,
            (1.5, 2.3),
            (lambda: collections.abc.Sequence[typing.Any], [1.5, 2.3]),
        ),
        (
            True,
            (datetime.datetime(1970, 1, 1, 0, 0, 1, tzinfo=datetime.timezone.utc),),
            (lambda: collections.abc.Sequence[datetime.datetime], [1]),
        ),
        (
            False,
            [1, 2],
            (lambda: list[int], [1, 2]),
        ),
        (
            False,
            [1, 2],
            (lambda: list[int], [1.5, 2.3]),
        ),
        (
            False,
            [1.0, 2.0],
            (lambda: list[float], [1, 2]),
        ),
        (
            False,
            [1.5, 2.3],
            (lambda: list[typing.Any], [1.5, 2.3]),
        ),
        (
            False,
            [datetime.datetime(1970, 1, 1, 0, 0, 1, tzinfo=datetime.timezone.utc)],
            (lambda: list[datetime.datetime], [1]),
        ),
        (
            True,
            (1, 2),
            (lambda: tuple[int, ...], [1, 2]),
        ),
        (
            True,
            (1, 2),
            (lambda: tuple[int, ...], [1.5, 2.3]),
        ),
        (
            True,
            (1.0, 2.0),
            (lambda: tuple[float, ...], [1, 2]),
        ),
        (
            True,
            (1.5, 2.3),
            (lambda: tuple[typing.Any, ...], [1.5, 2.3]),
        ),
        (
            True,
            (datetime.datetime(1970, 1, 1, 0, 0, 1, tzinfo=datetime.timezone.utc),),
            (lambda: tuple[datetime.datetime, ...], [1]),
        ),
        (
            True,
            [1, 2],
            (lambda: list[int], [1, 2]),
        ),
        (
            True,
            [1, 2],
            (lambda: list[int], [1.5, 2.3]),
        ),
        (
            True,
            [1.0, 2.0],
            (lambda: list[float], [1, 2]),
        ),
        (
            True,
            [1.5, 2.3],
            (lambda: list[typing.Any], [1.5, 2.3]),
        ),
        (
            True,
            [
                datetime.datetime(1970, 1, 1, 0, 0, 1, tzinfo=datetime.timezone.utc),
            ],
            (lambda: list[datetime.datetime], [1]),
        ),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_array_3_9(
    prefer_immutable_types_for_nonmutable_sequence, expected, input
):
    from ..to_jsonic import ToJsonicConverter

    typ_ = input[0]
    if isinstance(typ_, types.FunctionType):
        typ_ = typ_()

    assert (
        ToJsonicConverter(
            prefer_immutable_types_for_nonmutable_sequence=prefer_immutable_types_for_nonmutable_sequence
        )(typ_, input[1])
        == expected
    )


@pytest.mark.parametrize(
    ("expected", "input"),
    [
        (
            "",
            (typing.Union[str, typing.Sequence[str]], ""),
        ),
        (
            "0",
            (typing.Union[str, typing.Sequence[str]], "0"),
        ),
        (
            (),
            (typing.Union[str, typing.Sequence[str]], []),
        ),
        (
            (),
            (typing.Union[str, typing.Sequence[str]], ()),
        ),
        (
            [],
            (typing.Union[str, typing.MutableSequence[str]], []),
        ),
        (
            [],
            (typing.Union[str, typing.MutableSequence[str]], ()),
        ),
        (
            "",
            (typing.Union[str, typing.List[str], typing.Tuple[str, ...]], ""),
        ),
        (
            "0",
            (typing.Union[str, typing.List[str], typing.Tuple[str, ...]], "0"),
        ),
        (
            [],
            (typing.Union[str, typing.List[str], typing.Tuple[str, ...]], []),
        ),
        (
            (),
            (typing.Union[str, typing.List[str], typing.Tuple[str, ...]], ()),
        ),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_iterable_union(expected, input):
    from ..to_jsonic import ToJsonicConverter

    assert (
        ToJsonicConverter(prefer_immutable_types_for_nonmutable_sequence=True)(input[0], input[1])
        == expected
    )


@pytest.mark.parametrize(
    ("expected", "input"),
    [
        (
            ("a",),
            (typing.Tuple[str], ["a"]),
        ),
        (
            ("a", 1),
            (typing.Tuple[str, int], ["a", 1]),
        ),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_tuples(expected, input):
    from ..to_jsonic import ToJsonicConverter

    assert ToJsonicConverter()(input[0], input[1]) == expected


@pytest.mark.parametrize(
    ("expected", "input"),
    [
        (
            {1, 2},
            (typing.Set[int], [1, 2]),
        ),
        (
            {1, 2},
            (typing.Set[int], [1.5, 2.3]),
        ),
        (
            {1.0, 2.0},
            (typing.Set[float], [1, 2]),
        ),
        (
            {1.5, 2.3},
            (typing.Set[typing.Any], [1.5, 2.3]),
        ),
        (
            {datetime.datetime(1970, 1, 1, 0, 0, 1, tzinfo=datetime.timezone.utc)},
            (typing.Set[datetime.datetime], [1]),
        ),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_set(expected, input):
    from ..to_jsonic import ToJsonicConverter

    assert ToJsonicConverter()(input[0], input[1]) == expected


@pytest.mark.parametrize(
    ("expected", "input"),
    [
        (
            {"a": 12, "b": 456},
            (typing.Mapping[str, int], {"a": 12.123, "b": 456}),
        ),
        (
            {"a": 1.5, "b": 2},
            (typing.Mapping[str, typing.Any], {"a": 1.5, "b": 2}),
        ),
        (
            {"a": 1.5, "b": {"c": 123}},
            (
                typing.Mapping[str, typing.Union[float, typing.Mapping[str, int]]],
                {"a": 1.5, "b": {"c": 123}},
            ),
        ),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_mappings(expected, input):
    from ..to_jsonic import ToJsonicConverter

    assert ToJsonicConverter()(input[0], input[1]) == expected


@pytest.mark.parametrize(
    ("input"),
    [
        (typing.Sequence[int], ["a", 2]),
        (typing.Sequence[float], [1, "b"]),
        (typing.Set[int], [1, 2, 1]),
        (typing.Mapping[str, float], {1: 2, 3: 4}),
        (
            typing.Mapping[str, typing.Union[float, typing.Mapping[str, int]]],
            {"a": 1.5, "b": {"c": "123"}},
        ),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_fail(input):
    from ..to_jsonic import ToJsonicConverter, ToJsonicConverterError

    with pytest.raises(ToJsonicConverterError):
        ToJsonicConverter()(input[0], input[1])


@pytest.mark.parametrize(
    ("expected", "input"),
    [
        (
            {"a": 12, "b": 456.0},
            (typing.TypedDict("foo", a=int, b=float), {"a": 12.123, "b": 456}),  # type: ignore
        ),
        (
            {"a": 1.5, "b": {"c": 5}},
            (typing.TypedDict("foo", a=float, b=typing.TypedDict("bar", c=int)), {"a": 1.5, "b": {"c": 5.0}}),  # type: ignore
        ),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_nested_mappings(expected, input):
    from ..to_jsonic import ToJsonicConverter

    assert ToJsonicConverter()(input[0], input[1]) == expected


@dataclasses.dataclass
class Foo:
    a: int
    b: typing.Optional[int] = 999
    c: str = "abc"
    d: typing.List[typing.Any] = dataclasses.field(default_factory=list)


@pytest.mark.parametrize(
    ("expected", "input"),
    [
        (
            Foo(a=12, b=999, c="abc", d=[]),
            (Foo, {"a": 12.123}),
        ),
        (
            Foo(a=12, b=None, c="abc", d=[]),
            (Foo, {"a": 12.123, "b": None}),
        ),
        (
            Foo(a=12, b=456, c="abc", d=[]),
            (Foo, {"a": 12, "b": 456}),
        ),
        (
            Foo(a=1, b=999, c="def", d=[]),
            (Foo, {"a": 1, "c": "def"}),
        ),
        (
            Foo(a=1, b=999, c="abc", d=[1]),
            (Foo, {"a": 1, "d": [1]}),
        ),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_dataclasses(expected, input):
    from ..to_jsonic import ToJsonicConverter

    assert ToJsonicConverter()(input[0], input[1]) == expected


@dataclasses.dataclass
class Bar1:
    bar: typing.Union["Bar1", int]


@pytest.mark.parametrize("class_", [Bar1])
def test_pytyped_jsonic_data_to_jsonic_dataclasses_recursive(class_):
    from ..to_jsonic import ToJsonicConverter

    expected = (lambda Bar: Bar(bar=Bar(bar=Bar(bar=123))))(class_)
    input = {
        "bar": {
            "bar": {
                "bar": 123,
            }
        }
    }

    assert ToJsonicConverter()(class_, input) == expected


NT1 = namedtuple("NT1", ["a", "b"])


class NT2(typing.NamedTuple):
    a: int
    b: int


@pytest.mark.parametrize(
    ("expected", "input"),
    [
        (NT1(1, 2), (NT1, {"a": 1, "b": 2})),
        (NT1(1, 2), (NT1, [1, 2])),
        (NT2(1, 2), (NT2, {"a": 1, "b": 2})),
        (NT2(1, 2), (NT2, [1, 2])),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_namedtuple(expected, input):
    from ..to_jsonic import ToJsonicConverter

    assert ToJsonicConverter()(input[0], input[1]) == expected


if hasattr(typing, "Literal"):
    Literals = typing.Literal["A", "B", "C"]
    UnionedLiterals = typing.Union[typing.Literal["A"], typing.Literal["B", "C"]]

    @pytest.mark.parametrize(
        ("expected", "input"),
        [
            ("A", (Literals, "A")),
            ("B", (Literals, "B")),
            ("C", (Literals, "C")),
            (ToJsonicConverterError, (Literals, "D")),
            ("A", (UnionedLiterals, "A")),
            ("B", (UnionedLiterals, "B")),
            ("C", (UnionedLiterals, "C")),
            (ToJsonicConverterError, (UnionedLiterals, "D")),
        ],
    )
    def test_literal(expected, input):
        from ..to_jsonic import ToJsonicConverter

        if isinstance(expected, type) and issubclass(expected, BaseException):
            with pytest.raises(expected):
                ToJsonicConverter()(input[0], input[1])
        else:
            assert ToJsonicConverter()(input[0], input[1]) == expected
