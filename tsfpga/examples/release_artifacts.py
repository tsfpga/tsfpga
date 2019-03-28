# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import join, dirname
import sys

PATH_TO_TSFPGA = join(dirname(__file__), "..", "..")
sys.path.append(PATH_TO_TSFPGA)
import tsfpga
from tsfpga.module import get_modules
from tsfpga.examples import MODULE_FOLDERS
from tsfpga.system_utils import create_directory


def main():
    version = "0.0.0.0"
    release_dir = create_directory(join(tsfpga.ROOT, "fpga-" + version), empty=True)

    for module in get_modules(MODULE_FOLDERS):
        if module.registers is not None:
            module.registers.create_c_header(join(release_dir, "header"))
            module.registers.create_html_page(join(release_dir, "doc"))
            module.registers.create_html_table(join(release_dir, "doc", "tables"))


if __name__ == "__main__":
    main()
