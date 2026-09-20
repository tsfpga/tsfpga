# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

import os
import sys
import tempfile
from contextlib import contextmanager
from copy import deepcopy
from inspect import signature
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, Any, NoReturn

from vunit.ui import VUnit

from tsfpga.generics import (
    BitVectorGenericValue,
    GenericValue,
    GenericValues,
    StringGenericValue,
)
from tsfpga.hdl_file import HdlFile
from tsfpga.system_utils import (
    copy_and_combine_dicts,
    create_directory,
    create_file,
    read_file,
)

from .build_result import YosysBuildResult
from .common import run_ghdl, run_yosys, to_yosys_path
from .utilization_parser import (
    YosysIntelUtilizationParser,
    YosysMicrochipUtilizationParser,
    YosysUtilizationParser,
    YosysXilinxUtilizationParser,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from tsfpga.module import BaseModule
    from tsfpga.module_list import ModuleList
    from tsfpga.vivado.build_result_checker import SizeChecker


class YosysNetlistBuild:
    """
    Used for handling a synthesis-only (netlist) build of a design, using Yosys with the
    ``ghdl-yosys-plugin`` as the VHDL front end.

    Since this is a netlist build, there is no implementation (place & route) step, and hence
    no bitstream is produced.
    This is a great tool for getting quick feedback on the resource utilization of a design, or
    a sub-component of a design, during development.

    The ``top`` is typically a VHDL entity, in which case all of its VHDL dependencies are found
    automatically via the compile order.
    It can also be a Verilog/SystemVerilog module (or the design can have no VHDL at all), in
    which case any VHDL entities that shall be instantiated from it (or from other VHDL
    entities) must be explicitly listed using the ``vhdl_entities`` argument.

    .. note::
        Requires GHDL, Yosys, and the ``ghdl-yosys-plugin`` module to be installed and
        available.
        See the `ghdl-yosys-plugin documentation
        <https://github.com/ghdl/ghdl-yosys-plugin>`__ for installation instructions.
    """

    #: Will always be ``True`` for this class, since it is a netlist build.
    is_netlist_build = True

    #: The parser used to interpret the Yosys utilization report.
    #: The base class uses the one that reports only raw cell counts, since the plain ``synth``
    #: command does not target any specific architecture.
    #: Overridden by the architecture-specific subclasses (:class:`.YosysXilinxNetlistBuild`,
    #: :class:`.YosysIntelNetlistBuild`, :class:`.YosysMicrochipNetlistBuild`).
    _utilization_parser: type[YosysUtilizationParser] = YosysUtilizationParser

    #: Whether the ``synth_command`` needs an explicit ``-flatten`` flag appended to it in order
    #: to flatten the design before synthesis (see :meth:`._get_synth_command`).
    #: This is the case for e.g. the ``synth`` and ``synth_xilinx`` commands.
    #: Some ``synth_*`` commands (e.g. ``synth_intel`` and ``synth_microchip``) instead flatten
    #: the design by default, and do not accept a ``-flatten`` flag. Such subclasses shall set
    #: this attribute to ``False``.
    _needs_explicit_flatten_flag: bool = True

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        name: str,
        modules: ModuleList,
        top: str | None = None,
        vhdl_entities: list[str] | None = None,
        generics: GenericValues | None = None,
        build_result_checkers: list[SizeChecker] | None = None,
        synth_command: str = "synth",
        vhdl_standard: str = "08",
        ghdl_path: Path | None = None,
        yosys_path: Path | None = None,
        ghdl_plugin_path: Path | None = None,
        ghdl_prefix: Path | None = None,
        defined_at: Path | None = None,
        **other_arguments: Any,  # noqa: ANN401
    ) -> None:
        """
        Class constructor. Performs a shallow copy of the mutable arguments, so that the user
        can e.g. append items to their list after creating an object.

        Arguments:
            name: Project name.
            modules: Modules that shall be included in the build.
                Only VHDL source files are considered, since the build uses the GHDL front end.
            top: Name of top level entity.
                If left out, the top level name will be inferred from the ``name``.
                Is typically a VHDL entity, but can also be a Verilog/SystemVerilog module -- see
                ``vhdl_entities`` below.
            vhdl_entities: Only used if ``top`` is not a VHDL entity (i.e. if it is a
                Verilog/SystemVerilog module, or if the design has no VHDL at all).
                A list of the names of the VHDL entities that shall be made available for
                instantiation from the non-VHDL top level (or from other VHDL entities), since
                there is in that case no single VHDL top level to automatically find these
                dependencies from.
                Not used, and shall be left as ``None``, if ``top`` is a VHDL entity, since in
                that case all of its VHDL dependencies are found automatically via the compile
                order.
            generics: A dict with generics values (name: value). Use this parameter
                for "static" generics that do not change between multiple builds of this
                project.

                Compare to the build-time generic argument in :meth:`build`.

                The generic value shall be of type :data:`.GenericValue`.
            build_result_checkers:
                Checkers that will be executed after a successful build. Is used to automatically
                check that e.g. resource utilization is not greater than expected.
            synth_command: The Yosys ``synth*`` command that shall be used to synthesize the
                design (e.g. ``"synth"`` or ``"synth_xilinx"``).
            vhdl_standard: The VHDL standard that shall be used by GHDL when analyzing the
                source files (e.g. ``"93"`` or ``"08"``).
            ghdl_path: Path to the GHDL executable.
                If omitted, the default location from the system PATH will be used.
            yosys_path: Path to the Yosys executable.
                If omitted, the default location from the system PATH will be used.
            ghdl_plugin_path: Path to the ``ghdl-yosys-plugin`` module (typically named
                ``ghdl.so``).
                Can be left out if the plugin is already available to Yosys without explicitly
                loading it (e.g. if it has been installed in the Yosys plugin directory).
            ghdl_prefix: Value to set the ``GHDL_PREFIX`` environment variable to when running
                Yosys with the ``ghdl-yosys-plugin``. The plugin is loaded as part of the Yosys
                process, and can not find the GHDL standard libraries (``std``, ``ieee``, ...)
                on its own the way the standalone ``ghdl`` executable can.
                Corresponds to the "library prefix" printed by ``ghdl --disp-config``.
                If left out, this is auto-detected by calling ``ghdl --disp-config`` against
                the executable given by ``ghdl_path`` above.
                Set explicitly to override the auto-detected value, or if auto-detection fails.
            defined_at: Optional path to the file where you defined this project.
                To get a useful ``build_fpga.py --list`` message. Is useful when you have many
                projects set up.
            other_arguments: Optional further arguments. Will not be used by tsfpga, but will
                instead be passed on to

                * :func:`BaseModule.get_synthesis_files()
                  <tsfpga.module.BaseModule.get_synthesis_files>`
                * :func:`BaseModule.pre_build() <tsfpga.module.BaseModule.pre_build>`
                * :func:`YosysNetlistBuild.pre_create`
                * :func:`YosysNetlistBuild.pre_build`
                * :func:`YosysNetlistBuild.post_build`

                along with further arguments supplied at build-time to :meth:`.create` and
                :meth:`.build`.

                .. note::
                    This is a "kwargs" style argument. You can pass any number of named arguments.
        """
        self.name = name
        self.modules = modules.copy()
        self.top = name + "_top" if top is None else top
        self.vhdl_entities = [] if vhdl_entities is None else list(vhdl_entities)
        self.static_generics = {} if generics is None else generics.copy()
        self.build_result_checkers = (
            [] if build_result_checkers is None else build_result_checkers.copy()
        )
        self.synth_command = synth_command
        self.defined_at = defined_at
        self.other_arguments = None if other_arguments is None else other_arguments.copy()

        self._vhdl_standard = vhdl_standard
        self._ghdl_path = ghdl_path
        self._yosys_path = yosys_path
        self._ghdl_plugin_path = ghdl_plugin_path
        self._ghdl_prefix = ghdl_prefix

        # Lazily created/cached. See '_get_vunit_project'.
        self._vunit_proj: VUnit | None = None
        # Owns the VUnit project's throwaway output directory: holding it here ties that
        # directory's lifetime to this object's.
        self._vunit_output_dir: tempfile.TemporaryDirectory[str] | None = None

    def project_file(self, project_path: Path) -> Path:
        """
        Arguments:
            project_path: A path containing a Yosys netlist build.

        Return:
            The Yosys command script of this build, in the given folder.
        """
        return project_path / f"{self.name}.ys"

    def _get_ghdl_workdir(self, project_path: Path) -> Path:
        return project_path / "ghdl"

    def _get_vunit_project(self) -> VUnit:
        if self._vunit_proj is None:
            # VUnit is used only to calculate the compile order of the VHDL source files.
            # Cleanup errors are ignored because this is scratch space: failing to delete it
            # must not fail a build.
            self._vunit_output_dir = tempfile.TemporaryDirectory(
                prefix="tsfpga_yosys_vunit_", ignore_cleanup_errors=True
            )
            argv = [
                "--output-path",
                self._vunit_output_dir.name,
                "--log-level",
                "error",
                "--no-color",
            ]

            # VUnit's simulation builtins must not be compiled, they would add dozens of
            # VUnit-internal VHDL files to the compile order.
            # On the latest VUnit release they are compiled unless 'compile_builtins' is set to
            # False. That argument does not exist in newer VUnit versions, which instead do not
            # compile them unless 'add_vhdl_builtins' is called explicitly.
            builtins_arguments = (
                {"compile_builtins": False}
                if "compile_builtins" in signature(VUnit.from_argv).parameters
                else {}
            )

            with _suppress_stdout():
                self._vunit_proj = VUnit.from_argv(argv=argv, **builtins_arguments)

            for module in self.modules:
                vunit_library = self._vunit_proj.add_library(
                    library_name=module.library_name, allow_duplicate=True
                )
                for hdl_file in module.get_synthesis_files(
                    include_verilog_files=False, include_systemverilog_files=False
                ):
                    vunit_library.add_source_file(hdl_file.path)

        return self._vunit_proj

    def _find_vhdl_source_file(self, entity_name: str) -> tuple[BaseModule, HdlFile] | None:
        """
        Arguments:
            entity_name: Name of a VHDL entity.

        Return: A tuple ``(module, hdl_file)`` for the VHDL source file that defines the given
            entity name, or ``None`` if no such VHDL source file is found in the modules of
            this build.
        """
        matches = [
            (module, hdl_file)
            for module in self.modules
            for hdl_file in module.get_synthesis_files(
                include_verilog_files=False, include_systemverilog_files=False
            )
            if hdl_file.path.stem == entity_name
        ]

        if len(matches) > 1:
            raise ValueError(f'Found multiple VHDL source files for entity "{entity_name}".')

        return matches[0] if matches else None

    def _get_synthesis_files_in_compile_order(self) -> list[tuple[str, str]]:
        """
        Return: A list of tuples ``(file_path, library_name)`` in the order they need to be
            analyzed by GHDL.
        """
        vunit_proj = self._get_vunit_project()
        top_level_match = self._find_vhdl_source_file(self.top)

        if top_level_match is None:
            # The 'top' is not a VHDL entity (e.g. it is a Verilog/SystemVerilog module, or the
            # design has no VHDL at all). There is no single VHDL top level to compute an
            # implementation subset relative to, so analyze all the VHDL source files in the
            # modules of this build instead.
            compile_order = vunit_proj.get_compile_order()
        else:
            # Look up the source file directly by its (unique, resolved) path, rather than
            # reconstructing a file name pattern, since the VHDL file ending can be either
            # '.vhd', '.vhdl' or '.vho' (see 'HdlFile.file_endings_mapping').
            _, top_hdl_file = top_level_match
            top_source_file = vunit_proj.get_source_file(str(top_hdl_file.path.resolve()))
            compile_order = vunit_proj.get_implementation_subset([top_source_file])

        return [
            (Path(source_file.name).resolve().as_posix(), source_file.library.name)
            for source_file in compile_order
        ]

    def _get_verilog_source_files(self) -> list[Path]:
        """
        Return: A list of paths to all the Verilog and SystemVerilog source files (not headers)
            found in the modules of this build.
            These are read directly by Yosys, bypassing GHDL entirely, and may be instantiated
            from the VHDL top level as unbound components with a matching name.
        """
        source_types = (HdlFile.Type.VERILOG_SOURCE, HdlFile.Type.SYSTEMVERILOG_SOURCE)

        return [
            hdl_file.path
            for module in self.modules
            for hdl_file in module.get_synthesis_files(include_vhdl_files=False)
            if hdl_file.type in source_types
        ]

    def _get_verilog_include_directories(self) -> list[Path]:
        """
        Return: A sorted list of the unique directories that contain Verilog and SystemVerilog
            header files in the modules of this build.
            Used so that Yosys can resolve ```` `include ```` directives in the source files.
        """
        header_types = (HdlFile.Type.VERILOG_HEADER, HdlFile.Type.SYSTEMVERILOG_HEADER)

        return sorted(
            {
                hdl_file.path.parent
                for module in self.modules
                for hdl_file in module.get_synthesis_files(include_vhdl_files=False)
                if hdl_file.type in header_types
            }
        )

    def _get_read_verilog_command(self) -> str | None:
        """
        Return: A Yosys ``read_verilog`` command that reads all the Verilog and SystemVerilog
            source files found in the modules of this build, or ``None`` if there are no such
            files.
        """
        verilog_files = self._get_verilog_source_files()
        if not verilog_files:
            return None

        # Note the asymmetry: file paths below are quoted, since Yosys splits unquoted command
        # arguments on whitespace, which would otherwise break for paths containing spaces
        # (e.g. common on Windows).
        # Include directories can NOT be quoted, however. Yosys' 'read_verilog' takes the
        # directory as everything after the "-I" in the token, so a quoted path ends up
        # containing the quote characters and never matches a real directory.
        # This means that include directories containing spaces are not supported by Yosys.
        include_flags = " ".join(
            f"-I{to_yosys_path(directory)}" for directory in self._get_verilog_include_directories()
        )
        file_arguments = " ".join(f'"{to_yosys_path(file_path)}"' for file_path in verilog_files)

        # The '-sv' flag enables the SystemVerilog parser, which is a superset of Verilog and
        # hence works fine for plain Verilog files as well.
        command = f"read_verilog -sv {include_flags} {file_arguments}"
        return " ".join(command.split())

    def create(
        self,
        project_path: Path,
        **other_arguments: Any,  # noqa: ANN401
    ) -> bool:
        """
        Analyze all the VHDL source files with GHDL, so that the design is ready to be
        elaborated and synthesized by :meth:`.build`.

        Arguments:
            project_path: Path where the GHDL analysis result shall be placed.
            other_arguments: Optional further arguments. Will not be used by tsfpga, but will
                instead be sent to

                * :func:`BaseModule.get_synthesis_files()
                  <tsfpga.module.BaseModule.get_synthesis_files>`
                * :func:`YosysNetlistBuild.pre_create`

                along with further ``other_arguments`` supplied to :meth:`.__init__`.

        Return:
            True if everything went well.
        """
        print(f"Creating Yosys netlist build {self.name} in {project_path}")

        # The pre-create hook might have side effects. E.g. change some register constants.
        # So we make a deep copy of the module list before the hook is called.
        self.modules = deepcopy(self.modules)

        all_arguments = copy_and_combine_dicts(self.other_arguments, other_arguments)
        if not self.pre_create(project_path=project_path, **all_arguments):
            print("ERROR: Project pre-create hook returned False. Failing the build.")
            return False

        workdir = self._get_ghdl_workdir(project_path=project_path)
        create_directory(workdir, empty=True)

        for file_path, library_name in self._get_synthesis_files_in_compile_order():
            arguments = [
                "-a",
                f"--std={self._vhdl_standard}",
                f"--workdir={workdir}",
                f"-P={workdir}",
                f"--work={library_name}",
                file_path,
            ]

            if not run_ghdl(ghdl_path=self._ghdl_path, arguments=arguments, cwd=workdir):
                print(f'ERROR: GHDL analysis failed for "{self.name}".')
                return False

        return True

    def pre_create(
        self,
        **kwargs: Any,  # noqa: ANN401, ARG002
    ) -> bool:
        """
        Override this function in a subclass if you wish to do something useful with it.
        Will be called from :meth:`.create` right before the GHDL analysis is started.

        .. Note::
            This default method does nothing. Shall be overridden by project that utilize
            this mechanism.

        Arguments:
            kwargs: Will have all the :meth:`.create` parameters in it, as well as everything in
                the ``other_arguments`` argument to :func:`YosysNetlistBuild.__init__`.

        Return:
            True if everything went well.
        """
        return True

    def _get_synth_command(self) -> str:
        # The design is flattened so that the produced utilization report contains the
        # primitive counts for the whole design, and not just the top level.
        flatten_flag = " -flatten" if self._needs_explicit_flatten_flag else ""
        return f"{self.synth_command} -top {self.top}{flatten_flag}"

    def _get_ghdl_elaborate_command(
        self, workdir: Path, entity_name: str, library_name: str, generic_arguments: str
    ) -> str:
        # Note: Unlike the paths used in '_get_read_verilog_command' and '_get_yosys_script',
        # the 'workdir' path below is deliberately *not* quoted. The 'ghdl' command, provided by
        # the 'ghdl-yosys-plugin', tokenizes its own argument line by naive whitespace splitting
        # and does not strip surrounding quotes, so quoting here would actually break paths that
        # contain spaces even worse than leaving them unquoted (verified empirically). This is a
        # limitation of the plugin, not something that can be worked around from this side.
        parts = [
            "ghdl",
            f"--std={self._vhdl_standard}",
            f"--workdir={workdir}",
            f"-P={workdir}",
            f"--work={library_name}",
        ]
        if generic_arguments:
            parts.append(generic_arguments)
        parts.append(entity_name)

        return " ".join(parts)

    def _get_ghdl_commands(
        self,
        workdir: Path,
        all_generics: GenericValues,
    ) -> list[str]:
        """
        Return: A list of Yosys ``ghdl`` commands that elaborate the VHDL entities of this
            build, making them available to Yosys.
        """
        top_level_match = self._find_vhdl_source_file(self.top)
        if top_level_match is not None:
            # The 'top' is a VHDL entity: elaborate it directly. GHDL will pull in everything it
            # depends on, including any Verilog/SystemVerilog modules read by
            # '_get_read_verilog_command', which are bound by name to unbound VHDL component
            # instantiations.
            top_level_module, _ = top_level_match
            entities = [(self.top, top_level_module)]
        else:
            # The 'top' is a Verilog/SystemVerilog module (or the design has no VHDL at all).
            # Elaborate each of the explicitly listed 'vhdl_entities' individually, so that they
            # become available (under their own entity name) for Yosys's 'hierarchy' pass to
            # bind to instantiations from the Verilog/SystemVerilog top level (or from other
            # VHDL entities). Any entity that ends up unused is pruned by Yosys.
            entities = []
            for entity_name in self.vhdl_entities:
                match = self._find_vhdl_source_file(entity_name)
                if match is None:
                    raise ValueError(
                        f'Could not find a VHDL source file for entity "{entity_name}" '
                        '(listed in "vhdl_entities").'
                    )
                module, _ = match
                entities.append((entity_name, module))

        generic_arguments = " ".join(
            f"-g{name}={_get_ghdl_generic_value(value)}" for name, value in all_generics.items()
        )

        return [
            self._get_ghdl_elaborate_command(
                workdir=workdir,
                entity_name=entity_name,
                library_name=module.library_name,
                generic_arguments=generic_arguments,
            )
            for entity_name, module in entities
        ]

    def _get_hierarchy_command(self, all_generics: GenericValues) -> str | None:
        """
        Return: A Yosys ``hierarchy`` command that sets the top level parameters, when ``top`` is
            a Verilog/SystemVerilog module. ``None`` when there is nothing to set, or when
            ``top`` is a VHDL entity (where generics are instead passed to GHDL).
        """
        if not all_generics or self._find_vhdl_source_file(self.top) is not None:
            return None

        # Note that the 'synth' command runs 'hierarchy' itself, but the parameter values set
        # here are preserved by that later run.
        parameters = " ".join(
            f"-chparam {name} {_get_verilog_parameter_value(value)}"
            for name, value in all_generics.items()
        )
        return f"hierarchy -top {self.top} {parameters}"

    def _get_yosys_script(
        self,
        workdir: Path,
        all_generics: GenericValues,
        utilization_report_file: Path,
    ) -> str:
        commands = []

        # Read any Verilog/SystemVerilog source files before elaborating the VHDL, so that Yosys
        # can bind the unbound components in the VHDL design to the modules read here.
        read_verilog_command = self._get_read_verilog_command()
        if read_verilog_command is not None:
            commands.append(read_verilog_command)

        commands += self._get_ghdl_commands(workdir=workdir, all_generics=all_generics)

        hierarchy_command = self._get_hierarchy_command(all_generics=all_generics)
        if hierarchy_command is not None:
            commands.append(hierarchy_command)

        commands += [
            self._get_synth_command(),
            f'tee -o "{to_yosys_path(utilization_report_file)}" stat',
        ]

        return "\n".join(commands) + "\n"

    def build(
        self,
        project_path: Path,
        output_path: Path | None = None,
        generics: GenericValues | None = None,
        **pre_and_post_build_parameters: Any,  # noqa: ANN401
    ) -> YosysBuildResult:
        """
        Synthesize the design with Yosys.

        Arguments:
            project_path: A path containing the result of a call to :meth:`.create`.
            output_path: The utilization report, and any other artifacts, will be placed here.
                Will default to ``project_path`` if not set.
            generics: A dict with generics values (`dict(name: value)`). Use for run-time
                generics, i.e. values that can change between each build of this project.
                Compare to the create-time generics argument in :meth:`.__init__`.
                The generic value types follow the same rules as for :meth:`.__init__`.
            pre_and_post_build_parameters: Optional further arguments. Will not be used by
                tsfpga, but will instead be sent to

                * :func:`BaseModule.pre_build() <tsfpga.module.BaseModule.pre_build>`
                * :func:`YosysNetlistBuild.pre_build`
                * :func:`YosysNetlistBuild.post_build`

                along with further ``other_arguments`` supplied to :meth:`.__init__`.

                .. note::
                    This is a "kwargs" style argument. You can pass any number of named arguments.

        Return:
            Result object with build information.
        """
        workdir = self._get_ghdl_workdir(project_path=project_path)
        if not workdir.exists():
            raise ValueError(
                f'Project "{self.name}" does not exist in the specified location: {project_path}. '
                "Call 'create' before 'build'."
            )

        output_path = project_path if output_path is None else output_path
        create_directory(output_path, empty=False)

        print(f"Synthesizing Yosys netlist build {self.name} in {project_path}")

        all_generics = copy_and_combine_dicts(self.static_generics, generics)
        all_parameters = copy_and_combine_dicts(self.other_arguments, pre_and_post_build_parameters)
        all_parameters.update(
            project_path=project_path, output_path=output_path, generics=all_generics
        )

        # See 'create' for the rationale of doing this copy here as well.
        self.modules = deepcopy(self.modules)

        result = YosysBuildResult(name=self.name)

        for module in self.modules:
            if not module.pre_build(project=self, **all_parameters):
                print(
                    f"ERROR: Module {module.name} pre-build hook returned False. Failing the build."
                )
                result.success = False
                return result

            # Make sure register packages are up to date.
            module.create_register_synthesis_files()

        if not self.pre_build(**all_parameters):
            print("ERROR: Project pre-build hook returned False. Failing the build.")
            result.success = False
            return result

        utilization_report_file = output_path / f"{self.name}_utilization.txt"
        script = self._get_yosys_script(
            workdir=workdir,
            all_generics=all_generics,
            utilization_report_file=utilization_report_file,
        )

        script_file = self.project_file(project_path=output_path)
        create_file(script_file, script)

        if not run_yosys(
            yosys_path=self._yosys_path,
            ghdl_plugin_path=self._ghdl_plugin_path,
            script_file=script_file,
            cwd=output_path,
            ghdl_path=self._ghdl_path,
            ghdl_prefix=self._ghdl_prefix,
        ):
            print(f'ERROR: Yosys synthesis failed for "{self.name}".')
            result.success = False
            return result

        result.synthesis_size = self._get_size(utilization_report_file=utilization_report_file)
        result.success = self._check_size(build_result=result)

        # Send the result object, along with everything else, to the post-build function.
        all_parameters.update(build_result=result)

        if not self.post_build(**all_parameters):
            print("ERROR: Project post-build hook returned False. Failing the build.")
            result.success = False

        return result

    def pre_build(
        self,
        **kwargs: Any,  # noqa: ANN401, ARG002
    ) -> bool:
        """
        Override this function in a subclass if you wish to do something useful with it.
        Will be called from :meth:`.build` right before the call to Yosys.

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
        Will be called from :meth:`.build` right after the call to Yosys.

        .. Note::
            This default method does nothing. Shall be overridden by project that utilize
            this mechanism.

        Arguments:
            kwargs: Will have all the :meth:`.build` parameters in it. Including additional
                parameters from the user. Will also include ``build_result``.

        Return:
            True if everything went well.
        """
        return True

    def _get_size(self, utilization_report_file: Path) -> dict[str, int]:
        return self._utilization_parser.get_size(report=read_file(utilization_report_file))

    def _check_size(self, build_result: YosysBuildResult) -> bool:
        success = True
        for build_result_checker in self.build_result_checkers:
            checker_result = build_result_checker.check(build_result)
            success = success and checker_result

        return success

    def open(
        self,
        project_path: Path,
    ) -> NoReturn:
        """
        Not implemented. A Yosys netlist build has no GUI to open.
        """
        raise NotImplementedError("Yosys netlist build can not be opened")

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


