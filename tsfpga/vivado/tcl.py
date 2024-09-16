# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Optional

# First party libraries
from tsfpga.hdl_file import HdlFile
from tsfpga.system_utils import create_file

# Local folder libraries
from .common import to_tcl_path
from .generics import get_vivado_tcl_generic_value

if TYPE_CHECKING:
    # First party libraries
    from tsfpga.build_step_tcl_hook import BuildStepTclHook
    from tsfpga.constraint import Constraint
    from tsfpga.module_list import ModuleList


# Number of available Vivado implementation strategies
NUM_VIVADO_STRATEGIES = 33


class VivadoTcl:
    """
    Class with methods for translating a set of sources into Vivado TCL
    """

    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name

    # pylint: disable=too-many-arguments
    def create(
        self,
        project_folder: Path,
        modules: "ModuleList",
        part: str,
        top: str,
        run_index: int,
        generics: Optional[dict[str, str]] = None,
        constraints: Optional[list["Constraint"]] = None,
        tcl_sources: Optional[list[Path]] = None,
        build_step_hooks: Optional[list["BuildStepTclHook"]] = None,
        ip_cache_path: Optional[Path] = None,
        disable_io_buffers: bool = True,
        # Add no sources other than IP cores
        ip_cores_only: bool = False,
        # Will be passed on to module functions. Enables parameterization of e.g. IP cores.
        other_arguments: Optional[dict[str, Any]] = None,
    ) -> str:
        generics = {} if generics is None else generics
        other_arguments = {} if other_arguments is None else other_arguments

        tcl = f"""\
create_project -part "{part}" "{self.name}" {{{to_tcl_path(project_folder)}}}
set_property "target_language" "VHDL" [current_project]

"""
        if ip_cache_path is not None:
            tcl += f"config_ip_cache -use_cache_location {{{to_tcl_path(ip_cache_path)}}}\n\n"

        if not ip_cores_only:
            tcl += self._add_module_source_files(modules=modules, other_arguments=other_arguments)
            tcl += self._add_tcl_sources(tcl_sources)
            tcl += self._add_generics(generics)

            constraints = list(
                self._iterate_constraints(
                    modules=modules, constraints=constraints, other_arguments=other_arguments
                )
            )
            tcl += self._add_constraints(constraints=constraints)
            tcl += self._add_build_step_hooks(build_step_hooks, project_folder)

        tcl += self._add_ip_cores(modules=modules, other_arguments=other_arguments)
        tcl += self._add_project_settings()

        tcl += f"""
# ------------------------------------------------------------------------------
current_run [get_runs "synth_{run_index}"]
set_property "top" "{top}" [current_fileset]
reorder_files -auto -disable_unused

"""
        if disable_io_buffers:
            tcl += f"""\
set_property -name "STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS" \
-value "-no_iobuf" -objects [get_runs "synth_{run_index}"]

"""
        tcl += """
# ------------------------------------------------------------------------------
exit
"""
        return tcl

    def _add_module_source_files(
        self, modules: "ModuleList", other_arguments: dict[str, Any]
    ) -> str:
        if len(modules) == 0:
            return ""

        tcl = """
# ------------------------------------------------------------------------------
"""
        for module in modules:
            vhdl_files = []
            verilog_files = []
            system_verilog_files = []

            for hdl_file in module.get_synthesis_files(**other_arguments):
                if hdl_file.type == HdlFile.Type.VHDL:
                    vhdl_files.append(hdl_file.path)
                elif hdl_file.type in [HdlFile.Type.VERILOG_SOURCE, HdlFile.Type.VERILOG_HEADER]:
                    verilog_files.append(hdl_file.path)
                elif hdl_file.type in [
                    HdlFile.Type.SYSTEMVERILOG_SOURCE,
                    HdlFile.Type.SYSTEMVERILOG_HEADER,
                ]:
                    system_verilog_files.append(hdl_file.path)
                else:
                    raise NotImplementedError(f"Can not handle file: {hdl_file}")
                    # Encrypted source files (.vp?), etc, I do not know how
                    # to handle, since I have no use case for it at the moment.

            if vhdl_files:
                files_string = self._to_file_list(vhdl_files)
                tcl += f'read_vhdl -library "{module.library_name}" -vhdl2008 {files_string}\n'

            if verilog_files:
                files_string = self._to_file_list(verilog_files)
                tcl += f"read_verilog {files_string}\n"

            if system_verilog_files:
                files_string = self._to_file_list(system_verilog_files)
                tcl += f"read_verilog -sv {files_string}\n"

        return f"{tcl}\n"

    @staticmethod
    def _to_file_list(file_paths: list[Path]) -> str:
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
    def _add_tcl_sources(tcl_sources: Optional[list[Path]]) -> str:
        if tcl_sources is None or len(tcl_sources) == 0:
            return ""

        tcl = """
# ------------------------------------------------------------------------------
"""
        for tcl_source_file in tcl_sources:
            tcl += f"source -notrace {{{to_tcl_path(tcl_source_file)}}}\n"

        return f"{tcl}\n"

    @staticmethod
    def _add_ip_cores(modules: "ModuleList", other_arguments: dict[str, Any]) -> str:
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
        if tcl == "":
            return ""

        return f"""
# ------------------------------------------------------------------------------
{tcl}\
"""

    def _add_build_step_hooks(
        self, build_step_hooks: Optional[list["BuildStepTclHook"]], project_folder: Path
    ) -> str:
        if build_step_hooks is None or len(build_step_hooks) == 0:
            return ""

        # There can be many hooks for the same step. Reorganize them into a dict.
        hook_steps: dict[str, list["BuildStepTclHook"]] = {}
        for build_step_hook in build_step_hooks:
            if build_step_hook.hook_step in hook_steps:
                hook_steps[build_step_hook.hook_step].append(build_step_hook)
            else:
                hook_steps[build_step_hook.hook_step] = [build_step_hook]

        tcl = """
# ------------------------------------------------------------------------------
"""
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
            tcl += f'add_files -fileset "utils_1" -norecurse {{{to_tcl_path(tcl_file)}}}\n'

            # Build step hook can only be applied to a run (e.g. impl_1), not on a project basis
            run_wildcard = '"synth_*"' if hooks[0].step_is_synth else '"impl_*"'
            tcl_block = f'set_property "{step}" {{{to_tcl_path(tcl_file)}}} ${{run}}'
            tcl += self._tcl_for_each_run(run_wildcard=run_wildcard, tcl_block=tcl_block)

        return f"{tcl}\n"

    def _add_project_settings(self) -> str:
        tcl = """
# ------------------------------------------------------------------------------
"""

        # Default value for when opening project in GUI.
        # Will be overwritten if using build() function.
        tcl += 'set_param "general.maxThreads" 7\n'

        # Enable VHDL assert statements to be evaluated. A severity level of failure will
        # stop the synthesis and produce an error.
        tcl_block = 'set_property "STEPS.SYNTH_DESIGN.ARGS.ASSERT" true ${run}'
        tcl += self._tcl_for_each_run(run_wildcard='"synth_*"', tcl_block=tcl_block)

        # Enable binary bitstream as well
        tcl_block = 'set_property "STEPS.WRITE_BITSTREAM.ARGS.BIN_FILE" true ${run}'
        tcl += self._tcl_for_each_run(run_wildcard='"impl_*"', tcl_block=tcl_block)

        return f"{tcl}\n"

    @staticmethod
    def _tcl_for_each_run(run_wildcard: str, tcl_block: str) -> str:
        """
        Apply TCL block for each defined run. Use ${run} for run variable in TCL.
        """
        # Apply indentation for all lines within the block.
        tcl_block = tcl_block.replace("\n", "\n  ")

        return f"""\
foreach run [get_runs {run_wildcard}] {{
  {tcl_block}
}}
"""

    @staticmethod
    def _add_generics(generics: Optional[dict[str, Any]]) -> str:
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
        return f"""
# ------------------------------------------------------------------------------
set_property "generic" {{{generics_string}}} [current_fileset]

"""

    @staticmethod
    def _iterate_constraints(
        modules: "ModuleList",
        constraints: Optional[list["Constraint"]],
        other_arguments: dict[str, Any],
    ) -> Iterable["Constraint"]:
        for module in modules:
            yield from module.get_scoped_constraints(**other_arguments)

        if constraints is not None:
            yield from constraints

    @staticmethod
    def _add_constraints(constraints: list["Constraint"]) -> str:
        if len(constraints) == 0:
            return ""

        tcl = """
# ------------------------------------------------------------------------------
"""
        for constraint in constraints:
            constraint_file = to_tcl_path(constraint.file)

            ref_flags = "" if constraint.ref is None else (f'-ref "{constraint.ref}" ')
            managed_flags = "" if constraint_file.endswith("xdc") else "-unmanaged "
            tcl += f"read_xdc {ref_flags}{managed_flags}{{{constraint_file}}}\n"

            get_file = f"[get_files {{{constraint_file}}}]"
            tcl += (
                'set_property "PROCESSING_ORDER" '
                f'"{constraint.processing_order.upper()}" {get_file}\n'
            )

            if constraint.used_in == "impl":
                tcl += f'set_property "USED_IN_SYNTHESIS" false {get_file}\n'
            elif constraint.used_in == "synth":
                tcl += f'set_property "USED_IN_IMPLEMENTATION" false {get_file}\n'

        return f"{tcl}\n"

    def build(
        self,
        project_file: Path,
        output_path: Path,
        num_threads: int,
        run_index: int,
        generics: Optional[dict[str, Any]] = None,
        synth_only: bool = False,
        from_impl: bool = False,
        impl_explore: bool = False,
        analyze_synthesis_timing: bool = True,
    ) -> str:
        if impl_explore:
            # For implementation explore, threads are divided to one each per job.
            # Number of jobs in parallel are the number of threads specified for build.
            # Clamp max threads between 1 and 32, which are allowed by Vivado 2018.3+.
            num_threads_general = min(max(1, num_threads // NUM_VIVADO_STRATEGIES), 32)
        else:
            # Max value in Vivado 2018.3+. set_param will give an error if higher number.
            num_threads_general = min(num_threads, 32)

        num_threads_synth = min(num_threads, 8)

        tcl = f"open_project {{{to_tcl_path(project_file)}}}\n"
        tcl += f'set_param "general.maxThreads" {num_threads_general}\n'
        tcl += f'set_param "synth.maxThreads" {num_threads_synth}\n\n'
        tcl += self._add_generics(generics)

        if not from_impl:
            synth_run = f"synth_{run_index}"

            tcl += self._synthesis(synth_run, num_threads, analyze_synthesis_timing)

        if not synth_only:
            impl_run = f"impl_{run_index}"

            if impl_explore:
                tcl += self._run_multiple(num_jobs=num_threads)
            else:
                tcl += self._run(impl_run, num_threads, to_step="write_bitstream")

            tcl += self._write_hw_platform(output_path)

        tcl += """
# ------------------------------------------------------------------------------
exit
"""
        return tcl

    def _synthesis(self, run: str, num_threads: int, analyze_synthesis_timing: bool) -> str:
        tcl = self._run(run, num_threads)
        if not analyze_synthesis_timing:
            return tcl

        # For synthesis flow we perform the timing checks by opening the design. It would have
        # been more efficient to use a post-synthesis hook (since the design would already be
        # open), if that mechanism had worked. It seems to be very bugged. So we add the
        # checkers to the build script.
        # For implementation, we use a pre-bitstream build hook which seems to work decently.
        #
        # Timing checks such as setup/hold/pulse width violations, are not reliable after synthesis,
        # and should not abort the build as we do below.
        # These need to be checked after implementation.
        tcl += """
# ------------------------------------------------------------------------------
open_run ${run}
set run_directory [get_property "DIRECTORY" ${run}]
set should_exit 0


# ------------------------------------------------------------------------------
# Generate report on simultaneous switching noise (SSN) for the design.
# It seems safe to do this after synthesis; inspecting the reports in a test build after both
# synthesis and implementation shows that the results are identical.
# Will generate a "Designutils 20-923" message if noise margins are not met.
# If the user would like this to fail the build, this message severity shall be raised to ERROR.
# At the moment we do not know how stable this mechanism is, so we do not fail the build
# per default.
# The call is very fast (< 1s) so it is fine to run always, even though not everyone will use it.
set current_part [get_property "PART" [current_project]]
set part_supports_ssn [get_parts ${current_part} -filter {ssn_report == 1}]
if {${part_supports_ssn} != ""} {
    set output_file [file join ${run_directory} "report_ssn.html"]
    report_ssn -phase -format html -file ${output_file}
}


# ------------------------------------------------------------------------------
# This call is duplicated in 'report_utilization.tcl' for implementation.
set output_file [file join ${run_directory} "hierarchical_utilization.rpt"]
report_utilization -hierarchical -hierarchical_depth 4 -file ${output_file}


# ------------------------------------------------------------------------------
# This code is duplicated in 'check_timing.tcl' for implementation.
set clock_interaction_report [
  report_clock_interaction -delay_type "min_max" -no_header -return_string
]
if {[string first "(unsafe)" ${clock_interaction_report}] != -1} {
  puts "ERROR: Unhandled clock crossing in ${run} run. See 'clock_interaction.rpt' and \
'timing_summary.rpt' in ${run_directory}."

  set output_file [file join ${run_directory} "clock_interaction.rpt"]
  report_clock_interaction -delay_type min_max -file ${output_file}

  set output_file [file join ${run_directory} "timing_summary.rpt"]
  report_timing_summary -file ${output_file}

  set should_exit 1
}


# ------------------------------------------------------------------------------
# This code is duplicated in 'check_cdc.tcl' for implementation.
# Check that there are no critical CDC rule violations in the design.
# List of CDC rules: https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/CDC-Rules-Precedence
# If this makes your build fail on a false positive, you can waive the rule using the
# 'create_waiver' command in a (scoped) constraint file.
# Rules can be disable in general (not recommended), or for specific paths using the '-from'
# and '-to' flags (recommended).
set cdc_report [report_cdc -return_string -no_header -details -severity "Critical"]
if {[string first "Critical" ${cdc_report}] != -1} {
  set output_file [file join ${run_directory} "cdc.rpt"]
  puts "ERROR: Critical CDC rule violation in ${run} run. See ${output_file}."

  report_cdc -details -file ${output_file}

  set should_exit 1
}


# ------------------------------------------------------------------------------
if {${should_exit} eq 1} {
  exit 1
}

"""
        return tcl

    @staticmethod
    def _run(run: str, num_threads: int, to_step: Optional[str] = None) -> str:
        to_step = "" if to_step is None else f' -to_step "{to_step}"'

        tcl = f"""
# ------------------------------------------------------------------------------
set run [get_runs "{run}"]
reset_run ${{run}}
launch_runs ${{run}} -jobs {num_threads}{to_step}
"""

        tcl += """
wait_on_run ${run}

if {[get_property "PROGRESS" ${run}] != "100%"} {
  puts "ERROR: Run ${run} failed."
  exit 1
}

"""
        return tcl

    def _run_multiple(self, num_jobs: int = 4, base_name: str = "impl_explore_") -> str:
        """
        Currently, this creates a .tcl that waits for all active runs to complete.
        """
        tcl = "\nset build_succeeded 0\n"
        tcl += f'reset_runs [get_runs "{base_name}*"]\n'
        tcl += (
            f'launch_runs -jobs {num_jobs} [get_runs "{base_name}*"] -to_step "write_bitstream"\n'
        )
        tcl += "\n"

        tcl += f'wait_on_runs -quiet -exit_condition ANY_ONE_MET_TIMING [get_runs "{base_name}*"]\n'
        tcl += "\n"

        tcl += 'reset_runs [get_runs -filter {STATUS == "Queued..."}]\n'

        # Wait on runs that are still going, since Vivado can't kill runs in progress reliably.
        # Killing runs in progress causes a zombie process which will lock up VUnit's Process class.
        tcl += (
            f'wait_on_runs -quiet [get_runs -filter {{STATUS != "Not started"}} "{base_name}*"]\n'
        )
        tcl += "\n"

        tcl_block = """\
set build_succeeded 1
puts "Run ${run} met timing"\
"""
        tcl += self._tcl_for_each_run(
            run_wildcard=f'-filter {{PROGRESS == "100%"}} "{base_name}*"', tcl_block=tcl_block
        )

        tcl += """
if {${build_succeeded} eq 0} {
  puts "No build met timing, exiting."
  exit 1
}

"""

        return tcl

    def _write_hw_platform(self, output_path: Path) -> str:
        """
        TCL command to create a Xilinx support archive (.xsa) file, for use as a
        hardware platform.
        Used to be known as a "hdf" or "hwdef" file.

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
# ------------------------------------------------------------------------------
puts "Creating hardware platform {xsa_file}..."
write_hw_platform -fixed -force -quiet -include_bit {{{xsa_file}}}

"""

        return tcl
