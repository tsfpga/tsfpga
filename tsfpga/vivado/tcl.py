# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# First party libraries
from tsfpga.system_utils import create_file

# Local folder libraries
from .common import to_tcl_path
from .generics import get_vivado_tcl_generic_value


class VivadoTcl:
    """
    Class with methods for translating a set of sources into Vivado TCL
    """

    def __init__(
        self,
        name,
    ):
        self.name = name

    # pylint: disable=too-many-arguments
    def create(
        self,
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
        disable_io_buffers=True,
        # Add no sources other than IP cores
        ip_cores_only=False,
        # Will be passed on to module functions. Enables parameterization of e.g. IP cores.
        other_arguments=None,
    ):
        generics = {} if generics is None else generics
        other_arguments = {} if other_arguments is None else other_arguments

        tcl = f"create_project {self.name} {{{to_tcl_path(project_folder)}}} -part {part}\n"
        tcl += "set_property target_language VHDL [current_project]\n"

        if ip_cache_path is not None:
            tcl += f"config_ip_cache -use_cache_location {{{to_tcl_path(ip_cache_path)}}}\n"
            tcl += "\n"

        tcl += self._add_tcl_sources(tcl_sources)
        tcl += "\n"

        if not ip_cores_only:
            tcl += self._add_module_source_files(modules=modules, other_arguments=other_arguments)
            tcl += "\n"
            tcl += self._add_generics(generics)
            tcl += "\n"
            tcl += self._add_constraints(
                self._iterate_constraints(
                    modules=modules, constraints=constraints, other_arguments=other_arguments
                )
            )
            tcl += "\n"
            tcl += self._add_build_step_hooks(build_step_hooks, project_folder)
            tcl += "\n"

        tcl += self._add_ip_cores(modules=modules, other_arguments=other_arguments)
        tcl += "\n"
        tcl += self._add_project_settings()
        tcl += "\n"
        tcl += f"current_run [get_runs synth_{run_index}]\n"
        tcl += "\n"
        tcl += f"set_property top {top} [current_fileset]\n"
        tcl += "reorder_files -auto -disable_unused\n"
        tcl += "\n"

        if disable_io_buffers:
            tcl += (
                "set_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} "
                f"-value -no_iobuf -objects [get_runs synth_{run_index}]"
            )
            tcl += "\n"

        tcl += "exit\n"
        return tcl

    def _add_module_source_files(self, modules, other_arguments):
        tcl = ""
        for module in modules:
            vhdl_files = []
            verilog_source_files = []
            for hdl_file in module.get_synthesis_files(**other_arguments):
                if hdl_file.is_vhdl:
                    vhdl_files.append(hdl_file.path)
                elif hdl_file.is_verilog_source:
                    verilog_source_files.append(hdl_file.path)
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
                files_string = self._to_file_list(vhdl_files)
                tcl += f"read_vhdl -library {module.library_name} -vhdl2008 {files_string}\n"
            if verilog_source_files:
                files_string = self._to_file_list(verilog_source_files)
                tcl += f"read_verilog {files_string}\n"

        return tcl

    @staticmethod
    def _to_file_list(file_paths):
        """
        Return a TCL snippet for a file list, with each file enclosed in curly braces.
        E.g. "{file1}" or "{{file1} {file2} {file3}}"
        """
        if len(file_paths) == 1:
            files_string = to_tcl_path(file_paths[0])
        else:
            files_string = " ".join([f"{{{to_tcl_path(file_path)}}}" for file_path in file_paths])

        return f"{{{files_string}}}"

    @staticmethod
    def _add_tcl_sources(tcl_sources):
        if tcl_sources is None:
            return ""

        tcl = ""
        for tcl_source_file in tcl_sources:
            tcl += f"source -notrace {{{to_tcl_path(tcl_source_file)}}}\n"
        return tcl

    @staticmethod
    def _add_ip_cores(modules, other_arguments):
        tcl = ""
        for module in modules:
            for ip_core_file in module.get_ip_core_files(**other_arguments):
                create_function_name = f"create_ip_core_{ip_core_file.name}"
                tcl += f"proc {create_function_name} {{}} {{\n"

                if ip_core_file.variables:
                    for key, value in ip_core_file.variables.items():
                        tcl += f'  set {key} "{value}"\n'

                tcl += f"""\
  source -notrace {{{to_tcl_path(ip_core_file.path)}}}
}}
{create_function_name}
"""

        return tcl

    def _add_build_step_hooks(self, build_step_hooks, project_folder):
        if build_step_hooks is None:
            return ""

        # There can be many hooks for the same step. Reorganize them into a dict, according
        # to the format step_name: [list of hooks]
        hook_steps = {}
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
                source_hooks_tcl = "".join(
                    [f"source {{{to_tcl_path(hook.tcl_file)}}}\n" for hook in hooks]
                )
                create_file(tcl_file, source_hooks_tcl)

            # Add to fileset to enable archive and other project based functionality
            tcl += f"add_files -fileset utils_1 -norecurse {{{to_tcl_path(tcl_file)}}}\n"

            # Build step hook can only be applied to a run (e.g. impl_1), not on a project basis
            run_wildcard = "synth_*" if hooks[0].step_is_synth else "impl_*"
            tcl_block = f"set_property {step} {{{to_tcl_path(tcl_file)}}} ${{run}}"
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
        Generics are set according to this weird format:
        https://www.xilinx.com/support/answers/52217.html
        """
        if not generics:
            return ""

        generic_list = []
        for name, value in generics.items():
            value_tcl_formatted = get_vivado_tcl_generic_value(value=value)
            generic_list.append(f"{name}={value_tcl_formatted}")

        generics_string = " ".join(generic_list)
        return f"set_property generic {{{generics_string}}} [current_fileset]\n"

    @staticmethod
    def _iterate_constraints(modules, constraints, other_arguments):
        for module in modules:
            for constraint in module.get_scoped_constraints(**other_arguments):
                yield constraint

        if constraints is not None:
            for constraint in constraints:
                yield constraint

    @staticmethod
    def _add_constraints(constraints):
        tcl = ""
        for constraint in constraints:
            constraint_file = to_tcl_path(constraint.file)

            ref_flags = "" if constraint.ref is None else (f"-ref {constraint.ref} ")
            managed_flags = "" if constraint_file.endswith("xdc") else "-unmanaged "
            tcl += f"read_xdc {ref_flags}{managed_flags}{{{constraint_file}}}\n"

            get_file = f"[get_files {{{constraint_file}}}]"
            tcl += f"set_property PROCESSING_ORDER {constraint.processing_order} {get_file}\n"

            if constraint.used_in == "impl":
                tcl += f"set_property used_in_synthesis false {get_file}\n"
            elif constraint.used_in == "synth":
                tcl += f"set_property used_in_implementation false {get_file}\n"

        return tcl

    def build(
        self,
        project_file,
        output_path,
        num_threads,
        run_index,
        generics=None,
        synth_only=False,
        from_impl=False,
        analyze_synthesis_timing=True,
    ):
        # Max value in Vivado 2018.3+. set_param will give an error if higher number.
        num_threads_general = min(num_threads, 32)
        num_threads_synth = min(num_threads, 8)

        tcl = f"open_project {to_tcl_path(project_file)}\n"
        tcl += f"set_param general.maxThreads {num_threads_general}\n"
        tcl += f"set_param synth.maxThreads {num_threads_synth}\n"
        tcl += "\n"
        tcl += self._add_generics(generics)
        tcl += "\n"

        if not from_impl:
            synth_run = f"synth_{run_index}"

            tcl += self._synthesis(synth_run, num_threads, analyze_synthesis_timing)
            tcl += "\n"

        if not synth_only:
            impl_run = f"impl_{run_index}"

            tcl += self._run(impl_run, num_threads, to_step="write_bitstream")
            tcl += self._write_hw_platform(output_path)
            tcl += "\n"

        tcl += "exit\n"

        return tcl

    def _synthesis(self, run, num_threads, analyze_synthesis_timing):
        tcl = self._run(run, num_threads)
        if analyze_synthesis_timing:
            # For synthesis flow we perform the timing checks by opening the design. It would have
            # been more efficient to use a post-synthesis hook (since the design would already be
            # open), if that mechanism had worked. It seems to be very bugged. So we add the
            # checkers to the build script.
            # For implementation, we use a pre-bitstream build hook which seems to work decently.
            tcl += """
