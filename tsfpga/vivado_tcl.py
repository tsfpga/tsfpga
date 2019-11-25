# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import join

from tsfpga.vivado_utils import to_tcl_path


class VivadoTcl:
    """
    Class with methods for translating a set of sources into Vivado TCL
    """

    def __init__(self, name,):
        self.name = name

    @staticmethod
    def _add_modules(modules):
        tcl = ""
        for module in modules:
            vhdl_files = []
            verilog_source_files = []
            for hdl_file in module.get_synthesis_files():
                if hdl_file.is_vhdl:
                    vhdl_files.append(to_tcl_path(hdl_file.filename))
                elif hdl_file.is_verilog_source:
                    verilog_source_files.append(to_tcl_path(hdl_file.filename))
                else:
                    raise NotImplementedError("Can not handle file: " + hdl_file.filename)
                    # Verilog headers do not need to be handled at all if the
                    # source file that uses them is in the same directory. If
                    # it is not, the path needs to be added to include_dirs with
                    # a tcl command like:
                    #   set_property include_dirs {/some/path /some/other/path} [current_fileset]
                    # See https://www.xilinx.com/support/answers/54006.html

                    # Encrypted source files (verilog (.vp?), VHDL) I do not know how
                    # to handle, since I have no use case for it at the moment.

            if vhdl_files:
                tcl += "read_vhdl -library %s -vhdl2008 {%s}\n" % \
                    (module.library_name, " ".join(vhdl_files))
            if verilog_source_files:
                tcl += "read_verilog {%s}\n" % " ".join(verilog_source_files)

            for tcl_source_file in module.get_ip_core_files():
                tcl += "source -notrace %s\n" % to_tcl_path(tcl_source_file)
        return tcl

    @staticmethod
    def _add_tcl_sources(tcl_sources):
        tcl = ""
        for tcl_source_file in tcl_sources:
            tcl += "source -notrace %s\n" % to_tcl_path(tcl_source_file)
        return tcl

    @staticmethod
    def _add_generics(generics):
        """
        Generics are set accoring to this weird format: https://www.xilinx.com/support/answers/52217.html
        """
        if generics is None:
            return ""

        generic_list = []
        for name, value in generics.items():
            if isinstance(value, bool):
                generic_list.append("%s=%s" % (name, ("1'b1" if value else "1'b0")))
            else:
                generic_list.append("%s=%s" % (name, value))
        return "set_property generic {%s} [current_fileset]\n" % " ".join(generic_list)

    @staticmethod
    def _iterate_constraints(modules, constraints):
        for module in modules:
            for constraint in module.get_scoped_constraints():
                yield constraint

        for constraint in constraints:
            yield constraint

    @staticmethod
    def _add_constraints(constraints):
        tcl = ""
        for constraint in constraints:
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

    # pylint: disable=too-many-arguments
    def create(self,
               part,
               modules,
               top,
               tcl_sources,
               generics,
               constraints,
               project_folder,
               ip_cache_path):
        tcl = f"create_project {self.name} {to_tcl_path(project_folder)} -part {part}\n"
        tcl += "set_property target_language VHDL [current_project]\n"
        if ip_cache_path is not None:
            tcl += f"config_ip_cache -use_cache_location {to_tcl_path(ip_cache_path)}\n"
        # Default value for when opening project in GUI. Will be overwritten if using build() function.
        tcl += "set_param general.maxThreads 4\n"
        tcl += "\n"
        tcl += self._add_modules(modules)
        tcl += "\n"
        tcl += self._add_tcl_sources(tcl_sources)
        tcl += "\n"
        tcl += self._add_generics(generics)
        tcl += "\n"
        all_constraints = self._iterate_constraints(modules, constraints)
        tcl += self._add_constraints(all_constraints)
        tcl += "\n"
        tcl += f"set_property top {top} [current_fileset]\n"
        tcl += "reorder_files -auto -disable_unused\n"
        tcl += "\n"
        tcl += "exit\n"
        return tcl

    @staticmethod
    def _run(run, num_threads):
        tcl = f"reset_run {run}\n"
        tcl += f"launch_runs {run} -jobs {num_threads}\n"
        tcl += "wait_on_run %s\n" % run
        tcl += "\n"
        tcl += "if {[get_property PROGRESS [get_runs %s]] != \"100%%\"} {\n" % run
        tcl += f"  puts \"ERROR: Run {run} failed.\"\n"
        tcl += "  exit 1\n"
        tcl += "}\n"
        tcl += "\n"
        tcl += f"open_run {run}\n"
        tcl += f"set run_directory [get_property DIRECTORY [get_runs {run}]]\n"
        return tcl

    def _check_clock_interaction(self, run):
        tcl = r"if {[regexp {\(unsafe\)} [report_clock_interaction -delay_type min_max -return_string]]} "
        tcl += "{\n"
        tcl += f"  puts \"ERROR: Unhandled clock crossing in {run} run. See reports in ${{run_directory}}\"\n"
        tcl += "\n"
        tcl += self._save_clock_interaction_report()
        tcl += self._save_timing_report()
        tcl += "\n"
        tcl += "  exit 1\n"
        tcl += "}\n"
        return tcl

    @staticmethod
    def _save_clock_interaction_report():
        tcl = "set output_file [file join ${run_directory} \"clock_interaction.rpt\"]\n"
        tcl += "report_clock_interaction -delay_type min_max -file ${output_file}\n"
        return tcl

    @staticmethod
    def _save_timing_report():
        tcl = "set output_file [file join ${run_directory} \"timing_summary.rpt\"]\n"
        tcl += "report_timing_summary -file ${output_file}\n"
        return tcl

    def _check_timing(self, run):
        tcl = "if {[expr {[get_property SLACK [get_timing_paths -delay_type min_max]] < 0}]} {\n"
        tcl += f"  puts \"ERROR: Timing not OK after {run} run. See reports in ${{run_directory}}\"\n"
        tcl += "\n"
        tcl += self._save_timing_report()
        tcl += "\n"
        tcl += "  exit 1\n"
        tcl += "}\n"
        return tcl

    @staticmethod
    def _report_utilization():
        tcl = "set output_file [file join ${run_directory} \"hierarchical_utilization.rpt\"]\n"
        tcl += "report_utilization -hierarchical -hierarchical_depth 4 -file ${output_file}\n"
        return tcl

    def _synthesis(self, run, num_threads):
        tcl = self._run(run, num_threads)
        tcl += "\n"
        tcl += self._report_utilization()
        tcl += "\n"
        tcl += self._check_clock_interaction(run)
        return tcl

    def _impl(self, run, num_threads):
        tcl = self._run(run, num_threads)
        tcl += "\n"
        tcl += self._report_utilization()
        tcl += "\n"
        tcl += self._check_timing(run)
        return tcl

    def _bitstream(self, output_path):
        bit_file = to_tcl_path(join(output_path, self.name))  # Vivado will append the appropriate file ending
        tcl = f"write_bitstream -force -bin {bit_file}\n"
        return tcl

    def _hwdef(self, output_path):
        # Vivado will append the wrong file ending (.hwdef) unless specified
        hwdef_file = to_tcl_path(join(output_path, self.name + ".hdf"))
        tcl = "write_hwdef -force %s\n" % hwdef_file
        return tcl

    def build(self, project_file, generics, output_path, synth_only, num_threads):
        synth_run = "synth_1"
        impl_run = "impl_1"
        num_threads = min(num_threads, 8)  # Max value in Vivado 2017.4. set_param will give an error if higher number.

        tcl = f"open_project {to_tcl_path(project_file)}\n"
        tcl += f"set_param general.maxThreads {num_threads}\n"
        tcl += "\n"
        tcl += self._add_generics(generics)
        tcl += "\n"
        tcl += self._synthesis(synth_run, num_threads)
        tcl += "\n"
        if not synth_only:
            tcl += self._impl(impl_run, num_threads)
            tcl += "\n"
            tcl += self._bitstream(output_path)
            tcl += self._hwdef(output_path)
            tcl += "\n"
        tcl += "exit\n"
        return tcl
