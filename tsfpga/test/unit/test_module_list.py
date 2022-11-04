# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from unittest import TestCase
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


class TestModuleList(TestCase):
    def setUp(self):
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

    def test_get(self):
        assert self.modules.get("a") == self.module_a
        assert self.modules.get("c") == self.module_c

        with pytest.raises(ValueError) as exception_info:
            self.modules.get("d")
        assert str(exception_info.value) == 'No module "d" available'

    def test_iteration(self):
        expected = [self.module_a, self.module_b, self.module_c]

        # pylint: disable=unnecessary-comprehension
        assert [module for module in self.modules] == expected
        assert list(self.modules) == expected

    def test_can_cast_to_string_without_error(self):
        print(self.modules)

    def test_concatenation(self):
        modules_2 = ModuleList()

        module_d = MagicMock()
        module_d.name = "d"
        modules_2.append(module_d)

        all_modules = self.modules + modules_2

        assert len(all_modules) == 4
        assert list(all_modules) == [self.module_a, self.module_b, self.module_c, module_d]

        # The addition should result in a new object. Should not affect the existing objects.
        assert len(self.modules) == 3
        assert len(modules_2) == 1

        assert (all_modules is not modules_2) and (all_modules is not self.modules)

        # pylint: disable=protected-access
        assert (all_modules._modules is not modules_2._modules) and (
            all_modules._modules is not self.modules._modules
        )

    def test_concatenation_with_unknown_object_should_raise_interrupt(self):
        with pytest.raises(TypeError) as exception_info:
            # pylint: disable=pointless-statement
            self.modules + 3
        assert str(exception_info.value) == "Can only concatenate with another ModuleList"

    def test_copy(self):
        modules_copy = self.modules.copy()

        modules_copy.append(4)
        assert len(self.modules) == 3
