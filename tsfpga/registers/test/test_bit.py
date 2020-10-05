# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

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
