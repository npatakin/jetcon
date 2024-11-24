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


def _interpolate(
    node: JetNode,
    tree: JetNode,
) -> JetNode:
    # recursively interpolate inner nodes first
    for key, value in node.items():
        if isinstance(value, JetNode):
            node[key] = _interpolate(value, tree)

        if isinstance(value, list):
            _value = []
            for _v in value:
                if isinstance(_v, JetNode):
                    _v = _interpolate(_v, tree)

                if isinstance(_v, str):
                    _v = _interpolate_string(_v, tree)

                _value.append(_v)
            node[key] = _value

        if isinstance(value, str):
            node[key] = _interpolate_string(value, tree)

    return node


def interpolate(
    tree: JetNode
) -> JetNode:
    return _interpolate(tree, tree)
