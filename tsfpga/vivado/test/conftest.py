# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import sys

import tsfpga

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
PATH_TO_VUNIT = tsfpga.REPO_ROOT.parent / "vunit"
sys.path.insert(0, str(PATH_TO_VUNIT.resolve()))
