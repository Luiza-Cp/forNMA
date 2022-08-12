"""Interface/types.py - defines custom types used by forNMA's interface."""
from __future__ import annotations

from typing import TypedDict, Literal, Any


class ForNMAEmitDict(TypedDict):
    type: Literal['progress', 'log', 'warning']
    message: str
    data: list[Any]


class ForNMAReturnDict(TypedDict):
    status: Literal['ok', 'error']
    message: str
    data: list[Any]
