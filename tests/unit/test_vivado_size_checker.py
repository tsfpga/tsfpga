# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from unittest import mock
import io

from tsfpga.vivado.size_checker import UtilizationParser, EqualTo, LessThan, TotalLuts


def test_utilzation_parser():
    report = " \
Writing top or top) or (top here should not cause issues\n\
Also writing pipes | | | | should be fine\n\
Random sections of dashes should be fine:\n\
---------------------------------------------------------------\n\
-----------------------+----------------------------+----------\n\
But this should hit:\n\
| x | x | a | b | c | d |\n\
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\
| x | (top) | 1 | 2 | 3 | 4 |\n\
"

    result = UtilizationParser.get_size(report)
    assert result["a"] == 1
    assert result["b"] == 2
    assert result["c"] == 3
    assert result["d"] == 4
    assert len(result) == 4


@mock.patch("sys.stdout", new_callable=io.StringIO)
def test_size_checker_less_than_pass(mock_stdout):
    result_size = {"Total LUTs": 5}
    assert TotalLuts(LessThan(10)).check(result_size)
    assert mock_stdout.getvalue() == "Result size check passed for Total LUTs: 5 (< 10)\n"


@mock.patch("sys.stdout", new_callable=io.StringIO)
def test_size_checker_equal_to_fail(mock_stdout):
    result_size = {"Total LUTs": 5}
    assert not TotalLuts(EqualTo(50)).check(result_size)
    assert mock_stdout.getvalue() == "Result size check failed for Total LUTs. Got 5, expected 50.\n"
