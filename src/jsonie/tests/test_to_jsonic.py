import dataclasses
import datetime
import decimal
import typing

import pytest


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
    ("expected", "input"),
    [
        (
            [1, 2],
            (typing.Sequence[int], [1, 2]),
        ),
        (
            [1, 2],
            (typing.Sequence[int], [1.5, 2.3]),
        ),
        (
            [1.0, 2.0],
            (typing.Sequence[float], [1, 2]),
        ),
        (
            [1.5, 2.3],
            (typing.Sequence[typing.Any], [1.5, 2.3]),
        ),
        (
            [datetime.datetime(1970, 1, 1, 0, 0, 1, tzinfo=datetime.timezone.utc)],
            (typing.Sequence[datetime.datetime], [1]),
        ),
    ],
)
def test_pytyped_jsonic_data_to_jsonic_array(expected, input):
    from ..to_jsonic import ToJsonicConverter

    assert ToJsonicConverter()(input[0], input[1]) == expected


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
            [],
            (typing.Union[str, typing.Sequence[str]], []),
        ),
        (
            [],
            (typing.Union[str, typing.Sequence[str]], ()),
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

    assert ToJsonicConverter()(input[0], input[1]) == expected


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
