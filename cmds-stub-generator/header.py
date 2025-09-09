"""
maya.cmds stub file generated for Maya {VERSION} using:
https://github.com/nils-soderman/maya-cmds-stub-generator
"""

from __future__ import annotations
from typing import TypeVar, TypeAlias, Union, Sequence, Callable, Literal, Any, overload

try:  # warnings.deprecated was added in Python 3.13
    from warnings import deprecated  # type: ignore
except ImportError:
    def deprecated(msg: str):
        def decorator(func: Callable) -> Callable:
            return func
        return decorator

T = TypeVar("T")
multiuse: TypeAlias = Union[Sequence[T], T]
