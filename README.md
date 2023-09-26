# Leval

![License](https://img.shields.io/github/license/valohai/leval)
[![Coverage](https://img.shields.io/codecov/c/github/valohai/leval)](https://app.codecov.io/gh/valohai/leval)
[![CI](https://github.com/valohai/leval/actions/workflows/ci.yml/badge.svg)](https://github.com/valohai/leval/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/leval)](https://pypi.org/project/leval)

> A limited expression evaluator

A little more suited for dynamic usage than `ast.literal_eval()`
while remaining as safe as the functions you pass in.

Under the hood, it uses the `ast` module to parse the expression,
then walks the AST in Python to evaluate the result. You can
also specify a depth limit for the complexity of the expression,
as well as a time limit for the evaluation.

## Example usage

### Simple API

For many use cases, the `simple_eval()` function is sufficient.
You can specify a depth limit and a time limit, and optional mappings
of variables and functions.

The `values` mapping can also be keyed by a tuple of strings, which
is what attribute accesses are folded to.

Operations are generally limited to numbers only in the simple API.

```python
from leval.simple import simple_eval

assert simple_eval('1 + 2') == 3
assert simple_eval('x < -80 or x > 125 or x == 85', values={'x': 85})
assert simple_eval('abs(x) > 80', values={'x': -85}, functions={'abs': abs})
assert simple_eval('x.y.z + 8', values={('x', 'y', 'z'): 34}) == 42
```

### Advanced API

Under the hood, `simple_eval` simply

1. initializes an evaluation universe, which defines the functions, variables
   and operations available
2. creates an Evaluator to evaluate the expression with the given universe

Both of these classes are designed to be easily subclassable. There are examples
in the `test_leval.py` file.