def _get_synth_command_with_family(synth_command: str, family: str | None) -> str:
    """
    Shared helper used by the architecture-specific subclasses below to append an optional
    ``-family <family>`` flag to their ``synth_*`` command.
    """
    return synth_command if family is None else f"{synth_command} -family {family}"


class YosysXilinxNetlistBuild(YosysNetlistBuild):
    """
    Used for handling a Yosys netlist build that targets Xilinx primitives (LUTs, FDs,
    RAMBs, DSP48s, ...), using the Yosys ``synth_xilinx`` command.

    Since the produced utilization report uses the same resource naming convention as the
    Vivado utilization report, the checkers in :mod:`.vivado.build_result_checker` can be used
    directly to check e.g. the LUT or RAMB count of the design.
    """

    _utilization_parser = YosysXilinxUtilizationParser

    def __init__(
        self,
        family: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """
        Arguments:
            family: Optionally target a specific Xilinx device family (e.g. ``"xc7"``).
                See the Yosys ``synth_xilinx`` command documentation for valid values.
            kwargs: Further arguments accepted by :meth:`.YosysNetlistBuild.__init__`.
                Note that ``synth_command`` may not be set, since it is set by this class.
        """
        synth_command = _get_synth_command_with_family(synth_command="synth_xilinx", family=family)
        super().__init__(synth_command=synth_command, **kwargs)


class YosysIntelNetlistBuild(YosysNetlistBuild):
    """
    Used for handling a Yosys netlist build that targets Intel (Altera) primitives
    (``*_lcell_comb``, ``dffeas``, ``altsyncram``, ...), using the Yosys ``synth_intel`` command.

    .. note::
        Targets the MAX10, Cyclone IV, Cyclone IV E and Cyclone 10 LP families.
        For ALM-based Intel devices (Cyclone V, Cyclone 10 GX) the ``synth_intel_alm`` command
        shall be used instead, which is not covered by this class. Use the base
        :class:`.YosysNetlistBuild` with ``synth_command="synth_intel_alm"`` for that, though note
        that no aggregated resource counts will be available in that case.

    Since the produced utilization report uses the resource names ``"Total LUTs"``, ``"FFs"``,
    ``"Block RAMs"`` and ``"DSP Blocks"``, the corresponding checkers in
    :mod:`.vivado.build_result_checker` can be used directly.
    """

    _utilization_parser = YosysIntelUtilizationParser
    _needs_explicit_flatten_flag = False

    def __init__(
        self,
        family: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """
        Arguments:
            family: Optionally target a specific Intel device family (e.g. ``"cycloneiv"``).
                See the Yosys ``synth_intel`` command documentation for valid values.
            kwargs: Further arguments accepted by :meth:`.YosysNetlistBuild.__init__`.
                Note that ``synth_command`` may not be set, since it is set by this class.
        """
        synth_command = _get_synth_command_with_family(synth_command="synth_intel", family=family)
        super().__init__(synth_command=synth_command, **kwargs)


class YosysMicrochipNetlistBuild(YosysNetlistBuild):
    """
    Used for handling a Yosys netlist build that targets Microchip primitives
    (``CFG*``, ``SLE``, ``RAM1K20``, ``MACC_PA``, ...), using the Yosys ``synth_microchip``
    command.

    .. note::
        Targets the PolarFire family, which is the only one currently supported by the Yosys
        ``synth_microchip`` command.

    Since the produced utilization report uses the resource names ``"Total LUTs"``, ``"FFs"``,
    ``"Block RAMs"`` and ``"DSP Blocks"``, the corresponding checkers in
    :mod:`.vivado.build_result_checker` can be used directly.
    """

    _utilization_parser = YosysMicrochipUtilizationParser
    _needs_explicit_flatten_flag = False

    def __init__(
        self,
        family: str | None = None,
        discard_ffinit: bool = False,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """
        Arguments:
            family: Optionally target a specific Microchip device family.
                See the Yosys ``synth_microchip`` command documentation for valid values.
            discard_ffinit: The Yosys ``synth_microchip`` command will raise an error if the
                design contains a flip-flop with an initial value that can not be legalized to
                a supported flip-flop type (which is a common occurrence, since e.g. VHDL signals
                initialized to a default value result in flip-flops with an initial value).
                Set this to ``True`` to instead discard the initial value and let synthesis
                proceed. Corresponds to the Yosys ``-discard-ffinit`` flag.
            kwargs: Further arguments accepted by :meth:`.YosysNetlistBuild.__init__`.
                Note that ``synth_command`` may not be set, since it is set by this class.
        """
        synth_command = _get_synth_command_with_family(
            synth_command="synth_microchip", family=family
        )
        if discard_ffinit:
            synth_command += " -discard-ffinit"

        super().__init__(synth_command=synth_command, **kwargs)


def _get_ghdl_generic_value(
    value: GenericValue,
) -> str:
    """
    Convert a generic value of a native Python type (or one of the tsfpga generic value
    wrapper classes) to a string suitable for the ``-g<name>=<value>`` argument of the
    ``ghdl-yosys-plugin`` ``ghdl`` command.
    """
    # Note that bool is a sub-class of int in Python, so check for bool must be first.
    if isinstance(value, bool):
        # The plugin does not recognize "1"/"0" as boolean literals, only "true"/"false".
        return "true" if value else "false"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        return str(value)

    if isinstance(value, BitVectorGenericValue):
        return value.value

    if isinstance(value, StringGenericValue):
        return value.value

    message = f'Unsupported type for generic. Got type="{type(value)}", value="{value}".'
    if isinstance(value, str):
        message += (
            " Please use either of the explicit types StringGenericValue or BitVectorGenericValue."
        )

    raise TypeError(message)


#: Guards the global ``sys.stdout`` swap in :func:`._suppress_stdout`.
#: Netlist builds are created from VUnit test-runner worker threads (see
#: :class:`.BuildProjectList`), which installs its own object as the global ``sys.stdout``.
#: Without this lock, two threads entering the swap concurrently interleave their
#: save/restore, and the last one out installs an already-closed file as ``sys.stdout``,
#: breaking every subsequent print in the process.
_SUPPRESS_STDOUT_LOCK = Lock()


@contextmanager
def _suppress_stdout() -> Iterator[None]:
    """
    Suppress the (very chatty) printouts made by VUnit when creating a project.

    Note that this swaps the process-global ``sys.stdout``, so it is serialized with a lock and
    the critical section is kept as small as possible.
    """
    with _SUPPRESS_STDOUT_LOCK, Path(os.devnull).open("w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout


def _get_verilog_parameter_value(value: GenericValue) -> str:
    """
    Convert a generic value of a native Python type (or one of the tsfpga generic value
    wrapper classes) to a string suitable for the ``-chparam`` argument of the Yosys
    ``hierarchy`` command.
    """
    if isinstance(value, bool):
        # Note that this must be before the 'int' check below, since 'bool' is a subclass of it.
        return "1" if value else "0"

    if isinstance(value, BitVectorGenericValue):
        return f"{value.length}'b{value.value}"

    if isinstance(value, (int, float)):
        return str(value)

    message = (
        "Yosys can not set string parameters of a Verilog/SystemVerilog top level. "
        f'Got type="{type(value)}", value="{value}".'
    )
    raise TypeError(message)
