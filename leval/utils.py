import ast
from typing import Tuple

from .excs import InvalidOperation


def expand_name(node: ast.Attribute) -> Tuple[str, ...]:
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
