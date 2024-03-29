import datetime
import decimal
import typing

from .typing_compat import GenericAlias

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

if hasattr(typing, "ForwardRef"):
    JsonicType = typing.Union[typing.Type[JsonicValue], GenericAlias, typing._SpecialForm, typing.ForwardRef]  # type: ignore
else:
    JsonicType = typing.Union[typing.Type[JsonicValue], GenericAlias, typing._SpecialForm]  # type: ignore
