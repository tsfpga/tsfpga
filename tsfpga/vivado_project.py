# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import shutil

from tsfpga import TSFPGA_TCL
from tsfpga.vivado_tcl import VivadoTcl
from tsfpga.vivado_utils import run_vivado_tcl, run_vivado_gui
from tsfpga.build_step_tcl_hook import BuildStepTclHook


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
            defined_at=None,
    ):
        """
        Args:
            name (str): Project name.
            modules (list(:class:`Module <.BaseModule>`)): Modules that shall be included in the project.
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
            build_step_hooks (list(BuildStepTclHook)): Build step hooks that will be applied to the project.
            vivado_path (`pathlib.Path`): A path to the Vivado executable. If omitted,
                the default location from the system PATH will be used.
            defined_at (`pathlib.Path`): Optional path to the file where you defined your
                project. To get a useful build.py --list message. Is useful when you have many
                projects set up.
        """
        self.name = name
        self.modules = modules
        self.part = part
        self.static_generics = generics
        self.constraints = constraints
        self.defined_at = defined_at

        self.top = name + "_top" if top is None else top
        self._vivado_path = vivado_path

        self._setup_tcl_sources_list(tcl_sources)
        self._setup_build_step_hooks(build_step_hooks)

        self.tcl = VivadoTcl(name=self.name)

    def _setup_tcl_sources_list(self, tcl_sources_from_user):
        # Lists are immutable. Since we assign and modify this one we have to copy it.
        self.tcl_sources = [] if tcl_sources_from_user is None else tcl_sources_from_user.copy()
        self.tcl_sources += [
            TSFPGA_TCL / "vivado_directive_settings.tcl",
            TSFPGA_TCL / "vivado_messages.tcl",
        ]

    def _setup_build_step_hooks(self, build_step_hooks_from_user):
        # Lists are immutable. Since we assign and modify this one we have to copy it.
        self.build_step_hooks = [] if build_step_hooks_from_user is None else build_step_hooks_from_user.copy()
        self.build_step_hooks.append(BuildStepTclHook(TSFPGA_TCL / "vivado_impl_post.tcl",
                                                      "STEPS.WRITE_BITSTREAM.TCL.PRE"))

    def project_file(self, project_path):
        """
        Return the path of the project file of this project, in the given folder

        Args:
            project_path (`pathlib.Path`): A path containing a Vivado project.
        """
        return project_path / (self.name + ".xpr")

    def _create_tcl(self, project_path, ip_cache_path):
        """
        Make a TCL file that creates a Vivado project
        """
        if project_path.exists():
            raise ValueError(f"Folder already exists: {project_path}")
        project_path.mkdir(parents=True)

        create_vivado_project_tcl = project_path / "create_vivado_project.tcl"
        with open(create_vivado_project_tcl, "w") as file_handle:
            file_handle.write(self.tcl.create(
                project_folder=project_path,
                modules=self.modules,
                part=self.part,
                top=self.top,
                generics=self.static_generics,
                constraints=self.constraints,
                tcl_sources=self.tcl_sources,
                build_step_hooks=self.build_step_hooks,
                ip_cache_path=ip_cache_path,
            ))

        return create_vivado_project_tcl

    def create(self, project_path, ip_cache_path=None):
        """
        Create a Vivado project

        Args:
            project_path (`pathlib.Path`): Path where the project shall be placed.
            ip_cache_path (`pathlib.Path`): Path to a folder where the Vivado IP cache can be placed.
        """
        print(f"Creating Vivado project in {project_path}")
        create_vivado_project_tcl = self._create_tcl(project_path, ip_cache_path)
        run_vivado_tcl(self._vivado_path, create_vivado_project_tcl)

    def _build_tcl(self, project_path, output_path, num_threads, run_index, generics, synth_only):
        """
        Make a TCL file that builds a Vivado project
        """
        project_file = self.project_file(project_path)
        if not project_file.exists():
            raise ValueError(f"Project file does not exist in the specified location: {project_file}")

        if self.static_generics is None:
            all_generics = generics
        else:
            # Add the two dictionaries
            all_generics = self.static_generics.copy()
            all_generics.update(generics)

        build_vivado_project_tcl = project_path / "build_vivado_project.tcl"
        with open(build_vivado_project_tcl, "w") as file_handle:
            file_handle.write(self.tcl.build(
                project_file=project_file,
                output_path=output_path,
                num_threads=num_threads,
                run_index=run_index,
                generics=all_generics,
                synth_only=synth_only))

        return build_vivado_project_tcl

    def pre_build(self, **kwargs):
        """
        Override this function in a child class if you wish to do something useful with it.
        Will be called from :meth:`.build` right before the call to Vivado.

        Args:
            kwargs: Will have all the build parameters in it. Including additional parameters
                from the user.
        """

    def post_build(self, **kwargs):
        """
        Override this function in a child class if you wish to do something useful with it.
        Will be called from :meth:`.build` right after the call to Vivado.

        Args:
            kwargs: Will have all the build parameters in it. Including additional parameters
                from the user.
        """

    def build(self,
              project_path,
              output_path=None,
              run_index=1,
              generics=None,
              synth_only=False,
              num_threads=12,
              **pre_and_post_build_parameters):
        """
        Build a Vivado project

        Args:
            project_path (`pathlib.Path`): A path containing a Vivado project.
            output_path (`pathlib.Path`): Results (bit file, ...) will be placed here.
            run_index (int): Select Vivado run (synth_X and impl_X).
            generics: A dict with generics values (`dict(name: value)`). Use for run-time
                generics, i.e. Values that can change between each build of this project.

                Compare to the create-time generics argument in :meth:`.__init__`.
            synth_only (bool): Run synthesis and then stop.
            num_threads (int): Number of parallell threads to use during run.
            pre_and_post_build_parameters: Additional parameters that will be
                sent to pre- and post build functions. Note that this is a "kwargs" style
                argument; you can pass any number of named arguments.
        """
        if output_path is None and not synth_only:
            raise ValueError("Must specify output_path when doing an implementation run")

        if synth_only:
            print(f"Synthesizing Vivado project in {project_path}")
        else:
            print(f"Building Vivado project in {project_path}, placing artifacts in {output_path}")

        # Send all available information to pre- and post build
        pre_and_post_build_parameters.update(
            project_path=project_path,
            output_path=output_path,
            run_index=run_index,
            generics=generics,
            synth_only=synth_only,
            num_threads=num_threads
        )

        self.pre_build(**pre_and_post_build_parameters)

        build_vivado_project_tcl = self._build_tcl(project_path=project_path,
                                                   output_path=output_path,
                                                   num_threads=num_threads,
                                                   run_index=run_index,
                                                   generics=generics,
                                                   synth_only=synth_only)
        run_vivado_tcl(self._vivado_path, build_vivado_project_tcl)

        if not synth_only:
            impl_folder = project_path / (self.name + ".runs") / f"impl_{run_index}"
            shutil.copy2(impl_folder / (self.top + ".bit"), output_path / (self.name + ".bit"))
            shutil.copy2(impl_folder / (self.top + ".bin"), output_path / (self.name + ".bin"))

        self.post_build(**pre_and_post_build_parameters)

    def open(self, project_path):
        """
        Open the project in Vivado GUI.

        Args:
            project_path (`pathlib.Path`): A path containing a Vivado project.
        """
        run_vivado_gui(self._vivado_path, self.project_file(project_path))

    def __str__(self):
        result = str(self.__class__.__name__)
        if self.defined_at is not None:
            result += f" defined at: {self.defined_at.resolve()}"
        result += "\nName:      " + self.name
        result += "\nTop level: " + self.top
        if self.static_generics is None:
            generics = "-"
        else:
            generics = ", ".join([f"{name}={value}" for name, value in self.static_generics.items()])
        result += "\nGenerics:  " + generics

        return result
