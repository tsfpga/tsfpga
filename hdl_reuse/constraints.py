from os.path import basename, join, exists, splitext, dirname


class EntityConstraint:
    """
    Class for handling constraints that will be applied to an entity.
    This function is dependent on the constraint file name being the same as module file name being the same as entity name.
    """

    def __init__(self, file, used_in):
        self.file = file
        self.name = splitext(basename(file))[0]
        self.used_in = used_in

        self._valiate()

    def _valiate(self):
        entity_file = join(dirname(self.file), "..", self.name + ".vhd")
        assert self.used_in in ["all", "impl"], self.used_in
        assert exists(entity_file), "Could not find a matching entity file %s for constraint file %s" % (entity_file, self.file)

    def load_tcl(self):
        """
        The TCL snippet that loads this constraint file.
        """
        tcl = "read_xdc -ref %s -unmanaged %s\n" % (self.name, self.file)
        if self.used_in == "impl":
            tcl += "set_property used_in_synthesis false [get_files %s]\n" % self.file
        return tcl
