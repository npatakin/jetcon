import inspect
import importlib
from typing import Callable, Any
from functools import partial, partialmethod

from jetcon.keywords import Keywords
from jetcon.node import JetNode

# This registry maps syntax keywords to builder functions.
# Each builder function takes a string specification from a node's key and
# additional keyword arguments, returning a constructed class instance.
BUILDERS = dict()


def register_builder(
    keyword: str,
    builder: Callable[[str, dict[str, Any]], Any]
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


def _build_function(
    spec: str,
    kwargs: dict[str, Any]
) -> Callable | Any:
    # import callable from string spec
    factory = _import_from_string(spec)

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


def _build_class(
    spec: str,
    kwargs: dict[str, Any]
) -> Callable | Any:
    # import callable from string spec
    factory = _import_from_string(spec)

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


register_builder(Keywords.func.value, _build_function)
register_builder(Keywords.cls.value, _build_class)


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
        return BUILDERS[kw](spec=node.pop(kw), kwargs=node)
    return node
