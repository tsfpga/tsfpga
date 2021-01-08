# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import sys

import tsfpga

PATH_TO_VUNIT = tsfpga.REPO_ROOT.parent / "vunit"
sys.path.append(str(PATH_TO_VUNIT.resolve()))
