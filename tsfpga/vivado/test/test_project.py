# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest

from tsfpga.module import BaseModule
from tsfpga.system_utils import create_directory, create_file
from tsfpga.vivado.project import VivadoProject

# pylint: disable=unused-import
from tsfpga.test.conftest import fixture_tmp_path  # noqa: F401


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


def test_top_name():
    assert VivadoProject(name="apa", modules=[], part="").top == "apa_top"
    assert VivadoProject(name="apa", modules=[], part="", top="hest").top == "hest"


def test_project_file_name_is_same_as_project_name():
    project_path = Path("projects/apa")
    assert (
        VivadoProject(name="apa", modules=[], part="").project_file(project_path)
        == project_path / "apa.xpr"
    )


def test_project_create(tmp_path):
    with patch("tsfpga.vivado.project.run_vivado_tcl", autospec=True) as _:
        assert VivadoProject(name="apa", modules=[], part="").create(tmp_path / "projects" / "apa")
    assert (tmp_path / "projects" / "apa" / "create_vivado_project.tcl").exists()


def test_project_create_should_raise_exception_if_project_path_already_exists(tmp_path):
    project_path = create_directory(tmp_path / "projects" / "apa")
    with pytest.raises(ValueError) as exception_info:
        VivadoProject(name="apa", modules=[], part="").create(project_path)
    assert str(exception_info.value) == f"Folder already exists: {project_path}"


def test_can_cast_project_to_string_without_error():
    print(VivadoProject(name="name", modules=[], part=""))
    print(
        VivadoProject(
            name="name",
            modules=[],
            part="",
            generics=dict(stuff="and", things=True),
            defined_at=Path(__file__),
        )
    )


