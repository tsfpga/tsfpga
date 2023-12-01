# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from unittest.mock import MagicMock

# Third party libraries
import pytest

# First party libraries
from tsfpga.module_list import ModuleList


def test_module_list_indexing():
    modules = ModuleList()

    module_a = MagicMock()
    module_b = MagicMock()

    modules.append(module_a)
    modules.append(module_b)

    assert modules[0] is module_a
    assert modules[1] is module_b


@pytest.fixture
def module_list_test():
    class ModuleListTest:
        def __init__(self):
            self.modules = ModuleList()

            self.module_a = MagicMock()
            self.module_b = MagicMock()
            self.module_c = MagicMock()

            self.module_a.name = "a"
            self.module_b.name = "b"
            self.module_c.name = "c"

            self.modules.append(self.module_a)
            self.modules.append(self.module_b)
            self.modules.append(self.module_c)

    return ModuleListTest()


# False positive for pytest fixtures
# pylint: disable=redefined-outer-name


def test_get(module_list_test):
    assert module_list_test.modules.get("a") == module_list_test.module_a
    assert module_list_test.modules.get("c") == module_list_test.module_c

    with pytest.raises(ValueError) as exception_info:
        module_list_test.modules.get("d")
    assert str(exception_info.value) == 'No module "d" available'


def test_iteration(module_list_test):
    expected = [module_list_test.module_a, module_list_test.module_b, module_list_test.module_c]

    # pylint: disable=unnecessary-comprehension
    assert [module for module in module_list_test.modules] == expected
    assert list(module_list_test.modules) == expected


def test_can_cast_to_string_without_error(module_list_test):
    print(module_list_test.modules)


def test_concatenation(module_list_test):
    modules_2 = ModuleList()

    module_d = MagicMock()
    module_d.name = "d"
    modules_2.append(module_d)

    all_modules = module_list_test.modules + modules_2

    assert len(all_modules) == 4
    assert list(all_modules) == [
        module_list_test.module_a,
        module_list_test.module_b,
        module_list_test.module_c,
        module_d,
    ]

    # The addition should result in a new object. Should not affect the existing objects.
    assert len(module_list_test.modules) == 3
    assert len(modules_2) == 1

    assert (all_modules is not modules_2) and (all_modules is not module_list_test.modules)

    # pylint: disable=protected-access
    assert (all_modules._modules is not modules_2._modules) and (
        all_modules._modules is not module_list_test.modules._modules
    )


def test_concatenation_with_unknown_object_should_raise_interrupt(module_list_test):
    with pytest.raises(TypeError) as exception_info:
        # pylint: disable=pointless-statement
        module_list_test.modules + 3
    assert str(exception_info.value) == "Can only concatenate with another ModuleList"


def test_copy(module_list_test):
    modules_copy = module_list_test.modules.copy()

    modules_copy.append(4)
    assert len(module_list_test.modules) == 3
