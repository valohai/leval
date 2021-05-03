from ..excs import InvalidOperation
from .default import EvaluationUniverse


class VerifierUniverse(EvaluationUniverse):
    """
    An universe that attempts to have the evaluator walk as much of the tree as possible, but does no computation.
    """

    def get_value(self, name):
        return True

    def evaluate_function(self, name: str, arg_getters):
        for getter in arg_getters:
            getter()
        return True

    def evaluate_binary_op(self, op, left, right):
        bin_op = self.ops.get(type(op))
        if not bin_op:
            raise InvalidOperation(  # pragma: no cover
                "Binary operator {} is not allowed".format(op), node=op
            )
        return True

    def evaluate_bool_op(self, op, value_getters):
        for getter in value_getters:
            getter()
        return True
