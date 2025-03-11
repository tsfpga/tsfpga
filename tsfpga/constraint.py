# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pathlib import Path

    from .hdl_file import HdlFile


class Constraint:
    """
    Class for handling a constraint file.

    Can handle the regular global constraint files as well as scoped constraints.
    For the latter to work the constraint file name must be the same as the .vhd file name,
    which must be the same as the entity name.
    """

    def __init__(
        self,
        file: Path,
        used_in_synthesis: bool = True,
        used_in_implementation: bool = True,
        used_in: Literal["all", "synth", "impl"] | None = None,
        scoped_constraint: bool = False,
        processing_order: Literal["early", "normal", "late"] = "normal",
    ) -> None:
        """
        Arguments:
            file: Path to the constraint file. Typically ends in .xdc or .tcl.
            used_in_synthesis: Optionally disable the constraint for synthesis.
            used_in_implementation: Optionally disable the constraint for implementation.
            used_in: Old way of controlling when the constraint is applied.

                .. deprecated:: 13.1.3
                    Use the `used_in_synthesis` and `used_in_implementation` arguments instead.
            scoped_constraint: If enabled the constraint file will be loaded with the "-ref"
                argument in Vivado. An entity with the same name must exist.
            processing_order: Optionally the processing order can be changed to "early" or "late".
        """
        self.file = file
        self.ref = file.stem if scoped_constraint else None
        self.processing_order = processing_order.lower()

        if used_in is not None:
            print(
                f"DEPRECATED: {self.__class__.__name__}.__init__() argument 'used_in' is "
                "deprecated and will be removed."
            )
            if (not used_in_synthesis) or (not used_in_implementation):
                raise ValueError("Using both 'used_in_*' and deprecated 'used_in' arguments.")

            self.used_in_synthesis = used_in in ("all", "synth")
            self.used_in_implementation = used_in in ("all", "impl")
        else:
            self.used_in_synthesis = used_in_synthesis
            self.used_in_implementation = used_in_implementation

    def validate_scoped_entity(self, source_files: list[HdlFile]) -> bool:
        """
        Make sure that a matching entity file exists in case this is a scoped constraint.
        The list of source files should be the synthesis files for the module that this
        constraint belongs to.
        """
        if self.ref is not None and not any(
            [source_file.path.stem == self.ref] for source_file in source_files
        ):
            raise FileNotFoundError(
                f"Could not find a matching entity file for scoped constraint file {self.file}"
            )

        return True

    def __str__(self) -> str:
        return str(self.file)
