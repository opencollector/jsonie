import abc
import base64
import collections.abc
import dataclasses
import datetime
import decimal
import json
import math
import sys
import types
import typing

import iso8601  # type: ignore

from . import typing_compat
from .exceptions import ToJsonicConverterError
from .pointer import JSONPointer
from .types import (
    JSONArray,
    JsonicArray,
    JsonicObject,
    JsonicSet,
    JsonicType,
    JsonicValue,
    JSONObject,
    JSONValue,
    TypedClass,
)
from .utils import cause, date_clone, datetime_clone, english_enumerate, is_optional

CustomConverterNameResolverFunc = typing.Callable[[JsonicType], str]
CustomConverterConvertFunc = typing.Callable[
    ["ToJsonicConverter", "ConverterContext", JSONPointer, JsonicType, JSONValue],
    typing.Tuple[JsonicValue, float],
]


class CustomConverter(typing.Protocol):
    @abc.abstractmethod
    def resolve_name(self, typ: JsonicType) -> str: ...  # pragma: nocover

    def __call__(
        self,
        converter: "ToJsonicConverter",
        tctx: "TraversalContext",
        typ: JsonicType,
        value: JSONValue,
    ) -> typing.Tuple[JsonicValue, float]: ...  # pragma: nocover


class CustomConverterFuncAdapter:
    convert: CustomConverterConvertFunc  # type: ignore

    @abc.abstractmethod
    def resolve_name(self, typ: JsonicType) -> str: ...  # pragma: nocover

    def __call__(
        self,
        converter: "ToJsonicConverter",
        tctx: "TraversalContext",
        typ: JsonicType,
        value: JSONValue,
    ) -> typing.Tuple[JsonicValue, float]:
        return self.convert(converter, tctx, typ, value)  # type: ignore

    def __init__(
        self, resolve_name: CustomConverterNameResolverFunc, convert: CustomConverterConvertFunc
    ):
        self.resolve_name = resolve_name  # type: ignore
        self.convert = convert  # type: ignore


