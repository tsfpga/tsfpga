# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import hashlib
from os.path import abspath, exists, basename, join, dirname
from platform import system
from shutil import which

from tsfpga.vivado_utils import to_tcl_path, run_vivado_tcl
from tsfpga.system_utils import create_file, delete


class VivadoSimlib:

    _libraries = ["unisim", "secureip", "unimacro", "unifast", "xpm"]

    _tcl = "set_param general.maxthreads 4\n" \
        "compile_simlib -simulator {simulator_name} -simulator_exec_path {{{simulator_folder}}} " \
        "-family all -language all -library all -no_ip_compile -dir {{{output_path}}} -force"

    def __init__(self, vunit_proj, output_path, vivado_path="vivado"):
        self._vunit_proj = vunit_proj
        self._vivado_path = vivado_path

        self._find_simulator()
        self.output_path = join(output_path, self._get_version_tag())
        self._done_token = join(self.output_path, "done.txt")

    def compile_if_needed(self):
        if exists(self._done_token):
            return False
        self.compile()
        return True

    def compile(self):
        delete(self._done_token)
        print(f"Compiling Vivado simlib in {self.output_path}")
        tcl_file = join(self.output_path, "compile_simlib.tcl")
        tcl = self._tcl.format(simulator_name=self._simulator_name,
                               simulator_folder=to_tcl_path(self._simulator_folder),
                               output_path=to_tcl_path(self.output_path))
        create_file(tcl_file, tcl)
        run_vivado_tcl(self._vivado_path, tcl_file)
        create_file(self._done_token, "Done!")

    def add_to_vunit_project(self):
        for library in self._libraries:
            library_path = join(self.output_path, library)
            assert exists(library_path)
            self._vunit_proj.add_external_library(library, library_path)

    def _get_version_tag(self):
        """
        Return a version string on the format vivado-simlib-WW.XX.YY.ZZ,
        suitable for storage and versioning in Artifactory.
        """
        tag = "vivado-simlib-"
        tag += system().lower()
        tag += "." + self._get_tcl_hash()
        tag += "." + self._get_vivado_version_tag()
        tag += "." + self._get_simulator_tag()
        return tag

    def _get_tcl_hash(self):
        """
        Return a (partial) hash of the TCL script that is used to compile simlib.
        """
        return hashlib.md5(self._tcl.encode()).hexdigest()[0:8]

    def _get_vivado_version_tag(self):
        """
        Return e.g. vivado_2019_1
        """
        vivado_path = self._vivado_path
        if vivado_path == "vivado":
            vivado_path = which(vivado_path)
            assert vivado_path is not None, "Could not find vivado location"
        vivado_version = basename(abspath(join(dirname(vivado_path), "..")))
        return "vivado_" + vivado_version.replace(".", "_")

    def _find_simulator(self):
        # Update naming for Vivado's convetion
        vunit_simulator_name = self._vunit_proj.get_simulator_name()
        self._simulator_name = "riviera" if vunit_simulator_name == "rivierapro" else vunit_simulator_name

        # pylint: disable=protected-access
        self._simulator_folder = self._vunit_proj._simulator_class.find_prefix()

    def _get_simulator_tag(self):
        """
        Return e.g. modelsim_modeltech_pe_10_6c or riviera_riviera_pro_2018_10_x64.
        """
        simulator_version = basename(abspath(join(self._simulator_folder, "..")))
        return self._simulator_name + "_" + simulator_version.replace(".", "_").replace("-", "_").lower()
