import re
from typing import Any
from functools import reduce

from jetcon.node import JetNode

# Define match pattern for looking for values in strings
# This patterns corresponds to "${this.value}" string
# Numbers cannot be the first character similarly as in Python.
LERP_PATTERN = re.compile("\$\{{1}[a-z]+[a-z0-9._]+\}{1}", re.IGNORECASE)

# This pattern extracts keys from substring found by LERP_PATTERN
# Assume we have "${this.value}", then this pattern matches "this.value"
EXTRACT_PATTERN = re.compile("[a-z0-9_]+", re.IGNORECASE)


def find_matches(
    value: str
) -> list[str]:
    return re.findall(LERP_PATTERN, value)


def find_value(
    tree: JetNode,
    value: str,
) -> Any:
    return reduce(dict.get, re.findall(EXTRACT_PATTERN, value), tree)


def _interpolate_string(
    value: str,
    tree: JetNode
) -> Any:
    matches = find_matches(value)

    values = [find_value(tree, m) for m in matches]
    # replace matches to string casted values
    for _m, _v in zip(matches, values):
        if not value.replace(_m, ""):
            # this case correspond to a single match
            # so just replace the whole value
            value = _v
        else:
            # this is the multiple matche case
            # replace every match with string cased value
            value = value.replace(_m, str(_v))

    return value


def _interpolate_node(
    node: JetNode,
    tree: JetNode,
) -> JetNode:
    return JetNode({k: _interpolate(v, tree) for k, v in node.items()})


def _interpolate_list(
    lst: list,
    tree: JetNode,
) -> list:
    return [_interpolate(v, tree) for v in lst]


def _interpolate(
    node: Any,
    tree: JetNode,
) -> Any:
    if isinstance(node, list):
        return _interpolate_list(node, tree)

    if isinstance(node, JetNode):
        return _interpolate_node(node, tree)

    if isinstance(node, str):
        return _interpolate_string(node, tree)

    return node


def interpolate(
    tree: JetNode
) -> JetNode:
    return _interpolate_node(tree, tree)