# pylint: disable=too-many-instance-attributes
@pytest.mark.usefixtures("fixture_tmp_path")
class TestVivadoProject(unittest.TestCase):

    tmp_path = None

    def setUp(self):
        self.project_path = self.tmp_path / "projects" / "apa" / "project"
        self.output_path = self.tmp_path / "projects" / "apa"
        self.ip_cache_path = MagicMock()
        self.static_generics = dict(name="value")
        self.num_threads = 4
        self.run_index = 3
        self.synth_only = False

        self.mocked_run_vivado_tcl = None

    def _create(self, project):
        with patch(
            "tsfpga.vivado.project.run_vivado_tcl", autospec=True
        ) as self.mocked_run_vivado_tcl:
            return project.create(project_path=self.project_path, ip_cache_path=self.ip_cache_path)

    def test_default_pre_create_hook_should_pass(self):
        class CustomVivadoProject(VivadoProject):

            pass

        project = CustomVivadoProject(name="apa", modules=[], part="")
        self._create(project)
        self.mocked_run_vivado_tcl.assert_called_once()

    def test_project_pre_create_hook_returning_false_should_fail_and_not_call_vivado_run(self):
        class CustomVivadoProject(VivadoProject):
            def pre_create(self, **kwargs):  # pylint: disable=no-self-use, unused-argument
                return False

        assert not self._create(CustomVivadoProject(name="apa", modules=[], part=""))
        self.mocked_run_vivado_tcl.assert_not_called()

    def test_create_should_call_pre_create_with_correct_parameters(self):
        project = VivadoProject(name="apa", modules=[], part="")
        with patch("tsfpga.vivado.project.VivadoProject.pre_create") as mocked_pre_create:
            self._create(project)
        mocked_pre_create.assert_called_once_with(
            project_path=self.project_path, ip_cache_path=self.ip_cache_path
        )
        self.mocked_run_vivado_tcl.assert_called_once()

    def _build(self, project):
        with patch(
            "tsfpga.vivado.project.run_vivado_tcl", autospec=True
        ) as self.mocked_run_vivado_tcl, patch(
            "tsfpga.vivado.project.VivadoProject._get_size", autospec=True
        ) as _, patch(
            "tsfpga.vivado.project.shutil.copy2", autospec=True
        ) as _:
            create_file(self.project_path / "apa.xpr")
            return project.build(
                project_path=self.project_path,
                output_path=self.output_path,
                run_index=self.run_index,
                generics=self.static_generics,
                synth_only=self.synth_only,
                num_threads=self.num_threads,
                other_parameter="hest",
            )

    def test_build_module_pre_build_hook_and_create_regs_are_called(self):
        module_one = MagicMock(spec=BaseModule)
        module_two = MagicMock(spec=BaseModule)

        project = VivadoProject(name="apa", modules=[module_one, module_two], part="")
        build_result = self._build(project)
        assert build_result.success

        module_one.pre_build.assert_called_once_with(
            project=project,
            other_parameter="hest",
            project_path=self.project_path,
            output_path=self.output_path,
            run_index=self.run_index,
            generics=self.static_generics,
            synth_only=self.synth_only,
            num_threads=self.num_threads,
        )
        module_one.create_regs_vhdl_package.assert_called_once()

    def test_default_pre_and_post_build_hooks_should_pass(self):
        class CustomVivadoProject(VivadoProject):

            pass

        build_result = self._build(CustomVivadoProject(name="apa", modules=[], part=""))
        assert build_result.success
        self.mocked_run_vivado_tcl.assert_called_once()

    def test_project_pre_build_hook_returning_false_should_fail_and_not_call_vivado_run(self):
        class CustomVivadoProject(VivadoProject):
            def pre_build(self, **kwargs):  # pylint: disable=no-self-use, unused-argument
                return False

        build_result = self._build(CustomVivadoProject(name="apa", modules=[], part=""))
        assert not build_result.success
        self.mocked_run_vivado_tcl.assert_not_called()

    def test_project_post_build_hook_returning_false_should_fail(self):
        class CustomVivadoProject(VivadoProject):
            def post_build(self, **kwargs):  # pylint: disable=no-self-use, unused-argument
                return False

        build_result = self._build(CustomVivadoProject(name="apa", modules=[], part=""))
        assert not build_result.success
        self.mocked_run_vivado_tcl.assert_called_once()

    def test_module_pre_build_hook_returning_false_should_fail_and_not_call_vivado(self):
        module = MagicMock(spec=BaseModule)
        project = VivadoProject(name="apa", modules=[module], part="")

        module.pre_build.return_value = True
        build_result = self._build(project)
        assert build_result.success
        self.mocked_run_vivado_tcl.assert_called_once()

        module.pre_build.return_value = False
        build_result = self._build(project)
        assert not build_result.success
        self.mocked_run_vivado_tcl.assert_not_called()

    @patch("tsfpga.vivado.project.VivadoTcl", autospec=True)
    def test_different_generic_combinations(self, mocked_vivado_tcl):
        mocked_vivado_tcl.return_value.build.return_value = ""

        self.static_generics = None
        build_result = self._build(VivadoProject(name="apa", modules=[], part=""))
        assert build_result.success
        # Note: In python 3.8 we can use call_args.kwargs straight away
        _, kwargs = mocked_vivado_tcl.return_value.build.call_args
        assert kwargs["generics"] is None

        self.static_generics = dict(static="value")
        build_result = self._build(VivadoProject(name="apa", modules=[], part=""))
        assert build_result.success
        _, kwargs = mocked_vivado_tcl.return_value.build.call_args
        assert kwargs["generics"] == dict(static="value")

        self.static_generics = dict(static="value")
        build_result = self._build(
            VivadoProject(name="apa", modules=[], part="", generics=dict(runtime="a value"))
        )
        assert build_result.success
        _, kwargs = mocked_vivado_tcl.return_value.build.call_args
        assert kwargs["generics"] == dict(static="value", runtime="a value")

        self.static_generics = None
        build_result = self._build(
            VivadoProject(name="apa", modules=[], part="", generics=dict(runtime="a value"))
        )
        assert build_result.success
        _, kwargs = mocked_vivado_tcl.return_value.build.call_args
        assert kwargs["generics"] == dict(runtime="a value")
