# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.system_utils import create_file
from tsfpga.test import file_equals
from tsfpga.fix_lint import fix_trailing_whitespace, fix_tabs


def test_fix_trailing_whitespace(tmp_path):
    data = "Apa \nhest    \nzebra"
    data_fixed = "Apa\nhest\nzebra"

    file = create_file(tmp_path / "temp_file_for_test.txt", data)
    fix_trailing_whitespace(file)
    assert file_equals(file, data_fixed)


def test_fix_tabs(tmp_path):
    data = "Apa\thest \t zebra"
    data_fixed = "Apa hest   zebra"
    file = create_file(tmp_path / "data_width_1.txt", data)
    fix_tabs(file, tab_width=1)
    assert file_equals(file, data_fixed)

    data_fixed = "Apa  hest    zebra"
    file = create_file(tmp_path / "data_width_2.txt", data)
    fix_tabs(file, tab_width=2)
    assert file_equals(file, data_fixed)
