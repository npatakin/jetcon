import os
from pathlib import Path
from warnings import warn


class JetContext:
    # default directory that is used for path resolver during import
    # PARENT_FOLDER: Path = Path(os.getcwd())
    # global dependency stack that tracks visited files during import
    visit_stack: list[Path] = list()

    def __init__(self) -> None:
        raise RuntimeError(f"Context class {JetContext.__name__} cannot be instantiated")

    # @staticmethod
    # def _set_resolver(path: Path) -> None:
    #     if not path.is_absolute():
    #         _path = path.resolve()
    #         warn(f"Resolve path is not absolute: {path}. "
    #              f"Inferring abspath from working directory: {_path}")
    #         path = _path
    #     JetContext.PARENT_FOLDER = path
    #
    # @staticmethod
    # def _get_resolver() -> Path:
    #     return JetContext.PARENT_FOLDER
    #
    # @staticmethod
    # def _reset_resolver() -> None:
    #     JetContext.PARENT_FOLDER = Path(os.getcwd())

    @staticmethod
    def _resolve_path(path: str | Path):
        return (JetContext.visit_stack[-1].parent / path).resolve()

    @staticmethod
    def _add_visit(path: Path) -> None:
        JetContext.visit_stack.append(path)

    @staticmethod
    def _rm_visit(path: Path) -> None:
        JetContext.visit_stack.remove(path)

    @staticmethod
    def _is_visited(path: str) -> bool:
        return str(path) in JetContext.visit_stack
