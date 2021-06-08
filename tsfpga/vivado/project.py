# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from copy import deepcopy
import shutil

from tsfpga import TSFPGA_TCL
from tsfpga.system_utils import create_file, read_file
from tsfpga.build_step_tcl_hook import BuildStepTclHook
from .build_result import BuildResult
from .common import run_vivado_tcl, run_vivado_gui
from .hierarchical_utilization_parser import HierarchicalUtilizationParser
from .logic_level_distribution_parser import LogicLevelDistributionParser
from .tcl import VivadoTcl


class VivadoProject:
    """
    Used for handling a Xilinx Vivado HDL project
    """

    # pylint: disable=too-many-arguments,too-many-instance-attributes
    def __init__(
        self,
        name,
        modules,
        part,
        top=None,
        generics=None,
        constraints=None,
        tcl_sources=None,
        build_step_hooks=None,
        vivado_path=None,
        default_run_index=1,
        defined_at=None,
    ):
        """
        Class constructor. Performs a shallow copy of the mutable arguments, so that the user
        can e.g. append items to their list after creating an object.

        Arguments:
            name (str): Project name.
            modules (list(:class:`Module <.BaseModule>`)): Modules that shall be included in the
                project.
            part (str): Part identification.
            top (str): Name of top level entity. If left out, the top level name will be
                inferred from the ``name``.
            generics: A dict with generics values (`dict(name: value)`). Use this parameter
                for "static" generics that do not change between multiple builds of this
                project. These will be set in the project when it is created.

                Compare to the build-time generic argument in :meth:`build`.
            constraints (list(Constraint)): Constraints that will be applied to the project.
            tcl_sources (list(`pathlib.Path`)): A list of TCL files. Use for e.g. block design,
                pinning, settings, etc.
            build_step_hooks (list(BuildStepTclHook)): Build step hooks that will be applied to the
                project.
            vivado_path (`pathlib.Path`): A path to the Vivado executable. If omitted,
                the default location from the system PATH will be used.
            default_run_index (int): Default run index (synth_X and impl_X) that is set in the
                project. Can also use the argument to :meth:`build() <VivadoProject.build>` to
                specify at build-time.
            defined_at (`pathlib.Path`): Optional path to the file where you defined your
                project. To get a useful ``build.py --list`` message. Is useful when you have many
                projects set up.
        """
        self.name = name
        self.modules = modules.copy()
        self.part = part
        self.static_generics = None if generics is None else generics.copy()
        self.constraints = [] if constraints is None else constraints.copy()
        self.tcl_sources = [] if tcl_sources is None else tcl_sources.copy()
        self.build_step_hooks = [] if build_step_hooks is None else build_step_hooks.copy()
        self.default_run_index = default_run_index
        self.defined_at = defined_at

        # Will be set by child class when applicable
        self.is_netlist_build = False
        self.analyze_synthesis_timing = True
        self.report_logic_level_distribution = False

        self.top = name + "_top" if top is None else top
        self._vivado_path = vivado_path

        self.tcl = VivadoTcl(name=self.name)

    def project_file(self, project_path):
        """
        Arguments:
            project_path (`pathlib.Path`): A path containing a Vivado project.
        Return:
            `pathlib.Path`: The project file of this project, in the given folder
        """
        return project_path / (self.name + ".xpr")

    def _setup_tcl_sources(self):
        tsfpga_tcl_sources = [
            TSFPGA_TCL / "vivado_default_run.tcl",
            TSFPGA_TCL / "vivado_fast_run.tcl",
            TSFPGA_TCL / "vivado_messages.tcl",
        ]

        # Add tsfpga TCL sources first. The user might want to change something in the tsfpga
        # settings. Conversely, tsfpga should not modify something that the user has set up.
        self.tcl_sources = tsfpga_tcl_sources + self.tcl_sources

    def _setup_build_step_hooks(self):
        # Check the implemented timing and resource utilization via TCL build hooks.
        # This is different than for synthesis, where it is embedded in the build script.
        # This is due to Vivado limitations related to post-synthesis hooks.
        # Specifically, the report_utilization figures do not include IP cores when it is run in
        # a post-synthesis hook.
        self.build_step_hooks.append(
            BuildStepTclHook(TSFPGA_TCL / "report_utilization.tcl", "STEPS.WRITE_BITSTREAM.TCL.PRE")
        )
        self.build_step_hooks.append(
            BuildStepTclHook(TSFPGA_TCL / "check_timing.tcl", "STEPS.WRITE_BITSTREAM.TCL.PRE")
        )

        if not self.analyze_synthesis_timing:
            # In this special case however, the synthesized design is never opened, and
            # report_utilization is not run by the build_vivado_project.tcl.
            # So in order to get a utilization report anyway we add it as a hook.
            # This mode is exclusively used by netlist builds, which very rarely include IP cores,
            # so it is acceptable that the utilization report might be erroneous with regards to
            # IP cores.
            self.build_step_hooks.append(
                BuildStepTclHook(
                    TSFPGA_TCL / "report_utilization.tcl", "STEPS.SYNTH_DESIGN.TCL.POST"
                )
            )

        if self.report_logic_level_distribution:
            # Used by netlist builds
            self.build_step_hooks.append(
                BuildStepTclHook(
                    TSFPGA_TCL / "report_logic_level_distribution.tcl",
                    "STEPS.SYNTH_DESIGN.TCL.POST",
                )
            )

    def _create_tcl(self, project_path, ip_cache_path):
        """
        Make a TCL file that creates a Vivado project
        """
        if project_path.exists():
            raise ValueError(f"Folder already exists: {project_path}")
        project_path.mkdir(parents=True)

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
            build_step_hooks=self.build_step_hooks,
            ip_cache_path=ip_cache_path,
            disable_io_buffers=self.is_netlist_build,
        )
        create_file(create_vivado_project_tcl, tcl)

        return create_vivado_project_tcl

    def create(self, project_path, ip_cache_path=None):
        """
        Create a Vivado project

        Arguments:
            project_path (`pathlib.Path`): Path where the project shall be placed.
            ip_cache_path (`pathlib.Path`): Path to a folder where the Vivado IP cache can be
                placed. If omitted, the Vivado IP cache mechanism will not be enabled.

        Returns:
            bool: True if everything went well.
        """
        print(f"Creating Vivado project in {project_path}")
        self._setup_tcl_sources()
        self._setup_build_step_hooks()

        # The pre-create hook might have side effects. E.g. change some register constants.
        # So we make a deep copy of the module list before the hook is called.
        # Note that the modules are copied before the pre-build hooks as well,
        # since we do not know if we might be performing a create-only or
        # build-only operation. The copy does not take any significant time, so this is not
        # an issue.
        self.modules = deepcopy(self.modules)

        if not self.pre_create(project_path=project_path, ip_cache_path=ip_cache_path):
            print("ERROR: Project pre-create hook returned False. Failing the build.")
            return False

        create_vivado_project_tcl = self._create_tcl(project_path, ip_cache_path)
        return run_vivado_tcl(self._vivado_path, create_vivado_project_tcl)

    def pre_create(self, **kwargs):  # pylint: disable=no-self-use, unused-argument
        """
        Override this function in a child class if you wish to do something useful with it.
        Will be called from :meth:`.create` right before the call to Vivado.

        An example use case for this function is when TCL source scripts for the Vivado project
        have to be auto generated. This could e.g. be scripts that set IP repo paths based on the
        Vivado system PATH.

        .. Note::
            This default method does nothing. Shall be overridden by project that utilize
            this mechanism.

        Arguments:
            kwargs: Will have all the :meth:`.create` parameters in it.

        Return:
            bool: True if everything went well.
        """
        return True

    def _build_tcl(self, project_path, output_path, num_threads, run_index, generics, synth_only):
        """
        Make a TCL file that builds a Vivado project
        """
        project_file = self.project_file(project_path)
        if not project_file.exists():
            raise ValueError(
                f"Project file does not exist in the specified location: {project_file}"
            )

        if self.static_generics is None:
            all_generics = generics
        elif generics is None:
            all_generics = self.static_generics
        else:
            # Add the two dictionaries. This will prefer the values in the run-time generics,
            # if the same generic is present in both.
            all_generics = generics
            all_generics.update(self.static_generics)

        build_vivado_project_tcl = project_path / "build_vivado_project.tcl"
        tcl = self.tcl.build(
            project_file=project_file,
            output_path=output_path,
            num_threads=num_threads,
            run_index=run_index,
            generics=all_generics,
            synth_only=synth_only,
            analyze_synthesis_timing=self.analyze_synthesis_timing,
        )
        create_file(build_vivado_project_tcl, tcl)

        return build_vivado_project_tcl

    def pre_build(self, **kwargs):  # pylint: disable=no-self-use, unused-argument
        """
        Override this function in a child class if you wish to do something useful with it.
        Will be called from :meth:`.build` right before the call to Vivado.

        Arguments:
            kwargs: Will have all the :meth:`.build` parameters in it. Including additional
                parameters from the user.

        Return:
            bool: True if everything went well.
        """
        return True

    def post_build(self, **kwargs):  # pylint: disable=no-self-use, unused-argument
        """
        Override this function in a child class if you wish to do something useful with it.
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
            bool: True if everything went well.
        """
        return True

    def build(
        self,
        project_path,
        output_path=None,
        run_index=None,
        generics=None,
        synth_only=False,
        num_threads=12,
        **pre_and_post_build_parameters,
    ):
        """
        Build a Vivado project

        Arguments:
            project_path (`pathlib.Path`): A path containing a Vivado project.
            output_path (`pathlib.Path`): Results (bit file, ...) will be placed here.
            run_index (int): Select Vivado run (synth_X and impl_X) to build with.
            generics: A dict with generics values (`dict(name: value)`). Use for run-time
                generics, i.e. values that can change between each build of this project.

                Compare to the create-time generics argument in :meth:`.__init__`.
            synth_only (bool): Run synthesis and then stop.
            num_threads (int): Number of parallel threads to use during run.
            pre_and_post_build_parameters: Additional parameters that will be
                sent to :meth:`.pre_build` and :meth:`.post_build` functions.

                .. note::
                    This is a "kwargs" style argument. You can pass any number of named arguments.

        Return:
            :class:`.build_result.BuildResult`: Result object with build information.
        """
        synth_only = synth_only or self.is_netlist_build

        if output_path is None and not synth_only:
            raise ValueError("Must specify output_path when doing an implementation run")

        if synth_only:
            print(f"Synthesizing Vivado project in {project_path}")
        else:
            print(f"Building Vivado project in {project_path}, placing artifacts in {output_path}")

        # Run index is optional to specify at build-time
        run_index = self.default_run_index if run_index is None else run_index

        # Send all available information to pre- and post build functions
        pre_and_post_build_parameters.update(
            project_path=project_path,
            output_path=output_path,
            run_index=run_index,
            generics=generics,
            synth_only=synth_only,
            num_threads=num_threads,
        )

        # The pre-build hooks (either project pre-build hook or any of the module's pre-build hooks)
        # might have side effects. E.g. change some register constants. So we make a deep copy of the
        # module list before any of these hooks are called. Note that the modules are copied before
        # the pre-create hook as well, since we do not know if we might be performing a create-only
        # or build-only operation. The copy does not take any significant time, so this is not
        # an issue.
        self.modules = deepcopy(self.modules)

        result = BuildResult(self.name)

        for module in self.modules:
            if not module.pre_build(project=self, **pre_and_post_build_parameters):
                print(
                    f"ERROR: Module {module.name} pre-build hook returned False. Failing the build."
                )
                result.success = False
                return result

            # Make sure register packages are up to date
            module.create_regs_vhdl_package()

        if not self.pre_build(**pre_and_post_build_parameters):
            print("ERROR: Project pre-build hook returned False. Failing the build.")
            result.success = False
            return result

        build_vivado_project_tcl = self._build_tcl(
            project_path=project_path,
            output_path=output_path,
            num_threads=num_threads,
            run_index=run_index,
            generics=generics,
            synth_only=synth_only,
        )

        if not run_vivado_tcl(self._vivado_path, build_vivado_project_tcl):
            result.success = False
            return result

        result.synthesis_size = self._get_size(project_path, f"synth_{run_index}")
        if self.report_logic_level_distribution:
            result.logic_level_distribution = self._get_logic_level_distribution(
                project_path, f"synth_{run_index}"
            )

        if not synth_only:
            impl_folder = project_path / f"{self.name}.runs" / f"impl_{run_index}"
            shutil.copy2(impl_folder / f"{self.top}.bit", output_path / f"{self.name}.bit")
            shutil.copy2(impl_folder / f"{self.top}.bin", output_path / f"{self.name}.bin")
            result.implementation_size = self._get_size(project_path, f"impl_{run_index}")

        # Send the result object, along with everything else, to the post-build function
        pre_and_post_build_parameters.update(build_result=result)

        if not self.post_build(**pre_and_post_build_parameters):
            print("ERROR: Project post-build hook returned False. Failing the build.")
            result.success = False

        return result

    def open(self, project_path):
        """
        Open the project in Vivado GUI.

        Arguments:
            project_path (`pathlib.Path`): A path containing a Vivado project.

        Returns:
            bool: True if everything went well.
        """
        return run_vivado_gui(self._vivado_path, self.project_file(project_path))

    def _get_size(self, project_path, run):
        """
        Reads the hierarchical utilization report and returns the top level size
        for the specified run.
        """
        report_as_string = read_file(
            project_path / f"{self.name}.runs" / run / "hierarchical_utilization.rpt"
        )
        return HierarchicalUtilizationParser.get_size(report_as_string)

    def _get_logic_level_distribution(self, project_path, run):
        """
        Reads the hierarchical utilization report and returns the top level size
        for the specified run.
        """
        report_as_string = read_file(
            project_path / f"{self.name}.runs" / run / "logical_level_distribution.rpt"
        )
        return LogicLevelDistributionParser.get_table(report_as_string)

    def __str__(self):
        result = self.name
        if self.defined_at is not None:
            result += f"\nDefined at: {self.defined_at.resolve()}"
        result += f"\nType:       {self.__class__.__name__}"
        result += f"\nTop level:  {self.top}"
        if self.static_generics is None:
            generics = "-"
        else:
            generics = ", ".join(
                [f"{name}={value}" for name, value in self.static_generics.items()]
            )
        result += f"\nGenerics:   {generics}"

        return result


