# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import json
from pathlib import Path

# First party libraries
from tsfpga.system_utils import create_file, path_relative_to


def create_ghdl_ls_configuration(output_path, modules, vunit_proj, simlib=None):
    """
    Create a configuration file (hdl-prj.json) for the vhdl-lsp VHDL Language Server
    (https://github.com/ghdl/ghdl-language-server).

    Can be used with modules and an "empty" VUnit project, or with a complete VUnit
    project with all user files added.

    Execution of this function takes roughly 12 ms for a large project (62 modules and a
    VUnit project).

    Arguments:
        output_path (pathlib.Path): Output folder.
        modules: A list of Module objects.
        vunit_proj: A VUnit project.
        simlib (VivadoSimlibCommon): Source from this Vivado simlib project will be added.
    """

    def get_relative_path(path):
        return path_relative_to(path=path, other=output_path)

    data = dict(options=dict(ghdl_analysis=[]), files=[])

    def add_compiled_library(path):
        relative_path = get_relative_path(path)
        data["options"]["ghdl_analysis"].append(f"-P{relative_path}")

    data["options"]["ghdl_analysis"] += [
        "--std=08",
    ]

    # pylint: disable=protected-access
    compiled_vunit_libraries_path = Path(vunit_proj._output_path) / "ghdl" / "libraries"
    for compiled_library_path in compiled_vunit_libraries_path.glob("*"):
        add_compiled_library(compiled_library_path)

    if simlib is not None:
        for library_name in simlib.library_names:
            add_compiled_library(simlib.output_path / library_name)

    # The same file might be present in both module file list as well as VUnit project.
    # However the opposite might also be true in many cases.
    # E.g. files that depend on IP cores that are not included in the simulation project.
    # For this reason, add all files to a set first to avoid duplicates.
    files = set()

    if modules is not None:
        for module in modules:
            for hdl_file in module.get_simulation_files(include_ip_cores=False):
                files.add(hdl_file.path)

    for source_file in vunit_proj.get_compile_order():
        files.add(Path(source_file.name).resolve())

    for file_path in files:
        data["files"].append(dict(file=str(get_relative_path(file_path)), language="vhdl"))

    create_file(output_path / "hdl-prj.json", json.dumps(data))
