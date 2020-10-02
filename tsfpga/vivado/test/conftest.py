# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import sys

import tsfpga

PATH_TO_VUNIT = tsfpga.REPO_ROOT.parent / "vunit"
sys.path.append(str(PATH_TO_VUNIT.resolve()))
