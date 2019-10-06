# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import argparse
from os.path import join, dirname, basename, abspath
from shutil import copy2, make_archive
import sys

PATH_TO_TSFPGA = join(dirname(__file__), "..", "..")
sys.path.append(PATH_TO_TSFPGA)
from tsfpga.examples import MODULE_FOLDERS
from tsfpga.module import get_modules
from tsfpga.system_utils import create_directory, delete


def main():
    args = arguments()
    version = "0.0.0.0"

    release_dir = create_directory(join(args.output_path, args.project_name + "-" + version), empty=True)
    print("Creating release in " + abspath(release_dir) + ".zip")

    for module in get_modules(MODULE_FOLDERS):
        if module.registers is not None:
            module.registers.create_c_header(join(release_dir, "c"))
            module.registers.create_cpp_interface(join(release_dir, "cpp", "include"))
            module.registers.create_cpp_header(join(release_dir, "cpp", "include"))
            module.registers.create_cpp_implementation(join(release_dir, "cpp"))
            module.registers.create_html_page(join(release_dir, "doc"))
            module.registers.create_html_table(join(release_dir, "doc", "tables"))

    copy2(join(args.build_path, args.project_name + ".bit"), release_dir)
    copy2(join(args.build_path, args.project_name + ".hdf"), release_dir)

    make_archive(release_dir, "zip", release_dir)

    # Remove folder so that only zip remains
    delete(release_dir)


def arguments():
    parser = argparse.ArgumentParser("Create release artifacts of an FPGA build",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--build-path",
                        type=str,
                        required=True,
                        help="location of the FPGA build")
    parser.add_argument("--output-path",
                        type=str,
                        default=join(PATH_TO_TSFPGA, "generated"),
                        help="the resulting zip will be placed here")
    parser.add_argument("--project-name",
                        type=str,
                        required=False,
                        help="name of the FPGA build. If none given it will be deduced from the build path.")
    args = parser.parse_args()

    if not args.project_name:
        args.project_name = basename(dirname(args.build_path))

    return args


if __name__ == "__main__":
    main()
