# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from unittest.mock import MagicMock
import pytest

from hdl_registers.register_list import RegisterList

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

    rst = module_documentation.get_submodule_rst(heading_character="-")
    assert "Dummy from excluded.vhd." in rst

    rst = module_documentation.get_submodule_rst(
        heading_character="-", exclude_files={excluded_vhd}
    )
    assert "Dummy from excluded.vhd." not in rst
