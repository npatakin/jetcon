import inspect
from typing import Any, Callable
from dataclasses import is_dataclass, fields

from jetcon.node import JetNode
from jetcon.keywords import Keywords
from jetcon.build import (
    build_dataclass,
    build_class,
    build_function
)


def cast(
    node: JetNode,
    factory: Callable,
) -> Any:
    if is_dataclass(factory):
        for field in fields(factory):
            _node = node.get(field.name, field.default)

            if isinstance(_node, JetNode) and is_dataclass(field.type):
                node[field.name] = cast(_node, field.type)

        try:
            node.pop(Keywords.data.value, None)
            return build_dataclass(factory, node, partial=False)
        except Exception as e:
            raise ValueError(
                f"Broadcasting to dataclass {factory.__name__} failed. {e}"
            )
    if inspect.isclass(factory):
        try:
            node.pop(Keywords.cls.value, None)
            return build_class(factory, node, partial=False)
        except Exception as e:
            raise ValueError(
                f"Broadcasting to class {factory.__name__} failed. {e}"
            )
    if inspect.isfunction(factory):
        try:
            node.pop(Keywords.func.value, None)
            return build_function(factory, node, partial=False)
        except Exception as e:
            raise ValueError(
                f"Broadcasting to function {factory.__name__} failed. {e}"
            )
    raise ValueError(f"Factory is not recognized {factory.__name__}.")


def to_dict(
    node: JetNode,
    recursive: bool = True
) -> dict:
    if recursive:
        # recursively cast inner nodes to dict
        for key, value in node.items():
            if isinstance(value, JetNode):
                node[key] = to_dict(value)

            if isinstance(value, list):
                _value = []
                for _v in value:
                    if isinstance(_v, JetNode):
                        _v = to_dict(_v)
                    _value.append(_v)
                node[key] = _value

    return cast(node, dict)
