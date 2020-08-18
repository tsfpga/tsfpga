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
PATH_TO_VUNIT = PATH_TO_TSFPGA.parent / "vunit"
sys.path.append(str(PATH_TO_VUNIT))

from vunit.color_printer import COLOR_PRINTER, NO_COLOR_PRINTER

from tsfpga.build_project_list import BuildProjectList
from tsfpga.system_utils import create_directory, delete
from tsfpga.vivado.project import BuildResult

from examples.tsfpga_example_env import get_tsfpga_modules, TSFPGA_EXAMPLES_TEMP_DIR


def arguments(default_temp_dir=TSFPGA_EXAMPLES_TEMP_DIR):
    parser = argparse.ArgumentParser("Create, synth and build an FPGA project",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--no-color",
                        action="store_true",
                        help="disable color in printouts")
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

    sys.exit(setup_and_run(modules, projects, args))


def setup_and_run(modules, projects, args):
    """
    Returns 0 if everything passed, otherwise non-zero.
    """
    if args.list_only:
        print(projects.list_projects(args.project_filters, args.netlist_builds))
        return 0

    if args.generate_registers_only:
        # Generate register output from all modules. Note that this is not used by the build
        # flow or simulation flow, it is only for the user to inspect the artifacts.
        generate_registers(modules, args.project_path.parent / "registers")
        return 0

    if not args.project_filters:
        print("Must explicitly select builds. Available projects are:")
        print(projects.list_projects(args.project_filters, args.netlist_builds))
        return -1

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

        if not project.is_netlist_build:
            collect_artifacts(project, output_path)

    if build_results:
        return print_results(build_results, args.no_color)
    return 0


def build(args, project, project_path, output_path):
    if not args.use_existing_project:
        project.create(project_path=project_path, ip_cache_path=args.ip_cache_path)

    if args.create_only:
        # Return BuildResult object with success, but no sizes.
        return BuildResult(project.name)

    create_directory(output_path, empty=False)
    result = project.build(project_path=project_path,
                           output_path=output_path,
                           synth_only=args.synth_only,
                           num_threads=args.num_threads)
    return result


def print_results(build_results, no_color):
    """
    Print result summary. Return 0 if all passed otherwise non-zero.
    """
    printer = NO_COLOR_PRINTER if no_color else COLOR_PRINTER
    green = COLOR_PRINTER.GREEN + COLOR_PRINTER.INTENSITY
    red = COLOR_PRINTER.RED + COLOR_PRINTER.INTENSITY

    name_length = max([len(build_result.name) for build_result in build_results])
    separator_length = max(len("pass") + 1 + name_length, 40)
    separator = "=" * separator_length

    num_pass = 0
    num_fail = 0
    num_total = len(build_results)

    print("\n" + ("=" * 4) + " Summary " + ("=" * (len(separator) - 4 - len(" Summary "))))
    for build_result in build_results:
        if build_result.success:
            num_pass += 1
            printer.write("pass", fg=green)
        else:
            num_fail += 1
            printer.write("fail", fg=red)

        print(f" {build_result.name}")

        if build_result.implementation_size:
            build_step = "Implementation"
            size = build_result.implementation_size
        else:
            build_step = "Synthesis"
            size = build_result.synthesis_size

        if size:
            print(f"{build_step} size:")
            print(json.dumps(size, indent=2))
            print("")

    print(separator)
    if num_pass > 0:
        printer.write("pass", fg=green)
        print(f" {num_pass} of {num_total}")
    if num_fail > 0:
        printer.write("fail", fg=red)
        print(f" {num_fail} of {num_total}")

    print(separator)
    if num_fail == 0:
        printer.write("All passed!", fg=green)
        print()
    else:
        printer.write("Some failed!", fg=red)
        print()

    return num_fail


def generate_registers(modules, output_path):
    print(f"Generating registers in {output_path.resolve()}")

    for module in modules:
        # Create the package in the modules' folder as well, for completeness sake
        module.create_regs_vhdl_package()

        if module.registers is not None:
            vhdl_path = create_directory(output_path / "vhdl", empty=False)
            module.registers.create_vhdl_package(vhdl_path)

            module.registers.copy_source_definition(output_path / "toml")

            module.registers.create_c_header(output_path / "c")
            module.registers.create_cpp_interface(output_path / "cpp" / "include")
            module.registers.create_cpp_header(output_path / "cpp" / "include")
            module.registers.create_cpp_implementation(output_path / "cpp")
            module.registers.create_html_page(output_path / "doc")
            module.registers.create_html_table(output_path / "doc" / "tables")


def collect_artifacts(project, output_path):
    version = "0.0.0.0"
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


if __name__ == "__main__":
    main()
