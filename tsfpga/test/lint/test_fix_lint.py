# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from pathlib import Path
import unittest

from tsfpga.system_utils import create_file, delete
from tsfpga.test import file_equals
from tsfpga.fix_lint import fix_trailing_whitespace, fix_tabs


THIS_DIR = Path(__file__).parent


class TestFixLint(unittest.TestCase):

    file = THIS_DIR / "temp_file_for_test.txt"

    def setUp(self):
        delete(self.file)

    def test_fix_trailing_whitespace(self):
        data = "Apa \nhest    \nzebra"
        data_fixed = "Apa\nhest\nzebra"

        create_file(self.file, data)
        fix_trailing_whitespace(self.file)
        assert file_equals(self.file, data_fixed)

    def test_fix_tabs(self):
        data = "Apa\thest \t zebra"
        data_fixed = "Apa hest   zebra"
        create_file(self.file, data)
        fix_tabs(self.file, tab_width=1)
        assert file_equals(self.file, data_fixed)

        data_fixed = "Apa  hest    zebra"
        create_file(self.file, data)
        fix_tabs(self.file, tab_width=2)
        assert file_equals(self.file, data_fixed)
