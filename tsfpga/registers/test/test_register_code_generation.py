# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import unittest

import pytest

import tsfpga
from tsfpga.system_utils import create_directory
from tsfpga.registers.register_list import from_toml

from examples.tsfpga_example_env import get_default_registers


@pytest.mark.usefixtures("fixture_tmp_path")
class TestRegisterList(unittest.TestCase):

    tmp_path = None

    def setUp(self):
        self.register_list = from_toml(
            module_name="ddr_buffer",
            toml_file=tsfpga.TSFPGA_EXAMPLE_MODULES / "ddr_buffer" / "regs_ddr_buffer.toml",
            default_registers=get_default_registers(),
        )

    def test_can_generate_vhdl_package_without_error(self):
        create_directory(self.tmp_path / "vhdl")
        self.register_list.create_vhdl_package(self.tmp_path / "vhdl")

    def test_can_generate_c_header_without_error(self):
        self.register_list.create_c_header(self.tmp_path / "c")

    def test_can_generate_cpp_without_error(self):
        self.register_list.create_cpp_interface(self.tmp_path / "cpp")
        self.register_list.create_cpp_header(self.tmp_path / "cpp")
        self.register_list.create_cpp_implementation(self.tmp_path / "cpp")

    def test_can_generate_html_without_error(self):
        self.register_list.create_html_constant_table(self.tmp_path / "html")
        self.register_list.create_html_register_table(self.tmp_path / "html")
        self.register_list.create_html_page(self.tmp_path / "html")
