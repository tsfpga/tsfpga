# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import copy
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    # Local folder libraries
    from .module import BaseModule


class ModuleList:
    """
    Wrapper for a list of modules, with convenience functions.
    """

    def __init__(self) -> None:
        self._modules: list["BaseModule"] = []

    def append(self, module: "BaseModule") -> None:
        """
        Append a module to the list.
        """
        self._modules.append(module)

    def get(self, module_name: "str") -> "BaseModule":
        """
        Get the module with the specified name. If no module matched, an exception is raised.
        """
        for module in self._modules:
            if module.name == module_name:
                return module

        raise ValueError(f'No module "{module_name}" available')

    def __iter__(self) -> Iterator["BaseModule"]:
        return iter(self._modules)

    def __getitem__(self, index: int) -> "BaseModule":
        return self._modules[index]

    def __len__(self) -> int:
        return len(self._modules)

    def __add__(self, other: "ModuleList") -> "ModuleList":
        if not isinstance(other, self.__class__):
            raise TypeError(f"Can only concatenate with another {self.__class__.__name__}")

        # Note that the list concatenation implies a shallow copy of the lists
        result = self.__class__()
        result._modules = self._modules + other._modules
        return result

    def __copy__(self) -> "ModuleList":
        result = self.__class__()
        result._modules = self._modules.copy()
        return result

    def copy(self) -> "ModuleList":
        """
        Create a shallow copy of the module list. This public function is available as a
        convenience and to mimic the interface of a regular python list.
        """
        return copy.copy(self)

    def __str__(self) -> str:
        return str(self._modules)
