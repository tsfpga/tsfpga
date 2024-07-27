# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import argparse
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

# Third party libraries
from hdl_registers.generator.c.header import CHeaderGenerator
from hdl_registers.generator.cpp.header import CppHeaderGenerator
from hdl_registers.generator.cpp.implementation import CppImplementationGenerator
from hdl_registers.generator.cpp.interface import CppInterfaceGenerator
from hdl_registers.generator.html.page import HtmlPageGenerator
from hdl_registers.generator.python.accessor import PythonAccessorGenerator
from hdl_registers.generator.python.pickle import PythonPickleGenerator

# First party libraries
from tsfpga.build_project_list import BuildProjectList
from tsfpga.system_utils import create_directory

if TYPE_CHECKING:
    # First party libraries
    from tsfpga.module_list import ModuleList
    from tsfpga.vivado.project import VivadoProject


def arguments(default_temp_dir: Path) -> argparse.Namespace:
    """
    Setup of arguments for the example build flow.

    Arguments:
        default_temp_dir: Default value for output paths.
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

    group.add_argument(
        "--collect-artifacts-only",
        action="store_true",
        help="collect artifacts of previously successful builds",
    )

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


def setup_and_run(  # pylint: disable=too-many-return-statements
    modules: "ModuleList",
    projects: BuildProjectList,
    args: argparse.Namespace,
    collect_artifacts_function: Optional[Callable[["VivadoProject", Path], bool]],
) -> int:
    """
    Setup and execute build projects.
    As instructed by the arguments.

    Arguments:
        modules: When running a register generation, registers from these
            modules will be included.
        projects: These build projects will be built.
        args: Command line argument namespace.
        collect_artifacts_function: Function pointer to a function that collects build artifacts.
            Will be run after a successful implementation build.
            The function must return ``True`` if successful and ``False`` otherwise.
            It will receive the ``project`` and ``output_path`` as arguments.
            Can be ``None`` if no special artifact collection operation shall be run.

    Return:
        0 if everything passed, otherwise non-zero.
        Can be used for system exit code.
    """
    if args.list_only:
        print(projects)
        return 0

    if args.generate_registers_only:
        # Generate register output from all modules. Note that this is not used by the
        # build flow or simulation flow, it is only for the user to inspect the artifacts.
        generate_register_artifacts(
            modules=modules, output_path=args.projects_path.parent / "registers"
        )
        return 0

    if args.open:
        projects.open(projects_path=args.projects_path)
        return 0

    if args.collect_artifacts_only:
        # We have to assume that the project exists if the user sent this argument.
        # The 'collect_artifacts_function' call below will probably fail if it does not.
        create_ok = True

    elif args.use_existing_project:
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

    # If doing only synthesis, there are no artifacts to collect.
    collect_artifacts_function = (
        None if (args.synth_only or args.netlist_builds) else collect_artifacts_function
    )

    if args.collect_artifacts_only:
        assert collect_artifacts_function is not None, "No artifact collection available"

        for project in projects.projects:
            # Assign the arguments in the exact same way as the call to 'projects.build()' below.
            # Ensures that the correct output path is used in all scenarios.
            project_build_output_path = projects.get_build_project_output_path(
                project=project, projects_path=args.projects_path, output_path=args.output_path
            )
            # Collect artifacts function must return True.
            assert collect_artifacts_function(project, project_build_output_path)

        return 0

    build_ok = projects.build(
        projects_path=args.projects_path,
        num_parallel_builds=args.num_parallel_builds,
        num_threads_per_build=args.num_threads_per_build,
        output_path=args.output_path,
        collect_artifacts=collect_artifacts_function,
        synth_only=args.synth_only,
        from_impl=args.from_impl,
    )

    if build_ok:
        return 0

    return 1


def generate_register_artifacts(modules: "ModuleList", output_path: Path) -> None:
    """
    Generate register artifacts from the given modules.

    Arguments:
        modules: Registers from these modules will be included.
        output_path: Register artifacts will be placed here.
    """
    print(f"Generating register artifacts in {output_path.resolve()}...")

    # Empty the output directory so we don't have leftover old artifacts.
    create_directory(directory=output_path, empty=True)

    for module in modules:
        if module.registers is not None:
            CHeaderGenerator(module.registers, output_path / "c").create()

            CppInterfaceGenerator(module.registers, output_path / "cpp" / "include").create()
            CppHeaderGenerator(module.registers, output_path / "cpp" / "include").create()
            CppImplementationGenerator(module.registers, output_path / "cpp").create()

            HtmlPageGenerator(module.registers, output_path / "html").create()

            PythonPickleGenerator(module.registers, output_path / "python").create()
            PythonAccessorGenerator(module.registers, output_path / "python").create()
