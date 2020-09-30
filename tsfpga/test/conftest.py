# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import sys
import pytest

import tsfpga

PATH_TO_VUNIT = tsfpga.REPO_ROOT.parent / "vunit"
sys.path.append(str(PATH_TO_VUNIT.resolve()))


@pytest.fixture
def fixture_tmp_path(request, tmp_path):
    """
    A pytest fixture for usage in unittest.TestCase style test classes which gives
    access to a unique temp path for each test case.
    """
    # Set class member tmp_path
    request.cls.tmp_path = tmp_path
