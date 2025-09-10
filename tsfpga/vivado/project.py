# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

import contextlib
import re
import shutil
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

from tsfpga import TSFPGA_TCL
from tsfpga.build_step_tcl_hook import BuildStepTclHook
from tsfpga.constraint import Constraint
from tsfpga.hdl_file import HdlFile
from tsfpga.system_utils import create_file, read_file

from .build_result import BuildResult
from .common import run_vivado_gui, run_vivado_tcl, to_tcl_path
from .hierarchical_utilization_parser import HierarchicalUtilizationParser
from .logic_level_distribution_parser import LogicLevelDistributionParser
from .tcl import VivadoTcl
from .timing_parser import FoundNoSlackError, TimingParser

if TYPE_CHECKING:
    from tsfpga.module_list import ModuleList
    from tsfpga.vivado.generics import BitVectorGenericValue, StringGenericValue

    from .build_result_checker import MaximumLogicLevel, SizeChecker


class VivadoProject:
    """
    Used for handling a Xilinx Vivado HDL project
    """

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        modules: ModuleList,
        part: str,
        top: str | None = None,
        generics: dict[str, bool | float | StringGenericValue | BitVectorGenericValue]
        | None = None,
        constraints: list[Constraint] | None = None,
        tcl_sources: list[Path] | None = None,
        build_step_hooks: list[BuildStepTclHook] | None = None,
        vivado_path: Path | None = None,
        default_run_index: int = 1,
        impl_explore: bool = False,
        defined_at: Path | None = None,
        **other_arguments: Any,  # noqa: ANN401
    ) -> None:
        """
        Class constructor. Performs a shallow copy of the mutable arguments, so that the user
        can e.g. append items to their list after creating an object.

        Arguments:
            name: Project name.
            modules: Modules that shall be included in the project.
            part: Part identification.
            top: Name of top level entity.
                If left out, the top level name will be inferred from the ``name``.
            generics: A dict with generics values (name: value). Use this parameter
                for "static" generics that do not change between multiple builds of this
                project. These will be set in the project when it is created.

                Compare to the build-time generic argument in :meth:`build`.

                The generic value shall be of type

                * :class:`bool` (suitable for VHDL type ``boolean`` and ``std_logic``),
                * :class:`int` (suitable for VHDL type ``integer``, ``natural``, etc.),
                * :class:`float` (suitable for VHDL type ``real``),
                * :class:`.BitVectorGenericValue` (suitable for VHDL type ``std_logic_vector``,
                  ``unsigned``, etc.), or
                * :class:`.StringGenericValue` (suitable for VHDL type ``string``).
            constraints: Constraints that will be applied to the project.
            tcl_sources: A list of TCL files. Use for e.g. block design, pinning, settings, etc.
            build_step_hooks: Build step hooks that will be applied to the project.
            vivado_path: A path to the Vivado executable.
                If omitted, the default location from the system PATH will be used.
            default_run_index: Default run index (synth_X and impl_X) that is set in the
                project.
                Can also use the argument to :meth:`build() <VivadoProject.build>` to
                specify at build-time.
            impl_explore: Run multiple implementation strategies in parallel.
            defined_at: Optional path to the file where you defined this project.
                To get a useful ``build_fpga.py --list`` message. Is useful when you have many
                projects set up.
            other_arguments: Optional further arguments. Will not be used by tsfpga, but will
                instead be passed on to

                * :func:`BaseModule.get_synthesis_files()
                  <tsfpga.module.BaseModule.get_synthesis_files>`
                * :func:`BaseModule.get_ip_core_files()
                  <tsfpga.module.BaseModule.get_ip_core_files>`
                * :func:`BaseModule.get_scoped_constraints()
                  <tsfpga.module.BaseModule.get_scoped_constraints>`
                * :func:`VivadoProject.pre_create`
                * :func:`BaseModule.pre_build() <tsfpga.module.BaseModule.pre_build>`
                * :func:`VivadoProject.pre_build`
                * :func:`VivadoProject.post_build`

                along with further arguments supplied at build-time to :meth:`.create` and
                :meth:`.build`.

                .. note::
                    This is a "kwargs" style argument. You can pass any number of named arguments.
        """
        self.name = name
        self.modules = modules.copy()
        self.part = part
        self.static_generics = {} if generics is None else generics.copy()
        self.constraints = [] if constraints is None else constraints.copy()
        self.tcl_sources = [] if tcl_sources is None else tcl_sources.copy()
        self.build_step_hooks = [] if build_step_hooks is None else build_step_hooks.copy()
        self._vivado_path = vivado_path
        self.default_run_index = default_run_index
        self.impl_explore = impl_explore
        self.defined_at = defined_at
        self.other_arguments = None if other_arguments is None else other_arguments.copy()

        # Will be set by subclass when applicable
        self.is_netlist_build = False
        self.open_and_analyze_synthesized_design = True
        self.ip_cores_only = False

        self.top = name + "_top" if top is None else top

        self.tcl = VivadoTcl(name=self.name)

        for constraint in self.constraints:
            if not isinstance(constraint, Constraint):
                raise TypeError(f'Got bad type for "constraints" element: {constraint}')

        for tcl_source in self.tcl_sources:
            if not isinstance(tcl_source, Path):
                raise TypeError(f'Got bad type for "tcl_sources" element: {tcl_source}')

        for build_step_hook in self.build_step_hooks:
            if not isinstance(build_step_hook, BuildStepTclHook):
                raise TypeError(f'Got bad type for "build_step_hooks" element: {build_step_hook}')

    def project_file(self, project_path: Path) -> Path:
        """
        Arguments:
            project_path: A path containing a Vivado project.

        Return:
            The project file of this project, in the given folder
        """
        return project_path / f"{self.name}.xpr"

    def _setup_tcl_sources(self) -> None:
        tsfpga_tcl_sources = [
            TSFPGA_TCL / "vivado_default_run.tcl",
            TSFPGA_TCL / "vivado_fast_run.tcl",
            TSFPGA_TCL / "vivado_messages.tcl",
        ]

        if self.impl_explore:
            tsfpga_tcl_sources.append(TSFPGA_TCL / "vivado_strategies.tcl")

        # Add tsfpga TCL sources first. The user might want to change something in the tsfpga
        # settings. Conversely, tsfpga should not modify something that the user has set up.
        self.tcl_sources = tsfpga_tcl_sources + self.tcl_sources

    def _setup_and_create_build_step_hooks(
        self, project_path: Path
    ) -> dict[str, tuple[Path, list[BuildStepTclHook]]]:
        """
        Add all necessary tsfpga build step hooks to the list of hooks supplied by the user.
        Create the TCL files for these hooks in the project folder.
        """
        # Shallow copy so that we do not append the state of this object.
        # If this method is called twice, once at create-time and once at build-time, we do not
        # want duplicates.
        build_step_hooks = self.build_step_hooks.copy()

        # Check that no ERROR messages have been sent by Vivado. After synthesis as well as
        # after implementation.
        build_step_hooks.append(
            BuildStepTclHook(
                TSFPGA_TCL / "check_no_error_messages.tcl", "STEPS.SYNTH_DESIGN.TCL.POST"
            )
        )
        build_step_hooks.append(
            BuildStepTclHook(
                TSFPGA_TCL / "check_no_error_messages.tcl", "STEPS.WRITE_BITSTREAM.TCL.PRE"
            )
        )

        # Check the implemented timing and resource utilization via TCL build hooks.
        # This is different than for synthesis, where it is embedded in the build script.
        # This is due to Vivado limitations related to post-synthesis hooks.
        # Specifically, the report_utilization figures do not include IP cores when it is run in
        # a post-synthesis hook.
        build_step_hooks.append(
            BuildStepTclHook(TSFPGA_TCL / "report_utilization.tcl", "STEPS.WRITE_BITSTREAM.TCL.PRE")
        )
        build_step_hooks.append(
            BuildStepTclHook(TSFPGA_TCL / "check_timing.tcl", "STEPS.WRITE_BITSTREAM.TCL.PRE")
        )
        build_step_hooks.append(
            BuildStepTclHook(TSFPGA_TCL / "check_cdc.tcl", "STEPS.WRITE_BITSTREAM.TCL.PRE")
        )

        if not self.open_and_analyze_synthesized_design:
            # In this special case, used only by the fastest netlist builds, the synthesized design
            # is never opened (to save execution time).
            # So in order to get access to some design metrics, we need to add hooks instead.

            # Note that this report is does not report numbers from IP cores within the design,
            # when the report is generated via a hook.
            # But since this mode is used exclusively by netlist builds, which very rarely include
            # IP cores, this is deemed acceptable on order to save time.
            build_step_hooks.append(
                BuildStepTclHook(
                    TSFPGA_TCL / "report_utilization.tcl", "STEPS.SYNTH_DESIGN.TCL.POST"
                )
            )

            # Note that this report is better if generated on an open design, since it will then
            # list each clock domain separately.
            # If done like this with a hook, all paths will be on one line, no matter which clock
            # domain they belong to.
            build_step_hooks.append(
                BuildStepTclHook(
                    TSFPGA_TCL / "report_logic_level_distribution.tcl",
                    "STEPS.SYNTH_DESIGN.TCL.POST",
                )
            )

        organized_build_step_hooks = self._organize_build_step_hooks(
            build_step_hooks=build_step_hooks, project_folder=project_path
        )
        self._create_build_step_hook_files(build_step_hooks=organized_build_step_hooks)

        return organized_build_step_hooks

    @staticmethod
    def _organize_build_step_hooks(
        build_step_hooks: list[BuildStepTclHook], project_folder: Path
    ) -> dict[str, tuple[Path, list[BuildStepTclHook]]]:
        """
        Since there can be many hooks for the same step, reorganize them into a dict:
        {step name: (script file in project, [list of hooks for that step])}

        Vivado will only accept one TCL script as hook for each step.
        So if we want to add more we have to create a new TCL file, that sources the other files,
        and add that as the hook to Vivado.
        """
        result = {}
        for build_step_hook in build_step_hooks:
            if build_step_hook.hook_step in result:
                result[build_step_hook.hook_step][1].append(build_step_hook)
            else:
                tcl_file = project_folder / (
                    "hook_" + build_step_hook.hook_step.replace(".", "_") + ".tcl"
                )
                result[build_step_hook.hook_step] = (tcl_file, [build_step_hook])

        return result

    def _create_build_step_hook_files(
        self, build_step_hooks: dict[str, tuple[Path, list[BuildStepTclHook]]]
    ) -> None:
        for step_name, (tcl_file, hooks) in build_step_hooks.items():
            source_hooks_tcl = "\n".join(
                [f"source {{{to_tcl_path(hook.tcl_file)}}}" for hook in hooks]
            )
            create_file(
                tcl_file,
                f"""\
# ------------------------------------------------------------------------------
# Hook script for the "{step_name}" build step.
# This file is auto-generated by tsfpga. Do not edit manually.
{source_hooks_tcl}
""",
            )

    def _create_tcl(
        self,
        project_path: Path,
        ip_cache_path: Path | None,
        build_step_hooks: dict[str, tuple[Path, list[BuildStepTclHook]]],
        all_arguments: dict[str, Any],
    ) -> Path:
        """
        Make a TCL file that creates a Vivado project
        """
        project_file = self.project_file(project_path=project_path)
        if project_file.exists():
            raise ValueError(f'Project "{self.name}" already exists: {project_file}')
        project_path.mkdir(parents=True, exist_ok=True)

        create_vivado_project_tcl = project_path / "create_vivado_project.tcl"
        tcl = self.tcl.create(
            project_folder=project_path,
            modules=self.modules,
            part=self.part,
            top=self.top,
            run_index=self.default_run_index,
            generics=self.static_generics,
            constraints=self.constraints,
            tcl_sources=self.tcl_sources,
            build_step_hooks=build_step_hooks,
            ip_cache_path=ip_cache_path,
            disable_io_buffers=self.is_netlist_build,
            ip_cores_only=self.ip_cores_only,
            other_arguments=all_arguments,
        )
        create_file(create_vivado_project_tcl, tcl)

        return create_vivado_project_tcl

    def create(
        self,
        project_path: Path,
        ip_cache_path: Path | None = None,
        **other_arguments: Any,  # noqa: ANN401
    ) -> bool:
        """
        Create a Vivado project

        Arguments:
            project_path: Path where the project shall be placed.
            ip_cache_path: Path to a folder where the Vivado IP cache can be
                placed. If omitted, the Vivado IP cache mechanism will not be enabled.
            other_arguments: Optional further arguments. Will not be used by tsfpga, but will
                instead be sent to

                * :func:`BaseModule.get_synthesis_files()
                  <tsfpga.module.BaseModule.get_synthesis_files>`
                * :func:`BaseModule.get_ip_core_files()
                  <tsfpga.module.BaseModule.get_ip_core_files>`
                * :func:`BaseModule.get_scoped_constraints()
                  <tsfpga.module.BaseModule.get_scoped_constraints>`
                * :func:`VivadoProject.pre_create`

                along with further ``other_arguments`` supplied to :meth:`.__init__`.

                .. note::
                    This is a "kwargs" style argument. You can pass any number of named arguments.

        Return:
            True if everything went well.
        """
        print(f"Creating Vivado project in {project_path}")
        self._setup_tcl_sources()
        build_step_hooks = self._setup_and_create_build_step_hooks(project_path=project_path)

        # The pre-create hook might have side effects. E.g. change some register constants.
        # So we make a deep copy of the module list before the hook is called.
        # Note that the modules are copied before the pre-build hooks as well,
        # since we do not know if we might be performing a create-only or
        # build-only operation. The copy does not take any significant time, so this is not
        # an issue.
        self.modules = deepcopy(self.modules)

        # Send all available arguments that are reasonable to use in pre-create and module getter
        # functions. Prefer run-time values over the static.
        all_arguments = copy_and_combine_dicts(self.other_arguments, other_arguments)
        all_arguments.update(generics=self.static_generics, part=self.part)

        if not self.pre_create(
            project_path=project_path, ip_cache_path=ip_cache_path, **all_arguments
        ):
            print("ERROR: Project pre-create hook returned False. Failing the build.")
            return False

        create_vivado_project_tcl = self._create_tcl(
            project_path=project_path,
            ip_cache_path=ip_cache_path,
            build_step_hooks=build_step_hooks,
            all_arguments=all_arguments,
        )
        return run_vivado_tcl(self._vivado_path, create_vivado_project_tcl)

    def pre_create(
        self,
        **kwargs: Any,  # noqa: ANN401, ARG002
    ) -> bool:
        """
        Override this function in a subclass if you wish to do something useful with it.
        Will be called from :meth:`.create` right before the call to Vivado.

        An example use case for this function is when TCL source scripts for the Vivado project
        have to be auto generated. This could e.g. be scripts that set IP repo paths based on the
        Vivado system PATH.

        .. Note::
            This default method does nothing. Shall be overridden by project that utilize
            this mechanism.

        Arguments:
            kwargs: Will have all the :meth:`.create` parameters in it, as well as everything in
                the ``other_arguments`` argument to :func:`VivadoProject.__init__`.

        Return:
            True if everything went well.
        """
        return True

    def _build_tcl(  # noqa: PLR0913
        self,
        project_path: Path,
        output_path: Path | None,
        num_threads: int,
        run_index: int,
        all_generics: dict[str, bool | float | StringGenericValue | BitVectorGenericValue],
        synth_only: bool,
        from_impl: bool,
        impl_explore: bool,
    ) -> Path:
        """
        Make a TCL file that builds a Vivado project
        """
        project_file = self.project_file(project_path=project_path)
        if not project_file.exists():
            raise ValueError(
                f'Project "{self.name}" does not exist in the specified location: {project_file}'
            )

        build_vivado_project_tcl = project_path / "build_vivado_project.tcl"
        tcl = self.tcl.build(
            project_file=project_file,
            output_path=output_path,
            num_threads=num_threads,
            run_index=run_index,
            generics=all_generics,
            synth_only=synth_only,
            from_impl=from_impl,
            open_and_analyze_synthesized_design=self.open_and_analyze_synthesized_design,
            impl_explore=impl_explore,
        )
        create_file(build_vivado_project_tcl, tcl)

        return build_vivado_project_tcl

    def pre_build(
        self,
        **kwargs: Any,  # noqa: ANN401, ARG002
    ) -> bool:
        """
        Override this function in a subclass if you wish to do something useful with it.
        Will be called from :meth:`.build` right before the call to Vivado.

        Arguments:
            kwargs: Will have all the :meth:`.build` parameters in it. Including additional
                parameters from the user.

        Return:
            True if everything went well.
        """
        return True

    def post_build(
        self,
        **kwargs: Any,  # noqa: ANN401, ARG002
    ) -> bool:
        """
        Override this function in a subclass if you wish to do something useful with it.
        Will be called from :meth:`.build` right after the call to Vivado.

        An example use case for this function is to encrypt the bit file, or generate any other
        material that shall be included in FPGA release artifacts.

        .. Note::
            This default method does nothing. Shall be overridden by project that utilize
            this mechanism.

        Arguments:
            kwargs: Will have all the :meth:`.build` parameters in it. Including additional
                parameters from the user. Will also include ``build_result`` with
                implemented/synthesized size, which can be used for asserting the expected resource
                utilization.

        Return:
            True if everything went well.
        """
        return True

    def build(  # noqa: C901, PLR0912, PLR0913
        self,
        project_path: Path,
        output_path: Path | None = None,
        run_index: int | None = None,
        generics: dict[str, bool | float | StringGenericValue | BitVectorGenericValue]
        | None = None,
        synth_only: bool = False,
        from_impl: bool = False,
        num_threads: int = 12,
        **pre_and_post_build_parameters: Any,  # noqa: ANN401
    ) -> BuildResult:
        """
        Build a Vivado project

        Arguments:
            project_path: A path containing a Vivado project.
            output_path: Results (bit file, ...) will be placed here.
            run_index: Select Vivado run (synth_X and impl_X) to build with.
            generics: A dict with generics values (`dict(name: value)`). Use for run-time
                generics, i.e. values that can change between each build of this project.

                Compare to the create-time generics argument in :meth:`.__init__`.

                The generic value types follow the same rules as for :meth:`.__init__`.
            synth_only: Run synthesis and then stop.
            from_impl: Run the ``impl`` steps and onward on an existing synthesized design.
            num_threads: Number of parallel threads to use during run.
            pre_and_post_build_parameters: Optional further arguments. Will not be used by tsfpga,
                but will instead be sent to

                * :func:`BaseModule.pre_build() <tsfpga.module.BaseModule.pre_build>`
                * :func:`VivadoProject.pre_build`
                * :func:`VivadoProject.post_build`

                along with further ``other_arguments`` supplied to :meth:`.__init__`.

                .. note::
                    This is a "kwargs" style argument. You can pass any number of named arguments.

        Return:
            Result object with build information.
        """
        synth_only = synth_only or self.is_netlist_build

        if synth_only:
            print(f"Synthesizing Vivado project in {project_path}")
        else:
            if output_path is None:
                raise ValueError("Must specify 'output_path' when doing an implementation build.")

            print(f"Building Vivado project in {project_path}, placing artifacts in {output_path}")

        # Combine to all available generics. Prefer run-time values over static.
        all_generics = copy_and_combine_dicts(self.static_generics, generics)

        # Run index is optional to specify at build-time
        run_index = self.default_run_index if run_index is None else run_index

        # Send all available information to pre- and post build functions. Prefer build-time values
        # over the static arguments.
        all_parameters = copy_and_combine_dicts(self.other_arguments, pre_and_post_build_parameters)
        all_parameters.update(
            project_path=project_path,
            output_path=output_path,
            run_index=run_index,
            generics=all_generics,
            synth_only=synth_only,
            from_impl=from_impl,
            num_threads=num_threads,
        )

        # The pre-build hooks (either project pre-build hook or any of the module's pre-build hooks)
        # might have side effects. E.g. change some register constants. So we make a deep copy of
        # the module list before any of these hooks are called. Note that the modules are copied
        # before the pre-create hook as well, since we do not know if we might be performing a
        # create-only or build-only operation. The copy does not take any significant time, so this
        # is not an issue.
        self.modules = deepcopy(self.modules)

        result = BuildResult(name=self.name, synthesis_run_name=f"synth_{run_index}")

        for module in self.modules:
            if not module.pre_build(project=self, **all_parameters):
                print(
                    f"ERROR: Module {module.name} pre-build hook returned False. Failing the build."
                )
                result.success = False
                return result

            # Make sure register packages are up to date
            module.create_register_synthesis_files()

        if not self.pre_build(**all_parameters):
            print("ERROR: Project pre-build hook returned False. Failing the build.")
            result.success = False
            return result

        # We ignore the type of 'output_path' going from 'Path | None' to 'Path'.
        # It is only used if 'synth_only' is False, and we have an assertion that 'output_path' is
        # not None in that case above.

        build_vivado_project_tcl = self._build_tcl(
            project_path=project_path,
            output_path=output_path,
            num_threads=num_threads,
            run_index=run_index,
            all_generics=all_generics,
            synth_only=synth_only,
            from_impl=from_impl,
            impl_explore=self.impl_explore,
        )

        if not run_vivado_tcl(self._vivado_path, build_vivado_project_tcl):
            result.success = False
            return result

        result.synthesis_size = self._get_size(
            project_path=project_path, run_name=f"synth_{run_index}"
        )

        if not synth_only:
            if self.impl_explore:
                runs_path = project_path / f"{self.name}.runs"
                for run_path in runs_path.iterdir():
                    if "impl_explore_" in run_path.name:
                        # Check files for existence, since not all runs may have completed
                        bit_file = run_path / f"{self.top}.bit"
                        bin_file = run_path / f"{self.top}.bin"
                        if bit_file.exists() or bin_file.exists():
                            result.implementation_run_name = run_path.name
                            break
            else:
                result.implementation_run_name = f"impl_{run_index}"
                impl_folder = project_path / f"{self.name}.runs" / result.implementation_run_name
                bit_file = impl_folder / f"{self.top}.bit"
                bin_file = impl_folder / f"{self.top}.bin"

            shutil.copy2(bit_file, output_path / f"{self.name}.bit")
            shutil.copy2(bin_file, output_path / f"{self.name}.bin")
            result.implementation_size = self._get_size(
                project_path=project_path, run_name=result.implementation_run_name
            )

        # Send the result object, along with everything else, to the post-build function
        all_parameters.update(build_result=result)

        if not self.post_build(**all_parameters):
            print("ERROR: Project post-build hook returned False. Failing the build.")
            result.success = False

        return result

    def open(self, project_path: Path) -> bool:
        """
        Open the project in Vivado GUI.

        Arguments:
            project_path: A path containing a Vivado project.

        Return:
            True if everything went well.
        """
        return run_vivado_gui(self._vivado_path, self.project_file(project_path))

    def _get_size(self, project_path: Path, run_name: str) -> dict[str, int]:
        """
        Read the hierarchical utilization report and return the top level size
        for the specified run.
        """
        report_as_string = read_file(
            project_path / f"{self.name}.runs" / run_name / "hierarchical_utilization.rpt"
        )
        return HierarchicalUtilizationParser.get_size(report_as_string)

    def __str__(self) -> str:
        result = f"{self.name}\n"

        if self.defined_at is not None:
            result += f"Defined at: {self.defined_at.resolve()}\n"

        result += f"Type:       {self.__class__.__name__}\n"
        result += f"Top level:  {self.top}\n"

        generics = self._dict_to_string(self.static_generics) if self.static_generics else "-"
        result += f"Generics:   {generics}\n"

        if self.other_arguments:
            result += f"Arguments:  {self._dict_to_string(self.other_arguments)}\n"

        return result

    @staticmethod
    def _dict_to_string(data: dict[str, Any]) -> str:
        return ", ".join([f"{name}={value}" for name, value in data.items()])