class VivadoNetlistProject(VivadoProject):
    """
    Used for handling Vivado build of a module without top level pinning.
    """

    def __init__(self, analyze_synthesis_timing=False, build_result_checkers=None, **kwargs):
        """
        Arguments:
            analyze_synthesis_timing (bool): Enable analysis of the synthesized design's timing.
                This will make the build flow open the design, and check for unhandled clock
                crossings and pulse width violations.
                Enabling it will add significant build time (can be as much as +40%).
                Also, in order for clock crossing check to work, the clocks have to be created
                using a constraint file.
            build_result_checkers (list(:class:`.SizeChecker`, :class:`.MaximumLogicLevel`)):
                Checkers that will be executed after a successful build. Is used to automatically
                check that e.g. resource utilization is not greater than expected.
            kwargs: Other arguments accepted by :meth:`.VivadoProject.__init__`.
        """
        super().__init__(**kwargs)

        self.is_netlist_build = True
        self.analyze_synthesis_timing = analyze_synthesis_timing
        self.report_logic_level_distribution = True
        self.build_result_checkers = [] if build_result_checkers is None else build_result_checkers

    def build(self, **kwargs):  # pylint: disable=arguments-differ
        """
        Build the project.

        Arguments:
            kwargs: All arguments as accepted by :meth:`.VivadoProject.build`.
        """
        result = super().build(**kwargs)
        result.success = result.success and self._check_size(result)

        return result

    def _check_size(self, build_result):
        if not build_result.success:
            print(f"Can not do post_build check for {self.name} since it did not succeed.")
            return False

        success = True
        for build_result_checker in self.build_result_checkers:
            checker_result = build_result_checker.check(build_result)
            success = success and checker_result

        return success
