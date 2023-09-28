"""
Tests and examples for the expression rewriting behavior.
"""
import pytest

from leval.rewriter_evaluator import RewriterEvaluator
from leval.universe.simple import SimpleUniverse

REWRITE_TEST_MAPPING = {
    "zoop": 1,
    "break": 5,
    "continue": 8,
    "def": 3,
    ("def", "break"): 128,
}


class PrefixRewriteEvaluator(RewriterEvaluator):
    def rewrite_keyword(self, kw: str) -> str:
        return f"kw_{kw}"


class FunctionRewriteEvaluator(RewriterEvaluator):
    def rewrite_keyword(self, kw: str) -> str:
        return f"get_value({kw!r})"


def test_dunder_rewriter():
    dunder_mapping = {f"kw_{k}": v for (k, v) in REWRITE_TEST_MAPPING.items()}
    evu = SimpleUniverse(values=dunder_mapping, functions={})
    evaluator = PrefixRewriteEvaluator(evu)
    assert evaluator.evaluate_expression("continue * break - def + break") == 42


class RewriteUndoingUniverse(SimpleUniverse):
    def undo_prefix(self, name: str) -> str:
        if name.startswith("kw_"):
            return name[3:]
        return name

    def get_value(self, name):
        # Remove trailing underscores from name segments
        # to undo what DunderRewriteEvaluator does:
        if isinstance(name, tuple):
            name = tuple(self.undo_prefix(bit) for bit in name)
        else:
            name = self.undo_prefix(name)
        return super().get_value(name)


def test_dunder_rewriter_with_rewriting_universe():
    evu = RewriteUndoingUniverse(values=REWRITE_TEST_MAPPING, functions={})
    evaluator = PrefixRewriteEvaluator(evu)
    # The rewriter turns this into `kw_def.kw_break * kw_continue`,
    # and the undoing universe reverts that change.
    assert evaluator.evaluate_expression("def.break * continue + zoop") == 1025


def test_call_rewriter():
    evu = SimpleUniverse(
        values={},
        functions={"get_value": lambda kw: REWRITE_TEST_MAPPING[kw]},
    )
    evaluator = FunctionRewriteEvaluator(evu)
    assert evaluator.evaluate_expression("continue * break + break - def") == 42


def test_rewriter_isnt_silly():
    # Ensure the rewriter actually tokenizes the expression to
    # replace keywords instead of blindly rewriting strings.
    evu = SimpleUniverse(values={}, functions={})
    evaluator = FunctionRewriteEvaluator(evu)
    assert evaluator.evaluate_expression('"continue"') == "continue"


def test_rewriter_expressions():
    evu = SimpleUniverse(values={"quit": False, "kw_continue": True}, functions={})
    evaluator = PrefixRewriteEvaluator(evu)
    assert evaluator.evaluate_expression("quit or continue")


@pytest.mark.parametrize(
    "case",
    [
        '"""',
        "try:\nthere is no try",
    ],
)
def test_rewrite_parse_error_is_syntax_error(case):
    with pytest.raises(SyntaxError):
        evu = SimpleUniverse(values={}, functions={})
        PrefixRewriteEvaluator(evu).evaluate_expression(case)
