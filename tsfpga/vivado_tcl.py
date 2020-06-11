# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.vivado_utils import to_tcl_path
from tsfpga.system_utils import create_file


class VivadoTcl:
    """
    Class with methods for translating a set of sources into Vivado TCL
    """

    def __init__(self, name,):
        self.name = name

    # pylint: disable=too-many-arguments
    def create(self,
               project_folder,
               modules,
               part,
               top,
               run_index,
               generics=None,
               constraints=None,
               tcl_sources=None,
               build_step_hooks=None,
               ip_cache_path=None,
               disable_io_buffers=True):
        tcl = f"create_project {self.name} {to_tcl_path(project_folder)} -part {part}\n"
        tcl += "set_property target_language VHDL [current_project]\n"
        if ip_cache_path is not None:
            tcl += f"config_ip_cache -use_cache_location {to_tcl_path(ip_cache_path)}\n"
        tcl += "\n"
        tcl += self._add_modules(modules)
        tcl += "\n"
        tcl += self._add_generics(generics)
        tcl += "\n"
        tcl += self._add_constraints(self._iterate_constraints(modules, constraints))
        tcl += "\n"
        tcl += self._add_tcl_sources(tcl_sources)
        tcl += "\n"
        tcl += self._add_build_step_hooks(build_step_hooks, project_folder)
        tcl += "\n"
        tcl += self._add_project_settings()
        tcl += "\n"
        tcl += f"current_run [get_runs synth_{run_index}]\n"
        tcl += "\n"
        tcl += f"set_property top {top} [current_fileset]\n"
        tcl += "reorder_files -auto -disable_unused\n"
        tcl += "\n"
        if disable_io_buffers:
            tcl += f"set_property -name {{STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS}} -value -no_iobuf -objects [get_runs synth_{run_index}]"
        tcl += "\n"
        tcl += "exit\n"
        return tcl

    def _add_modules(self, modules):
        tcl = ""
        for module in modules:
            vhdl_files = []
            verilog_source_files = []
            for hdl_file in module.get_synthesis_files():
                if hdl_file.is_vhdl:
                    vhdl_files.append(to_tcl_path(hdl_file.path))
                elif hdl_file.is_verilog_source:
                    verilog_source_files.append(to_tcl_path(hdl_file.path))
                else:
                    raise NotImplementedError(f"Can not handle file: {hdl_file}")
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

            tcl += self._add_tcl_sources(module.get_ip_core_files())
        return tcl

    @staticmethod
    def _add_tcl_sources(tcl_sources):
        if tcl_sources is None:
            return ""

        tcl = ""
        for tcl_source_file in tcl_sources:
            tcl += "source -notrace %s\n" % to_tcl_path(tcl_source_file)
        return tcl

    def _add_build_step_hooks(self, build_step_hooks, project_folder):
        if build_step_hooks is None:
            return ""

        # There can be many hooks for the same step. Reorganize them into a dict, according
        # to the format step_name: [list of hooks]
        hook_steps = dict()
        for build_step_hook in build_step_hooks:
            if build_step_hook.hook_step in hook_steps:
                hook_steps[build_step_hook.hook_step].append(build_step_hook)
            else:
                hook_steps[build_step_hook.hook_step] = [build_step_hook]

        tcl = ""
        for step, hooks in hook_steps.items():
            # Vivado will only accept one TCL script as hook for each step. So if we want
            # to add more we have to create a new TCL file, that sources the other files,
            # and add that as the hook to Vivado.
            if len(hooks) == 1:
                tcl_file = hooks[0].tcl_file
            else:
                tcl_file = project_folder / ("hook_" + step.replace(".", "_") + ".tcl")
                source_hooks_tcl = "".join([f"source {to_tcl_path(hook.tcl_file)}\n" for hook in hooks])
                create_file(tcl_file, source_hooks_tcl)

            # Add to fileset to enable archive and other project based functionality
            tcl += f"add_files -fileset utils_1 -norecurse {to_tcl_path(tcl_file)}\n"

            # Build step hook can only be applied to a run (e.g. impl_1), not on a project basis
            run_wildcard = "synth_*" if hooks[0].step_is_synth else "impl_*"
            tcl_block = f"set_property {step} {to_tcl_path(tcl_file)} ${{run}}"
            tcl += self._tcl_for_each_run(run_wildcard, tcl_block)

        return tcl

    def _add_project_settings(self):
        tcl = ""
        # Default value for when opening project in GUI.
        # Will be overwritten if using build() function.
        tcl += "set_param general.maxThreads 7\n"
        # Enable VHDL assert statements to be evaluated. A severity level of failure will
        # stop the synthesis and produce an error.
        tcl_block = "set_property STEPS.SYNTH_DESIGN.ARGS.ASSERT true ${run}"
        tcl += self._tcl_for_each_run("synth_*", tcl_block)
        # Enable binary bitstream as well
        tcl_block = "set_property STEPS.WRITE_BITSTREAM.ARGS.BIN_FILE true ${run}"
        tcl += self._tcl_for_each_run("impl_*", tcl_block)
        return tcl

    @staticmethod
    def _tcl_for_each_run(run_wildcard, tcl_block):
        """
        Apply TCL block for each defined run. Use ${run} for run variable in TCL.
        """
        tcl = ""
        tcl += f"foreach run [get_runs {run_wildcard}] {{\n"
        tcl += tcl_block + "\n"
        tcl += "}\n"
        return tcl

    @staticmethod
    def _add_generics(generics):
        """
        Generics are set according to this weird format: https://www.xilinx.com/support/answers/52217.html
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

        if constraints is not None:
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

    def build(self, project_file, output_path, num_threads, run_index, generics=None, synth_only=False):
        # Max value in Vivado 2017.4. set_param will give an error if higher number.
        num_threads = min(num_threads, 8)

        synth_run = f"synth_{run_index}"
        impl_run = f"impl_{run_index}"

        tcl = f"open_project {to_tcl_path(project_file)}\n"
        tcl += f"set_param general.maxThreads {num_threads}\n"
        tcl += "\n"
        tcl += self._add_generics(generics)
        tcl += "\n"
        tcl += self._synthesis(synth_run, num_threads)
        tcl += "\n"
        if not synth_only:
            tcl += self._run(impl_run, num_threads, to_step="write_bitstream")
            tcl += "\n"
            tcl += self._write_hw_platform(output_path)
            tcl += "\n"
        tcl += "exit\n"
        return tcl

    def _synthesis(self, run, num_threads):
        tcl = self._run(run, num_threads)
        tcl += "\n"
        tcl += f"open_run {run}\n"
        tcl += f"set run_directory [get_property DIRECTORY [get_runs {run}]]\n"
        tcl += "\n"
        tcl += "set output_file [file join ${run_directory} \"hierarchical_utilization.rpt\"]\n"
        tcl += "report_utilization -hierarchical -hierarchical_depth 4 -file ${output_file}\n"
        tcl += "\n"
        tcl += r"if {[regexp {\(unsafe\)} [report_clock_interaction -delay_type min_max -return_string]]} "
        tcl += "{\n"
        tcl += f"  puts \"ERROR: Unhandled clock crossing in {run} run. See reports in ${{run_directory}}\"\n"
        tcl += "\n"
        tcl += "  set output_file [file join ${run_directory} \"clock_interaction.rpt\"]\n"
        tcl += "  report_clock_interaction -delay_type min_max -file ${output_file}\n"
        tcl += "\n"
        tcl += "  set output_file [file join ${run_directory} \"timing_summary.rpt\"]\n"
        tcl += "  report_timing_summary -file ${output_file}\n"
        tcl += "\n"
        tcl += "  exit 1\n"
        tcl += "}\n"
        return tcl

    @staticmethod
    def _run(run, num_threads, to_step=None):
        to_step = "" if to_step is None else " -to_step " + to_step

        tcl = f"reset_run {run}\n"
        tcl += f"launch_runs {run} -jobs {num_threads}{to_step}\n"
        tcl += "wait_on_run %s\n" % run
        tcl += "\n"
        tcl += "if {[get_property PROGRESS [get_runs %s]] != \"100%%\"} {\n" % run
        tcl += f"  puts \"ERROR: Run {run} failed.\"\n"
        tcl += "  exit 1\n"
        tcl += "}\n"
        return tcl

    def _write_hw_platform(self, output_path):
        xsa_file = to_tcl_path(output_path / (self.name + ".xsa"))
        tcl = f"write_hw_platform -fixed -force {xsa_file}\n"
        return tcl
