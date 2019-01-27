from os.path import join, dirname, abspath
import sys
import argparse

PATH_TO_HLD_REUSE = join(dirname(__file__), "..", "..")
sys.path.append(PATH_TO_HLD_REUSE)
from tsfpga.examples import MODULE_FOLDERS
from tsfpga.fpga_project_list import FPGAProjectList


def arguments(projects):
    parser = argparse.ArgumentParser("Build/synth/create an FPGA project")
    parser.add_argument("--list", "-l", action="store_true", help="list the available projects")
    parser.add_argument("--use-existing-project", action="store_true", help="build and existing project")
    parser.add_argument("--create-only", action="store_true", help="only create a project")
    parser.add_argument("--synth-only", action="store_true", help="only synthesize a project")
    parser.add_argument("--project-path", type=str, default=".", help="the FPGA build project will be placed here")
    parser.add_argument("--output-path", type=str, required=False, help="the output products (bit file, ...) will be placed here")
    parser.add_argument("--num-threads", type=int, default=8, help="number of threads to use when building project")
    parser.add_argument("project_name", nargs="?", choices=projects.names(), help="which project to build")
    args = parser.parse_args()

    if not args.project_name and not args.list:
        sys.exit("Need to specify project name")

    return args


def main():
    projects = FPGAProjectList(MODULE_FOLDERS)
    args = arguments(projects)

    if args.list:
        print("Available projects:\n\n%s" % projects)
        return

    project = projects.get(args.project_name)
    project_path = abspath(join(args.project_path, "build_" + project.name))

    if not args.output_path:
        args.output_path = project_path

    if not args.use_existing_project:
        project.create(project_path)

    if args.create_only:
        return

    project.build(project_path, args.output_path, args.synth_only, args.num_threads)


if __name__ == "__main__":
    main()
