# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from unittest.mock import MagicMock

# Third party libraries
import pytest
from hdl_registers.register_list import RegisterList

# First party libraries
from tsfpga.module import BaseModule
from tsfpga.module_documentation import ModuleDocumentation
from tsfpga.system_utils import create_file

# pylint: disable=redefined-outer-name


@pytest.fixture
def module_documentation(tmp_path):
    module = BaseModule(path=tmp_path / "apa", library_name="apa")
    module_documentation_object = ModuleDocumentation(module)

    data = """\
-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -------------------------------------------------------------------------------------------------
-- Dummy from hest.vhd.
-- -------------------------------------------------------------------------------------------------

"""
    create_file(module.path / "src" / "hest.vhd", contents=data)

    return module_documentation_object


def test_documentation_header_with_no_overview_and_no_registers(module_documentation):
    rst = module_documentation.get_rst_document()

    assert "\nhest.vhd\n--------" in rst
    assert "Dummy from hest.vhd." in rst

    assert "Register interface" not in rst


def test_documentation_header_with_overview_and_registers(module_documentation):
    # pylint: disable=protected-access
    module = module_documentation._module
    module._registers = MagicMock(spec=RegisterList)

    data = "Dummy from apa.rst."
    create_file(module.path / "doc" / "apa.rst", contents=data)

    rst = module_documentation.get_rst_document()

    assert "\nhest.vhd\n--------" in rst
    assert "Dummy from hest.vhd." in rst

    assert "Dummy from apa.rst" in rst

    assert "Register interface" in rst
    assert ":download:`separate HTML page <apa_regs.html>`" in rst


def test_submodule_documentation_with_file_exclude(module_documentation):
    data = """\
-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -------------------------------------------------------------------------------------------------
-- Dummy from excluded.vhd.
-- -------------------------------------------------------------------------------------------------

"""
    # pylint: disable=protected-access
    excluded_vhd = create_file(
        module_documentation._module.path / "rtl" / "excluded.vhd", contents=data
    )

    rst = module_documentation.get_submodule_rst(heading_character="-", heading_character_2="_")
    assert "Dummy from excluded.vhd." in rst

    rst = module_documentation.get_submodule_rst(
        heading_character="-", heading_character_2="_", exclude_files={excluded_vhd}
    )
    assert "Dummy from excluded.vhd." not in rst


def test_submodule_documentation_with_folder_exclude(module_documentation):
    data = """\
-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -------------------------------------------------------------------------------------------------
-- Dummy from excluded.vhd.
-- -------------------------------------------------------------------------------------------------

"""
    # pylint: disable=protected-access
    create_file(module_documentation._module.path / "rtl" / "excluded.vhd", contents=data)

    rst = module_documentation.get_submodule_rst(heading_character="-", heading_character_2="_")
    assert "Dummy from excluded.vhd." in rst

    rst = module_documentation.get_submodule_rst(
        heading_character="-",
        heading_character_2="_",
        exclude_module_folders=["rtl"],
    )
    assert "Dummy from excluded.vhd." not in rst


def test_include_sim_but_not_test_folder(module_documentation):
    data = """\
-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -------------------------------------------------------------------------------------------------
-- Dummy from bfm.vhd.
-- -------------------------------------------------------------------------------------------------

"""
    # pylint: disable=protected-access
    create_file(module_documentation._module.path / "sim" / "bfm.vhd", contents=data)

    data = """\
-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -------------------------------------------------------------------------------------------------
-- Dummy from tb.vhd.
-- -------------------------------------------------------------------------------------------------

"""
    # pylint: disable=protected-access
    create_file(module_documentation._module.path / "test" / "tb.vhd", contents=data)

    rst = module_documentation.get_submodule_rst(heading_character="-", heading_character_2="_")
    assert "Dummy from bfm.vhd." in rst
    assert "Dummy from tb.vhd." not in rst

    rst = module_documentation.get_submodule_rst(
        heading_character="-", heading_character_2="_", exclude_module_folders=["sim"]
    )
    assert "Dummy from bfm.vhd." not in rst
    assert "Dummy from tb.vhd." not in rst
