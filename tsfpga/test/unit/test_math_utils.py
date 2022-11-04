# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Third party libraries
import pytest

# First party libraries
from tsfpga.math_utils import to_binary_string


def test_to_binary_string():
    assert to_binary_string(int_value=2, result_width=3) == "010"
    assert to_binary_string(int_value=15, result_width=4) == "1111"
    assert to_binary_string(int_value=0, result_width=5) == "00000"

    with pytest.raises(ValueError) as exception_info:
        to_binary_string(int_value=15, result_width=3)
    assert str(exception_info.value) == "Value 15 does not fit in 3 bits"

    with pytest.raises(ValueError) as exception_info:
        to_binary_string(int_value=-7, result_width=10)
    assert str(exception_info.value) == "Negative value -7 not supported"
