# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


def to_binary_string(int_value, result_width):
    """
    Convert natural integer value to a string of 1's and 0's.
    Most significant bit is the first (left-most) character in the string.

    Arguments:
        int_value (int): The value to be converted.
        result_width (int): The number of bits in the result. The supplied ``int_value`` must fit.

    Returns:
        str: A string of  length ``result_width`` containing only "1" and "0".
    """
    if int_value < 0:
        raise ValueError(f"Negative value {int_value} not supported")

    # bin() returns e.g. "0b10101010"
    binary_string = bin(int_value)[2:]
    if len(binary_string) > result_width:
        raise ValueError(f"Value {int_value} does not fit in {result_width} bits")

    # Pad with zeros to the full length
    formatting_string = f"{{:0>{result_width}}}"
    padded_binary_string = formatting_string.format(binary_string)
    assert len(padded_binary_string) == result_width

    return padded_binary_string
