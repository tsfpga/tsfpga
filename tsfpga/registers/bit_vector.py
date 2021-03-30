# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from .register_field import RegisterField


class BitVector(RegisterField):

    """
    Used to represent a bit vector field in a register.
    """

    def __init__(self, name, base_index, description, width, default_value):
        """
        Arguments:
            name (str): The name of the bit vector.
            base_index (int): The zero-based index within the register for the lowest bit of this
                bit vector.
            description (str): Textual bit vector description.
            width (int) : The width of the bit vector field.
            default_value (str): Default value as a string. Must be of length ``width`` and contain
                only "1" and "0".
        """
        self.name = name
        self.base_index = base_index
        self.description = description

        self._width = None
        # Assign self._width via setter.
        self.width = width

        self._default_value = None
        # Assign self.default_value via setter
        self.default_value = default_value

    @property
    def width(self):
        """
        Getter for width.
        """
        return self._width

    @width.setter
    def width(self, value):
        """
        Setter for width that performs sanity checks.
        """
        if self._width is not None:
            message = f'Bit vector "{self.name}" changing "width" is not allowed. Got: "{value}".'
            raise ValueError(message)

        if not isinstance(value, int):
            message = (
                f'Bit vector "{self.name}" should have integer value for "width". Got: "{value}".'
            )
            raise ValueError(message)

        if value < 1 or value > 32:
            raise ValueError(f'Invalid bit vector width for "{self.name}". Got: "{value}".')

        self._width = value

    @property
    def default_value(self):
        """
        Getter for default_value.
        """
        return self._default_value

    @default_value.setter
    def default_value(self, value):
        """
        Setter for default_value that performs sanity checks.
        """
        if not isinstance(value, str):
            message = (
                f'Bit vector "{self.name}" should have string value for "default_value". '
                f'Got: "{value}"'
            )
            raise ValueError(message)

        if len(value) != self.width:
            message = (
                f'Bit vector "{self.name}" should have "default_value" of length {self.width}. '
                f'Got: "{value}".'
            )
            raise ValueError(message)

        for character in value:
            if character not in ["0", "1"]:
                message = (
                    f'Bit vector "{self.name}" invalid binary value for "default_value". '
                    f'Got: "{value}".'
                )
                raise ValueError(message)

        self._default_value = value

    @property
    def range(self):
        return f"{self.base_index + self.width - 1}:{self.base_index}"

    @property
    def default_value_str(self):
        return f"0b{self.default_value}"

    @property
    def default_value_uint(self):
        return int(self.default_value, base=2)

    def __repr__(self):
        return f"""{self.__class__.__name__}(\
name={self.name},\
base_index={self.base_index},\
description={self.description},
width={self.width},\
default_value={self.default_value},\
)"""
