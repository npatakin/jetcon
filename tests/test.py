import unittest

from jetcon import JetConfig
from dataclasses import dataclass


LOG = "-" * 8 + "\nCheck {} ...."
OK = "-" * 8 + "\n{}: OK"


class CLS:
    def __init__(self, a, b=1, *args, **kwargs):
        print(f"CLS Called with a={a}, b={b}, args={args}, kwargs={kwargs}")
        self.a = a
        self.b = b
        self.args = args
        self.kwargs = kwargs


def FN(a, b=1, *args, **kwargs):
    print(f"FN Called with a={a}, b={b}, args={args}, kwargs={kwargs}")
    return True


@dataclass
class DATACLASS:
    a: str
    b: str = "hello"

    def __post_init__(self):
        print(f"DATACLASS called with a={self.a}, b={self.b}")


class JetConfigMethods(unittest.TestCase):
    def test_read_compose(self):
        node = JetConfig.read("./configs/import/main.yaml")
        self.assertIsNotNone(node)
        self.assertIsNotNone(node.sub_import.var_a)
        self.assertIsNotNone(node.sub_import.var_b)
        self.assertIsNotNone(node.section_main.subsection_main.sub_import)

    def test_build(self):
        log = LOG.format(JetConfig.build.__name__)
        ok = OK.format(JetConfig.build.__name__)

        print(log)
        node = JetConfig.read("./configs/import/main.yaml")

        print("Build partial class: __main__.CLS")
        pc = node.pcls.build()
        self.assertEqual(pc.func, CLS)

        print("Build class: __main__.CLS")
        c = node.cls.build()
        self.assertIsInstance(c, CLS)
        self.assertEqual(c.a, 'cls_a')
        self.assertEqual(c.b, 'cls_b')
        self.assertEqual(c.kwargs, {"d": 'cls_kwarg'})

        print("Build partial function: __main__.FN")
        pf = node.pfn.build()
        self.assertEqual(pf.func, FN)

        print("Build function: __main__.FN")
        f = node.fn.build()
        self.assertEqual(f, True)

        print("Build partial dataclass: __main__.DATACLASS")
        pd = node.pdata.build()
        self.assertEqual(pd.func, DATACLASS)

        print("Build class: __main__.DATACLASS")
        d = node.data.build()
        self.assertIsInstance(d, DATACLASS)
        self.assertEqual(d.a, 'data_a')
        self.assertEqual(d.b, "hello")

        print(ok)

    def test_merge(self):
        log = LOG.format(JetConfig.merge.__name__)
        ok = OK.format(JetConfig.merge.__name__)

        print(log)
        node = JetConfig.read("./configs/merge/main.yaml")

        self.assertEqual(node.section.subsection.c1, None)
        self.assertEqual(node.section.subsection.c2, None)

        self.assertEqual(node.section.sub2.a, 1)
        self.assertEqual(node.section.sub2.b, 2)
        self.assertEqual(node.section.sub2.c, 3)
        self.assertEqual(node.section.sub2.d, 4)

        self.assertEqual(node.section.a, 1)
        self.assertEqual(node.section.b, 2)
        self.assertEqual(node.section.c, 3)
        self.assertEqual(node.section.d, 4)

        print(ok)


if __name__ == "__main__":
    unittest.main()
