import types
import typing

typing_GenericAlias: typing.Type = getattr(typing, "_GenericAlias")
typing_UnionGenericAlias: typing.Optional[typing.Type] = getattr(typing, "_UnionGenericAlias", None)
GenericAlias: typing.Any

if hasattr(types, "GenericAlias"):
    GenericAlias = typing.Union[types.GenericAlias, typing_GenericAlias]  # type: ignore
else:
    GenericAlias = typing_GenericAlias


types_UnionType: typing.Any
UnionType: typing.Any

if hasattr(types, "UnionType"):
    # 3.10
    types_UnionType = types.UnionType  # type: ignore
    UnionType = typing.Union[types_UnionType, typing._UnionGenericAlias]  # type: ignore
else:
    types_UnionType = None
    if typing_UnionGenericAlias is not None:
        # 3.9 and later
        UnionType = typing_UnionGenericAlias  # type: ignore
    else:
        # 3.8 and earlier
        UnionType = typing_GenericAlias


get_args: typing.Callable[[typing.Any], typing.Tuple[typing.Any, ...]]


if hasattr(typing, "get_args"):
    get_args = typing.get_args
else:

    def get_args(t: GenericAlias) -> typing.Tuple[typing.Any, ...]:
        return t.__args__


get_origin: typing.Callable[[typing.Any], typing.Optional[typing.Any]]

if hasattr(typing, "get_origin"):
    get_origin = typing.get_origin
else:

    def get_origin(t: GenericAlias) -> typing.Optional[typing.Any]:
        return t.__origin__


def _expand_union_types(
    t: typing.Union[UnionType, typing.Type]
) -> typing.Tuple[typing.Union[UnionType, typing.Type], ...]:
    if isinstance(t, UnionType):
        return typing.cast(typing.Tuple[typing.Union[UnionType, typing.Type], ...], get_args(t))
    else:
        return (t,)


_generic_alias_types = _expand_union_types(GenericAlias)


def _origin_is_union(origin: typing.Any):
    return isinstance(origin, typing._SpecialForm) and origin._name == "Union"  # type: ignore


def is_union_type(typ: typing.Union[typing.Type, GenericAlias, UnionType]) -> bool:
    if isinstance(typ, _generic_alias_types):
        return _origin_is_union(get_origin(typ))
    elif types_UnionType is not None:
        return isinstance(typ, types_UnionType)
    return False


def is_generic_type(typ: typing.Any) -> bool:
    return isinstance(typ, _generic_alias_types) and not is_union_type(typ)


def is_genuine_type(typ: typing.Union[GenericAlias, UnionType, typing.Type]) -> bool:
    return not isinstance(typ, _generic_alias_types) and not isinstance(typ, typing._SpecialForm)  # type: ignore


if hasattr(typing, "Literal"):

    def is_literal_type(typ: GenericAlias) -> bool:
        return get_origin(typ) is typing.Literal

else:

    def is_literal_type(typ: GenericAlias) -> bool:
        return False
