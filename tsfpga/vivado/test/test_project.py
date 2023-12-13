# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third party libraries
import pytest

# First party libraries
from tsfpga.build_step_tcl_hook import BuildStepTclHook
from tsfpga.constraint import Constraint
from tsfpga.module import BaseModule
from tsfpga.system_utils import create_directory, create_file
from tsfpga.vivado.generics import StringGenericValue
from tsfpga.vivado.project import VivadoNetlistProject, VivadoProject, copy_and_combine_dicts


def test_casting_to_string():
    project = VivadoProject(name="my_project", modules=[], part="")
    assert (
        str(project)
        == """\
my_project
Type:       VivadoProject
Top level:  my_project_top
Generics:   -
"""
    )

    project = VivadoProject(
        name="my_project",
        modules=[],
        part="",
        top="apa",
        generics=dict(hest=True, zebra=3, foo=StringGenericValue("/home/test.vhd")),
    )
    assert (
        str(project)
        == """\
my_project
Type:       VivadoProject
Top level:  apa
Generics:   hest=True, zebra=3, foo=/home/test.vhd
"""
    )

    project = VivadoProject(name="my_project", modules=[], part="", apa=123, hest=456)
    assert (
        str(project)
        == """\
my_project
Type:       VivadoProject
Top level:  my_project_top
Generics:   -
Arguments:  apa=123, hest=456
"""
    )


def test_modules_list_should_be_copied():
    modules = [1]
    proj = VivadoProject(name="name", modules=modules, part="part")

    modules.append(2)
    assert len(proj.modules) == 1


def test_static_generics_dictionary_should_be_copied():
    generics = dict(apa=3)
    proj = VivadoProject(name="name", modules=[], part="part", generics=generics)

    generics["apa"] = False
    assert proj.static_generics["apa"] == 3


def test_constraints_list_should_be_copied():
    constraints = [Constraint(file="1")]
    proj = VivadoProject(name="name", modules=[], part="part", constraints=constraints)

    constraints.append(Constraint(file="2"))
    assert len(proj.constraints) == 1


def test_bad_constraint_type_should_raise_error():
    # Correct type should not give error
    VivadoProject(name="name", modules=[], part="part", constraints=[Constraint(file=None)])

    # Bad type should raise exception
    with pytest.raises(TypeError) as exception_info:
        VivadoProject(name="name", modules=[], part="part", constraints=["file.vhd"])
    assert str(exception_info.value) == 'Got bad type for "constraints" element: file.vhd'


def test_bad_tcl_sources_type_should_raise_error():
    # Correct type should not give error
    VivadoProject(name="name", modules=[], part="part", tcl_sources=[Path()])

    # Bad type should raise exception
    with pytest.raises(TypeError) as exception_info:
        VivadoProject(name="name", modules=[], part="part", tcl_sources=["file.tcl"])
    assert str(exception_info.value) == 'Got bad type for "tcl_sources" element: file.tcl'


def test_bad_build_step_hooks_type_should_raise_error():
    # Correct type should not give error
    VivadoProject(
        name="name",
        modules=[],
        part="part",
        build_step_hooks=[BuildStepTclHook(tcl_file="", hook_step="")],
    )

    # Bad type should raise exception
    with pytest.raises(TypeError) as exception_info:
        VivadoProject(name="name", modules=[], part="part", build_step_hooks=["file.tcl"])
    assert str(exception_info.value) == 'Got bad type for "build_step_hooks" element: file.tcl'


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


def test_copy_and_combine_dict_with_both_arguments_none():
    assert copy_and_combine_dicts(None, None) == {}


def test_copy_and_combine_dict_with_first_argument_valid():
    dict_first = dict(first=1)

    result = copy_and_combine_dicts(dict_first, None)
    assert result == dict(first=1)
    assert dict_first == dict(first=1)

    dict_first["first_dummy"] = True
    assert result == dict(first=1)


def test_copy_and_combine_dict_with_second_argument_valid():
    dict_second = dict(second=2)

    result = copy_and_combine_dicts(None, dict_second)
    assert result == dict(second=2)
    assert dict_second == dict(second=2)

    dict_second["second_dummy"] = True
    assert result == dict(second=2)


def test_copy_and_combine_dict_with_both_arguments_valid():
    dict_first = dict(first=1)
    dict_second = dict(second=2)

    result = copy_and_combine_dicts(dict_first, dict_second)
    assert result == dict(first=1, second=2)
    assert dict_first == dict(first=1)
    assert dict_second == dict(second=2)

    dict_first["first_dummy"] = True
    dict_second["second_dummy"] = True
    assert result == dict(first=1, second=2)


