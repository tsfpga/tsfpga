# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import sys
import pytest

import tsfpga

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
PATH_TO_HDL_REGISTERS = tsfpga.REPO_ROOT.parent.resolve() / "hdl_registers"
sys.path.insert(0, str(PATH_TO_HDL_REGISTERS))
PATH_TO_VUNIT = tsfpga.REPO_ROOT.parent.parent.resolve() / "vunit" / "vunit"
sys.path.insert(0, str(PATH_TO_VUNIT))


@pytest.fixture
def fixture_tmp_path(request, tmp_path):
    """
    A pytest fixture for usage in unittest.TestCase style test classes which gives
    access to a unique temp path for each test case.
    """
    # Set class member tmp_path
    request.cls.tmp_path = tmp_path