class VivadoNetlistProject(VivadoProject):
    """
    Used for handling Vivado build of a module without top level pinning.
    """

    _clock_period_ns = 2.0

    def __init__(
        self,
        analyze_synthesis_timing: bool = False,
        build_result_checkers: list[SizeChecker | MaximumLogicLevel] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """
        Arguments:
            analyze_synthesis_timing: Enable analysis of the synthesized design's timing.
                This will make the build flow open the design, check for unhandled clock
                crossings, pulse width violations, etc, and calculate a maximum frequency estimate.

                .. note::
                    Enabling this will add significant build time (can be as much as +40%).
            build_result_checkers:
                Checkers that will be executed after a successful build. Is used to automatically
                check that e.g. resource utilization is not greater than expected.
            kwargs: Further arguments accepted by :meth:`.VivadoProject.__init__`.
        """
        super().__init__(**kwargs)

        self.is_netlist_build = True
        self.open_and_analyze_synthesized_design = analyze_synthesis_timing
        self.build_result_checkers = [] if build_result_checkers is None else build_result_checkers

    def create(
        self,
        project_path: Path,
        **kwargs: Any,  # noqa: ANN401
    ) -> bool:
        """
        Create the project.

        Arguments:
            project_path: Path where the project shall be placed.
            kwargs: All arguments as accepted by :meth:`.VivadoProject.create`.
        """
        # Create and add a TCL for auto-creating clocks.
        # Whether it is used or not depends on settings, but note that these settings can
        # change between subsequent builds, so we need to always have the file in place and be part
        # of the project.
        tcl_path = create_file(
            self._get_auto_clock_constraint_path(project_path=project_path), contents="# Unused.\n"
        )
        # Add it "early" so that any other user constraints that might be in place
        # can override the clocks.
        self.constraints.append(Constraint(file=tcl_path, processing_order="early"))

        if self.open_and_analyze_synthesized_design:
            self._set_auto_clock_constraint(tcl_path=tcl_path)

        return super().create(project_path=project_path, **kwargs)

    def build(
        self,
        project_path: Path,
        **kwargs: Any,  # noqa: ANN401
    ) -> BuildResult:
        """
        Build the project.

        Arguments:
            project_path: A path containing a Vivado project.
            kwargs: All other arguments as accepted by :meth:`.VivadoProject.build`.
        """
        # Update hook script files, since the user might turn on and off the
        # 'analyze_synthesis_timing' flag, which affects what scripts are added to the
        # post-synthesis hook step.
        self._setup_and_create_build_step_hooks(project_path=project_path)

        if self.open_and_analyze_synthesized_design:
            # Update, since the HDL (and details about clocks) might have changed since last time.
            self._set_auto_clock_constraint(
                tcl_path=self._get_auto_clock_constraint_path(project_path=project_path)
            )

        result = super().build(project_path=project_path, **kwargs)

        if not result.success:
            print(f'Can not do post-build check for "{self.name}" since it did not succeed.')
            return result

        result.success = result.success and self._check_size(build_result=result)

        run_path = project_path / f"{self.name}.runs" / result.synthesis_run_name

        if self.open_and_analyze_synthesized_design:
            # Report might not exist or might not contain any slack information,
            # if we could not auto detect any clocks.
            # Could happen if the top-level file is Verilog, or if there are no clocks at all,
            # or if our auto-detect failed.
            with contextlib.suppress(FileNotFoundError, FoundNoSlackError):
                slack_ns = TimingParser.get_slack_ns(read_file(run_path / "timing.rpt"))
                # Positive slack = margin, meaning we can use a lower period,
                # meaning higher frequency.
                # Hence the subtraction.
                result.maximum_synthesis_frequency_hz = 1e9 / (self._clock_period_ns - slack_ns)

        result.logic_level_distribution = self._get_logic_level_distribution(run_path=run_path)

        return result

    def _get_auto_clock_constraint_path(self, project_path: Path) -> Path:
        return project_path / f"auto_create_{self.top}_clocks.tcl"

    def _set_auto_clock_constraint(self, tcl_path: Path) -> None:
        # Try to auto-detect clocks in the top-level file, and create them automatically.
        top_file = self._find_top_level_file()
        clock_names = (
            self._find_vhdl_clock_names(vhdl_file=top_file)
            if top_file.path.suffix.lower() in HdlFile.file_endings_mapping[HdlFile.Type.VHDL]
            else []
        )

        if clock_names:
            create_clock_tcl = "\n".join(
                [
                    f'create_clock -name "{clock_name}" -period {self._clock_period_ns} '
                    f'[get_ports "{clock_name}"];'
                    for clock_name in clock_names
                ]
            )
            tcl = f"""\
# Auto-create the clocks found in the top-level HDL file:
# {top_file.path}
{create_clock_tcl}
"""
            create_file(tcl_path, tcl)

    def _find_top_level_file(self) -> HdlFile:
        top_files = [
            hdl_file
            for module in self.modules
            for hdl_file in module.get_synthesis_files()
            if hdl_file.path.stem == self.top
        ]
        if len(top_files) == 0:
            raise ValueError(
                f'Could not find HDL source file corresponding to top-level "{self.top}".'
            )
        if len(top_files) > 1:
            raise ValueError(
                f"Found multiple HDL source files corresponding to "
                f'top-level "{self.top}": {top_files}.'
            )

        return top_files[0]

    def _find_vhdl_clock_names(self, vhdl_file: HdlFile) -> list[str]:
        """
        Find a list of all clock port names in the VHDL file.
        It handles all ports that contain "clk" or "clock" in their name as clocks.
        This magic word can be either in the beginning, middle or end of the port name
        (separated by underscore).
        """
        top_vhd = read_file(vhdl_file.path)

        entity_matches = re.findall(
            rf"^\s*entity\s+{self.top}\s+is(.+)^\s*end\s+entity",
            top_vhd,
            re.DOTALL | re.MULTILINE | re.IGNORECASE,
        )
        if len(entity_matches) == 0:
            raise ValueError(
                f'Could not find "{self.top}" entity declaration in "{vhdl_file.path}".'
            )
        if len(entity_matches) > 1:
            raise ValueError(
                f'Found multiple "{self.top}" entity declarations in "{vhdl_file.path}".'
            )

        entity_vhd = entity_matches[0]
        port_matches = re.findall(
            r"^\s*port(\s|\()(.+)$",
            entity_vhd,
            re.DOTALL | re.MULTILINE | re.IGNORECASE,
        )

        if len(port_matches) == 0:
            raise ValueError(f'Could not find "port" block in "{vhdl_file.path}".')
        if len(port_matches) > 1:
            raise ValueError(f'Found multiple "port" blocks in "{vhdl_file.path}".')

        port_vhd = port_matches[0][1]
        clock_matches = re.findall(
            r"^\s*(\w+_)?(clk|clock)(_\w+)?\s*:",
            port_vhd,
            re.DOTALL | re.MULTILINE | re.IGNORECASE,
        )

        return [f"{prefix}{clock}{suffix}" for prefix, clock, suffix in clock_matches]

    def _check_size(self, build_result: BuildResult) -> bool:
        success = True
        for build_result_checker in self.build_result_checkers:
            checker_result = build_result_checker.check(build_result)
            success = success and checker_result

        return success

    @staticmethod
    def _get_logic_level_distribution(run_path: Path) -> str:
        return LogicLevelDistributionParser.get_table(
            read_file(run_path / "logic_level_distribution.rpt")
        )


class VivadoIpCoreProject(VivadoProject):
    """
    A Vivado project that is only used to generate simulation models of IP cores.
    """

    ip_cores_only = True

    def __init__(
        self,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """
        Arguments:
            kwargs: Arguments as accepted by :meth:`.VivadoProject.__init__`.
        """
        super().__init__(**kwargs)

    def build(
        self,
        **kwargs: Any,  # noqa: ANN401
    ) -> NoReturn:
        """
        Not implemented.
        """
        raise NotImplementedError("IP core project can not be built")


def copy_and_combine_dicts(
    dict_first: dict[str, Any] | None, dict_second: dict[str, Any] | None
) -> dict[str, Any]:
    """
    Will prefer values in the second dict, in case the same key occurs in both.
    Will return an empty dictionary if both are ``None``.
    """
    if dict_first is None:
        if dict_second is None:
            return {}

        return dict_second.copy()

    if dict_second is None:
        return dict_first.copy()

    result = dict_first.copy()
    result.update(dict_second)

    return result
