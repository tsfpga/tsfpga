# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import abspath, dirname, exists, join
import toml


def create_configuration(output_path,
                         modules=None,
                         vunit_proj=None,
                         vivado_location=None,
                         ip_core_vivado_project_sources_directory=None):
    """
    Create a configuration file (vhdl_ls.toml) for the rust_hdl VHDL Language Server.

    Can be used with modules and an "empty" VUnit project, or with a complete VUnit
    project with all user files added.

    Execution of this function takes roughly 12 ms for a large project (62 modules and a
    VUnit project).

    :param output_path: Output folder.
    :param modules: A list of Module objects.
    :param vunit_proj: A VUnit project.
    :param vunit_proj: Vivado binary path. Will add unisim from this Vivado installation.
    :param ip_core_vivado_project_sources_directory: Path to the sources directory of a
        Vivado project that contains generated "simulation" and "synthesis" files
        of IP cores (the "generate_target" TCL command). See simulate.py for an example
        of using this.
    """
    toml_data = dict(libraries=dict())

    if modules is not None:
        for module in modules:
            vhd_file_wildcard = join(abspath(module.path), "**", "*.vhd")
            toml_data["libraries"][module.library_name] = dict(
                files=[vhd_file_wildcard])

    if vunit_proj is not None:
        for source_file in vunit_proj.get_compile_order():
            if source_file.library.name not in toml_data["libraries"]:
                toml_data["libraries"][source_file.library.name] = dict(
                    files=[])
            toml_data["libraries"][source_file.library.name]["files"].append(
                abspath(source_file.name))

    if vivado_location is not None:
        vcomponents_package = abspath(join(dirname(vivado_location),
                                           "..",
                                           "data",
                                           "vhdl",
                                           "src",
                                           "unisims",
                                           "unisim_retarget_VCOMP.vhd"))
        if not exists(vcomponents_package):
            raise FileNotFoundError("Could not find unisim file: " + vcomponents_package)

        toml_data["libraries"]["unisim"] = dict(files=[vcomponents_package])

    if ip_core_vivado_project_sources_directory is not None:
        ip_sources_dir = join(ip_core_vivado_project_sources_directory, "ip")
        if not exists(ip_sources_dir):
            raise FileNotFoundError("Could not find IP sources dir: " + ip_sources_dir)

        # Add file from the "synth" folder rather than "sim". It seems that "synth"
        # always contains a VHDL file while "sim" sometimes contains a Verilog file.
        vhd_file_wildcard = join(abspath(ip_sources_dir), "*", "synth", "*.vhd")
        toml_data["libraries"]["xil_defaultlib"] = dict(files=[vhd_file_wildcard])

    with open(join(output_path, "vhdl_ls.toml"), "w") as output_file_handle:
        toml.dump(toml_data, output_file_handle)
