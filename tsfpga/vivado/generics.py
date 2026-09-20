# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

# 'StringGenericValue' and 'BitVectorGenericValue' are generic, backend-agnostic types (used by
# e.g. 'tsfpga.yosys.project' as well) that historically lived in this module. They are now
# defined in 'tsfpga.generics', and re-exported here for backward compatibility.
from tsfpga.generics import BitVectorGenericValue, GenericValue, StringGenericValue


def get_vivado_tcl_generic_value(
    value: GenericValue,
) -> str:
    """
    Convert generic values of different types to the format recognized by Vivado TCL:
    https://www.xilinx.com/support/answers/52217.html

    Arguments:
        value: A generic value of native Python type..

    Return:
        The ``value`` formatted as TCL.
    """
    # Note that bool is a sub-class of int in Python, so check for bool must be first
    if isinstance(value, bool):
        return f"1'b{int(value)}"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        return str(value)

    if isinstance(value, BitVectorGenericValue):
        return f"{value.length}'b{value.value}"

    if isinstance(value, StringGenericValue):
        return f'"{value.value}"'

    message = f'Unsupported type for generic. Got type="{type(value)}", value="{value}".'

    # When the type is a string, we can be a little more helpful and indicate what types shall
    # be used instead.
    if isinstance(value, str):
        message += (
            " Please use either of the explicit types StringGenericValue or BitVectorGenericValue."
        )

    raise TypeError(message)
