# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from pathlib import Path
import pytest
import unittest

from tsfpga.constraint import Constraint
from tsfpga.hdl_file import HdlFile
from tsfpga.system_utils import create_file, delete


class TestConstraint(unittest.TestCase):

    _modules_folder = Path(__file__).parent / "modules_for_test"

    def setUp(self):
        delete(self._modules_folder)
        self.file = create_file(self._modules_folder / "a" / "scoped_constraints" / "apa.tcl")

    def test_constraint(self):
        constraint = Constraint(self.file)
        constraint.validate_scoped_entity([])

        assert constraint.ref is None
        assert constraint.used_in == "all"

        constraint = Constraint(self.file, used_in="impl")
        assert constraint.used_in == "impl"

    def test_scoped_constraint(self):
        constraint = Constraint(self.file, scoped_constraint=True)
        assert constraint.ref == "apa"

        source_files = [HdlFile(self._modules_folder / "a" / "apa.vhd")]
        constraint.validate_scoped_entity(source_files)

    def test_matching_entity_not_existing_should_raise_exception(self):
        constraint = Constraint(self.file, scoped_constraint=True)
        with pytest.raises(FileNotFoundError) as exception_info:
            constraint.validate_scoped_entity([])
        assert str(exception_info.value).startswith("Could not find a matching entity file")
