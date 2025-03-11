# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import contextlib
import io
from pathlib import Path

import pytest

from tsfpga.constraint import Constraint
from tsfpga.hdl_file import HdlFile


def test_constraint():
    constraint = Constraint(Path("dummy.tcl"))
    constraint.validate_scoped_entity([])

    assert constraint.ref is None
    assert constraint.used_in_synthesis
    assert constraint.used_in_implementation


def test_constraint_used_in():
    constraint = Constraint(Path("dummy.tcl"), used_in_synthesis=False)
    assert not constraint.used_in_synthesis
    assert constraint.used_in_implementation

    constraint = Constraint(Path("dummy.tcl"), used_in_implementation=False)
    assert constraint.used_in_synthesis
    assert not constraint.used_in_implementation


def test_constraint_used_in_deprecated():
    constraint = Constraint(Path("dummy.tcl"), used_in="impl")
    assert not constraint.used_in_synthesis
    assert constraint.used_in_implementation

    constraint = Constraint(Path("dummy.tcl"), used_in="synth")
    assert constraint.used_in_synthesis
    assert not constraint.used_in_implementation

    constraint = Constraint(Path("dummy.tcl"), used_in="all")
    assert constraint.used_in_synthesis
    assert constraint.used_in_implementation


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


def test_used_in_deprecated_warning():
    string_io = io.StringIO()
    with contextlib.redirect_stdout(string_io):
        Constraint(Path("dummy.tcl"), used_in="impl")
    assert "DEPRECATED: " in string_io.getvalue()

    string_io = io.StringIO()
    with contextlib.redirect_stdout(string_io):
        Constraint(Path("dummy.tcl"), used_in_synthesis=False, used_in_implementation=False)
    assert "DEPRECATED: " not in string_io.getvalue()


def test_using_both_new_and_deprecated_should_raise_exception():
    string_io = io.StringIO()
    with contextlib.redirect_stdout(string_io), pytest.raises(ValueError) as exception_info:
        Constraint(Path("dummy.tcl"), used_in="impl", used_in_synthesis=False)
    assert "DEPRECATED: " in string_io.getvalue()
    assert "Using both 'used_in_*' and deprecated 'used_in'" in str(exception_info.value)
