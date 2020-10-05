# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


class Bit:

    """
    Used to represent a bit in a register.
    """

    def __init__(self, name, index, description):
        """
        Arguments:
            name (str): The name of the bit.
            index (int): The zero-based index of this bit within the register.
            description (str): Textual bit description.
        """
        self.name = name
        self.index = index
        self.description = description

    def __repr__(self):
        return f"""{self.__class__.__name__}(\
name={self.name},\
index={self.index},\
description={self.description},
)"""
