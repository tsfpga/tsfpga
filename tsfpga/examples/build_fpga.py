# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import sys
from pathlib import Path
from shutil import copy2, make_archive
from typing import TYPE_CHECKING

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install.
REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

# Import before others since it modifies PYTHONPATH. pylint: disable=unused-import
import tsfpga.examples.example_pythonpath  # noqa: F401

# First party libraries
from tsfpga.build_project_list import BuildProjectList
from tsfpga.examples.build_fpga_utils import arguments, generate_register_artifacts, setup_and_run
from tsfpga.examples.example_env import TSFPGA_EXAMPLES_TEMP_DIR, get_tsfpga_example_modules
from tsfpga.system_utils import create_directory, delete

if TYPE_CHECKING:
    # First party libraries
    from tsfpga.vivado.project import VivadoProject


def main() -> None:
    """
    Main function for building FPGA projects. If you are setting up a new build flow from scratch,
    you probably want to copy and modify this function, and reuse the others.
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


def collect_artifacts(project: "VivadoProject", output_path: Path) -> bool:
    """
    Example of a method to collect build artifacts. Will create a zip file with the bitstream,
    hardware definition (.xsa) and register documentation.

    Arguments:
        project: Project object that has been built, and who's artifacts shall now be collected.
        output_path: Path to the build output. Artifact zip will be placed here as well.

    Return:
        True if everything went well.
    """
    version = "0.0.0"
    release_dir = create_directory(output_path / f"{project.name}-{version}", empty=True)
    print(f"Creating release in {release_dir.resolve()}.zip")

    generate_register_artifacts(modules=project.modules, output_path=release_dir / "registers")
    copy2(output_path / f"{project.name}.bit", release_dir)
    copy2(output_path / f"{project.name}.bin", release_dir)
    if (output_path / f"{project.name}.xsa").exists():
        copy2(output_path / f"{project.name}.xsa", release_dir)

    make_archive(str(release_dir), "zip", release_dir)

    # Remove folder so that only zip remains
    delete(release_dir)

    return True


if __name__ == "__main__":
    main()
