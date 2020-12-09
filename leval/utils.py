import ast
import functools
from numbers import Number
from typing import Tuple

from leval.excs import InvalidOperands, InvalidOperation


def numbers_only_binop(name, func):
    """
    Decorate `func` to ensure its two arguments are numbers.
    """

    @functools.wraps(func)
    def binop(a, b):
        if not (isinstance(a, Number) and isinstance(b, Number)):
            raise InvalidOperands(
                f'operator "{name}" can only be used with numbers, not {a!r} and {b!r}'
            )
        return func(a, b)

    return binop


def expand_name(node: ast.Attribute) -> Tuple[str]:
    """
    Turn an Attribute node into a tuple of identifier strings.

    e.g. `foo.bar.quux` -> `('foo', 'bar', 'quux')`
    """
    attr_bits = []

    def walk_attr(kid):
        if isinstance(kid, ast.Attribute):
            attr_bits.append(kid.attr)
            walk_attr(kid.value)
        elif isinstance(kid, ast.Name):
            attr_bits.append(kid.id)
        else:
            raise InvalidOperation(  # pragma: no cover
                f"Unsupported attribute structure in {node}", node=node
            )

    walk_attr(node)
    return tuple(str(bit) for bit in attr_bits[::-1])