def test_copy_and_combine_dict_with_both_arguments_valid_and_same_key():
    dict_first = dict(first=1, common=3)
    dict_second = dict(second=2, common=4)

    result = copy_and_combine_dicts(dict_first, dict_second)
    assert result == dict(first=1, second=2, common=4)
    assert dict_first == dict(first=1, common=3)
    assert dict_second == dict(second=2, common=4)

    dict_first["first_dummy"] = True
    dict_second["second_dummy"] = True
    assert result == dict(first=1, second=2, common=4)


@pytest.fixture
def vivado_project_test(tmp_path):
    class VivadoProjectTest:  # pylint: disable=too-many-instance-attributes
        def __init__(self):
            self.project_path = tmp_path / "projects" / "apa" / "project"
            self.output_path = tmp_path / "projects" / "apa"
            self.ip_cache_path = MagicMock()
            self.build_time_generics = dict(enable=True)
            self.num_threads = 4
            self.run_index = 3
            self.synth_only = False
            self.from_impl = False

            self.mocked_run_vivado_tcl = None

        def create(self, project, **other_arguments):
            with patch(
                "tsfpga.vivado.project.run_vivado_tcl", autospec=True
            ) as self.mocked_run_vivado_tcl:
                return project.create(
                    project_path=self.project_path,
                    ip_cache_path=self.ip_cache_path,
                    **other_arguments,
                )

        def build(self, project):
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
                    generics=self.build_time_generics,
                    synth_only=self.synth_only,
                    num_threads=self.num_threads,
                    other_parameter="hest",
                )

    return VivadoProjectTest()


# False positive for pytest fixtures
# pylint: disable=redefined-outer-name


def test_default_pre_create_hook_should_pass(vivado_project_test):
    class CustomVivadoProject(VivadoProject):
        pass

    project = CustomVivadoProject(name="apa", modules=[], part="")
    vivado_project_test.create(project)
    vivado_project_test.mocked_run_vivado_tcl.assert_called_once()


def test_project_pre_create_hook_returning_false_should_fail_and_not_call_vivado_run(
    vivado_project_test,
):
    class CustomVivadoProject(VivadoProject):
        def pre_create(self, **kwargs):  # pylint: disable=unused-argument
            return False

    assert not vivado_project_test.create(CustomVivadoProject(name="apa", modules=[], part=""))
    vivado_project_test.mocked_run_vivado_tcl.assert_not_called()


def test_create_should_call_pre_create_with_correct_parameters(vivado_project_test):
    project = VivadoProject(name="apa", modules=[], part="", generics=dict(apa=123), hest=456)
    with patch("tsfpga.vivado.project.VivadoProject.pre_create") as mocked_pre_create:
        vivado_project_test.create(project, zebra=789)
    mocked_pre_create.assert_called_once_with(
        project_path=vivado_project_test.project_path,
        ip_cache_path=vivado_project_test.ip_cache_path,
        part="",
        generics=dict(apa=123),
        hest=456,
        zebra=789,
    )
    vivado_project_test.mocked_run_vivado_tcl.assert_called_once()


def test_build_module_pre_build_hook_and_create_regs_are_called(vivado_project_test):
    project = VivadoProject(
        name="apa",
        modules=[MagicMock(spec=BaseModule), MagicMock(spec=BaseModule)],
        part="",
        apa=123,
    )
    build_result = vivado_project_test.build(project)
    assert build_result.success

    for module in project.modules:
        module.pre_build.assert_called_once_with(
            project=project,
            other_parameter="hest",
            apa=123,
            project_path=vivado_project_test.project_path,
            output_path=vivado_project_test.output_path,
            run_index=vivado_project_test.run_index,
            generics=vivado_project_test.build_time_generics,
            synth_only=vivado_project_test.synth_only,
            from_impl=vivado_project_test.from_impl,
            num_threads=vivado_project_test.num_threads,
        )
        module.create_register_synthesis_files.assert_called_once()
        module.create_register_simulation_files.assert_not_called()


def test_default_pre_and_post_build_hooks_should_pass(vivado_project_test):
    class CustomVivadoProject(VivadoProject):
        pass

    build_result = vivado_project_test.build(CustomVivadoProject(name="apa", modules=[], part=""))
    assert build_result.success
    vivado_project_test.mocked_run_vivado_tcl.assert_called_once()


def test_project_pre_build_hook_returning_false_should_fail_and_not_call_vivado_run(
    vivado_project_test,
):
    class CustomVivadoProject(VivadoProject):
        def pre_build(self, **kwargs):  # pylint: disable=unused-argument
            return False

    build_result = vivado_project_test.build(CustomVivadoProject(name="apa", modules=[], part=""))
    assert not build_result.success
    vivado_project_test.mocked_run_vivado_tcl.assert_not_called()