class NameMapper(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def resolve(
        self,
        converter: "ToJsonicConverter",
        tctx: "TraversalContext",
        typ: JsonicType,
        name: str,
    ) -> typing.Optional[str]: ...

    @abc.abstractmethod
    def reverse_resolve(
        self,
        converter: "ToJsonicConverter",
        tctx: "TraversalContext",
        typ: JsonicType,
        name: str,
    ) -> typing.Optional[str]: ...


NameMapperResolveFunc = typing.Callable[
    ["ToJsonicConverter", JSONPointer, JsonicType, str], typing.Optional[str]
]


class NameMapperFuncAdapter(NameMapper):
    def resolve(
        self,
        converter: "ToJsonicConverter",
        tctx: "TraversalContext",
        typ: JsonicType,
        name: str,
    ) -> typing.Optional[str]: ...

    def reverse_resolve(
        self,
        converter: "ToJsonicConverter",
        tctx: "TraversalContext",
        typ: JsonicType,
        name: str,
    ) -> typing.Optional[str]: ...

    def __init__(self, resolve: NameMapperResolveFunc, reverse_resolve: NameMapperResolveFunc):
        self.resolve = resolve  # type: ignore
        self.reverse_resolve = reverse_resolve  # type: ignore


class IdentityNameMapper(tuple, NameMapper):
    def resolve(
        self,
        converter: "ToJsonicConverter",
        tctx: "TraversalContext",
        typ: JsonicType,
        name: str,
    ) -> str:
        return name

    def reverse_resolve(
        self,
        converter: "ToJsonicConverter",
        tctx: "TraversalContext",
        typ: JsonicType,
        name: str,
    ) -> str:
        return name


identity_mapper = IdentityNameMapper()


T = typing.TypeVar("T", bound=JsonicValue)


class ConverterContext(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def stopped(self) -> bool: ...

    @abc.abstractmethod
    def validation_error_occurred(self, error: ToJsonicConverterError) -> None: ...


class DefaultConverterContext(ConverterContext):
    @property
    def stopped(self):
        return False

    def validation_error_occurred(self, error: ToJsonicConverterError) -> None:
        raise error


class ErrorCollectingConverterContext(ConverterContext):
    @property
    def stopped(self):
        return False

    def validation_error_occurred(self, error: ToJsonicConverterError) -> None:
        self.errors.append(error)

    def __init__(self):
        self.errors = []


EMPTY_DICT: typing.Dict[str, typing.Any] = {}


def infer_global_ns(o: typing.Any) -> typing.Dict[str, typing.Any]:
    g = getattr(o, "__globals__", None)
    if g is not None:
        return g
    if isinstance(o, types.ModuleType):
        return o.__dict__
    elif isinstance(o, type):
        mod_name = getattr(o, "__module__", None)
        if mod_name is not None:
            m = sys.modules.get(mod_name)
            if m is not None:
                return infer_global_ns(m)
    else:
        wrap = getattr(o, "__wrapped__", None)
        if wrap is not None:
            return infer_global_ns(wrap)
    return EMPTY_DICT


@dataclasses.dataclass
class TraversalContext:
    ctx: ConverterContext
    pointer: JSONPointer
    governing_object: typing.Any
    parent: typing.Optional["TraversalContext"] = None

    def get_global_ns(self) -> typing.Dict[str, typing.Any]:
        return infer_global_ns(self.governing_object)

    def get_local_ns(self) -> typing.Optional[typing.Dict[str, typing.Any]]:
        return None

    def subcontext_with_pointer(self, pointer: JSONPointer) -> "TraversalContext":
        return TraversalContext(
            self.ctx,
            pointer,
            self.governing_object,
            self,
        )


Visitor = typing.Callable[
    ["ToJsonicConverter", TraversalContext, JsonicType, JsonicValue],
    JsonicValue,
]


def is_namedtuple(typ: typing.Type[T]) -> bool:
    return (
        hasattr(typ, "_fields")
        and hasattr(typ, "_make")
        and hasattr(typ, "_replace")
        and hasattr(typ, "_asdict")
    )


class NamedTupleType(typing.Protocol):
    _fields: typing.Sequence[str]

    def _make(self, values: typing.Iterable[str]) -> typing.Tuple: ...  # pragma: nocover


class ToJsonicConverter:
    custom_types: typing.Mapping[JsonicType, CustomConverter] = {}
    name_mappers: typing.Mapping[JsonicType, NameMapper] = {}
    visitor: typing.Optional[Visitor] = None
    prefer_immutable_types_for_nonmutable_sequence: bool = False

    pytype_to_json_type_mappings: typing.Dict[typing.Type, str] = {
        int: "number",
        float: "number",
        str: "string",
        bytes: "string",
        decimal.Decimal: "number or string",
        datetime.datetime: "number or string",
        datetime.date: "string",
        type(None): "null",
    }
    abctype_to_json_type_mappings: typing.Sequence[typing.Tuple[abc.ABCMeta, str]] = (
        (collections.abc.Sequence, "array"),
        (collections.abc.Mapping, "object"),
        (collections.abc.Set, "array"),
    )

    def py_type_repr(self, typ: typing.Type) -> str:
        typename = self.pytype_to_json_type_mappings.get(typ)
        if typename is not None:
            return typename
        for t, typename in self.abctype_to_json_type_mappings:
            if issubclass(typ, t):
                return typename
        return f"unknown type: {typ}"

    def type_repr(self, typ: typing_compat.GenericAlias) -> str:  # type: ignore
        custom_converter = self.custom_types.get(typ)
        if custom_converter is not None:
            return custom_converter.resolve_name(typ)
        for typ_, custom_converter in self.custom_types.items():
            if typing_compat.is_genuine_type(typ_) and isinstance(typ, type) and issubclass(typ, typ_):  # type: ignore
                return custom_converter.resolve_name(typ)
        if typing_compat.is_union_type(typ):
            return f"any of {english_enumerate((self.type_repr(t) for t in typing_compat.get_args(typ)), conj=', or ')}"
        elif typing_compat.is_literal_type(typ):  # type: ignore
            args = typing_compat.get_args(typ)
            return f"any of literal {english_enumerate((str(v) for v in args), conj=', or ')}"
        elif typing_compat.is_generic_type(typ):  # type: ignore
            origin = typing_compat.get_origin(typ)
            if issubclass(
                typing.cast(abc.ABCMeta, origin), (collections.abc.Sequence, collections.abc.Set)
            ):
                args = typing_compat.get_args(typ)
                if len(args) == 1:
                    return f"array of {self.type_repr(args[0])}"
            elif issubclass(typing.cast(abc.ABCMeta, origin), collections.abc.Mapping):
                args = typing_compat.get_args(typ)
                if len(args) == 2:
                    return f"object of {{{self.type_repr(args[0])}: {self.type_repr(args[1])}}}"
            return f"unknown type: {typ.__origin__}"
        elif isinstance(typ, typing._SpecialForm):
            if str(typ) == "typing.Any":
                return "any value"
            return f"unknown type: {typ}"
        else:
            return self.py_type_repr(typ)

    def _lookup_name_mapper(self, typ: typing.Union[JsonicType, typing._TypedDictMeta, typing._SpecialForm, typing_compat.GenericAlias]) -> typing.Optional[NameMapper]:  # type: ignore
        name_mapper = self.name_mappers.get(typ)
        if name_mapper is not None:
            return name_mapper
        name_mapper = self.name_mappers.get(typing.Any)
        if name_mapper is not None:
            return name_mapper
        name_mapper = self.name_mappers.get(object)
        if name_mapper is not None:
            return name_mapper
        return None

    def _convert_with_pytype(
        self, tctx: TraversalContext, typ: typing.Type, value: JsonicValue
    ) -> typing.Tuple[JsonicValue, float]:
        if isinstance(value, typ):
            return value, 0.5
        if isinstance(value, str):
            if issubclass(typ, datetime.datetime):
                try:
                    return datetime_clone(typ, iso8601.parse_date(value)), 3.0
                except iso8601.ParseError as e:
                    tctx.ctx.validation_error_occurred(
                        cause(
                            ToJsonicConverterError(
                                tctx.pointer, f"bad date time string ({json.dumps(value)})"
                            ),
                            e,
                        )
                    )
                    return (None, math.inf)

            elif issubclass(typ, datetime.date):
                try:
                    return date_clone(typ, iso8601.parse_date(value)), 3.0
                except iso8601.ParseError as e:
                    tctx.ctx.validation_error_occurred(
                        cause(
                            ToJsonicConverterError(
                                tctx.pointer, f"bad date time string ({json.dumps(value)})"
                            ),
                            e,
                        )
                    )
                    return (None, math.inf)
            elif issubclass(typ, decimal.Decimal):
                try:
                    return typ(value), 2.0
                except (ValueError, decimal.InvalidOperation) as e:
                    tctx.ctx.validation_error_occurred(
                        cause(
                            ToJsonicConverterError(
                                tctx.pointer, f"bad decimal string ({json.dumps(value)})"
                            ),
                            e,
                        )
                    )
                    return (None, math.inf)
            elif issubclass(typ, bytes):
                try:
                    return base64.b64decode(value.encode("ascii")), 2.0
                except ValueError as e:
                    tctx.ctx.validation_error_occurred(
                        cause(
                            ToJsonicConverterError(
                                tctx.pointer, f"bad base64 string ({json.dumps(value)})"
                            ),
                            e,
                        )
                    )
                    return (None, math.inf)
        elif isinstance(value, (int, float)):
            if issubclass(typ, (int, float)):
                return typ(value), 2.0
            elif issubclass(typ, datetime.datetime):
                return typ.utcfromtimestamp(value).replace(tzinfo=datetime.timezone.utc), 3.0
            elif issubclass(typ, decimal.Decimal):
                try:
                    return typ(value), 2.0
                except (ValueError, decimal.InvalidOperation) as e:
                    tctx.ctx.validation_error_occurred(
                        cause(
                            ToJsonicConverterError(
                                tctx.pointer, f"bad decimal string ({json.dumps(value)})"
                            ),
                            e,
                        )
                    )
                    return (None, math.inf)
        tctx.ctx.validation_error_occurred(
            ToJsonicConverterError(
                tctx.pointer,
                f"value has type {self.py_type_repr(type(value))} ({json.dumps(value)}) where {self.py_type_repr(typ)} expected",
            )
        )
        return (None, math.inf)

    def _convert_with_array(
        self, tctx: TraversalContext, typ: JsonicType, value: JSONArray
    ) -> typing.Tuple[JsonicArray, float]:
        retval: typing.MutableSequence[JsonicValue] = []
        confidence = 1.0
        for i, item in enumerate(value):
            pair = self._convert(tctx.subcontext_with_pointer(tctx.pointer[i]), typ, item)
            retval.append(pair[0])
            confidence *= pair[1]
        return (retval, confidence ** (1 / float(len(value))) if value else 2.0)

    def _convert_with_set(
        self, tctx: TraversalContext, typ: JsonicType, value: JSONArray
    ) -> typing.Tuple[JsonicSet, float]:
        occurred_item: typing.MutableMapping[JsonicValue, int] = {}
        retval: typing.MutableSet[JsonicValue] = set()
        confidence = 1.0
        for i, item in enumerate(value):
            stctx = tctx.subcontext_with_pointer(tctx.pointer[i])
            pair = self._convert(stctx, typ, item)
            if pair[0] in occurred_item:
                stctx.ctx.validation_error_occurred(
                    ToJsonicConverterError(
                        stctx.pointer,
                        f"identical item {item} already occurred at index {occurred_item[pair[0]]}",
                    )
                )
                if stctx.ctx.stopped:
                    break
                else:
                    continue
            occurred_item[pair[0]] = i
            retval.add(pair[0])
            confidence *= pair[1]
        return (
            typing.cast(JsonicSet, retval),
            confidence ** (1 / float(len(value))) if value else 2.0,
        )  # this cast should've been unnecessary, because Sequences are casted implicitly in a covariant context.

    def _convert_with_homogenious_object(
        self,
        tctx: TraversalContext,
        key_type: JsonicType,
        value_type: JsonicType,
        value: JSONObject,
    ) -> typing.Tuple[JsonicObject, float]:
        retval: typing.MutableMapping[str, JsonicValue] = {}
        confidence = 1.0
        for k, v in value.items():
            jk_pair = self._convert(tctx, key_type, k)
            if not isinstance(jk_pair[0], str):
                tctx.ctx.validation_error_occurred(
                    ToJsonicConverterError(
                        tctx.pointer,
                        f"key has type {self.type_repr(key_type)}, which deduces {k} into {self.type_repr(type(jk_pair[0]))}",
                    )
                )
                if tctx.ctx.stopped:
                    break
                else:
                    continue
            jv_pair = self._convert(
                tctx.subcontext_with_pointer(tctx.pointer / jk_pair[0]), value_type, v
            )
            typ = typing.Mapping[key_type, value_type]  # type: ignore
            name_mapper = self._lookup_name_mapper(typ)
            n: str
            if name_mapper is None:
                n = jk_pair[0]
            else:
                _n = name_mapper.resolve(self, tctx, typ, jk_pair[0])
                if _n is None:
                    continue
                n = _n
            retval[n] = jv_pair[0]
            confidence *= math.sqrt(jk_pair[1] * jv_pair[1])
        return (retval, confidence ** (1 / float(len(value))) if value else 2.0)

    def _convert_with_generic_type(self, tctx: TraversalContext, typ: typing_compat.GenericAlias, value: JSONValue) -> typing.Tuple[JsonicValue, float]:  # type: ignore
        origin = typing.cast(abc.ABCMeta, typing_compat.get_origin(typ))
        custom_converter = self.custom_types.get(origin)
        if custom_converter is not None:
            return custom_converter(self, tctx, typ, value)
        args = typing_compat.get_args(typ)
        if issubclass(origin, tuple):
            if len(args) == 2 and args[1] is ...:
                elem_type = args[0]
                if not isinstance(value, collections.abc.Sequence):
                    tctx.ctx.validation_error_occurred(
                        ToJsonicConverterError(
                            tctx.pointer,
                            f"value has type {self.py_type_repr(type(value))} ({json.dumps(value)}) where an array of {self.type_repr(elem_type)} expected",
                        )
                    )
                    return (None, math.inf)
                pair = self._convert_with_array(tctx, elem_type, value)
                confidence = pair[1]
                if isinstance(value, tuple):
                    confidence *= 0.5
                return (tuple(pair[0]), confidence)
            else:
                if not isinstance(value, collections.abc.Sequence) or len(args) != len(value):
                    tctx.ctx.validation_error_occurred(
                        ToJsonicConverterError(
                            tctx.pointer,
                            f"value has type {self.py_type_repr(type(value))} ({json.dumps(value)}) where an array [{', '.join(self.type_repr(elem_type) for elem_type in args)}] expected",
                        )
                    )
                    return (None, math.inf)
                confidence = 1.0
                retval: typing.MutableSequence[JsonicValue] = []
                for i, (elem_type, v) in enumerate(zip(args, value)):
                    _pair = self._convert_inner(
                        tctx.subcontext_with_pointer(tctx.pointer[i]), elem_type, v
                    )
                    retval.append(_pair[0])
                    confidence *= _pair[1]
                return (tuple(retval), confidence ** (1 / float(len(value))) if value else 2.0)
        elif issubclass(origin, collections.abc.Sequence):
            assert len(args) == 1
            elem_type = args[0]
            if not isinstance(value, collections.abc.Sequence):
                tctx.ctx.validation_error_occurred(
                    ToJsonicConverterError(
                        tctx.pointer,
                        f"value has type {self.py_type_repr(type(value))} ({json.dumps(value)}) where an array of {self.type_repr(elem_type)} expected",
                    )
                )
                return (None, math.inf)
            if (
                issubclass(origin, collections.abc.MutableSequence)
                or not self.prefer_immutable_types_for_nonmutable_sequence
            ):
                return self._convert_with_array(tctx, elem_type, value)
            else:
                pair = self._convert_with_array(tctx, elem_type, value)
                return (tuple(pair[0]), pair[1])
        elif issubclass(origin, collections.abc.Set):
            assert len(args) == 1
            elem_type = args[0]
            if not isinstance(value, collections.abc.Sequence):
                tctx.ctx.validation_error_occurred(
                    ToJsonicConverterError(
                        tctx.pointer,
                        f"value has type {self.py_type_repr(type(value))} ({json.dumps(value)}) where an array of {self.type_repr(elem_type)} expected",
                    )
                )
                return (None, math.inf)
            return self._convert_with_set(tctx, elem_type, value)
        elif issubclass(origin, collections.abc.Mapping):
            assert len(args) == 2
            key_type, elem_type = args
            if not isinstance(value, collections.abc.Mapping):
                tctx.ctx.validation_error_occurred(
                    ToJsonicConverterError(
                        tctx.pointer,
                        f"value has type {self.py_type_repr(type(value))} ({json.dumps(value)}) where an mapping of {{{self.type_repr(key_type)}: {self.type_repr(elem_type)}}} expected",
                    )
                )
                return (None, math.inf)
            return self._convert_with_homogenious_object(tctx, key_type, elem_type, value)

        tctx.ctx.validation_error_occurred(
            ToJsonicConverterError(
                tctx.pointer,
                f"value has type {self.py_type_repr(type(value))} ({json.dumps(value)}) where {self.type_repr(typ)} expected",
            )
        )
        return (None, math.inf)

    def _convert_with_literal_type(self, tctx: TraversalContext, typ: typing_compat.GenericAlias, value: JSONValue) -> typing.Tuple[JsonicValue, float]:  # type: ignore
        possible_literals = {
            v for v in typing_compat.get_args(typ) if isinstance(v, (bool, int, float, str))
        }
        if value in possible_literals:
            return (value, 1.0)
        else:
            tctx.ctx.validation_error_occurred(
                ToJsonicConverterError(
                    tctx.pointer,
                    f"value is ({json.dumps(value)}) where any of {english_enumerate((str(v) for v in possible_literals), conj=', or ')} expected",
                )
            )
            return (None, math.inf)

    def _convert_with_union(self, tctx: TraversalContext, typ: typing_compat.GenericAlias, value: JSONValue) -> typing.Iterable[typing.Tuple[JsonicValue, float]]:  # type: ignore
        args = typing_compat.get_args(typ)
        if len(args) == 2 and None.__class__ in args:
            # special case: typing.Optional
            if value is None:
                yield None, 1.0
                return
            t = args[1] if args[0] is None.__class__ else args[0]
            yield self._convert(tctx, t, value)
        else:
            for i, t in enumerate(args):
                try:
                    pair = self._convert(tctx, t, value)
                    yield pair[0], (pair[1] * len(args) + i)
                except ToJsonicConverterError:
                    continue

    def _convert_with_typeddict(self, tctx: TraversalContext, typ: typing._TypedDictMeta, value: JSONValue) -> typing.Tuple[typing.Optional[JsonicObject], float]:  # type: ignore
        if not isinstance(value, collections.abc.Mapping):
            tctx.ctx.validation_error_occurred(
                ToJsonicConverterError(
                    tctx.pointer,
                    f"value has type {self.py_type_repr(type(value))} ({json.dumps(value)}) where {self.type_repr(typ)} expected",
                )
            )
            return (None, math.inf)
        entries: typing.List[typing.Tuple[str, JsonicValue]] = []
        confidence = 1.0
        for n, vtyp in self._get_type_hints(tctx, typ).items():
            name_mapper = self._lookup_name_mapper(typ)
            k: str
            if name_mapper is None:
                k = n
            else:
                _k = name_mapper.reverse_resolve(self, tctx, typ, n)
                if _k is None:
                    continue
                k = _k
            if k not in value:
                if is_optional(vtyp):
                    continue
                tctx.ctx.validation_error_occurred(
                    ToJsonicConverterError(tctx.pointer, f"property {k} does not exist in {value}")
                )
                if tctx.ctx.stopped:
                    break
                else:
                    continue
            else:
                jv_pair = self._convert(
                    tctx.subcontext_with_pointer(tctx.pointer / k), vtyp, value[k]
                )
                entries.append((n, jv_pair[0]))
                confidence *= jv_pair[1]
        return typ(entries), confidence ** (1 / float(len(entries))) if entries else 1.0

    def _convert_with_dataclass(
        self,
        tctx: TraversalContext,
        typ: typing.Type[TypedClass],
        value: JSONValue,
    ) -> typing.Tuple[typing.Optional[JsonicObject], float]:
        if not isinstance(value, collections.abc.Mapping):
            tctx.ctx.validation_error_occurred(
                ToJsonicConverterError(
                    tctx.pointer,
                    f"value has type {self.py_type_repr(type(value))} ({json.dumps(value)}) where {self.type_repr(typ)} expected",
                )
            )
            return (None, math.inf)
        assert dataclasses.is_dataclass(typ)
        attrs: typing.MutableMapping[str, JsonicValue] = {}
        confidence = 1.0
        for field in dataclasses.fields(typ):
            if not field.init:
                continue
            n = field.name
            jv_pair: typing.Tuple[JsonicValue, float]
            k: str
            name_mapper = self._lookup_name_mapper(typ)
            if name_mapper is None:
                k = n
            else:
                _k = name_mapper.reverse_resolve(self, tctx, typ, n)
                if _k is None:
                    continue
                k = _k
            if k not in value:
                if (
                    field.default is not dataclasses.MISSING
                    or field.default_factory is not dataclasses.MISSING  # type: ignore
                ):
                    continue
                if field.default is not dataclasses.MISSING:
                    jv_pair = (field.default, 1.0)
                elif field.default_factory is not dataclasses.MISSING:  # type: ignore
                    jv_pair = (field.default_factory(), 1.0)  # type: ignore
                else:
                    tctx.ctx.validation_error_occurred(
                        ToJsonicConverterError(
                            tctx.pointer, f"property {k} does not exist in {value}"
                        )
                    )
                    if tctx.ctx.stopped:
                        break
                    else:
                        continue
            else:
                jv_pair = self._convert(
                    tctx.subcontext_with_pointer(tctx.pointer / k), field.type, value[k]
                )
            attrs[n] = jv_pair[0]
            confidence *= jv_pair[1]
        try:
            return (
                typing.cast(typing.Callable, typ)(**attrs),
                confidence ** (1 / float(len(attrs))) if attrs else 1.0,
            )
        except ValueError as e:
            tctx.ctx.validation_error_occurred(ToJsonicConverterError(tctx.pointer, str(e)))
            return (None, math.inf)

    def _convert_with_namedtuple(
        self,
        tctx: TraversalContext,
        typ: NamedTupleType,
        value: JSONValue,
    ) -> typing.Tuple[typing.Optional[JsonicObject], float]:
        annotations: typing.Optional[typing.Mapping[str, typing.Any]] = getattr(
            typ, "__annotations__", None
        )
        if isinstance(value, collections.abc.Mapping):
            attrs: typing.MutableMapping[str, JsonicValue] = {}
            confidence = 1.0
            for n in typ._fields:
                k: str
                name_mapper = self._lookup_name_mapper(typ)
                if name_mapper is None:
                    k = n
                else:
                    _k = name_mapper.reverse_resolve(self, tctx, typ, n)
                    if _k is None:
                        continue
                    k = _k
                if k not in value:
                    tctx.ctx.validation_error_occurred(
                        ToJsonicConverterError(
                            tctx.pointer, f"property {k} does not exist in {value}"
                        )
                    )
                    if tctx.ctx.stopped:
                        break
                    else:
                        continue
                else:
                    if annotations:
                        jv_pair = self._convert(
                            tctx.subcontext_with_pointer(tctx.pointer / k), annotations[n], value[k]
                        )
                    else:
                        jv_pair = self._convert(
                            tctx.subcontext_with_pointer(tctx.pointer / k), typing.Any, value[k]
                        )
                attrs[n] = jv_pair[0]
                confidence *= jv_pair[1]
            try:
                return (
                    typing.cast(typing.Callable, typ)(**attrs),
                    confidence ** (1 / float(len(attrs))) if attrs else 1.0,
                )
            except ValueError as e:
                tctx.ctx.validation_error_occurred(ToJsonicConverterError(tctx.pointer, str(e)))
                return (None, math.inf)
        elif isinstance(value, collections.abc.Sequence) and not isinstance(value, str):
            values: typing.List[JsonicValue] = []
            confidence = 1.0
            try:
                if annotations:
                    for i, (n, v) in enumerate(zip(typ._fields, value)):
                        jv_pair = self._convert(
                            tctx.subcontext_with_pointer(tctx.pointer / i), annotations[n], v
                        )
                        values.append(jv_pair[0])
                        confidence *= jv_pair[1]
                else:
                    for i, (n, v) in enumerate(zip(typ._fields, value)):
                        jv_pair = self._convert(
                            tctx.subcontext_with_pointer(tctx.pointer / i), typing.Any, v
                        )
                        values.append(jv_pair[0])
                        confidence *= jv_pair[1]
                return (
                    typing.cast(typing.Callable, typ._make)(values),
                    confidence ** (1 / float(len(values))) if values else 1.0,
                )
            except ValueError as e:
                tctx.ctx.validation_error_occurred(ToJsonicConverterError(tctx.pointer, str(e)))
                return (None, math.inf)
        else:
            tctx.ctx.validation_error_occurred(
                ToJsonicConverterError(
                    tctx.pointer,
                    f"expecting an object or array, got {self.py_type_repr(type(value))}",
                )
            )
            return (None, math.inf)

    def _get_type_hints(
        self, tctx: TraversalContext, typ: typing.Any
    ) -> typing.Dict[str, typing.Any]:
        global_ns = tctx.get_global_ns()
        return typing.get_type_hints(typ, global_ns, tctx.get_local_ns() or global_ns)

    def _eval_type(self, tctx: TraversalContext, typ: JsonicType):
        global_ns = tctx.get_global_ns()
        return typing._eval_type(typ, global_ns, tctx.get_local_ns() or global_ns)  # type: ignore

    def _convert_inner(
        self, tctx: TraversalContext, typ: JsonicType, value: JSONValue
    ) -> typing.Tuple[JsonicValue, float]:
        typ = self._eval_type(tctx, typ)
        custom_converter = self.custom_types.get(typ)
        if custom_converter is not None:
            return custom_converter(self, tctx, typ, value)
        for typ_, custom_converter in self.custom_types.items():
            if typing_compat.is_genuine_type(typ_) and isinstance(typ, type) and issubclass(typ, typ_):  # type: ignore
                return custom_converter(self, tctx, typ, value)
        if typing_compat.is_union_type(typ):
            candidates = sorted(
                self._convert_with_union(tctx, typ, value), key=lambda pair: pair[1]
            )
            if len(candidates) == 0:
                tctx.ctx.validation_error_occurred(
                    ToJsonicConverterError(
                        tctx.pointer,
                        f"value has type {self.py_type_repr(type(value))} ({json.dumps(value)}) where {self.type_repr(typ)} expected",
                    )
                )
                return (None, math.inf)
            return candidates[0]
        elif typing_compat.is_literal_type(typ):
            return self._convert_with_literal_type(tctx, typ, value)
        elif typing_compat.is_generic_type(typ):
            return self._convert_with_generic_type(tctx, typ, value)
        elif isinstance(typ, typing._SpecialForm):
            assert str(typ) == "typing.Any"
            return value, 1.0
        elif isinstance(typ, typing._TypedDictMeta):  # type: ignore
            return self._convert_with_typeddict(tctx, typ, value)
        elif dataclasses.is_dataclass(typ):
            return self._convert_with_dataclass(tctx, typ, value)
        elif is_namedtuple(typ):
            return self._convert_with_namedtuple(tctx, typ, value)
        else:
            return self._convert_with_pytype(tctx, typ, value)

    def _convert(
        self, tctx: TraversalContext, typ: JsonicType, value: JSONValue
    ) -> typing.Tuple[JsonicValue, float]:
        pair = self._convert_inner(tctx, typ, value)
        if self.visitor is not None:
            return self.visitor(self, tctx, typ, pair[0]), pair[1]
        else:
            return pair

    @typing.overload
    def convert(self, ctx: ConverterContext, typ: typing.Union[typing_compat.GenericAlias, typing._SpecialForm], value: JSONValue) -> typing.Any:  # type: ignore
        ...  # pragma: nocover

    @typing.overload
    def convert(
        self, ctx: ConverterContext, typ: typing.Type[T], value: JSONValue
    ) -> T: ...  # pragma: nocover

    def convert(self, ctx: ConverterContext, typ: JsonicType, value: JSONValue) -> typing.Any:
        pair = self._convert(TraversalContext(ctx, JSONPointer(), typ), typ, value)
        return pair[0]

    @typing.overload
    def __call__(self, typ: typing.Union[typing_compat.GenericAlias, typing._SpecialForm], value: JSONValue) -> typing.Any:  # type: ignore
        ...  # pragma: nocover

    @typing.overload
    def __call__(self, typ: typing.Type[T], value: JSONValue) -> T: ...  # pragma: nocover

    def __call__(self, typ: JsonicType, value: JSONValue) -> typing.Any:
        return self.convert(DefaultConverterContext(), typ, value)

    def __init__(
        self,
        custom_types: typing.Mapping[JsonicType, CustomConverter] = {},
        name_mappers: typing.Mapping[JsonicType, NameMapper] = {},
        visitor: typing.Optional[Visitor] = None,
        prefer_immutable_types_for_nonmutable_sequence: bool = False,
    ):
        self.custom_types = custom_types
        self.name_mappers = name_mappers
        self.visitor = visitor
        self.prefer_immutable_types_for_nonmutable_sequence = (
            prefer_immutable_types_for_nonmutable_sequence
        )


from_json = ToJsonicConverter()
