# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path

# Third party libraries
import tomlkit

# First party libraries
from tsfpga.system_utils import create_file
from tsfpga.vivado.ip_cores import VivadoIpCores


def create_configuration(
    output_path,
    modules=None,
    vunit_proj=None,
    vivado_location=None,
    ip_core_vivado_project_directory=None,
):
    """
    Create a configuration file (vhdl_ls.toml) for the rust_hdl VHDL Language Server.

    Can be used with modules and an "empty" VUnit project, or with a complete VUnit
    project with all user files added.

    Execution of this function takes roughly 12 ms for a large project (62 modules and a
    VUnit project).

    Arguments:
        output_path (pathlib.Path): Output folder.
        modules: A list of Module objects.
        vunit_proj: A VUnit project.
        vivado_location (pathlib.Path): Vivado binary path. Will add unisim from this Vivado
            installation.
        ip_core_vivado_project_directory (pathlib.Path): Path to a Vivado project that contains
            generated "simulation" and "synthesis" files of IP cores
            (the "generate_target" TCL command). See simulate.py for an example of using this.
    """
    toml_data = dict(libraries={})

    if modules is not None:
        for module in modules:
            vhd_file_wildcard = module.path.resolve() / "**" / "*.vhd"
            toml_data["libraries"][module.library_name] = dict(files=[str(vhd_file_wildcard)])

    if vunit_proj is not None:
        for source_file in vunit_proj.get_compile_order():
            if source_file.library.name not in toml_data["libraries"]:
                toml_data["libraries"][source_file.library.name] = dict(files=[])
            toml_data["libraries"][source_file.library.name]["files"].append(
                str(Path(source_file.name).resolve())
            )

    if vivado_location is not None:
        vcomponents_package = (
            vivado_location.parent.parent
            / "data"
            / "vhdl"
            / "src"
            / "unisims"
            / "unisim_retarget_VCOMP.vhd"
        )
        if not vcomponents_package.exists():
            raise FileNotFoundError(f"Could not find unisim file: {vcomponents_package}")

        toml_data["libraries"]["unisim"] = dict(files=[str(vcomponents_package.resolve())])

    if ip_core_vivado_project_directory is not None:
        ip_core_vivado_project_directory = ip_core_vivado_project_directory.resolve()
        toml_data["libraries"]["xil_defaultlib"] = dict(files=[])

        # Vivado 2020.2+ (?) seems to place the files in "gen"
        ip_gen_dir = (
            ip_core_vivado_project_directory / f"{VivadoIpCores.project_name}.gen" / "sources_1"
        )
        if ip_gen_dir.exists():
            vhd_file_wildcard = ip_gen_dir / "ip" / "**" / "*.vhd"
            toml_data["libraries"]["xil_defaultlib"]["files"].append(str(vhd_file_wildcard))

    create_file(output_path / "vhdl_ls.toml", tomlkit.dumps(toml_data))
