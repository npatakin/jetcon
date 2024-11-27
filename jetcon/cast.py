import inspect
from typing import Any, Callable
from dataclasses import is_dataclass, fields

from jetcon.node import JetNode
from jetcon.keywords import Keywords
from jetcon.build import (
    build_dataclass,
    build_callable,
)


def cast(
    node: JetNode,
    factory: Callable,
    pop_keywords: bool = True
) -> Any:

    if pop_keywords:
        for word in Keywords:
            node.pop(word.value, None)

    if inspect.isclass(factory) and is_dataclass(factory):
        for field in fields(factory):
            _node = node.get(field.name, field.default)

            if isinstance(_node, JetNode) and is_dataclass(field.type):
                node[field.name] = cast(_node, field.type)

        try:
            return build_dataclass(factory, node, partial=False)
        except Exception as e:
            raise ValueError(
                f"Broadcasting to dataclass {factory.__name__} failed. {e}"
            )
    if inspect.isclass(factory) or inspect.isfunction(factory):
        try:
            return build_callable(factory, node, partial=False)
        except Exception as e:
            raise ValueError(
                f"Broadcasting to callable {factory.__name__} failed. {e}"
            )
    raise ValueError(f"Factory is not recognized {factory.__name__}.")


def _cast_node_to_dict(
    dct: dict
) -> dict:
    return {k: _to_dict(v) for k, v in dct.items()}


def _cast_list_to_dict(
    lst: list
) -> list:
    return [_to_dict(v) for v in lst]


def _to_dict(
    node: Any
) -> Any:
    if isinstance(node, list):
        return _cast_list_to_dict(node)

    if isinstance(node, JetNode):
        return to_dict(node)

    return node


def to_dict(
    node: JetNode,
    recursive: bool = True
) -> dict:
    if recursive:
        return _cast_node_to_dict(node)

    return cast(node, factory=dict, pop_keywords=False)
