import ast
import io
import tokenize
from typing import Iterable, Tuple

from leval.excs import InvalidAttribute


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
        elif isinstance(kid, ast.Constant):
            raise InvalidAttribute(
                f"Accessing attributes of constants ({kid}) is not allowed",
                node=node,
            )
        else:
            raise InvalidAttribute(  # pragma: no cover
                f"Unsupported attribute structure in {node}",
                node=node,
            )

    walk_attr(node)
    return tuple(str(bit) for bit in attr_bits[::-1])


def tokenize_expression(expression: str) -> Iterable[tokenize.TokenInfo]:
    """
    Tokenize the given expression and return the tokens.

    Will likely misbehave if the expression is e.g. multi-line.
    """
    return tokenize.generate_tokens(io.StringIO(expression).readline)
