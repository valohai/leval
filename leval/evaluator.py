import ast
import time
from functools import partial
from typing import Any, Iterable, Optional

from leval.excs import (
    InvalidConstant,
    InvalidNode,
    InvalidOperation,
    NoSuchValue,
    Timeout,
    TooComplex,
)
from leval.universe.base import BaseEvaluationUniverse
from leval.utils import expand_name

try:
    from types import NoneType
except ImportError:
    NoneType = type(None)  # type: ignore


DEFAULT_ALLOWED_CONTAINER_TYPES = frozenset((tuple, set))
DEFAULT_ALLOWED_CONSTANT_TYPES = frozenset(
    (
        str,
        int,  # NB: this implicitly includes bool
        float,
        NoneType,
    ),
)


def _default_if_none(value, default):
    return value if value is not None else default


def _get_constant_node_value(node):
    if hasattr(node, "value"):  # Python 3.8 and above
        return node.value
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Str):
        return node.s
    raise InvalidConstant(f"Invalid constant {node}", node=node)  # pragma: no cover


class Evaluator(ast.NodeTransformer):
    default_allowed_constant_types: Iterable[type] = DEFAULT_ALLOWED_CONSTANT_TYPES
    default_allowed_container_types: Iterable[type] = DEFAULT_ALLOWED_CONTAINER_TYPES
    default_max_depth = 10

    def __init__(
        self,
        universe: BaseEvaluationUniverse,
        *,
        max_depth: Optional[int] = None,
        max_time: Optional[float] = None,
        allowed_constant_types: Optional[Iterable[type]] = None,
        allowed_container_types: Optional[Iterable[type]] = None,
        loose_is_operator: bool = True,
    ):
        """
        Initialize an evaluator with access to the given evaluation universe.
        """
        self.depth = None  # type: Optional[int]
        self.start_time = None  # type: Optional[float]
        self.universe = universe
        self.max_depth = _default_if_none(max_depth, self.default_max_depth)
        self.max_time = float(max_time or 0)
        self.loose_is_operator = bool(loose_is_operator)
        self.allowed_constant_types = frozenset(
            _default_if_none(
                allowed_constant_types,
                self.default_allowed_constant_types,
            ),
        )
        self.allowed_container_types = frozenset(
            _default_if_none(
                allowed_container_types,
                self.default_allowed_container_types,
            ),
        )

    def evaluate_expression(self, expression: str) -> Any:
        """
        Evaluate the given expression and return the ultimate result.
        """
        self.depth = 0
        self.start_time = time.time()
        return self.visit(self.parse(expression))

    def parse(self, expression: str) -> ast.AST:
        """
        Parse the given expression and return the AST.
        """
        return ast.parse(expression, "<expression>", "eval")

    def visit(self, node):  # noqa: D102
        if self.depth >= self.max_depth:
            raise TooComplex(
                f"Expression is too complex ({self.depth} > {self.max_depth})",
                node=node,
            )
        if self.max_time > 0:
            elapsed_time = time.time() - self.start_time
            if elapsed_time > self.max_time:
                raise Timeout(
                    f"Expression reached time limit {self.max_time}",
                    node=node,
                )
        node_name = node.__class__.__name__
        method = f"visit_{node_name}"
        visitor = getattr(self, method, None)
        if not visitor:
            raise InvalidNode(f"Operation {node_name} is not allowed", node=node)
        try:
            self.depth += 1
            return visitor(node)
        finally:
            self.depth -= 1

    def _visit_or_none(self, value: ast.AST) -> Any:
        try:
            return self.visit(value)
        except NoSuchValue:
            return None

    def visit_Compare(self, node):  # noqa: D102
        if len(node.ops) != 1:
            raise InvalidOperation("Only simple comparisons are supported", node=node)
        op = node.ops[0]
        if self.loose_is_operator and isinstance(op, (ast.Is, ast.IsNot)):
            left = self._visit_or_none(node.left)
            right = self._visit_or_none(node.comparators[0])
        else:
            left = self.visit(node.left)
            right = self.visit(node.comparators[0])
        return self.universe.evaluate_binary_op(op, left, right)

    def visit_Call(self, node):  # noqa: D102
        if not isinstance(node.func, ast.Name):
            raise InvalidOperation(f"Invalid call to func {node.func}", node=node)
        if node.keywords:
            raise InvalidOperation("Kwarg calls are not allowed", node=node)
        arg_getters = [partial(self.visit, arg) for arg in node.args]
        return self.universe.evaluate_function(node.func.id, arg_getters)

    def _visit_constantlike(self, node):
        value = _get_constant_node_value(node)

        if isinstance(value, tuple(self.allowed_constant_types)):
            return value

        raise InvalidConstant(
            f"Invalid constant {node} ({type(value)})",
            node=node,
        )

    visit_Constant = _visit_constantlike  # Python 3.8 and newer
    visit_Str = _visit_constantlike  # Python 3.7 and lower
    visit_Num = _visit_constantlike  # Python 3.7 and lower

    def visit_Name(self, node):  # noqa: D102
        if not isinstance(node.ctx, ast.Load):
            raise InvalidOperation(  # pragma: no cover
                "Invalid name operation",
                node=node,
            )
        return self.universe.get_value(node.id)

    def visit_Attribute(self, node):  # noqa: D102
        name = expand_name(node)  # Convert node into a tuple of identifiers first.
        return self.universe.get_value(name)

    def visit_BinOp(self, node):  # noqa: D102
        left = self.visit(node.left)
        right = self.visit(node.right)
        return self.universe.evaluate_binary_op(node.op, left, right)

    def visit_BoolOp(self, node):  # noqa: D102
        value_getters = [partial(self.visit, v_node) for v_node in node.values]
        return self.universe.evaluate_bool_op(node.op, value_getters)

    def visit_UnaryOp(self, node):  # noqa: D102
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.Not):
            return not operand
        raise InvalidOperation(  # pragma: no cover
            f"invalid unary op: {node.op}",
            node=node,
        )

    def visit_Set(self, node):  # noqa: D102
        if set not in self.allowed_container_types:
            raise InvalidOperation("Set construction not allowed", node=node)
        return {self.visit(n) for n in node.elts}

    def visit_Tuple(self, node):  # noqa: D102
        if tuple not in self.allowed_container_types:
            raise InvalidOperation("Tuple construction not allowed", node=node)
        return tuple(self.visit(n) for n in node.elts)

    def visit_Expression(self, node):  # noqa: D102
        return self.visit(node.body)
