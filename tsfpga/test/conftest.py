# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Import before others since it modifies PYTHONPATH. pylint: disable=unused-import
import tsfpga.examples.example_pythonpath  # noqa: F401

# Third party libraries
import pytest


@pytest.fixture
def fixture_tmp_path(request, tmp_path):
    """
    A pytest fixture for usage in unittest.TestCase style test classes which gives
    access to a unique temp path for each test case.
    """
    # Set class member tmp_path
    request.cls.tmp_path = tmp_path