def test_project_post_build_hook_returning_false_should_fail(vivado_project_test):
    class CustomVivadoProject(VivadoProject):
        def post_build(self, **kwargs):  # pylint: disable=unused-argument
            return False

    build_result = vivado_project_test.build(CustomVivadoProject(name="apa", modules=[], part=""))
    assert not build_result.success
    vivado_project_test.mocked_run_vivado_tcl.assert_called_once()


def test_project_build_hooks_should_be_called_with_correct_parameters(vivado_project_test):
    project = VivadoProject(
        name="apa", modules=[], part="", generics=dict(static_generic=2), apa=123
    )
    with patch("tsfpga.vivado.project.VivadoProject.pre_build") as mocked_pre_build, patch(
        "tsfpga.vivado.project.VivadoProject.post_build"
    ) as mocked_post_build:
        vivado_project_test.build(project)

    arguments = dict(
        project_path=vivado_project_test.project_path,
        output_path=vivado_project_test.output_path,
        run_index=vivado_project_test.run_index,
        generics=copy_and_combine_dicts(
            dict(static_generic=2), vivado_project_test.build_time_generics
        ),
        synth_only=vivado_project_test.synth_only,
        from_impl=vivado_project_test.from_impl,
        num_threads=vivado_project_test.num_threads,
        other_parameter="hest",
        apa=123,
    )
    mocked_pre_build.assert_called_once_with(**arguments)

    arguments.update(build_result=unittest.mock.ANY)
    mocked_post_build.assert_called_once_with(**arguments)


def test_module_pre_build_hook_returning_false_should_fail_and_not_call_vivado(vivado_project_test):
    module = MagicMock(spec=BaseModule)
    module.name = "whatever"
    project = VivadoProject(name="apa", modules=[module], part="")

    project.modules[0].pre_build.return_value = True
    build_result = vivado_project_test.build(project)
    assert build_result.success
    vivado_project_test.mocked_run_vivado_tcl.assert_called_once()

    project.modules[0].pre_build.return_value = False
    build_result = vivado_project_test.build(project)
    assert not build_result.success
    vivado_project_test.mocked_run_vivado_tcl.assert_not_called()


@patch("tsfpga.vivado.project.VivadoTcl", autospec=True)
def test_different_generic_combinations(mocked_vivado_tcl, vivado_project_test):
    mocked_vivado_tcl.return_value.build.return_value = ""

    # No generics
    vivado_project_test.build_time_generics = None
    build_result = vivado_project_test.build(VivadoProject(name="apa", modules=[], part=""))
    assert build_result.success
    # Note: In python 3.8 we can use call_args.kwargs straight away
    _, kwargs = mocked_vivado_tcl.return_value.build.call_args
    assert kwargs["generics"] == {}

    # Only build time generics
    vivado_project_test.build_time_generics = dict(runtime="value")
    build_result = vivado_project_test.build(VivadoProject(name="apa", modules=[], part=""))
    assert build_result.success
    _, kwargs = mocked_vivado_tcl.return_value.build.call_args
    assert kwargs["generics"] == dict(runtime="value")

    # Static and build time generics
    vivado_project_test.build_time_generics = dict(runtime="value")
    build_result = vivado_project_test.build(
        VivadoProject(name="apa", modules=[], part="", generics=dict(static="a value"))
    )
    assert build_result.success
    _, kwargs = mocked_vivado_tcl.return_value.build.call_args
    assert kwargs["generics"] == dict(runtime="value", static="a value")

    # Same key in both static and build time generic. Should prefer build time.
    vivado_project_test.build_time_generics = dict(static_and_runtime="build value")
    build_result = vivado_project_test.build(
        VivadoProject(
            name="apa", modules=[], part="", generics=dict(static_and_runtime="static value")
        )
    )
    assert build_result.success
    _, kwargs = mocked_vivado_tcl.return_value.build.call_args
    assert kwargs["generics"] == dict(static_and_runtime="build value")

    # Only static generics
    vivado_project_test.build_time_generics = None
    build_result = vivado_project_test.build(
        VivadoProject(name="apa", modules=[], part="", generics=dict(runtime="a value"))
    )
    assert build_result.success
    _, kwargs = mocked_vivado_tcl.return_value.build.call_args
    assert kwargs["generics"] == dict(runtime="a value")


def test_build_time_generics_are_copied(vivado_project_test):
    vivado_project_test.build_time_generics = dict(runtime="value")
    with patch("tsfpga.vivado.project.VivadoTcl", autospec=True) as mocked_vivado_tcl:
        mocked_vivado_tcl.return_value.build.return_value = ""
        build_result = vivado_project_test.build(
            VivadoProject(name="apa", modules=[], part="", generics=dict(static="a value"))
        )
    assert build_result.success
    assert vivado_project_test.build_time_generics == dict(runtime="value")


