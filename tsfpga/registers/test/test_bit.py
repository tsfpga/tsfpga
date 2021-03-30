# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from tsfpga.registers.bit import Bit


def test_repr():
    # Check that repr is an actual representation, not just "X object at 0xABCDEF"
    assert "apa" in repr(Bit(name="apa", index=0, description=""))

    # Different name
    assert repr(Bit(name="apa", index=0, description="Blah")) != repr(
        Bit(name="hest", index=0, description="Blah")
    )

    # Different index
    assert repr(Bit(name="apa", index=0, description="Blah")) != repr(
        Bit(name="apa", index=1, description="Blah")
    )

    # Different description
    assert repr(Bit(name="apa", index=0, description="Blah")) != repr(
        Bit(name="apa", index=0, description="Gaah")
    )

    # Different width
    assert repr(Bit(name="apa", index=0, width=10, description="Blah")) != repr(
        Bit(name="apa", index=0, width=9, description="Blah")
    )

    assert repr(Bit(name="apa", index=0, description="Blah")) != repr(
        Bit(name="apa", index=0, width=4, description="Blah")
    )

    assert "index=[4:0]" in repr(Bit(name="apa", index=0, width=5, description=""))
    assert "index=[17:5]" in repr(Bit(name="apa", index=5, width=13, description=""))
    assert "index=[31:0]" in repr(Bit(name="apa", index=0, width=32, description=""))
