# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import argparse
import sys
from pathlib import Path
from shutil import copy2, make_archive

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

# Import before others since it modifies PYTHONPATH. pylint: disable=unused-import
import tsfpga.examples.example_pythonpath  # noqa: F401

# First party libraries
from tsfpga.build_project_list import BuildProjectList
from tsfpga.examples.example_env import TSFPGA_EXAMPLES_TEMP_DIR, get_tsfpga_example_modules
from tsfpga.system_utils import create_directory, delete


def arguments(default_temp_dir=TSFPGA_EXAMPLES_TEMP_DIR):
    """
    Setup of arguments for the example build flow.

    Arguments:
        default_temp_dir (pathlib.Path): Default value for output paths.
    """
    parser = argparse.ArgumentParser(
        "Create, synth and build an FPGA project",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    group = parser.add_mutually_exclusive_group()

    group.add_argument("--list-only", action="store_true", help="list the available projects")

    group.add_argument(
        "--generate-registers-only",
        action="store_true",
        help="only generate the register artifacts (C/C++ code, HTML, ...) for inspection",
    )

    group.add_argument("--create-only", action="store_true", help="only create projects")

    group.add_argument("--synth-only", action="store_true", help="only synthesize projects")

    group.add_argument(
        "--from-impl",
        action="store_true",
        help="run impl and onwards on an existing synthesized projects",
    )

    group.add_argument("--open", action="store_true", help="open existing projects in the GUI")

    parser.add_argument(
        "--use-existing-project",
        action="store_true",
        help="build existing projects, or create first if they do not exist",
    )

    parser.add_argument(
        "--netlist-builds",
        action="store_true",
        help="use netlist build projects instead of top level build projects",
    )

    parser.add_argument(
        "--projects-path",
        type=Path,
        default=default_temp_dir / "projects",
        help="the FPGA build projects will be placed here",
    )

    parser.add_argument(
        "--ip-cache-path",
        type=Path,
        default=default_temp_dir / "vivado_ip_cache",
        help="location of Vivado IP cache",
    )

    parser.add_argument(
        "--output-path",
        type=Path,
        required=False,
        help="the output products (bit file, ...) will be placed here",
    )

    parser.add_argument(
        "--num-parallel-builds", type=int, default=8, help="Number of parallel builds to launch"
    )

    parser.add_argument(
        "--num-threads-per-build",
        type=int,
        default=4,
        help="number of threads for each build process",
    )

    parser.add_argument("--no-color", action="store_true", help="disable color in printouts")

    parser.add_argument(
        "project_filters",
        nargs="*",
        help="filter for which projects to build. Can use wildcards. Leave empty for all.",
    )

    args = parser.parse_args()

    assert (
        args.use_existing_project or not args.from_impl
    ), "Must set --use-existing-project when using --from-impl"

    return args


def main():
    """
    Main function for building FPGA projects. If you are setting up a new build flow from scratch,
    you probably want to copy and modify this function, and reuse the others.
    """
    args = arguments()
    modules = get_tsfpga_example_modules()
    projects = BuildProjectList(
        modules=modules,
        project_filters=args.project_filters,
        include_netlist_not_top_builds=args.netlist_builds,
        no_color=args.no_color,
    )

    sys.exit(setup_and_run(modules, projects, args))


def collect_artifacts(project, output_path):
    """
    Example of a method to collect build artifacts. Will create a zip file with the bitstream,
    hardware definition (.xsa) and register documentation.

    Arguments:
        project (:class:`.VivadoProject`): Project object that has been built,
            and who's artifacts shall now be collected.
        output_path (pathlib.Path): Path to the build output. Artifact zip will be placed here
            as well.
    """
    version = "0.0.0"
    release_dir = create_directory(output_path / f"{project.name}-{version}", empty=True)
    print(f"Creating release in {release_dir.resolve()}.zip")

    generate_registers(project.modules, release_dir / "registers")
    copy2(output_path / f"{project.name }.bit", release_dir)
    copy2(output_path / f"{project.name}.bin", release_dir)
    if (output_path / f"{project.name}.xsa").exists():
        copy2(output_path / f"{project.name}.xsa", release_dir)

    make_archive(release_dir, "zip", release_dir)

    # Remove folder so that only zip remains
    delete(release_dir)

    return True


def setup_and_run(modules, projects, args, collect_artifacts_function=collect_artifacts):
    """
    Setup build projects, and execute as instructed by the arguments.

    Arguments:
        modules (:class:`.ModuleList`): When running a register generation, registers from these
            modules will be included.
        projects (:class:`.BuildProjectList`): These build projects will be built.
        args: Command line argument namespace.
        collect_artifacts_function: Function pointer to a function that collects build artifacts.
            Will be run after a successful implementation build.
            The function must return ``True`` if successful and ``False`` otherwise.
            It will receive the ``project`` and ``output_path`` as arguments.

    Return:
        int: 0 if everything passed, otherwise non-zero. Can be used for system exit code.
    """
    if args.list_only:
        print(projects)
        return 0

    if args.generate_registers_only:
        # Generate register output from all modules. Note that this is not used by the
        # build flow or simulation flow, it is only for the user to inspect the artifacts.
        generate_registers(modules=modules, output_path=args.projects_path.parent / "registers")
        return 0

    if args.open:
        projects.open(projects_path=args.projects_path)
        return 0

    if args.use_existing_project:
        create_ok = projects.create_unless_exists(
            projects_path=args.projects_path,
            num_parallel_builds=args.num_parallel_builds,
            ip_cache_path=args.ip_cache_path,
        )
    else:
        create_ok = projects.create(
            projects_path=args.projects_path,
            num_parallel_builds=args.num_parallel_builds,
            ip_cache_path=args.ip_cache_path,
        )

    if not create_ok:
        return 1

    if args.create_only:
        return 0

    # If doing only synthesis there are no artifacts to collect
    collect_artifacts_function = (
        None if (args.synth_only or args.netlist_builds) else collect_artifacts_function
    )

    build_ok = projects.build(
        projects_path=args.projects_path,
        collect_artifacts=collect_artifacts_function,
        num_parallel_builds=args.num_parallel_builds,
        output_path=args.output_path,
        synth_only=args.synth_only,
        from_impl=args.from_impl,
        num_threads_per_build=args.num_threads_per_build,
    )

    if build_ok:
        return 0
    return 1


def generate_registers(modules, output_path):
    """
    Generate all register artifacts from the given modules.

    Arguments:
        modules (:class:`.ModuleList`): Registers from these modules will be included.
        output_path (pathlib.Path): Register artifacts will be placed here.
    """
    print(f"Generating registers in {output_path.resolve()}")

    for module in modules:
        if module.registers is not None:
            vhdl_path = create_directory(output_path / "vhdl", empty=False)
            module.registers.create_vhdl_package(vhdl_path)

            module.registers.copy_source_definition(output_path / "toml")

            module.registers.create_c_header(output_path / "c")
            module.registers.create_cpp_interface(output_path / "cpp" / "include")
            module.registers.create_cpp_header(output_path / "cpp" / "include")
            module.registers.create_cpp_implementation(output_path / "cpp")
            module.registers.create_html_page(output_path / "html")
            module.registers.create_html_register_table(output_path / "html" / "tables")
            module.registers.create_html_constant_table(output_path / "html" / "tables")
            module.registers.create_python_class(output_path / "python")


if __name__ == "__main__":
    main()
