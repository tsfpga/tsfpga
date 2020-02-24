# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import pytest

from tsfpga.system_utils import create_directory
from tsfpga.vivado_project import VivadoProject


def test_create_should_raise_exception_if_project_path_already_exists(tmp_path):
    create_directory(tmp_path / "projects" / "name")
    proj = VivadoProject(name="name", modules=[], part="part")
    with pytest.raises(ValueError) as exception_info:
        proj.create(tmp_path / "projects")
    assert str(exception_info.value).startswith("Folder already exists")


def test_build_should_raise_exception_if_project_does_not_exists(tmp_path):
    create_directory(tmp_path / "projects")
    proj = VivadoProject(name="name", modules=[], part="part")
    with pytest.raises(ValueError) as exception_info:
        proj.build(tmp_path / "projects", synth_only=True)
    assert str(exception_info.value).startswith("Project file does not exist")


def test_build_with_impl_run_should_raise_exception_if_no_output_path_is_given():
    proj = VivadoProject(name="name", modules=[], part="part")
    with pytest.raises(ValueError) as exception_info:
        proj.build("None")
    assert str(exception_info.value).startswith("Must specify output_path")
