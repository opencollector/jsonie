from __future__ import annotations

import dataclasses
import typing


@dataclasses.dataclass
class Baz:
    x: int
    y: str = "default"


@dataclasses.dataclass
class Qux:
    items: typing.Sequence[Baz]
    label: str


@dataclasses.dataclass
class SelfRef:
    value: int
    child: SelfRef | None = None
