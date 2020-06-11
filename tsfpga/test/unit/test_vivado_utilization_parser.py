# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.vivado_utilization_parser import VivadoUtilizationParser


def test_get_size():
    report_as_string = " \
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

    parser = VivadoUtilizationParser()
    result = parser.get_size(report_as_string)
    print(result)
    assert result["a"] == 1
    assert result["b"] == 2
    assert result["c"] == 3
    assert result["d"] == 4
    assert len(result) == 4
