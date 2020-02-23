# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.system_utils import load_python_module
from tsfpga.module import iterate_module_folders


class FpgaProjectList:

    """
    Represent a list of FPGA build projects.
    """

    def __init__(self, modules_folders):
        """
        Args:
            modules_folders: A list of paths to folders that contain modules.
        """
        self._get_projects(modules_folders)

    @staticmethod
    def _get_project_objects(path, module_name):
        project_file = path / ("project_" + module_name + ".py")

        if project_file.exists():
            return load_python_module(project_file).get_projects()
        return []

    def _get_projects(self, modules_folders):
        self.projects = []

        for module_path in iterate_module_folders(modules_folders):
            module_name = module_path.name
            self.projects += self._get_project_objects(module_path, module_name)

    def get(self, project_name):
        """
        Get the project with the specified name.

        Args:
            project_name: Project name string.

        Returns:
            A :class:`FPGA build project <.VivadoProject>` object.
        """
        for project in self.projects:
            if project.name == project_name:
                return project

    def names(self):
        """
        Returns:
            A list of names of the projects that are available.
        """
        names = []
        for project in self.projects:
            names.append(project.name)
        return names

    def __str__(self):
        return "\n\n".join(["%s" % project for project in self.projects])
