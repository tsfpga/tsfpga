# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from tsfpga.registers.register_array import RegisterArray


def test_registers_are_appended_properly_and_can_be_edited_in_place():
    register_array = RegisterArray(name="apa", base_index=0, length=4)

    register_hest = register_array.append_register(name="hest", mode="r")
    assert register_hest.index == 0

    register_zebra = register_array.append_register(name="zebra", mode="r")
    assert register_zebra.index == 1

    register_hest.description = "new desc"
    assert register_array.registers[0].description == "new desc"


def test_repr_basic():
    # Check that repr is an actual representation, not just "X object at 0xABCDEF"
    assert "apa" in repr(RegisterArray(name="apa", base_index=0, length=4))

    # Different name
    assert repr(RegisterArray(name="apa", base_index=0, length=4)) != repr(
        RegisterArray(name="hest", base_index=0, length=4)
    )

    # Different base_index
    assert repr(RegisterArray(name="apa", base_index=0, length=4)) != repr(
        RegisterArray(name="apa", base_index=8, length=4)
    )

    # Different length
    assert repr(RegisterArray(name="apa", base_index=0, length=4)) != repr(
        RegisterArray(name="apa", base_index=0, length=8)
    )


def test_repr_with_registers_appended():
    register_array_a = RegisterArray(name="apa", base_index=0, length=4)
    register_array_a.append_register(name="hest", mode="r")

    register_array_b = RegisterArray(name="apa", base_index=0, length=4)
    register_array_b.append_register(name="hest", mode="r")

    assert repr(register_array_a) == repr(register_array_b)

    register_array_a.append_register(name="zebra", mode="w")
    register_array_b.append_register(name="zebra", mode="r_w")

    assert repr(register_array_a) != repr(register_array_b)
