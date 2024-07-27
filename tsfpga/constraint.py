# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Local folder libraries
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
        used_in: str = "all",
        scoped_constraint: bool = False,
        processing_order: str = "normal",
    ) -> None:
        """
        Arguments:
            file: Path to the constraint file. Typically ends in .xdc or .tcl.
            used_in: Optionally the constraint can be enabled only for "synth" or "impl".
            scoped_constraint: If enabled the constraint file will be loaded with the "-ref"
                argument in Vivado. An entity with the same name must exist.
            processing_order: Optionally the processing order can be changed to "early" or "late".
        """
        self.file = file
        self.used_in = used_in
        self.ref = file.stem if scoped_constraint else None
        self.processing_order = processing_order.lower()

        assert self.used_in in ["all", "synth", "impl"], self.used_in
        assert self.processing_order in ["early", "normal", "late"], self.processing_order

    def validate_scoped_entity(self, source_files: list["HdlFile"]) -> bool:
        """
        Make sure that a matching entity file exists in case this is a scoped constraint.
        The list of source files should be the synthesis files for the module that this
        constraint belongs to.
        """
        if self.ref is not None:
            if not any([source_file.path.stem == self.ref] for source_file in source_files):
                raise FileNotFoundError(
                    f"Could not find a matching entity file for scoped constraint file {self.file}"
                )
        return True

    def __str__(self) -> str:
        return str(self.file)
