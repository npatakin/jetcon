import os
from pathlib import Path
from warnings import warn


class JetContext:
    # default directory that is used for path resolver during import
    PARENT_FOLDER: str = os.getcwd()
    # global dependency stack that tracks visited files during import
    VISITED_DEPS_FILES: list[str] = list()

    def __init__(self) -> None:
        raise RuntimeError(f"Contex class {JetContext.__name__} cannot be instansiated.")

    @staticmethod
    def _set_resolver(path: str) -> None:
        path = Path(path)

        if not path.is_absolute():
            _path = path.resolve()
            warn(f"Resolve path is not absolute: {path}. "
                 f"Inferring abspath from working directory: {_path}")
            path = _path
        JetContext.PARENT_FOLDER = str(path)

    @staticmethod
    def _get_resolver() -> str:
        return JetContext.PARENT_FOLDER

    @staticmethod
    def _reset_resolver() -> str:
        JetContext.PARENT_FOLDER = os.getcwd()

    @staticmethod
    def _add_visit(path: str) -> None:
        JetContext.VISITED_DEPS_FILES.append(path)

    @staticmethod
    def _rm_visit(path: str) -> None:
        JetContext.VISITED_DEPS_FILES.remove(path)

    @staticmethod
    def _is_visited(path: str) -> bool:
        return path in JetContext.VISITED_DEPS_FILES