open_run ${run}
set run_directory [get_property DIRECTORY [get_runs ${run}]]

# This call is duplicated in report_utilization.tcl for implementation.
set output_file [file join ${run_directory} "hierarchical_utilization.rpt"]
report_utilization -hierarchical -hierarchical_depth 4 -file ${output_file}


# After synthesis we check for unhandled clock crossings and abort the build based on the result.
# Other timing checks, e.g. setup/hold/pulse width violations, are not reliable after synthesis,
# and should not abort the build. These need to be checked after implementation.
"""

            tcl += """
# This code is duplicated in check_timing.tcl for implementation.
if {[regexp {\\(unsafe\\)} [report_clock_interaction -delay_type min_max -return_string]]} {
  puts "ERROR: Unhandled clock crossing in ${run} run. See clock_interaction.rpt and \
timing_summary.rpt in ${run_directory}."

  set output_file [file join ${run_directory} "clock_interaction.rpt"]
  report_clock_interaction -delay_type min_max -file ${output_file}

  set output_file [file join ${run_directory} "timing_summary.rpt"]
  report_timing_summary -file ${output_file}

  exit 1
}
"""
        return tcl

    @staticmethod
    def _run(run, num_threads, to_step=None):
        to_step = "" if to_step is None else " -to_step " + to_step

        tcl = f"""
set run {run}
reset_run ${{run}}
launch_runs ${{run}} -jobs {num_threads}{to_step}
"""

        tcl += """
wait_on_run ${run}

if {[get_property PROGRESS [get_runs ${run}]] != "100%"} {
  puts "ERROR: Run ${run} failed."
  exit 1
}
"""
        return tcl

    def _write_hw_platform(self, output_path):
        """
        TCL command to create a "hardware platform" .xsa file (aka, "hdf" or "hwdef" file).

        This is mainly used for Zynq devices to generate code to set up the PS at boot.
        There is also code generated for each MicroBlaze that is present in the design.
        If there is neither a block design nor a MicroBlaze available, the .xsa will be empty apart
        from some info about which part is used, etc.

        The '-quiet' flag is used since there was a Vivado bug observed in this very
        specific scenario:
        * Vivado 2022.1
        * UltraScale+ non-Zynq device (i.e. no block design)
        * Design contains MicroBlaze
        * Design contains ILA
        In this case the 'write_hw_platform' call would fail.
        This bug might be present in other Vivado versions and in other scenarios as well.
        Since this is a very fringe scenario, and it is unlikely that anyone would ever need the
        .xsa file specifically from the ILA build, we allow the command to fail quietly.
        """
        xsa_file = to_tcl_path(output_path / f"{self.name}.xsa")

        tcl = f"""
puts "Creating hardware platform {xsa_file}..."
write_hw_platform -fixed -force -quiet {{{xsa_file}}}
"""

        return tcl
