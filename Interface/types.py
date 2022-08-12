"""Interface/types.py - define variáveis de tipagem utilizada pelo pacote Interface do forNMA."""
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
