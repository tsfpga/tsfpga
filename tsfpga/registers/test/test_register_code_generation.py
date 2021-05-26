# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import unittest

import pytest

import tsfpga
from tsfpga.system_utils import create_directory, read_file
from tsfpga.registers.parser import from_toml

from examples.tsfpga_example_env import get_default_registers


@pytest.mark.usefixtures("fixture_tmp_path")
class TestRegisterList(unittest.TestCase):
    """
    Some happy path tests. See the individual code generation classes for notes on more
    exhaustive testing.
    """

    tmp_path = None

    def setUp(self):
        self.source_toml_file = (
            tsfpga.TSFPGA_EXAMPLE_MODULES / "ddr_buffer" / "regs_ddr_buffer.toml"
        )
        self.register_list = from_toml(
            module_name="ddr_buffer",
            toml_file=self.source_toml_file,
            default_registers=get_default_registers(),
        )

    def test_can_generate_vhdl_package_without_error(self):
        output_path = create_directory(self.tmp_path / "vhdl")

        self.register_list.create_vhdl_package(output_path)

        assert (output_path / "ddr_buffer_regs_pkg.vhd").exists()

    def test_can_generate_c_header_without_error(self):
        output_path = self.tmp_path / "c"

        self.register_list.create_c_header(output_path)

        assert (output_path / "ddr_buffer_regs.h").exists()

    def test_can_generate_cpp_without_error(self):
        output_path = self.tmp_path / "cpp"

        self.register_list.create_cpp_interface(output_path)
        self.register_list.create_cpp_header(output_path)
        self.register_list.create_cpp_implementation(output_path)

        assert (output_path / "i_ddr_buffer.h").exists()
        assert (output_path / "ddr_buffer.h").exists()
        assert (output_path / "ddr_buffer.cpp").exists()

    def test_can_generate_html_without_error(self):
        output_path = self.tmp_path / "html"

        self.register_list.create_html_constant_table(output_path)
        self.register_list.create_html_register_table(output_path)
        self.register_list.create_html_page(output_path)

        assert (output_path / "ddr_buffer_regs.html").exists()
        assert (output_path / "ddr_buffer_register_table.html").exists()
        assert (output_path / "ddr_buffer_constant_table.html").exists()
        assert (output_path / "regs_style.css").exists()

    def test_copy_source_definition(self):
        output_path = self.tmp_path / "toml"

        self.register_list.copy_source_definition(output_path)

        assert read_file(output_path / "regs_ddr_buffer.toml") == read_file(self.source_toml_file)

    def test_copy_source_definition_with_no_file_defined(self):
        self.register_list.source_definition_file = None
        output_path = self.tmp_path / "toml"
        self.register_list.copy_source_definition(output_path)

        assert not output_path.exists()
