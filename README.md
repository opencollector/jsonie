# Jsonie

[![codecov](https://codecov.io/gh/opencollector/jsonie/branch/main/graph/badge.svg)](https://codecov.io/gh/opencollector/jsonie)
[![github actions](https://github.com/opencollector/jsonie/workflows/main/badge.svg)](https://github.com/opencollector/jsonie/actions)

Jsonie handles validation and conversion between JSON documents and typed Python objects that have JSON'ic (JSON-like) structure.  Very few dependencies, no custom schema class required, no bloated implementation.

## Synopisis

```python
import dataclasses
import datetime
import decimal
import typing

from jsonie import from_json


class Foo(typing.TypedDict):
    a: int
    b: str
    c: decimal.Decimal


@dataclasses.dataclass
class Bar:
    dt: datetime.datetime
    d: typing.Optional[datetime.date]
    td: Foo


json_doc = {
    "dt": "1970-01-01T00:00:00Z",
    "d": None,
    "td": {
        "a": 123,
        "b": "str",
        "c": "3.1415926535897932384626433832795028",
    }
}
result = from_json(Bar, json_doc)
# gives Bar(dt=datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc), d=None, td=Foo(a=123, b="str", c=Decimal("3.1415926535897932384626433832795028"))
print(result)
```
