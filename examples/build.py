# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import argparse
from pathlib import Path
import json
from shutil import copy2, make_archive
import sys

PATH_TO_TSFPGA = Path(__file__).parent.parent
sys.path.append(str(PATH_TO_TSFPGA))
from tsfpga.build_project_list import BuildProjectList
from tsfpga.system_utils import create_directory, delete

from examples.tsfpga_example_env import get_tsfpga_modules, TSFPGA_EXAMPLES_TEMP_DIR


def arguments(default_temp_dir=TSFPGA_EXAMPLES_TEMP_DIR):
    parser = argparse.ArgumentParser("Create, synth and build an FPGA project",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--list-only",
                        action="store_true",
                        help="list the available projects")
    parser.add_argument("--open",
                        action="store_true",
                        help="open an existing project in the GUI")
    parser.add_argument("--use-existing-project",
                        action="store_true",
                        help="build an existing project (do not create)")
    parser.add_argument("--generate-registers-only",
                        action="store_true",
                        help="only generate the register artifacts (C/C++ code, HTML, ...) for inspection")
    parser.add_argument("--create-only",
                        action="store_true",
                        help="only create a project")
    parser.add_argument("--synth-only",
                        action="store_true",
                        help="only synthesize a project")
    parser.add_argument("--netlist-builds",
                        action="store_true",
                        help="list netlist build projects instead of top level build projects")
    parser.add_argument("--project-path",
                        type=Path,
                        default=default_temp_dir / "projects",
                        help="the FPGA build project will be placed here")
    parser.add_argument("--ip-cache-path",
                        type=Path,
                        default=default_temp_dir / "vivado_ip_cache",
                        help="location of Vivado IP cache")
    parser.add_argument("--output-path",
                        type=Path,
                        required=False,
                        help="the output products (bit file, ...) will be placed here")
    parser.add_argument("--num-threads",
                        type=int,
                        default=8,
                        help="number of threads to use when building project")
    parser.add_argument("project_filters",
                        nargs="*",
                        help="filter for which projects to build")
    parser.add_argument("--collect-artifacts-only",
                        action="store_true",
                        help="only create release zip from an existing build result")
    args = parser.parse_args()

    return args


def main():
    modules = get_tsfpga_modules()
    projects = BuildProjectList(modules)
    args = arguments()

    setup_and_run(modules, projects, args)


def setup_and_run(modules, projects, args):
    if args.list_only:
        print(projects.list_projects(args.project_filters, args.netlist_builds))
        return

    if args.generate_registers_only:
        # Generate register output from all modules. Note that this is not used by the build
        # flow or simulation flow, it is only for the user to inspect the artifacts.
        generate_registers(modules, args.project_path.parent / "registers")
        return

    if not args.project_filters:
        message = "Must explicitly select builds. Available projects are:\n"
        message += projects.list_projects(args.project_filters)
        sys.exit(message)

    build_results = []
    for project in projects.get_projects(args.project_filters, args.netlist_builds):
        project_path = args.project_path / project.name

        if args.open:
            project.open(project_path)
            continue

        output_path = args.output_path if args.output_path else project_path

        # Possible that the user wants to collect artifacts (bit file) from a previous build
        if not args.collect_artifacts_only:
            build_results.append(build(args, project, project_path, output_path))

        if args.create_only or args.synth_only:
            continue

        collect_artifacts(project, output_path)

    print_results(build_results, args.synth_only)


def build(args, project, project_path, output_path):
    if not args.use_existing_project:
        project.create(project_path=project_path, ip_cache_path=args.ip_cache_path)

    if args.create_only:
        # No build result available. Return empty dict.
        return dict()

    create_directory(output_path, empty=False)
    result = project.build(project_path=project_path,
                           output_path=output_path,
                           synth_only=args.synth_only,
                           num_threads=args.num_threads)
    return result


def print_results(build_results, synth_only):
    if synth_only:
        dict_field = "synthesized_size"
        build_step = "Synthesis"
    else:
        dict_field = "implemented_size"
        build_step = "Implementation"

    for build_result in build_results:
        if dict_field in build_result:
            print("-" * 80)
            print(f"{build_step} size for build {build_result['name']}:")
            print(json.dumps(build_result[dict_field], indent=2))
            print("")


def generate_registers(modules, output_path):
    print(f"Generating registers in {output_path.resolve()}")

    for module in modules:
        # Create the package in the modules' folder as well, for completeness sake
        module.create_regs_vhdl_package()

        if module.registers is not None:
            vhdl_path = create_directory(output_path / "vhdl", empty=False)
            module.registers.create_vhdl_package(vhdl_path)

            module.registers.copy_source_definition(output_path / "json")

            module.registers.create_c_header(output_path / "c")
            module.registers.create_cpp_interface(output_path / "cpp" / "include")
            module.registers.create_cpp_header(output_path / "cpp" / "include")
            module.registers.create_cpp_implementation(output_path / "cpp")
            module.registers.create_html_page(output_path / "doc")
            module.registers.create_html_table(output_path / "doc" / "tables")


def collect_artifacts(project, output_path):
    version = "0.0.0.0"
    release_dir = create_directory(output_path / (project.name + "-" + version), empty=True)
    print(f"Creating release in {release_dir.resolve()}.zip")

    generate_registers(project.modules, release_dir / "registers")
    copy2(output_path / (project.name + ".bit"), release_dir)
    copy2(output_path / (project.name + ".bin"), release_dir)
    if (output_path / (project.name + ".xsa")).exists():
        copy2(output_path / (project.name + ".xsa"), release_dir)

    make_archive(release_dir, "zip", release_dir)

    # Remove folder so that only zip remains
    delete(release_dir)


if __name__ == "__main__":
    main()
