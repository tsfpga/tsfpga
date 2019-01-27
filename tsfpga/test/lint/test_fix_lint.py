from os.path import join, dirname
import unittest

from tsfpga.system_utils import create_file, delete
from tsfpga.test import file_equals
from tsfpga.fix_lint import fix_trailing_whitespace


THIS_DIR = dirname(__file__)


class TestFixLint(unittest.TestCase):

    file = join(THIS_DIR, "temp_file_for_test.txt")

    def setUp(self):
        delete(self.file)

    def test_fix_trailing_whitespace(self):
        data = "Apa \nhest    \nzebra"
        data_fixed = "Apa\nhest\nzebra"

        create_file(self.file, data)
        fix_trailing_whitespace(self.file)
        assert file_equals(self.file, data_fixed)