def test_modules_are_deep_copied_before_pre_create_hook(vivado_project_test):
    class CustomVivadoProject(VivadoProject):
        def pre_create(self, **kwargs):
            self.modules[0].registers = "Some other value"
            return True

    module = MagicMock(spec=BaseModule)
    module.registers = "Some value"

    project = CustomVivadoProject(name="apa", modules=[module], part="")
    assert vivado_project_test.create(project)

    assert module.registers == "Some value"


def test_modules_are_deep_copied_before_pre_build_hook(vivado_project_test):
    class CustomVivadoProject(VivadoProject):
        def pre_build(self, **kwargs):
            self.modules[0].registers = "Some other value"
            return True

    module = MagicMock(spec=BaseModule)
    module.registers = "Some value"

    project = CustomVivadoProject(name="apa", modules=[module], part="")
    assert vivado_project_test.build(project).success

    assert module.registers == "Some value"


def test_get_size_is_called_correctly(vivado_project_test):
    project = VivadoProject(name="apa", modules=[], part="")

    def _build_with_size(synth_only):
        """
        The project.build() call is very similar to _build() method in this class, but it mocks
        the _get_size() method in a different way.
        """
        with patch(
            "tsfpga.vivado.project.run_vivado_tcl", autospec=True
        ) as vivado_project_test.mocked_run_vivado_tcl, patch(
            "tsfpga.vivado.project.HierarchicalUtilizationParser.get_size", autospec=True
        ) as mocked_get_size, patch(
            "tsfpga.vivado.project.shutil.copy2", autospec=True
        ) as _:
            # Only the first return value will be used if we are in synth_only
            mocked_get_size.side_effect = ["synth_size", "impl_size"]

            build_result = project.build(
                project_path=vivado_project_test.project_path,
                output_path=vivado_project_test.output_path,
                run_index=vivado_project_test.run_index,
                synth_only=synth_only,
            )

            assert build_result.synthesis_size == "synth_size"

            if synth_only:
                mocked_get_size.assert_called_once_with("synth_file")
                assert build_result.implementation_size is None
            else:
                assert mocked_get_size.call_count == 2
                mocked_get_size.assert_any_call("synth_file")
                mocked_get_size.assert_any_call("impl_file")

                assert build_result.implementation_size == "impl_size"

    create_file(vivado_project_test.project_path / "apa.xpr")

    create_file(
        vivado_project_test.project_path / "apa.runs" / "synth_3" / "hierarchical_utilization.rpt",
        contents="synth_file",
    )
    create_file(
        vivado_project_test.project_path / "apa.runs" / "impl_3" / "hierarchical_utilization.rpt",
        contents="impl_file",
    )

    _build_with_size(synth_only=True)
    _build_with_size(synth_only=False)


def test_netlist_build_should_set_logic_level_distribution(vivado_project_test):
    def _build_with_logic_level_distribution(project):
        """
        The project.build() call is very similar to _build() method in this class, except it
        also mocks the _get_logic_level_distribution() method.
        """
        with patch(
            "tsfpga.vivado.project.run_vivado_tcl", autospec=True
        ) as vivado_project_test.mocked_run_vivado_tcl, patch(
            "tsfpga.vivado.project.VivadoProject._get_size", autospec=True
        ) as _, patch(
            "tsfpga.vivado.project.shutil.copy2", autospec=True
        ) as _, patch(
            "tsfpga.vivado.project.LogicLevelDistributionParser.get_table", autospec=True
        ) as mocked_get_table:
            mocked_get_table.return_value = "logic_table"

            build_result = project.build(
                project_path=vivado_project_test.project_path,
                output_path=vivado_project_test.output_path,
                run_index=vivado_project_test.run_index,
            )

            if project.is_netlist_build:
                mocked_get_table.assert_called_once_with("logic_file")
                assert build_result.logic_level_distribution == "logic_table"
            else:
                mocked_get_table.assert_not_called()
                assert build_result.logic_level_distribution is None
                assert build_result.maximum_logic_level is None

    create_file(vivado_project_test.project_path / "apa.xpr")
    create_file(
        vivado_project_test.project_path
        / "apa.runs"
        / "synth_3"
        / "logical_level_distribution.rpt",
        contents="logic_file",
    )

    project = VivadoNetlistProject(name="apa", modules=[], part="")
    _build_with_logic_level_distribution(project=project)

    project = VivadoProject(name="apa", modules=[], part="")
    _build_with_logic_level_distribution(project=project)
