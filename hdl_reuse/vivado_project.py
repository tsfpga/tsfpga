from os import makedirs
from os.path import join, exists
from hdl_reuse.vivado_utils import run_vivado_tcl


class VivadoProject:
    """
    Used for handling a Xilinx Vivado HDL project
    """

    def __init__(
            self,
            name,
            modules,
            part,
            vivado_path,
            constraints,
    ):
        self.name = name
        self.modules = modules
        self.part = part
        self.vivado_path = vivado_path
        self.constraints = constraints

    def _create_tcl(self, project_path):
        tcl = "create_project %s %s -part %s\n" % (self.name, project_path, self.part)
        tcl += "set_property target_language VHDL [current_project]\n"
        tcl += "\n"
        tcl += self._add_modules_tcl()
        tcl += "\n"
        tcl += self._add_constraints_tcl()
        tcl += "\n"
        tcl += "set_property top %s_top [current_fileset]\n" % self.name
        tcl += "reorder_files -auto -disable_unused\n"
        return tcl

    def _add_modules_tcl(self):
        tcl = ""
        for module in self.modules:
            if module.get_synthesis_files():
                file_list_str = " ".join(module.get_synthesis_files())
                tcl += "add_files -norecurse {%s}\n" % file_list_str
                tcl += "set_property library %s [get_files {%s}]\n" % (module.library_name, file_list_str)
        return tcl

    def _add_constraints_tcl(self):
        tcl = ""
        for constraint_file in self.constraints:
            tcl += "read_xdc -unmanaged %s\n" % constraint_file
        return tcl

    def create_tcl(self, project_path):
        if exists(project_path):
            raise ValueError("Folder already exists: " + project_path)
        makedirs(project_path)

        create_vivado_project_tcl = join(project_path, "create_vivado_project.tcl")
        with open(create_vivado_project_tcl, "w") as file_handle:
            file_handle.write(self._create_tcl(project_path))

        return create_vivado_project_tcl

    def create(self, project_path):
        create_vivado_project_tcl = self.create_tcl(project_path)
        run_vivado_tcl(self.vivado_path, create_vivado_project_tcl)

    def build(self, output_path):
        pass
