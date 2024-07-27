# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


def to_binary_string(value: int, result_width: int) -> str:
    """
    Convert unsigned integer value to a zero-padded string of 1's and 0's.
    Most significant bit is the first (left-most) character in the string.

    For example, value 37, width 6, returns ``100101``.
    For example, value 37, width 8, returns ``00100101``.

    Arguments:
        value: The value to be converted.
        result_width: The supplied ``value`` will be interpreted as an unsigned value with
            this many bits.
            The result string will contain this many bit characters.
    """
    _check_unsigned_range(value=value, width=result_width)

    # Cast to binary, pad with zeros on the left.
    formatting_string = f"{{:0{result_width}b}}"
    padded_binary_string = formatting_string.format(value)
    assert len(padded_binary_string) == result_width

    return padded_binary_string


def to_binary_nibble_string(value: int, result_width_bits: int) -> str:
    """
    Convert unsigned integer value to a zero-padded string of 1's and 0's, with each nibble (4 bits)
    separated by "_".
    Most significant bit is the first (left-most) character in the string.

    For example, value 37, width 6, returns ``10_0101``.
    For example, value 37, width 8, returns ``0010_0101``.

    Arguments:
        value: The value to be converted.
        result_width_bits: The supplied ``value`` will be interpreted as an unsigned value with
            this many bits.
            The result string will contain this many bit characters, plus separators.
    """
    _check_unsigned_range(value=value, width=result_width_bits)

    result_width_nibbles = (result_width_bits + 4 - 1) // 4
    num_separators = result_width_nibbles - 1
    result_width = result_width_bits + num_separators

    # Cast to binary, pad with zeros on the left, separate every fourth character.
    formatting_string = f"{{:0{result_width}_b}}"
    result = formatting_string.format(value)
    assert len(result) == result_width

    return result


def to_hex_string(value: int, result_width_bits: int) -> str:
    """
    Convert unsigned integer value to a zero-padded string of 01ABCDEF.
    Most significant bit is the first (left-most) character in the string.

    For example, value 60, width 6, returns ``3C``.
    For example, value 60, width 9, returns ``03C``.

    Arguments:
        value: The value to be converted.
        result_width_bits: The supplied ``value`` will be interpreted as an unsigned value with
            this many bits.
            The result string will contain enough hex characters to represent this many
            bits (rounded up).
    """
    _check_unsigned_range(value=value, width=result_width_bits)

    result_width_nibbles = (result_width_bits + 4 - 1) // 4

    # Cast to hex, pad with zeros on the left.
    formatting_string = f"{{:0{result_width_nibbles}X}}"
    result = formatting_string.format(value)
    assert len(result) == result_width_nibbles

    return result


def to_hex_byte_string(value: int, result_width_bits: int) -> str:
    """
    Convert unsigned integer value to a zero-padded string of 01ABCDEF, with each byte
    (8 bits, 2 result characters) separated by "_".
    Most significant bit is the first (left-most) character in the string.

    For example, value 60, width 6, returns ``3C``.
    For example, value 60, width 9, returns ``0_3C``.

    Arguments:
        value: The value to be converted.
        result_width_bits: The supplied ``value`` will be interpreted as an unsigned value with
            this many bits.
            The result string will contain enough hex characters to represent this many
            bits (rounded up), plus separators.
    """
    hex_string = to_hex_string(value=value, result_width_bits=result_width_bits)

    result_width_nibbles = (result_width_bits + 4 - 1) // 4
    assert len(hex_string) % result_width_nibbles == 0, hex_string

    byte_strings = []
    if result_width_nibbles % 2 == 1:
        byte_strings.append(hex_string[0])
    for i in range(result_width_nibbles % 2, result_width_nibbles, 2):
        byte_strings.append(hex_string[i : i + 2])

    result = "_".join(byte_strings)

    result_width_bytes = (result_width_bits + 8 - 1) // 8
    num_separators = result_width_bytes - 1
    result_width = result_width_nibbles + num_separators
    assert len(result) == result_width, result

    return result


def _check_unsigned_range(value: int, width: int) -> None:
    if width < 1:
        raise ValueError(f'Invalid result width "{width}".')

    if not 0 <= value < 2**width:
        raise ValueError(f'Value "{value}" out of {width}-bit range.')
