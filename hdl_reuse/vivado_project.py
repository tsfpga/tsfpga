from os import makedirs
from os.path import join, exists

from hdl_reuse import HDL_REUSE_TCL
from hdl_reuse.constraints import Constraint
from hdl_reuse.vivado_tcl import VivadoTcl
from hdl_reuse.vivado_utils import run_vivado_tcl


class VivadoProject:
    """
    Used for handling a Xilinx Vivado HDL project
    """

    def __init__(  # pylint: disable=too-many-arguments
            self,
            name,
            modules,
            part,
            top=None,
            vivado_path=None,
            constraints=None,
    ):
        self.name = name
        self.modules = modules
        self.part = part

        self.top = name + "_top" if top is None else top
        self.vivado_path = "vivado" if vivado_path is None else vivado_path  # Default: Whatever version/location is in PATH will be used

        self.constraints = [] if constraints is None else constraints
        self._setup_constraints_list()

        self.tcl = VivadoTcl(name=self.name, modules=self.modules, part=self.part, top=self.top, constraints=self.constraints)

    def _setup_constraints_list(self):
        file = join(HDL_REUSE_TCL, "constrain_clock_crossings.tcl")
        self.constraints.append(Constraint(file))

        for module in self.modules:
            for constraint in module.get_entity_constraints():
                self.constraints.append(constraint)

    def create_tcl(self, project_path):
        """
        Make a TCL file that creates a Vivado project
        """
        if exists(project_path):
            raise ValueError("Folder already exists: " + project_path)
        makedirs(project_path)

        create_vivado_project_tcl = join(project_path, "create_vivado_project.tcl")
        with open(create_vivado_project_tcl, "w") as file_handle:
            file_handle.write(self.tcl.create(project_path))

        return create_vivado_project_tcl

    def create(self, project_path):
        """
        Create a Vivado project
        """
        create_vivado_project_tcl = self.create_tcl(project_path)
        run_vivado_tcl(self.vivado_path, create_vivado_project_tcl)

    def build_tcl(self, project_path, synth_only, num_threads, output_path):
        """
        Make a TCL file that builds a Vivado project
        """
        project = join(project_path, self.name + ".xpr")
        if not exists(project):
            raise ValueError("Project file does not exist in the specified location: " + project)

        build_vivado_project_tcl = join(project_path, "build_vivado_project.tcl")
        with open(build_vivado_project_tcl, "w") as file_handle:
            file_handle.write(self.tcl.build(project, synth_only, num_threads, output_path))

        return build_vivado_project_tcl

    def build(self, project_path, output_path=None, synth_only=False, num_threads=12):
        """
        Build a Vivado project
        """
        if output_path is None and not synth_only:
            raise ValueError("Must specify output_path when doing an implementation run")

        build_vivado_project_tcl = self.build_tcl(project_path, synth_only, num_threads, output_path)
        run_vivado_tcl(self.vivado_path, build_vivado_project_tcl)
