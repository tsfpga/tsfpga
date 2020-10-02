# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from unittest import TestCase
from unittest.mock import patch

import pytest

from tsfpga.yosys_project import YosysProject


@pytest.mark.usefixtures("fixture_tmp_path")
class TestYosysProject(TestCase):

    top = "dummy_top"
    formal_settings = dict(
        mode="dummy_mode",
        depth=20,
        engine_command="dummy_engine_command",
        solver_command="dummy_solver_command",
    )

    tmp_path = None
    compiled_libraries = ["library_1", "library_2"]
    src_files = ["file_1", "file_2.vhd"]
    generics = dict(dummy_generic="dummy_generic_val")

    def setUp(self):
        self.project_path = self.tmp_path

    def test_can_create(self):
        yosys_project = YosysProject(
            top=self.top, generics=self.generics, formal_settings=self.formal_settings
        )
        assert yosys_project.top == self.top
        assert yosys_project.generics == self.generics
        assert yosys_project.formal_settings == self.formal_settings

    def test_can_create_without_generics(self):
        yosys_project = YosysProject(top=self.top, formal_settings=self.formal_settings)
        assert yosys_project.generics == dict()

    def test_runs_symbiyosys(self):
        yosys_project = YosysProject(
            top=self.top, generics=self.generics, formal_settings=self.formal_settings
        )

        # Check run_function, but mock the subprocess
        with patch("tsfpga.yosys_project.Process", autospec=True):
            assert yosys_project.run_formal(
                project_path=self.project_path,
                src_files=self.src_files,
                compiled_libraries=self.compiled_libraries,
            )

        # Check that the output file was created
        assert (self.project_path / "run_symbiyosys.sby").exists()
