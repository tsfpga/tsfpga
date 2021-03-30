# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


class Bit:

    """
    Used to represent a bit array in a register.
    """

    def __init__(self, name, index, description, width=1, default_value=None):
        """
        Arguments:
            name (str): The name of the bit array.
            index (int): The zero-based index of this bit array within the register.
            width (int) : The width of the bit field.
            description (str): Textual bit array description.
        """
        self.name = name
        self.index = index
        self.width = width
        self.description = description
        self.default_value = default_value

    @property
    def bit_range(self):
        if self.width > 1:
            return f"[{self.width + self.index - 1}:{self.index}]"
        return self.index

    def __repr__(self):
        return f"""{self.__class__.__name__}(\
name={self.name},\
index={self.bit_range},\
width={self.width},\
description={self.description},
)"""
