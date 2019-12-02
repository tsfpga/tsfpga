# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import join, dirname, abspath
from shutil import copy2, make_archive
import argparse
import sys

PATH_TO_TSFPGA = join(dirname(__file__), "..")
sys.path.append(PATH_TO_TSFPGA)
import tsfpga
from tsfpga.fpga_project_list import FPGAProjectList
from tsfpga.system_utils import create_directory, delete


def arguments(projects):
    parser = argparse.ArgumentParser("Build/synth/create an FPGA project",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--list", "-l",
                        action="store_true",
                        help="list the available projects")
    parser.add_argument("--use-existing-project",
                        action="store_true",
                        help="build an existing project")
    parser.add_argument("--create-only",
                        action="store_true",
                        help="only create a project")
    parser.add_argument("--synth-only",
                        action="store_true",
                        help="only synthesize a project")
    parser.add_argument("--project-path",
                        default=join(PATH_TO_TSFPGA, "generated", "projects"),
                        help="the FPGA build project will be placed here")
    parser.add_argument("--ip-cache-path",
                        default=join(PATH_TO_TSFPGA, "generated", "vivado_ip_cache"),
                        help="location of Vivado IP cache")
    parser.add_argument("--output-path",
                        required=False,
                        help="the output products (bit file, ...) will be placed here")
    parser.add_argument("--num-threads",
                        type=int,
                        default=8,
                        help="number of threads to use when building project")
    parser.add_argument("project_name",
                        nargs="?",
                        choices=projects.names(), help="which project to build")
    parser.add_argument("--collect-artifacts-only",
                        action="store_true",
                        help="only create release zip from an existing build result")
    args = parser.parse_args()

    if not args.project_name and not args.list:
        sys.exit("Need to specify project name")

    return args


def main():
    module_folders = [tsfpga.TSFPGA_MODULES, join(dirname(__file__), "modules")]
    projects = FPGAProjectList(module_folders)
    args = arguments(projects)

    if args.list:
        print("Available projects:\n\n%s" % projects)
        return

    project = projects.get(args.project_name)
    project_path = abspath(join(args.project_path, project.name))

    if not args.output_path:
        args.output_path = project_path

    if not args.collect_artifacts_only:
        build(args, project, project_path)

    if not args.create_only:
        collect_artifacts(args, project)


def build(args, project, project_path):
    if not args.use_existing_project:
        project.create(project_path=project_path, ip_cache_path=args.ip_cache_path)

    if args.create_only:
        return

    create_directory(args.output_path, empty=False)
    project.build(project_path=project_path,
                  output_path=args.output_path,
                  synth_only=args.synth_only,
                  num_threads=args.num_threads)


def collect_artifacts(args, project):
    version = "0.0.0.0"

    release_dir = create_directory(join(args.output_path, project.name + "-" + version), empty=True)
    print("Creating release in " + abspath(release_dir) + ".zip")

    for module in project.modules:
        if module.registers is not None:
            module.registers.create_c_header(join(release_dir, "c"))
            module.registers.create_cpp_interface(join(release_dir, "cpp", "include"))
            module.registers.create_cpp_header(join(release_dir, "cpp", "include"))
            module.registers.create_cpp_implementation(join(release_dir, "cpp"))
            module.registers.create_html_page(join(release_dir, "doc"))
            module.registers.create_html_table(join(release_dir, "doc", "tables"))

    copy2(join(args.output_path, project.name + ".bit"), release_dir)
    copy2(join(args.output_path, project.name + ".bin"), release_dir)
    copy2(join(args.output_path, project.name + ".hdf"), release_dir)

    make_archive(release_dir, "zip", release_dir)

    # Remove folder so that only zip remains
    delete(release_dir)


if __name__ == "__main__":
    main()
