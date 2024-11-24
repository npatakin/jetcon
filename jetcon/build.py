import inspect
import importlib
from typing import get_type_hints
from dataclasses import fields, is_dataclass, MISSING
from typing import Callable, Any
from functools import partial as partial_fn
from functools import partialmethod as partial_md
from typeguard import check_type, TypeCheckError    # type: ignore

from jetcon.keywords import Keywords
from jetcon.node import JetNode

# This registry maps syntax keywords to builder functions.
# Each builder function takes a string specification from a node's key and
# additional keyword arguments, returning a constructed class instance.
BUILDERS = dict()


def register_builder(
    keyword: str,
    builder: Callable[[Callable, dict[str, Any], bool], Any]
) -> None:
    """
    Registers a builder function for a given keyword.

    Parameters
    ----------
    keyword : str
        The keyword to associate with the builder function.
    builder : Callable[[str, dict[str, Any]], Any]
        The builder function to register.

    Returns
    -------
    None
    """
    BUILDERS[keyword] = builder


def _import_from_string(
    spec: str,
    sub: str | None = None
) -> Callable:
    try:
        module_, class_ = spec.rsplit(".", 1)
        module_ = importlib.import_module(module_)
        cls = getattr(module_, class_)

        if sub is not None:
            return getattr(cls, sub)
        return cls

    except Exception as e:
        raise ImportError(f"Can't find class: {spec}; {e}")


def build_function(
    factory: Callable,
    kwargs: dict[str, Any],
    partial: bool,
) -> Callable | Any:
    # look for required arguments.
    required, total = set(), set()
    for arg in inspect.signature(factory).parameters.values():
        total.add(arg.name)
        # arg without default values is supposed to be required
        if arg.default is not inspect._empty:
            continue
        required.add(arg.name)

    if len(required - kwargs.keys()) > 0:
        if not partial:
            raise ValueError(f"Can't call function {factory} with partially initialized"
                             " arguments. Partial mode is disabled. "
                             f"Missing args: {required - kwargs.keys()}")

        # enabled => check unexpected args
        if len(kwargs.keys() - total) > 0:
            raise ValueError(f"Can't call function {factory} with partially initialized "
                             f"arguments. Unexpected arguments: {kwargs.keys() - total}")
        _factory = partial_fn(factory, **kwargs)
        _factory.__doc__ = factory.__doc__
        return _factory

    # this try catch block checks unexpected arguments errors mostly.
    try:
        return factory(**kwargs)
    except Exception as e:
        raise ValueError(f"Can't call function {factory}. {e}")


def build_class(
    factory: Callable,
    kwargs: dict[str, Any],
    partial: bool,
) -> Callable | Any:
    # look for required and total arguments
    required, total = set(), set()
    for arg in inspect.signature(factory.__init__).parameters.values():
        # skip self argument that is mandatory for __init__
        if arg.name == "self":
            continue
        total.add(arg.name)

        if arg.default is not inspect._empty:
            continue
        required.add(arg.name)

    if len(required - kwargs.keys()) > 0:
        # not all required args are passed, so check partial mode
        if not partial:
            # disabled => raise exepction
            raise ValueError(f"Can't create class {factory} with partially initialized"
                             " arguments. Partial mode is disabled. "
                             f"Missing args: {required - kwargs.keys()}")

        # enabled => check unexpected args
        if len(kwargs.keys() - total) > 0:
            raise ValueError(f"Can't create class {factory} with partially initialized "
                             f"arguments. Unexpected arguments: {kwargs.keys() - total}")
        # only expected args are presented, just call partial method
        factory.__init__ = partial_md(factory.__init__, **kwargs)
        # return partially initializer factory
        return factory

    # this try catch block checks unexpected arguments errors mostly.
    try:
        return factory(**kwargs)
    except Exception as e:
        raise ValueError(f"Can't create class {factory}. {e}")


def build_dataclass(
    factory: Callable,
    kwargs: dict[str, Any],
    partial: bool,
) -> Callable | Any:
    if not is_dataclass(factory):
        raise ValueError(f"Class {factory} is not dataclass")

    for field in fields(factory):
        # fetch arg from node
        arg = kwargs.get(field.name, field.default)

        if arg is MISSING and partial:
            continue

        # uses typing.get_type_hints to correctly parse type hints
        # field.type can be str when `from __future__ import annotations`
        # is used in module
        ftype = get_type_hints(factory)[field.name]
        try:
            # check type using typeguard
            check_type(arg, ftype)
        except TypeCheckError:
            raise ValueError(
                f"Dataclass {factory.__name__} typecheck error. "
                f"Arg: {field.name} has type {type(arg)}, but {ftype} is expected."
            )

    return build_class(factory, kwargs, partial)


register_builder(Keywords.func.value, build_function)
register_builder(Keywords.cls.value, build_class)
register_builder(Keywords.data.value, build_dataclass)


def _resolve_builder(
    node: JetNode
) -> str | None:
    # find specified keywords
    specified = node.keys() & BUILDERS.keys()

    # only one builder is allowed for a single node
    if len(specified) > 1:
        raise RuntimeError("Multiple builders have been detected. "
                           f"Incorrect node: {node}.")
    # if set is empty, then this is a simple node
    # simple nodes are not supposed to be rebuild via callable
    if len(specified) == 0:
        return None

    # remaining key set contains single element
    return specified.pop()


def _build_node(
    dct: dict,
    partial: bool
) -> dict:
    return JetNode({k: _build(v, partial) for k, v in dct.items()})


def _build_list(
    lst: list,
    partial: bool
) -> list:
    return [_build(v, partial) for v in lst]


def _build(
    node: Any,
    partial: bool = True
) -> Any:
    if isinstance(node, list):
        return _build_list(node, partial)

    if isinstance(node, JetNode):
        return build(node)

    return node


def build(
    node: JetNode,
    recursive: bool = True,
    partial: bool = True
) -> JetNode:
    if recursive:
        node = _build_node(node, partial)

    builder = _resolve_builder(node)

    if builder is not None:
        factory = _import_from_string(node.pop(builder))
        return BUILDERS[builder](factory, kwargs=node, partial=partial)

    return node

# def build(
#     node: JetNode,
#     recursive: bool = True,
#     partial: bool = True,
# ) -> JetNode:
#     if recursive:
#         node = _build_node(node)
#         # recursively build inner nodes first
#         for key, value in node.items():
#             if isinstance(value, JetNode):
#                 node[key] = build(value)

#             if isinstance(value, list):
#                 _value = []
#                 for _v in value:
#                     if isinstance(_v, JetNode):
#                         _v = build(_v)
#                     _value.append(_v)
#                 node[key] = _value

#     kw = _resolve_builder(node)

#     if kw is not None:
#         factory = _import_from_string(node.pop(kw))
#         return BUILDERS[kw](factory, kwargs=node, partial=partial)

#     return node
