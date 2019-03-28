# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import join, exists, basename

from tsfpga.system_utils import load_python_module
from tsfpga.module import iterate_module_folders


class FPGAProjectList:

    def __init__(self, modules_folders):
        self._get_projects(modules_folders)

    @staticmethod
    def _get_project_objects(folder, module_name):
        project_file = join(folder, "project_" + module_name + ".py")

        if exists(project_file):
            return load_python_module(project_file).get_projects()
        return []

    def _get_projects(self, modules_folders):
        self.projects = []

        for module_folder in iterate_module_folders(modules_folders):
            module_name = basename(module_folder)
            self.projects += self._get_project_objects(module_folder, module_name)

    def get(self, project_name):
        for project in self.projects:
            if project.name == project_name:
                return project

    def names(self):
        names = []
        for project in self.projects:
            names.append(project.name)
        return names

    def __str__(self):
        return "\n\n".join(["%s" % project for project in self.projects])
