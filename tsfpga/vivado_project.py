# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os import makedirs
from os.path import join, exists

from tsfpga import TSFPGA_TCL
from tsfpga.vivado_tcl import VivadoTcl
from tsfpga.vivado_utils import run_vivado_tcl


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
            tcl_sources=None,
            generics=None,
            vivado_path=None,
            constraints=None,
            defined_at=None,
    ):
        """
        :param top: Name of top level entity
        :param tcl_sources: Block design, settings, etc.
        :param generics: A dict with generics values. Use for static generics that
                         do not change between multiple builds of this project.
        :param vivado_path: Default: Whatever version/location is in PATH will be used
        :param constraints: A list of TCL files
        :param defined_at: To get a useful --list message
        """
        self.name = name
        self.modules = modules
        self.part = part
        self.static_generics = generics
        self.defined_at = defined_at

        self.top = name + "_top" if top is None else top
        self.vivado_path = "vivado" if vivado_path is None else vivado_path

        self._setup_constraints_list(constraints)
        self._setup_tcl_sources_list(tcl_sources)

        self.tcl = VivadoTcl(name=self.name)

    def _setup_constraints_list(self, constraints_from_user):
        # Lists are imutable. Since we assign and modify this one we have to copy it.
        self.constraints = [] if constraints_from_user is None else constraints_from_user.copy()

    def _setup_tcl_sources_list(self, tcl_sources_from_user):
        # Lists are imutable. Since we assign and modify this one we have to copy it.
        self.tcl_sources = [] if tcl_sources_from_user is None else tcl_sources_from_user.copy()
        self.tcl_sources += [
            join(TSFPGA_TCL, "vivado_directive_settings.tcl"),
            join(TSFPGA_TCL, "vivado_messages.tcl"),
        ]

    def project_file(self, project_path):
        """
        Return the project file path of this project, in the given folder
        """
        return join(project_path, self.name + ".xpr")

    def _create_tcl(self, project_path, ip_cache_path):
        """
        Make a TCL file that creates a Vivado project
        """
        if exists(project_path):
            raise ValueError("Folder already exists: " + project_path)
        makedirs(project_path)

        create_vivado_project_tcl = join(project_path, "create_vivado_project.tcl")
        with open(create_vivado_project_tcl, "w") as file_handle:
            file_handle.write(self.tcl.create(
                part=self.part,
                modules=self.modules,
                top=self.top,
                tcl_sources=self.tcl_sources,
                generics=self.static_generics,
                constraints=self.constraints,
                project_folder=project_path,
                ip_cache_path=ip_cache_path,
            ))

        return create_vivado_project_tcl

    def create(self, project_path, ip_cache_path=None):
        """
        Create a Vivado project
        """
        print("Creating Vivado project in " + project_path)
        create_vivado_project_tcl = self._create_tcl(project_path, ip_cache_path)
        run_vivado_tcl(self.vivado_path, create_vivado_project_tcl)

    def _build_tcl(self, project_path, output_path, generics, synth_only, num_threads):
        """
        Make a TCL file that builds a Vivado project
        """
        project_file = self.project_file(project_path)
        if not exists(project_file):
            raise ValueError("Project file does not exist in the specified location: " + project_file)

        if self.static_generics is None:
            all_generics = generics
        else:
            # Add the two dictionaries
            all_generics = self.static_generics.copy()
            all_generics.update(generics)

        build_vivado_project_tcl = join(project_path, "build_vivado_project.tcl")
        with open(build_vivado_project_tcl, "w") as file_handle:
            file_handle.write(self.tcl.build(
                project_file=project_file,
                output_path=output_path,
                generics=all_generics,
                synth_only=synth_only,
                num_threads=num_threads))

        return build_vivado_project_tcl

    def pre_build(self, **kwargs):
        """
        Override this function in a child class if you wish to do something useful with it.
        """

    def post_build(self, **kwargs):
        """
        Override this function in a child class if you wish to do something useful with it.
        """

    def build(self, project_path, output_path=None, generics=None, synth_only=False, num_threads=12):
        """
        Build a Vivado project

        :param generics: Use for run-time generics. Values that can change between each build of this project.
        """
        if output_path is None and not synth_only:
            raise ValueError("Must specify output_path when doing an implementation run")

        if synth_only:
            print("Synthesizing Vivado project in " + project_path)
        else:
            print(f"Building Vivado project in {project_path}, placing artifacts in {output_path}")

        self.pre_build(project_path=project_path,
                       output_path=output_path,
                       generics=generics,
                       synth_only=synth_only,
                       num_threads=num_threads)

        build_vivado_project_tcl = self._build_tcl(project_path=project_path,
                                                   output_path=output_path,
                                                   synth_only=synth_only,
                                                   generics=generics,
                                                   num_threads=num_threads)
        run_vivado_tcl(self.vivado_path, build_vivado_project_tcl)

        self.post_build(project_path=project_path,
                        output_path=output_path,
                        generics=generics,
                        synth_only=synth_only,
                        num_threads=num_threads)

    def __str__(self):
        result = str(self.__class__.__name__)
        if self.defined_at is not None:
            result += " defined at: " + self.defined_at
        result += "\nName:      " + self.name
        result += "\nTop level: " + self.top
        if self.static_generics is None:
            generics = "-"
        else:
            generics = ", ".join([f"{name}={value}" for name, value in self.static_generics.items()])
        result += "\nGenerics:  " + generics

        return result
