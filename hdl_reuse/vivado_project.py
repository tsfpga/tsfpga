from os import makedirs
from os.path import join, exists
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
            vivado_path="vivado",  # Whatever Vivado version/location is in PATH will be used
            constraints=None,
    ):
        self.name = name
        self.modules = modules
        self.part = part
        self.vivado_path = vivado_path
        self.constraints = [] if constraints is None else constraints

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

    @staticmethod
    def _launch_and_wait_on_run_tcl(run):
        tcl = "launch_runs %s\n" % (run)
        tcl += "wait_on_run %s\n" % run
        return tcl

    def _launch_and_check_run_tcl(self, run):
        tcl = self._launch_and_wait_on_run_tcl(run)
        tcl += "if {[get_property PROGRESS [get_runs %s]] != \"100%%\"} {\n" % run
        tcl += "  puts \"ERROR: Run %s failed\"\n" % run
        tcl += "  exit 1\n"
        tcl += "}\n"
        return tcl

    def _synthesis_tcl(self, run):
        return self._launch_and_check_run_tcl(run)

    def _impl_tcl(self, run):
        tcl = self._launch_and_check_run_tcl(run)
        tcl += "\n"
        tcl += "open_run %s\n" % run
        tcl += "if {[expr {[get_property SLACK [get_timing_paths -delay_type min_max]] < 0}]} {\n"
        tcl += "  puts \"ERROR: Timing not OK after %s run\"\n" % run
        tcl += "  exit 1\n"
        tcl += "}\n"
        return tcl

    def _bitstream_tcl(self, output_path):
        bit_file = join(output_path, self.name)  # Vivado will append the appropriate file ending
        tcl = "write_bitstream %s\n" % bit_file
        return tcl

    def _build_tcl(self, project, synth_only, num_threads, output_path):
        synth_run = "synth_1"
        impl_run = "impl_1"
        num_threads = 8 if num_threads > 8 else num_threads  # Max value in Vivado 2017.4. set_param will give an error if higher number.

        tcl = "open_project %s\n" % project
        tcl += "set_param general.maxThreads %i\n" % num_threads
        tcl += "\n"
        tcl += self._synthesis_tcl(synth_run)
        tcl += "\n"
        if not synth_only:
            tcl += self._impl_tcl(impl_run)
            tcl += "\n"
            tcl += self._bitstream_tcl(output_path)
        return tcl

    def build_tcl(self, project_path, synth_only, num_threads, output_path):
        project = join(project_path, self.name + ".xpr")
        if not exists(project):
            raise ValueError("Project file does not exist in the specified location: " + project)

        build_vivado_project_tcl = join(project_path, "build_vivado_project.tcl")
        with open(build_vivado_project_tcl, "w") as file_handle:
            file_handle.write(self._build_tcl(project, synth_only, num_threads, output_path))

        return build_vivado_project_tcl

    def build(self, project_path, output_path=None, synth_only=False, num_threads=12):
        if output_path is None and not synth_only:
            raise ValueError("Must specify output_path when doing an implementation run")

        build_vivado_project_tcl = self.build_tcl(project_path, synth_only, num_threads, output_path)
        run_vivado_tcl(self.vivado_path, build_vivado_project_tcl)
