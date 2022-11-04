# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path

# Third party libraries
import pytest

# First party libraries
from tsfpga.constraint import Constraint
from tsfpga.hdl_file import HdlFile


def test_constraint():
    constraint = Constraint(Path("dummy.tcl"))
    constraint.validate_scoped_entity([])

    assert constraint.ref is None
    assert constraint.used_in == "all"

    constraint = Constraint(Path("dummy.tcl"), used_in="impl")
    assert constraint.used_in == "impl"


def test_scoped_constraint(tmp_path):
    constraint = Constraint(
        tmp_path / "a" / "scoped_constraints" / "apa.tcl", scoped_constraint=True
    )
    assert constraint.ref == "apa"

    source_files = [HdlFile(tmp_path / "a" / "apa.vhd")]
    constraint.validate_scoped_entity(source_files)


def test_matching_entity_not_existing_should_raise_exception(tmp_path):
    constraint = Constraint(
        tmp_path / "a" / "scoped_constraints" / "dummy.tcl", scoped_constraint=True
    )
    with pytest.raises(FileNotFoundError) as exception_info:
        constraint.validate_scoped_entity([])
    assert str(exception_info.value).startswith("Could not find a matching entity file")


def test_can_cast_to_string_without_error():
    str(Constraint(Path("dummy.tcl"), used_in="impl"))
