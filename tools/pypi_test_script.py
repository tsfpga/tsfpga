# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Test script to see that everything from this package is importable.
# I.e. that a working installation is in place, along with all dependencies.
# Import all the things that are normally imported in
# 'simulate.py', 'build_fpga.py' and 'build_docs.py'.
# --------------------------------------------------------------------------------------------------

import tsfpga
import tsfpga.build_project_list
import tsfpga.examples.build_fpga_utils
import tsfpga.examples.simulation_utils
import tsfpga.git_utils
import tsfpga.system_utils
import tsfpga.tools.sphinx_doc  # noqa: F401


def main() -> None:
    print("done")


if __name__ == "__main__":
    main()
