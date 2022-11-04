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
from tsfpga.vivado.generics import (
    BitVectorGenericValue,
    StringGenericValue,
    get_vivado_tcl_generic_value,
)


def test_boolean_generics():
    assert get_vivado_tcl_generic_value(True) == "1'b1"
    assert get_vivado_tcl_generic_value(False) == "1'b0"


def test_integer_generics():
    assert get_vivado_tcl_generic_value(123) == "123"
    assert get_vivado_tcl_generic_value(0) == "0"
    assert get_vivado_tcl_generic_value(-7) == "-7"


def test_float_generics():
    assert get_vivado_tcl_generic_value(3.1415) == "3.1415"
    assert get_vivado_tcl_generic_value(0.0) == "0.0"
    assert get_vivado_tcl_generic_value(-1.72) == "-1.72"


def test_bit_vector_generics():
    assert get_vivado_tcl_generic_value(BitVectorGenericValue("1010")) == "4'b1010"

    with pytest.raises(ValueError) as exception_info:
        BitVectorGenericValue(1010)
    assert (
        str(exception_info.value) == "Expected BitVectorGenericValue value to be of type str: 1010"
    )

    with pytest.raises(ValueError) as exception_info:
        BitVectorGenericValue("102A")
    assert (
        str(exception_info.value)
        == 'Expected BitVectorGenericValue value to contain only "1" or "0": 102A'
    )


def test_string_generics():
    assert get_vivado_tcl_generic_value(StringGenericValue("apa")) == "apa"

    with pytest.raises(ValueError) as exception_info:
        StringGenericValue(3)
    assert str(exception_info.value) == "Expected StringGenericValue value to be of type str: 3"

    with pytest.raises(ValueError) as exception_info:
        StringGenericValue("apa hest")
    assert (
        str(exception_info.value)
        == "Expected StringGenericValue value to not contain spaces: apa hest"
    )


def test_unsupported_generic_type():
    with pytest.raises(ValueError) as exception_info:
        get_vivado_tcl_generic_value(dict(name="value"))
    assert (
        str(exception_info.value)
        == "Got unsupported type for generic. Type=<class 'dict'>, value={'name': 'value'}."
    )

    with pytest.raises(ValueError) as exception_info:
        get_vivado_tcl_generic_value("/home/test.vhd")
    assert (
        str(exception_info.value)
        == "Got unsupported type for generic. Type=<class 'str'>, value=/home/test.vhd."
    )

    with pytest.raises(ValueError) as exception_info:
        get_vivado_tcl_generic_value("01101")
    assert (
        str(exception_info.value)
        == "Got unsupported type for generic. Type=<class 'str'>, value=01101."
    )
