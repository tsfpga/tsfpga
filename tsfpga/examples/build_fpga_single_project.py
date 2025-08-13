# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

"""
Build FPGA projects from the command line.
Note that this is an example script that illustrates how FPGA build projects can be built one
by one.
This is not the recommended standard build flow, see 'build_fpga.py' instead.

The benefit of building one by one is that build status is written directly to STDOUT.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install.
REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

# Import before others since it modifies PYTHONPATH.
import tsfpga.examples.example_pythonpath  # noqa: F401

from tsfpga.build_project_list import BuildProjectList
from tsfpga.examples.build_fpga import collect_artifacts
from tsfpga.examples.build_fpga_utils import arguments, generate_register_artifacts
from tsfpga.examples.example_env import TSFPGA_EXAMPLES_TEMP_DIR, get_tsfpga_example_modules

if TYPE_CHECKING:
    import argparse

    from tsfpga.module_list import ModuleList
    from tsfpga.vivado.project import VivadoProject


def main() -> None:
    """
    Main function for building single FPGA projects.
    Note that this is not the recommended standard build flow, see 'build_fpga.py' instead.
    """
    args = arguments(default_temp_dir=TSFPGA_EXAMPLES_TEMP_DIR)
    modules = get_tsfpga_example_modules()
    projects = BuildProjectList(
        modules=modules,
        project_filters=args.project_filters,
        include_netlist_not_top_builds=args.netlist_builds,
        no_color=args.no_color,
    )

    sys.exit(
        setup_and_run(
            modules=modules,
            projects=projects,
            args=args,
            collect_artifacts_function=collect_artifacts,
        )
    )


def setup_and_run(  # noqa: C901, PLR0911, PLR0912
    modules: ModuleList,
    projects: BuildProjectList,
    args: argparse.Namespace,
    collect_artifacts_function: Callable[[VivadoProject, Path], bool] | None,
) -> int:
    """
    Setup and execute build projects one by one.
    As instructed by the arguments.

    Note that this is not the recommended standard build flow, see 'build_fpga.py' instead.

    Note that this functions is a modified clone of the one in 'build_fpga_utils.py'.

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
        for project in projects.projects:
            project.open(
                project_path=projects.get_build_project_path(
                    project=project, projects_path=args.projects_path
                )
            )

        return 0

    if args.collect_artifacts_only:
        # We have to assume that the projects exist if the user sent this argument.
        # The 'collect_artifacts_function' call below will probably fail if it does not.
        create_ok = True

    else:
        create_ok = True

        for project in projects.projects:
            project_path = projects.get_build_project_path(
                project=project, projects_path=args.projects_path
            )

            if (not args.use_existing_project) or (not project_path.exists()):
                create_ok &= project.create(
                    project_path=project_path, ip_cache_path=args.ip_cache_path
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
            assert collect_artifacts_function(
                project=project,
                output_path=projects.get_build_project_output_path(
                    project=project, projects_path=args.projects_path, output_path=args.output_path
                ),
            )

        return 0

    build_ok = True
    for project in projects.projects:
        project_output_path = projects.get_build_project_output_path(
            project=project, projects_path=args.projects_path, output_path=args.output_path
        )

        build_result = project.build(
            project_path=projects.get_build_project_path(
                project=project, projects_path=args.projects_path
            ),
            output_path=project_output_path,
            synth_only=args.synth_only,
            from_impl=args.from_impl,
        )
        build_ok &= build_result.success

        if build_result.success and (collect_artifacts_function is not None):
            build_ok &= collect_artifacts_function(project=project, output_path=project_output_path)

    if build_ok:
        return 0

    return 1


if __name__ == "__main__":
    main()
