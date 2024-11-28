import inspect
import importlib
from typing import get_type_hints
from dataclasses import fields, is_dataclass, MISSING
from typing import Callable, Any
from functools import reduce
from functools import partial as partial_fn
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
) -> Callable:

    if not spec:
        raise ValueError("Empty import string.")

    specs = spec.split(".")
    module_, var = spec.rsplit(".", 1)
    vars_ = [var]

    imported_module = None
    for _ in specs:
        try:
            imported_module = importlib.import_module(module_)
            break
        except ImportError:
            module_, var = module_.rsplit(".", 1)
            vars_.insert(0, var)

    if imported_module is None:
        raise ImportError("Unknown string spec.")

    return reduce(getattr, vars_, imported_module)


def build_callable(
    factory: Callable,
    kwargs: dict[str, Any],
    partial: bool,
) -> Callable | Any:
    # look for required arguments.
    required, total = set(), set()
    kwargable = False
    # signature of class factories does not contain self
    for arg in inspect.signature(factory).parameters.values():
        # args are ignored
        if arg.name == "args":
            continue
        # kwargable dow not check unexpected args
        if arg.name == "kwargs":
            kwargable = True
            continue
        total.add(arg.name)
        # arg without default values is supposed to be required
        if arg.default is not inspect._empty:
            continue
        required.add(arg.name)

    if len(required - kwargs.keys()) > 0:
        if not partial:
            raise ValueError(f"Can't build callable {factory} with partially initialized"
                             " arguments. Partial mode is disabled. "
                             f"Missing args: {required - kwargs.keys()}")

        # enabled => check unexpected args
        if not kwargable and len(kwargs.keys() - total) > 0:
            raise ValueError(f"Can't build callable {factory} with partially initialized "
                             f"arguments. Unexpected arguments: {kwargs.keys() - total}")
        _factory = partial_fn(factory, **kwargs)
        _factory.__doc__ = factory.__doc__
        return _factory

    # this try catch block checks unexpected arguments errors mostly.
    try:
        return factory(**kwargs)
    except Exception as e:
        raise ValueError(f"Can't build callable {factory}. {e}")


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

    return build_callable(factory, kwargs, partial)


register_builder(Keywords.func.value, build_callable)
register_builder(Keywords.cls.value, build_callable)
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
        return build(node, partial=partial)

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
