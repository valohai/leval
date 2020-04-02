import ast
from functools import partial

from .excs import TooComplex, InvalidNode, InvalidOperation
from .universe import EvaluationUniverse


class Evaluator(ast.NodeTransformer):
    allowed_constant_classes = (int, float, complex)
    max_depth = 10

    def __init__(self, universe: EvaluationUniverse):
        self.depth = 0
        self.universe = universe

    def evaluate_expression(self, expression):
        return self.visit(ast.parse(expression, "<expression>", "eval"))

    def visit(self, node):
        if self.depth >= self.max_depth:
            raise TooComplex(f"Expression is too complex")
        node_name = node.__class__.__name__
        method = f"visit_{node_name}"
        visitor = getattr(self, method, None)
        if not visitor:
            raise InvalidNode(f"Operation {node_name} is not allowed")
        try:
            self.depth += 1
            return visitor(node)
        finally:
            self.depth -= 1

    def visit_Compare(self, node):
        if len(node.ops) != 1:
            raise InvalidOperation("Only simple comparisons are supported")
        left = self.visit(node.left)
        right = self.visit(node.comparators[0])
        op = node.ops[0]
        return self.universe.evaluate_binary_op(op, left, right)

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise InvalidOperation(f"Invalid call to func {node.func}")
        if node.keywords:
            raise InvalidOperation("Kwarg calls are not allowed")
        arg_getters = [partial(self.visit, arg) for arg in node.args]
        return self.universe.evaluate_function(node.func.id, arg_getters)

    def visit_Num(self, node):
        return node.n

    def visit_Str(self, node):
        return node.s

    def visit_Constant(self, node):  # Python 3.8+
        if isinstance(node.value, self.allowed_constant_classes):
            return node.value
        raise InvalidOperation(f"Invalid constant {node}")

    def visit_Name(self, node):
        if not isinstance(node.ctx, ast.Load):
            raise InvalidOperation(f"Invalid name operation")
        return self.universe.get_value(node.id)

    def visit_Attribute(self, node):
        """
        Turns Attributes into tuples of identifiers, e.g. `foo.bar.quux` -> `('foo', 'bar', 'quux')`
        """
        attr_bits = []

        def walk_attr(kid):
            if isinstance(kid, ast.Attribute):
                attr_bits.append(kid.attr)
                walk_attr(kid.value)
            elif isinstance(kid, ast.Name):
                attr_bits.append(kid.id)
            else:
                raise InvalidOperation(f"Unsupported attribute structure in {node}")

        walk_attr(node)
        name = tuple(attr_bits[::-1])
        return self.universe.get_value(name)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return self.universe.evaluate_binary_op(node.op, left, right)

    def visit_BoolOp(self, node):
        value_getters = [partial(self.visit, v_node) for v_node in node.values]
        return self.universe.evaluate_bool_op(node.op, value_getters)

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.Not):
            return not operand
        raise InvalidOperation(f"invalid unary op: {node.op}")

    def visit_Set(self, node):
        return set(self.visit(n) for n in node.elts)

    def visit_Tuple(self, node):
        return tuple(self.visit(n) for n in node.elts)

    def visit_Expression(self, node):
        return self.visit(node.body)
