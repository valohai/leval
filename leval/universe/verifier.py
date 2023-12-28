from leval.excs import InvalidOperation
from leval.universe.default import EvaluationUniverse


class VerifierUniverse(EvaluationUniverse):
    """
    An universe that does no computation but walks as much of the tree as possible.
    """

    def get_value(self, name):  # noqa: D102
        return True

    def evaluate_function(self, name: str, arg_getters):  # noqa: D102
        for getter in arg_getters:
            getter()
        return True

    def evaluate_binary_op(self, op, left, right):  # noqa: D102
        bin_op = self.ops.get(type(op))
        if not bin_op:
            raise InvalidOperation(  # pragma: no cover
                f"Binary operator {op} is not allowed",
                node=op,
            )
        return True

    def evaluate_bool_op(self, op, value_getters):  # noqa: D102
        for getter in value_getters:
            getter()
        return True
