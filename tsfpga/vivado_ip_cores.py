from os.path import join, exists
import hashlib

from tsfpga.system_utils import create_file, delete
from tsfpga.vivado_project import VivadoProject


class VivadoIpCores:

    """
    Handle a list of IP core sources. Has a mechanism to detect whether a regenerate of IP files is needed.
    """

    _project_name = "vivado_ip_project"

    def __init__(self, modules, project_path, part_name="xc7z020clg400-1"):
        self._project_folder = join(project_path, self._project_name)
        self._part_name = part_name
        self._setup(modules)

    def _setup(self, modules):
        ip_tcl_files = []
        for module in modules:
            ip_tcl_files += module.get_ip_core_files()

        self._vivado_project = VivadoProject(
            name=self._project_name,
            modules=[],
            part=self._part_name,
            tcl_sources=ip_tcl_files
        )

        self._hash = self._calculate_hash(ip_tcl_files)

    @staticmethod
    def _calculate_hash(files):
        ip_hash = hashlib.md5()
        for file in files:
            ip_hash.update(file.encode())
            with open(file) as file_handle:
                ip_hash.update(file_handle.read().encode())

        return ip_hash.hexdigest()

    @property
    def compile_order_file(self):
        return join(self._project_folder, "compile_order.txt")

    @property
    def vivado_project_file(self):
        return self._vivado_project.project_file(self._project_folder)

    def generate_files(self):
        print("Generating IP cores")
        delete(self._project_folder)
        self._vivado_project.create(self._project_folder)
        self._save_hash()

    @property
    def _hash_file(self):
        return join(self._project_folder, "ip_files_hash.txt")

    def _save_hash(self):
        create_file(self._hash_file, self._hash)

    def _generate_needed(self):
        """
        Return True if a generate is needed
        """
        if not (exists(self._hash_file) and exists(self.compile_order_file)):
            return True

        with open(self._hash_file) as file_handle:
            saved_hash = file_handle.read()
        if saved_hash != self._hash:
            return True

        return False

    def generate_files_if_needed(self):
        if self._generate_needed():
            self.generate_files()
            return True

        return False
