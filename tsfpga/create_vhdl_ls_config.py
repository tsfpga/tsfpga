# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

# Third party libraries
import rtoml

# First party libraries
from tsfpga.vivado.ip_cores import VivadoIpCores

if TYPE_CHECKING:
    # Third party libraries
    from vunit.ui import VUnit

    # Local folder libraries
    from .module_list import ModuleList


def create_configuration(
    output_path: Path,
    modules: Optional["ModuleList"] = None,
    vunit_proj: Optional["VUnit"] = None,
    files: Optional[list[tuple[Path, str]]] = None,
    vivado_location: Optional[Path] = None,
    ip_core_vivado_project_directory: Optional[Path] = None,
) -> None:
    """
    Create a configuration file (``vhdl_ls.toml``) for the rust_hdl VHDL Language Server
    (https://github.com/VHDL-LS/rust_hdl).

    Can be used with modules and an "empty" VUnit project, or with a complete VUnit
    project with all user files added.
    Files can also be added manually with the ``files`` argument.

    Execution of this function takes roughly 12 ms for a large project (62 modules and a
    VUnit project).

    Arguments:
        output_path: vhdl_ls.toml file will be placed in this folder.
        modules: All files from these modules will be added.
        vunit_proj: All files in this VUnit project will be added.
            This includes the files from VUnit itself, and any user files.

            .. warning::
                Using a VUnit project with user files and location/check preprocessing enabled is
                dangerous, since it introduces the risk of editing a generated file.
        files: All files listed here will be added.
            Can be used to add additional files outside of the modules or the VUnit project.
            The list shall contain tuples: ``(Path, "library name")``.
        vivado_location: Vivado binary path.
            The ``unisim`` from this Vivado installation will be added.
        ip_core_vivado_project_directory: Path to a Vivado project that contains
            generated "simulation" and "synthesis" files of IP cores
            (the "generate_target" TCL command).
            See :py:mod:`.examples.simulate.py` for an example of using this.
    """
    toml_data: dict[str, dict[str, Any]] = dict(libraries={})

    def add_file(file_path: Path, library_name: str) -> None:
        """
        Note that 'file_path' may contain wildcards.
        """
        if library_name not in toml_data["libraries"]:
            toml_data["libraries"][library_name] = dict(files=[])

            if library_name in ["vunit_lib", "osvvm", "unisim", "xil_defaultlib"]:
                toml_data["libraries"][library_name]["is_third_party"] = True

        toml_data["libraries"][library_name]["files"].append(str(file_path.resolve()))

    if modules is not None:
        for module in modules:
            add_file(file_path=module.path / "**" / "*.vhd", library_name=module.library_name)

    if vunit_proj is not None:
        for source_file in vunit_proj.get_compile_order():
            add_file(file_path=Path(source_file.name), library_name=source_file.library.name)

    if files is not None:
        for file_path, library_name in files:
            add_file(file_path=file_path, library_name=library_name)

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

        add_file(file_path=vcomponents_package, library_name="unisim")

    if ip_core_vivado_project_directory is not None:
        # Vivado 2020.2+ (?) seems to place the files in "gen"
        ip_gen_dir = (
            ip_core_vivado_project_directory / f"{VivadoIpCores.project_name}.gen" / "sources_1"
        )
        if ip_gen_dir.exists():
            add_file(file_path=ip_gen_dir / "ip" / "**" / "*.vhd", library_name="xil_defaultlib")

    rtoml.dump(obj=toml_data, file=output_path / "vhdl_ls.toml", pretty=True)
