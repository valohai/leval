import ast
from functools import partial

from .excs import TooComplex, InvalidNode, InvalidOperation, InvalidConstant
from .universe.base import BaseEvaluationUniverse
from .utils import expand_name


class Evaluator(ast.NodeTransformer):
    allowed_constant_classes = (str, int, float, complex)
    max_depth = 10

    def __init__(self, universe: BaseEvaluationUniverse):
        """
        Initialize an evaluator with access to the given evaluation universe.
        """
        self.depth = 0
        self.universe = universe

    def evaluate_expression(self, expression: str):
        """
        Evaluate the given expression and return the ultimate result.
        """
        return self.visit(ast.parse(expression, "<expression>", "eval"))

    def visit(self, node):  # noqa: D102
        if self.depth >= self.max_depth:
            raise TooComplex("Expression is too complex", node=node)
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

    def visit_Compare(self, node):  # noqa: D102
        if len(node.ops) != 1:
            raise InvalidOperation("Only simple comparisons are supported", node=node)
        left = self.visit(node.left)
        right = self.visit(node.comparators[0])
        op = node.ops[0]
        return self.universe.evaluate_binary_op(op, left, right)

    def visit_Call(self, node):  # noqa: D102
        if not isinstance(node.func, ast.Name):
            raise InvalidOperation(f"Invalid call to func {node.func}", node=node)
        if node.keywords:
            raise InvalidOperation("Kwarg calls are not allowed", node=node)
        arg_getters = [partial(self.visit, arg) for arg in node.args]
        return self.universe.evaluate_function(node.func.id, arg_getters)

    def _visit_constantlike(self, node):
        if isinstance(node, ast.Num):
            value = node.n
        elif isinstance(node, ast.Str):
            value = node.s
        else:
            value = node.value

        if isinstance(value, self.allowed_constant_classes):
            return value

        raise InvalidConstant(f"Invalid constant {node} ({type(value)})", node=node)

    visit_Constant = _visit_constantlike  # Python 3.8 and newer
    visit_Str = _visit_constantlike  # Python 3.7 and lower
    visit_Num = _visit_constantlike  # Python 3.7 and lower

    def visit_Name(self, node):  # noqa: D102
        if not isinstance(node.ctx, ast.Load):
            raise InvalidOperation("Invalid name operation", node=node)
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
            f"invalid unary op: {node.op}", node=node
        )

    def visit_Set(self, node):  # noqa: D102
        return set(self.visit(n) for n in node.elts)

    def visit_Tuple(self, node):  # noqa: D102
        return tuple(self.visit(n) for n in node.elts)

    def visit_Expression(self, node):  # noqa: D102
        return self.visit(node.body)
