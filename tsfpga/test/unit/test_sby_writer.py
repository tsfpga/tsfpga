# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from pathlib import Path

import unittest
import pytest

from tsfpga.sby_writer import SbyWriter


@pytest.mark.usefixtures("fixture_tmp_path")
class TestSbyWriter(unittest.TestCase):

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
        self.output_path = self.tmp_path / Path("sby_writer_output.sby")

    def test_sby_writer(self):
        sby_writer = SbyWriter()
        sby_writer.write_sby(
            output_path=self.output_path,
            top=self.top,
            formal_settings=self.formal_settings,
            compiled_libraries=self.compiled_libraries,
            src_files=self.src_files,
            generics=self.generics,
        )

        assert self.output_path.exists()

    def test_should_work_with_empty_generics(self):
        sby_writer = SbyWriter()
        sby_writer.write_sby(
            output_path=self.output_path,
            top=self.top,
            formal_settings=self.formal_settings,
            compiled_libraries=self.compiled_libraries,
            src_files=self.src_files,
        )

        assert self.output_path.exists()

    def test_fails_on_nonexisting_setting(self):
        sby_writer = SbyWriter()
        bad_formal_settings = self.formal_settings.copy()
        bad_formal_settings["dummy_key"] = "apa"
        with pytest.raises(ValueError) as exception_info:
            sby_writer.write_sby(
                output_path=self.output_path,
                top=self.top,
                formal_settings=bad_formal_settings,
                compiled_libraries=self.compiled_libraries,
                src_files=self.src_files,
            )
        assert str(exception_info.value).startswith("Unexpected keys")
