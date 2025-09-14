"""
maya.cmds stub file generated for Maya {VERSION} using:
https://github.com/nils-soderman/maya-cmds-stub-generator
"""

from __future__ import annotations
from typing import (
    TypeVar,
    TypeAlias,
    Union,
    Sequence,
    Callable,
    Literal,
    Any,
    overload
)

try:
    from warnings import deprecated  # type: ignore
except ImportError:
    def deprecated(msg: str):
        def decorator(func: Callable) -> Callable:
            return func
        return decorator

T = TypeVar("T")
multiuse: TypeAlias = Union[Sequence[T], T]
