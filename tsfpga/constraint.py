# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import basename, splitext


class Constraint:
    """
    Class for handling a constraint file.

    Can handle the regular global constraint files as well as scoped constraints.
    For the latter to work the constraint file name must be the same as the module file name, which must the same as entity name.
    """

    def __init__(self, file, used_in="all", scoped_constraint=False, processing_order="normal"):
        self.file = file
        self.used_in = used_in
        self.ref = splitext(basename(file))[0] if scoped_constraint else None
        self.processing_order = processing_order.lower()

        assert self.used_in in ["all", "synth", "impl"], self.used_in
        assert self.processing_order in ["early", "normal", "late"], self.processing_order

    def validate_scoped_entity(self, source_files):
        """
        Make sure that a matching entity file exists in case this is a scoped constraint. The list of source files should be
        the synthesis files for the module that this constraint belongs to.
        """
        if self.ref is not None:
            entity_file_name = self.ref + ".vhd"
            if not any([source_file.filename.endswith(entity_file_name)] for source_file in source_files):
                raise FileNotFoundError(f"Could not find a matching entity file {entity_file_name} for constraint file {self.file}")
        return True

    def __str__(self):
        return self.file
