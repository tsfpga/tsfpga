# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from pathlib import Path
from unittest.mock import patch

import pytest

from tsfpga.formal_project import FormalConfig, FormalProject, FormalTestCase


def test_generics_dict_should_be_copied():
    """
    It should be possible to update the original dict object without affecting the already-created
    formal test case
    """
    formal_project = FormalProject(project_path=Path(), modules=[])

    generics = dict(a=1)
    formal_project.add_config(top="apa", generics=generics)

    generics.update(a=2)
    formal_project.add_config(top="hest", generics=generics)

    formal_project.add_config(top="zebra")

    # pylint: disable=protected-access
    assert formal_project._formal_config_list[0].top == "apa"
    assert formal_project._formal_config_list[0].generics == dict(a=1)
    assert formal_project._formal_config_list[1].top == "hest"
    assert formal_project._formal_config_list[1].generics == dict(a=2)
    assert formal_project._formal_config_list[2].top == "zebra"
    assert formal_project._formal_config_list[2].generics is None


def test_formal_project_run(tmp_path):
    project_path = tmp_path / "projects"
    formal_project = FormalProject(modules=[], project_path=project_path)
    formal_project.add_config(top="top", engine_command="engine")

    src_files = ["src_file1", "src_file2"]
    compiled_libraries = ["compiled_library1", "compiled_library2"]
    with patch(
        "tsfpga.formal_project.FormalProject._compile_source_code", autospec=True
    ) as mocked_compile_source_code, patch(
        "tsfpga.formal_project.FormalTestCase", autospec=True
    ) as mocked_formal_test_case, patch(
        "tsfpga.formal_project.TestList.keep_matches", autospec=True
    ):
        mocked_compile_source_code.return_value = (src_files, compiled_libraries)
        mocked_formal_test_case.return_value.name = "apa"

        formal_project.run()

    mocked_formal_test_case.return_value.set_src_files.assert_called_once_with(src_files=src_files)
    mocked_formal_test_case.return_value.run.assert_called_once()


def test_formal_test_case_fails_when_missing_settings(tmp_path):
    formal_config = FormalConfig(top="top")
    formal_test_case = FormalTestCase(formal_config)
    formal_test_case.set_compiled_libraries([])

    with pytest.raises(ValueError) as exception_info:
        formal_test_case.run(output_path=tmp_path, read_output=None)
    assert (
        exception_info.value is not None
    ), "Run should fail with ValueError when not ok src_files is missing"

    formal_test_case = FormalTestCase(formal_config)
    formal_test_case.set_src_files([])

    with pytest.raises(ValueError) as exception_info:
        formal_test_case.run(output_path=tmp_path, read_output=None)
    assert (
        exception_info.value is not None
    ), "Run should fail with ValueError when not ok compiled_libraries is missing"


def test_formal_test_case_run(tmp_path):
    formal_config = FormalConfig(top="top")
    formal_test_case = FormalTestCase(formal_config)

    formal_test_case.set_src_files([])
    formal_test_case.set_compiled_libraries([])

    with patch("tsfpga.yosys_project.Process", autospec=True):
        formal_test_case.run(output_path=tmp_path, read_output=None)


def test_create_formal_config_with_default_arguments():
    formal_config = FormalConfig(top="top")
    assert formal_config.test_name == "top"
