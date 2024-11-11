import inspect
import importlib
from typing import get_type_hints
from dataclasses import fields, is_dataclass
from typing import Callable, Any
from functools import partial, partialmethod
from typeguard import check_type, TypeCheckError    # type: ignore

from jetcon.keywords import Keywords
from jetcon.node import JetNode

# This registry maps syntax keywords to builder functions.
# Each builder function takes a string specification from a node's key and
# additional keyword arguments, returning a constructed class instance.
BUILDERS = dict()


def register_builder(
    keyword: str,
    builder: Callable[[Callable, dict[str, Any]], Any]
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
    kwargs: dict[str, Any]
) -> Callable | Any:
    # look for required arguments.
    required = set()
    for arg in inspect.signature(factory).parameters.values():
        # arg without default values is supposed to be required
        if arg.default is inspect._empty:
            continue
        required.add(arg.name)

    if len(required - kwargs.keys()) > 0:
        _factory = partial(factory, **kwargs)
        _factory.__doc__ = factory.__doc__
        return _factory

    return factory(**kwargs)


def build_class(
    factory: Callable,
    kwargs: dict[str, Any]
) -> Callable | Any:
    # look for required arguments
    required = set()
    for arg in inspect.signature(factory.__init__).parameters.values():
        # skip self argument that is mandatory for __init__
        if arg.name == "self":
            continue

        if arg.default is inspect._empty:
            continue
        required.add(arg.name)

    if len(required - kwargs.keys()) > 0:
        factory.__init__ = partialmethod(factory.__init__, **kwargs)
        # return partially initializer factory
        return factory

    return factory(**kwargs)


def build_dataclass(
    factory: Callable,
    kwargs: dict[str, Any],
    strict: bool = True
) -> Callable | Any:
    if not is_dataclass(factory):
        raise ValueError(f"Class {factory} is not dataclass")

    _fields = set([f.name for f in fields(factory)])

    if strict:
        # strict mode requires full set of args to be in node
        _nonexisting = kwargs.keys() - _fields
        if len(_nonexisting) > 0:
            raise ValueError(
                f"Fields {_nonexisting} does not exist in dataclass {factory}"
            )

    data = dict()

    for field in fields(factory):
        # uses typing.get_type_hints to correctly parse type hints
        # field.type can be str when `from __future__ import annotations`
        # is used in module
        ftype = get_type_hints(factory)[field.name]
        # fetch arg from node
        arg = kwargs.pop(field.name)
        try:
            # check type using typeguard
            check_type(arg, ftype)
        except TypeCheckError:
            raise ValueError(
                f"JetNode is not broadcastable to dataclass {factory.__name__}. "
                f"Arg: {arg} has type {type(arg)}, but {ftype} is expected."
            )

        data[field.name] = arg

    if len(kwargs) != 0 and strict:
        raise ValueError(f"Strict mode requires JetNode to have exactly the same number "
                         f"of kwargs as the dataclass {factory.__name__}.")

    return factory(**data)


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


def build(
    node: JetNode,
    recursive: bool = True
) -> JetNode:
    if recursive:
        # recursively build inner nodes first
        for key, value in node.items():
            if isinstance(value, JetNode):
                node[key] = build(value)

            if isinstance(value, list):
                _value = []
                for _v in value:
                    if isinstance(_v, JetNode):
                        _v = build(_v)
                    _value.append(_v)
                node[key] = _value

    kw = _resolve_builder(node)

    if kw is not None:
        factory = _import_from_string(node.pop(kw))
        return BUILDERS[kw](factory, kwargs=node)

    node._built = True
    return node
