# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


class BuildProjectList:

    """
    Interface to handle a list of FPGA build projects.
    """

    def __init__(self, modules):
        """
        Args:
            modules (list(:class:`.BaseModule`)): Module objects that can define build projects.
        """
        self._modules = modules

    def get(self, project_name):
        """
        Get the project with the specified name.

        Args:
            project_name (str): Project name.

        Returns:
            A :class:`FPGA build project <.VivadoProject>` object.
        """
        for module in self._modules:
            for project in module.get_build_projects():
                if project.name == project_name:
                    return project
        raise ValueError(f"Could not find project: {project_name}")

    def names(self):
        """
        Returns:
            list(str): Names of the projects that are available.
        """
        return [project.name for project in self._iterate_projects()]

    def _iterate_projects(self):
        for module in self._modules:
            for project in module.get_build_projects():
                yield project

    def __str__(self):
        return "\n\n".join([str(project) for project in self._iterate_projects()])
