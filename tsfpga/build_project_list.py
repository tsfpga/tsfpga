# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import fnmatch


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

    def get_projects(self, project_filters, include_netlist_not_top_builds=False):
        """
        Get projects matching any of the specified filters.

        Args:
            project_filters (list(str)): Project name filters.
            include_netlist_not_top_builds: Set True to get only netlist builds instead of only top level builds.

        Returns:
            A list of FPGA build project objects.
        """
        projects = list(self._iterate_projects(project_filters, include_netlist_not_top_builds))

        if not projects:
            raise ValueError(f"Could not find projects with filters: {project_filters}")

        return projects

    def list_projects(self, project_filters, include_netlist_not_top_builds=False):
        """
        Returns a string with a list of the projects matching the specified filters.

        Args:
            project_filters (list(str)): Project name filters.
            include_netlist_not_top_builds (bool): Set True to get only netlist builds (:class:`.VivadoNetlistProject`)
                instead of only top level builds (:class:`.VivadoProject`).

        Returns:
            A string listing projects matching the specified filters.
        """
        return "\n\n".join([str(project) for project in self._iterate_projects(project_filters, include_netlist_not_top_builds)])

    def _iterate_projects(self, project_filters=None, include_netlist_not_top_builds=False):
        projects = []
        for module in self._modules:
            projects += module.get_build_projects()
        for project in projects:
            if project.is_netlist_build == include_netlist_not_top_builds:
                if not project_filters:
                    yield project
                else:
                    for project_filter in project_filters:
                        if fnmatch.filter([project.name], project_filter):
                            yield project
