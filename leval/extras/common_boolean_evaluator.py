import keyword
import tokenize
from typing import Any, Dict, List, Optional, Tuple, Union

from leval.excs import NoSuchFunction
from leval.rewriter_evaluator import RewriterEvaluator
from leval.rewriter_utils import (
    convert_dash_identifiers,
    get_parts_from_dashed_identifier_tokens,
    make_glued_name_token,
)
from leval.universe.verifier import VerifierUniverse
from leval.universe.weakly_typed import WeaklyTypedSimpleUniverse

DEFAULT_FUNCTIONS = {
    "abs": abs,
    "min": min,
    "max": max,
}

ValuesDict = Dict[Union[Tuple[str, ...], str], Any]

KEYWORD_PREFIX = "K\u203f"
DASH_SEP = "\u203f\u203f"


def _rewrite_keyword(kw: str) -> str:
    if keyword.iskeyword(kw):
        return f"{KEYWORD_PREFIX}{kw}"
    return kw


def _convert_dash_tokens(tokens: List[tokenize.TokenInfo]):
    if not tokens:
        return []
    glued_name = "".join(
        get_parts_from_dashed_identifier_tokens(tokens, separator=DASH_SEP),
    )
    return [make_glued_name_token(tokens, glued_name)]


def _prepare_name(name: str) -> str:
    return DASH_SEP.join(_rewrite_keyword(p) for p in name.split("-"))


class _CommonEvaluator(RewriterEvaluator):
    def rewrite_keyword(self, kw: str) -> str:
        return _rewrite_keyword(kw)

    def process_tokens(self, tokens):
        return convert_dash_identifiers(tokens, _convert_dash_tokens)


class _CommonUniverse(WeaklyTypedSimpleUniverse):
    def evaluate_function(self, name, arg_getters):
        func = self.functions.get(name)
        if not func:
            raise NoSuchFunction(f"No function {name}")
        args = [getter() for getter in arg_getters]
        for arg in args:
            # This is using `type(...)` on purpose; we don't want to allow subclasses.
            if type(arg) not in (int, float, str, bool):
                raise TypeError(f"Invalid argument for {name}: {type(arg)}")
        return func(*args)


def _prepare_values(values: ValuesDict) -> ValuesDict:
    """
    Prepare a values dictionary by rewriting names like the evaluation would.
    """
    prepared_values = {}
    for key, value in values.items():
        if isinstance(key, tuple):
            key = tuple(_prepare_name(p) for p in key)
        elif isinstance(key, str):
            key = _prepare_name(key)
        else:
            raise TypeError(f"Invalid key type: {type(key)}")
        prepared_values[key] = value
    return prepared_values


class CommonBooleanEvaluator:
    functions: dict = DEFAULT_FUNCTIONS
    max_depth: int = 8
    max_time: float = 0.2
    verifier_universe_class = VerifierUniverse
    universe_class = _CommonUniverse
    evaluator_class = _CommonEvaluator

    def evaluate(self, expr: Optional[str], values: ValuesDict) -> Optional[bool]:
        """
        Evaluate the given expression against the given values.

        The values dictionary's keys will be prepared to the expected internal format.
        """
        if not expr:
            return None
        universe = self.universe_class(
            functions=self.functions,
            values=_prepare_values(values),
        )
        evl = self.evaluator_class(
            universe,
            max_depth=self.max_depth,
            max_time=self.max_time,
        )
        return bool(evl.evaluate_expression(expr))

    def verify(self, expression: str) -> bool:
        """
        Verify that the given expression is technically valid.
        """
        evl = self.evaluator_class(
            self.verifier_universe_class(),
            max_depth=self.max_depth,
        )
        return evl.evaluate_expression(expression)
