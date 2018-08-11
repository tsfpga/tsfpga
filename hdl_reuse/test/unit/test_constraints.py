from os.path import dirname, join
import pytest
import unittest

from hdl_reuse.constraints import Constraint
from hdl_reuse.test import create_file, delete


THIS_DIR = dirname(__file__)


class TestConstraint(unittest.TestCase):

    _modules_folder = join(THIS_DIR, "modules_for_test")

    def setUp(self):
        delete(self._modules_folder)
        self.file = create_file(join(self._modules_folder, "a", "scoped_constraints", "apa.tcl"))

    def test_constraint(self):
        constraint = Constraint(self.file)
        assert constraint.ref is None
        assert constraint.used_in == "all"

        constraint = Constraint(self.file, used_in="impl")
        assert constraint.used_in == "impl"

    def test_scoped_constraint(self):
        create_file(join(self._modules_folder, "a", "apa.vhd"))

        constraint = Constraint(self.file, scoped_constraint=True)
        assert constraint.ref == "apa"

    def test_matching_entity_not_existing_should_raise_exception(self):
        with pytest.raises(AssertionError) as exception_info:
            Constraint(self.file, scoped_constraint=True)
        assert str(exception_info.value).startswith("Could not find a matching entity file")
