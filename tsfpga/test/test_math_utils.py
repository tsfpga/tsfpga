# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Third party libraries
import pytest

# First party libraries
from tsfpga.math_utils import (
    to_binary_nibble_string,
    to_binary_string,
    to_hex_byte_string,
    to_hex_string,
)


def test_to_binary_string():
    assert to_binary_string(value=0, result_width=1) == "0"
    assert to_binary_string(value=1, result_width=1) == "1"
    assert to_binary_string(value=2, result_width=3) == "010"
    assert to_binary_string(value=15, result_width=4) == "1111"
    assert to_binary_string(value=0, result_width=5) == "00000"


def test_to_binary_string_width_out_of_range_should_raise_exception():
    with pytest.raises(ValueError) as exception_info:
        to_binary_string(value=15, result_width=0)
    assert str(exception_info.value) == 'Invalid result width "0".'

    with pytest.raises(ValueError) as exception_info:
        to_binary_string(value=-7, result_width=-3)
    assert str(exception_info.value) == 'Invalid result width "-3".'


def test_to_binary_string_value_out_of_range_should_raise_exception():
    with pytest.raises(ValueError) as exception_info:
        to_binary_string(value=15, result_width=3)
    assert str(exception_info.value) == 'Value "15" out of 3-bit range.'

    with pytest.raises(ValueError) as exception_info:
        to_binary_string(value=-7, result_width=10)
    assert str(exception_info.value) == 'Value "-7" out of 10-bit range.'


def test_to_binary_nibble_string():
    assert to_binary_nibble_string(value=0, result_width_bits=1) == "0"
    assert to_binary_nibble_string(value=1, result_width_bits=1) == "1"

    assert to_binary_nibble_string(value=2, result_width_bits=3) == "010"
    assert to_binary_nibble_string(value=7, result_width_bits=3) == "111"

    assert to_binary_nibble_string(value=15, result_width_bits=4) == "1111"

    assert to_binary_nibble_string(value=0, result_width_bits=5) == "0_0000"
    assert to_binary_nibble_string(value=16, result_width_bits=5) == "1_0000"

    assert to_binary_nibble_string(value=265, result_width_bits=9) == "1_0000_1001"
    assert to_binary_nibble_string(value=565, result_width_bits=10) == "10_0011_0101"
    assert to_binary_nibble_string(value=565, result_width_bits=12) == "0010_0011_0101"
    assert to_binary_nibble_string(value=2345, result_width_bits=12) == "1001_0010_1001"

    assert to_binary_nibble_string(value=5345, result_width_bits=13) == "1_0100_1110_0001"


def test_to_binary_nibble_string_width_out_of_range_should_raise_exception():
    with pytest.raises(ValueError) as exception_info:
        to_binary_nibble_string(value=15, result_width_bits=0)
    assert str(exception_info.value) == 'Invalid result width "0".'

    with pytest.raises(ValueError) as exception_info:
        to_binary_nibble_string(value=-7, result_width_bits=-3)
    assert str(exception_info.value) == 'Invalid result width "-3".'


def test_to_binary_nibble_string_value_out_of_range_should_raise_exception():
    with pytest.raises(ValueError) as exception_info:
        to_binary_nibble_string(value=15, result_width_bits=3)
    assert str(exception_info.value) == 'Value "15" out of 3-bit range.'

    with pytest.raises(ValueError) as exception_info:
        to_binary_nibble_string(value=-7, result_width_bits=10)
    assert str(exception_info.value) == 'Value "-7" out of 10-bit range.'


def test_to_hex_string():
    assert to_hex_string(value=0, result_width_bits=1) == "0"
    assert to_hex_string(value=1, result_width_bits=1) == "1"
    assert to_hex_string(value=2, result_width_bits=3) == "2"
    assert to_hex_string(value=2, result_width_bits=4) == "2"
    assert to_hex_string(value=2, result_width_bits=5) == "02"
    assert to_hex_string(value=15, result_width_bits=4) == "F"
    assert to_hex_string(value=0, result_width_bits=5) == "00"


def test_to_hex_string_width_out_of_range_should_raise_exception():
    with pytest.raises(ValueError) as exception_info:
        to_hex_string(value=15, result_width_bits=0)
    assert str(exception_info.value) == 'Invalid result width "0".'

    with pytest.raises(ValueError) as exception_info:
        to_hex_string(value=-7, result_width_bits=-3)
    assert str(exception_info.value) == 'Invalid result width "-3".'


def test_to_hex_string_value_out_of_range_should_raise_exception():
    with pytest.raises(ValueError) as exception_info:
        to_hex_string(value=15, result_width_bits=3)
    assert str(exception_info.value) == 'Value "15" out of 3-bit range.'

    with pytest.raises(ValueError) as exception_info:
        to_hex_string(value=-7, result_width_bits=10)
    assert str(exception_info.value) == 'Value "-7" out of 10-bit range.'


def test_to_hex_byte_string():
    assert to_hex_byte_string(value=0, result_width_bits=1) == "0"
    assert to_hex_byte_string(value=1, result_width_bits=1) == "1"

    assert to_hex_byte_string(value=2, result_width_bits=3) == "2"
    assert to_hex_byte_string(value=7, result_width_bits=3) == "7"

    assert to_hex_byte_string(value=15, result_width_bits=4) == "F"

    assert to_hex_byte_string(value=0, result_width_bits=5) == "00"
    assert to_hex_byte_string(value=15, result_width_bits=5) == "0F"
    assert to_hex_byte_string(value=16, result_width_bits=5) == "10"

    assert to_hex_byte_string(value=265, result_width_bits=9) == "1_09"
    assert to_hex_byte_string(value=565, result_width_bits=10) == "2_35"
    assert to_hex_byte_string(value=565, result_width_bits=12) == "2_35"
    assert to_hex_byte_string(value=2345, result_width_bits=12) == "9_29"

    assert to_hex_byte_string(value=5345, result_width_bits=13) == "14_E1"


def test_to_hex_byte_string_width_out_of_range_should_raise_exception():
    with pytest.raises(ValueError) as exception_info:
        to_hex_byte_string(value=15, result_width_bits=0)
    assert str(exception_info.value) == 'Invalid result width "0".'

    with pytest.raises(ValueError) as exception_info:
        to_hex_byte_string(value=-7, result_width_bits=-3)
    assert str(exception_info.value) == 'Invalid result width "-3".'


def test_to_hex_byte_string_value_out_of_range_should_raise_exception():
    with pytest.raises(ValueError) as exception_info:
        to_hex_byte_string(value=15, result_width_bits=3)
    assert str(exception_info.value) == 'Value "15" out of 3-bit range.'

    with pytest.raises(ValueError) as exception_info:
        to_hex_byte_string(value=-7, result_width_bits=10)
    assert str(exception_info.value) == 'Value "-7" out of 10-bit range.'
