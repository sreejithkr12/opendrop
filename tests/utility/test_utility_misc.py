import sys

from pytest import raises

from opendrop.utility.misc import recursive_load, EnumBuilder, get_classes_in_modules
from tests.samples import dummy_pkg


def test_get_classes_in_modules():
    clses = get_classes_in_modules(recursive_load(dummy_pkg), dummy_pkg.DummyClass)

    assert set(clses) == {
        dummy_pkg.DummyClass,
        dummy_pkg.module_a.MyFirstClass,
        dummy_pkg.subpkg.module_b.MySecondClass
    }


def test_recursive_load():
    modules = recursive_load(dummy_pkg)

    assert all(
        k in sys.modules
        for k in ['tests.samples.dummy_pkg.module_a', 'tests.samples.dummy_pkg.subpkg.module_b']
    )

    assert set(modules) == {
        dummy_pkg,
        dummy_pkg.module_a,
        dummy_pkg.subpkg,
        dummy_pkg.subpkg.module_b
    }


def test_enum_builder():
    class TestEnumMixin:
        def __init__(self, a0, a1, a2):
            self.a0 = a0
            self.a1 = a1
            self.a2 = a2

    test_builder = EnumBuilder('TestEnum', TestEnumMixin)

    # Test `add()`
    test_builder.add('ENUM0', (0, 1, 2))
    test_builder.add('ENUM1', ('a', 'b', 'c'))

    # Test `remove()`
    test_builder.remove('ENUM1')

    # Test `build()`
    TestEnum = test_builder.build()

    # Test created enum
    assert TestEnum.ENUM0.a0 == 0 and TestEnum.ENUM0.a1 == 1 and TestEnum.ENUM0.a2 == 2

    with raises(AttributeError):
        getattr(TestEnum, 'ENUM1')
