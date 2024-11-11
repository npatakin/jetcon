from enum import Enum


class Keywords(Enum):
    func = "_fn_"   # function
    cls = "_cls_"   # regular class
    data = "_data_"     # dataclass

    imports = "_import_"    # import directive
