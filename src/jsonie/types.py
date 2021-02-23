import datetime
import decimal
import typing

# JSON types
JSONScalar = typing.Union[bool, int, float, str]
JSONArray = typing.Sequence[typing.Any]
MutableJSONArray = typing.MutableSequence[typing.Any]
JSONObject = typing.Mapping[str, typing.Any]
MutableJSONObject = typing.MutableMapping[str, typing.Any]
JSONValue = typing.Union[JSONScalar, JSONArray, JSONObject, None]


# JSON'ic types
JsonicScalar = typing.Union[
    bool, int, float, str, bytes, datetime.datetime, datetime.date, decimal.Decimal, None
]
JsonicArray = typing.Sequence[typing.Any]  # FIXME: typing.Any is actually JsonicValue
JsonicSet = typing.Set[typing.Any]  # FIXME: typing.Any is actually JsonicValue
JsonicObject = typing.Mapping[str, typing.Any]  # FIXME: typing.Any is actually JsonicValue
TypedClass = object
JsonicValue = typing.Union[JsonicScalar, JsonicArray, JsonicSet, JsonicObject, TypedClass]
JsonicType = typing.Union[typing.Type[JsonicValue], typing._GenericAlias, typing._SpecialForm]  # type: ignore
