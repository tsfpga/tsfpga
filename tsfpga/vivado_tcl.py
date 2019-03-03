from os.path import join

from tsfpga.vivado_utils import to_tcl_path


class VivadoTcl:
    """
    Class with methods for translating a set of sources into Vivado TCL
    """

    def __init__(  # pylint: disable=too-many-arguments
            self,
            name,
            modules,
            part,
            top,
            tcl_sources,
            generics,
            constraints,
    ):
        self.name = name
        self.modules = modules
        self.part = part
        self.top = top
        self.tcl_sources = tcl_sources
        self.generics = generics
        self.constraints = constraints

    def _add_modules(self):
        tcl = ""
        for module in self.modules:
            if module.get_synthesis_files():
                file_list_str = " ".join([to_tcl_path(file) for file in module.get_synthesis_files()])
                tcl += "read_vhdl -library %s -vhdl2008 {%s}\n" % (module.library_name, file_list_str)
            for tcl_source_file in module.get_ip_core_files():
                tcl += "source -notrace %s\n" % to_tcl_path(tcl_source_file)
        return tcl

    def _add_tcl_sources(self):
        tcl = ""
        for tcl_source_file in self.tcl_sources:
            tcl += "source -notrace %s\n" % to_tcl_path(tcl_source_file)
        return tcl

    def _add_generics(self):
        """
        Generics are set accoring to this weird format: https://www.xilinx.com/support/answers/52217.html
        """
        if self.generics is None:
            return ""

        generic_list = []
        for name, value in self.generics.items():
            if isinstance(value, bool):
                generic_list.append("%s=%s" % (name, ("1'b1" if value else "1'b0")))
            else:
                generic_list.append("%s=%s" % (name, value))
        return "set_property generic {%s} [current_fileset]\n" % " ".join(generic_list)

    def _iterate_constraints(self):
        for module in self.modules:
            for constraint in module.get_scoped_constraints():
                yield constraint

        for constraint in self.constraints:
            yield constraint

    def _add_constraints(self):
        tcl = ""
        for constraint in self._iterate_constraints():
            file = to_tcl_path(constraint.file)
            ref_flags = "" if constraint.ref is None else (f"-ref {constraint.ref} ")
            managed_flags = "" if file.endswith("xdc") else "-unmanaged "

            tcl += f"read_xdc {ref_flags}{managed_flags}{file}\n"
            tcl += f"set_property PROCESSING_ORDER {constraint.processing_order} [get_files {file}]\n"

            if constraint.used_in == "impl":
                tcl += f"set_property used_in_synthesis false [get_files {file}]\n"
            elif constraint.used_in == "synth":
                tcl += f"set_property used_in_implementation false [get_files {file}]\n"

        return tcl

    def create(self, project_folder):
        tcl = "create_project %s %s -part %s\n" % (self.name, to_tcl_path(project_folder), self.part)
        tcl += "set_property target_language VHDL [current_project]\n"
        tcl += "\n"
        tcl += self._add_modules()
        tcl += "\n"
        tcl += self._add_tcl_sources()
        tcl += "\n"
        tcl += self._add_generics()
        tcl += "\n"
        tcl += self._add_constraints()
        tcl += "\n"
        tcl += "set_property top %s [current_fileset]\n" % self.top
        tcl += "reorder_files -auto -disable_unused\n"
        tcl += "\n"
        tcl += "exit\n"
        return tcl

    @staticmethod
    def _run(run, slack_less_than_requirement, timing_error_message):
        tcl = "reset_run %s\n" % run
        tcl += "launch_runs %s\n" % run
        tcl += "wait_on_run %s\n" % run
        tcl += "\n"
        tcl += "if {[get_property PROGRESS [get_runs %s]] != \"100%%\"} {\n" % run
        tcl += "  puts \"ERROR: Run %s failed.\"\n" % run
        tcl += "  exit 1\n"
        tcl += "}\n"
        tcl += "\n"
        tcl += "open_run %s\n" % run
        tcl += "if {[expr {[get_property SLACK [get_timing_paths -delay_type min_max]] < %i}]} {\n" % slack_less_than_requirement
        tcl += "  puts \"ERROR: %s\"\n" % timing_error_message
        tcl += "  exit 1\n"
        tcl += "}\n"
        return tcl

    def _synthesis(self, run):
        # -90 in slack timing check comes from the always failing -100 constraint applied to unhandled clock crossings
        tcl = self._run(run, -90, f"Timing not OK after {run} run. Probably due to an unhandled clock crossings.")
        return tcl

    def _impl(self, run):
        return self._run(run, 0, "Timing not OK after %s run." % run)

    def _bitstream(self, output_path):
        bit_file = to_tcl_path(join(output_path, self.name))  # Vivado will append the appropriate file ending
        tcl = "write_bitstream -force %s\n" % bit_file
        return tcl

    def _hwdef(self, output_path):
        # Vivado will append the wrong file ending (.hwdef) unless specified
        hwdef_file = to_tcl_path(join(output_path, self.name + ".hdf"))
        tcl = "write_hwdef -force %s\n" % hwdef_file
        return tcl

    def build(self, project_file, synth_only, num_threads, output_path):
        synth_run = "synth_1"
        impl_run = "impl_1"
        num_threads = min(num_threads, 8)  # Max value in Vivado 2017.4. set_param will give an error if higher number.

        tcl = "open_project %s\n" % to_tcl_path(project_file)
        tcl += "set_param general.maxThreads %i\n" % num_threads
        tcl += "\n"
        tcl += self._synthesis(synth_run)
        tcl += "\n"
        if not synth_only:
            tcl += self._impl(impl_run)
            tcl += "\n"
            tcl += self._bitstream(output_path)
            tcl += self._hwdef(output_path)
            tcl += "\n"
        tcl += "exit\n"
        return tcl
