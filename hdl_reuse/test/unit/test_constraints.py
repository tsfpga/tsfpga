from os.path import dirname, join
import pytest
import unittest

from hdl_reuse.constraints import EntityConstraint
from hdl_reuse.test import create_file, delete


THIS_DIR = dirname(__file__)


class TestEntityConstraint(unittest.TestCase):

    _modules_folder = join(THIS_DIR, "modules_for_test")

    def setUp(self):
        self.file = create_file(join(self._modules_folder, "a", "entity_constraints", "apa.tcl"))

    def tearDown(self):
        delete(self._modules_folder)

    def test_tcl(self):
        create_file(join(self._modules_folder, "a", "apa.vhd"))

        entity_constraint = EntityConstraint(self.file, used_in="all")
        assert entity_constraint.load_tcl() == "read_xdc -ref apa -unmanaged " + self.file + "\n"

    def test_matching_entity_not_existing_should_raise_exception(self):
        with pytest.raises(AssertionError):
            EntityConstraint(self.file, used_in="all")
