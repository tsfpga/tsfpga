# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

# Third party libraries
import pytest

# First party libraries
from tsfpga.module import BaseModule, get_modules
from tsfpga.system_utils import create_directory, create_file


def test_add_vunit_config_name():
    module = BaseModule(path=Path(), library_name="")

    test = MagicMock()
    pre_config = MagicMock()
    post_check = MagicMock()

    module.add_vunit_config(test=test, pre_config=pre_config, post_check=post_check)
    test.add_config.assert_called_once_with(
        name="test", generics={}, pre_config=pre_config, post_check=post_check
    )
    test.reset_mock()

    module.add_vunit_config(test=test, name="apa")
    test.add_config.assert_called_once_with(
        name="apa", generics={}, pre_config=None, post_check=None
    )
    test.reset_mock()

    module.add_vunit_config(test=test, generics=dict(apa="hest", foo="bar"))
    test.add_config.assert_called_once_with(
        name="apa_hest.foo_bar",
        generics=dict(apa="hest", foo="bar"),
        pre_config=None,
        post_check=None,
    )
    test.reset_mock()

    module.add_vunit_config(test=test, name="zebra", generics=dict(apa="hest", foo="bar"))
    test.add_config.assert_called_once_with(
        name="zebra.apa_hest.foo_bar",
        generics=dict(apa="hest", foo="bar"),
        pre_config=None,
        post_check=None,
    )


def test_add_vunit_config_random_seed():
    module = BaseModule(path=Path(), library_name="")
    test = MagicMock()

    # No seed at all
    module.add_vunit_config(test=test)
    assert "generics" not in test.add_config.call_args

    module.add_vunit_config(test=test, set_random_seed=False)
    assert "generics" not in test.add_config.call_args

    # No seed, with generics set
    module.add_vunit_config(test=test, generics={"apa": "whatever"})
    assert "seed" not in test.add_config.call_args.kwargs["generics"]

    # Static seed
    module.add_vunit_config(test=test, set_random_seed=0)
    assert isinstance(test.add_config.call_args.kwargs["generics"]["seed"], int)
    assert test.add_config.call_args.kwargs["generics"]["seed"] == 0

    module.add_vunit_config(test=test, set_random_seed=123)
    assert isinstance(test.add_config.call_args.kwargs["generics"]["seed"], int)
    assert test.add_config.call_args.kwargs["generics"]["seed"] == 123

    # Use random seed
    module.add_vunit_config(test=test, set_random_seed=True)
    assert isinstance(test.add_config.call_args.kwargs["generics"]["seed"], int)
    assert test.add_config.call_args.kwargs["generics"]["seed"] >= 0

    # Setting explicit value should still work
    module.add_vunit_config(test=test, generics={"seed": 711})
    assert test.add_config.call_args.kwargs["generics"]["seed"] == 711

    # If a value is already set it will be overwritten
    module.add_vunit_config(test=test, generics={"seed": -5}, set_random_seed=True)
    assert test.add_config.call_args.kwargs["generics"]["seed"] != -5


def test_file_list_filtering(tmp_path):
    module_name = "zebra"
    path = tmp_path / module_name

    create_directory(path / "folder_should_not_be_included")
    create_file(path / "should_not_be_included.apa")

    synth_files = {
        create_file(path / "syn.v"),
        create_file(path / "rtl" / "syn.v"),
        create_file(path / "src" / "syn.vhd"),
        create_file(path / "hdl" / "rtl" / "syn.vhd"),
        create_file(path / "hdl" / "package" / "syn.vhd"),
    }

    test_files = {
        create_file(path / "test" / "test.v"),
        create_file(path / "rtl" / "tb" / "test.vhd"),
    }

    sim_files = {create_file(path / "sim" / "sim.vhd")}

    my_module = BaseModule(path=path, library_name="zebra")

    files = {file.path for file in my_module.get_synthesis_files()}
    assert files == synth_files

    files = {file.path for file in my_module.get_simulation_files()}
    assert files == synth_files | test_files | sim_files

    files = {file.path for file in my_module.get_simulation_files(include_tests=False)}
    assert files == synth_files | sim_files

    files = {file.path for file in my_module.get_simulation_files(files_include=synth_files)}
    assert files == synth_files

    files = {file.path for file in my_module.get_simulation_files(files_avoid=synth_files)}
    assert files == test_files | sim_files


def test_get_synthesis_files_calls_get_simulation_files_with_correct_arguments():
    module = BaseModule(path=Path(), library_name="")
    with patch("tsfpga.module.BaseModule.get_synthesis_files") as get_synthesis_files:
        module.get_simulation_files(files_include=True, files_avoid=False, apa=123)
        get_synthesis_files.assert_called_once_with(files_include=True, files_avoid=False, apa=123)


def test_get_documentation_files(tmp_path):
    module_name = "zebra"
    path = tmp_path / module_name

    synth_files = {
        create_file(path / "rtl" / "syn.v"),
        create_file(path / "src" / "syn.vhd"),
    }

    # Test files
    create_file(path / "test" / "test.v")
    create_file(path / "rtl" / "tb" / "test.vhd")

    sim_files = {create_file(path / "sim" / "sim.vhd")}

    module = BaseModule(path=path, library_name="zebra")

    # Should include everything except test files
    files = {file.path for file in module.get_documentation_files()}
    assert files == synth_files | sim_files


def test_scoped_constraints(tmp_path):
    module_path = tmp_path / "apa"
    create_file(module_path / "src" / "hest.vhd")
    create_file(module_path / "scoped_constraints" / "hest.tcl")

    my_module = BaseModule(module_path, "apa")
    scoped_constraints = my_module.get_scoped_constraints()
    assert len(scoped_constraints) == 1
    assert scoped_constraints[0].ref == "hest"


def test_scoped_constraint_entity_not_existing_should_raise_error(tmp_path):
    module_path = tmp_path / "apa"
    create_file(module_path / "scoped_constraints" / "hest.tcl")

    module = BaseModule(module_path, "apa")
    with pytest.raises(FileNotFoundError) as exception_info:
        module.get_scoped_constraints()
    assert str(exception_info.value).startswith("Could not find a matching entity file")


def test_can_cast_to_string_without_error():
    str(BaseModule(Path("dummy"), "dummy"))


def test_test_case_name():
    assert (
        BaseModule.test_case_name(generics=dict(apa=3, hest_zebra="foo")) == "apa_3.hest_zebra_foo"
    )
    assert (
        BaseModule.test_case_name(name="foo", generics=dict(apa=3, hest_zebra="bar"))
        == "foo.apa_3.hest_zebra_bar"
    )


def test_getting_registers_calls_registers_hook(tmp_path):
    with patch("tsfpga.module.from_toml", autospec=True) as from_toml, patch(
        "tsfpga.module.BaseModule.registers_hook", autospec=True
    ) as registers_hook:
        create_file(tmp_path / "a" / "regs_a.toml")
        module = BaseModule(path=tmp_path / "a", library_name="a")
        registers = module.registers

        # TOML file exists so register creation from TOML should run
        from_toml.assert_called_once()
        registers_hook.assert_called_once()
        assert registers is not None

    with patch("tsfpga.module.from_toml", autospec=True) as from_toml, patch(
        "tsfpga.module.BaseModule.registers_hook", autospec=True
    ) as registers_hook:
        module = BaseModule(path=tmp_path / "b", library_name="b")
        registers = module.registers

        # TOML file does not exist, so register creation from TOML should not run
        from_toml.assert_not_called()
        # Register hook shall still run however
        registers_hook.assert_called_once()
        assert registers is None


def test_creating_synthesis_files_does_not_create_simulation_files(tmp_path):
    create_file(tmp_path / "a" / "regs_a.toml", "register.apa.mode = 'r_w'")
    module = BaseModule(path=tmp_path / "a", library_name="a")

    synthesis_file = module.register_synthesis_folder / "a_regs_pkg.vhd"
    simulation_file = module.register_simulation_folder / "a_register_read_write_pkg.vhd"

    module.get_synthesis_files()
    assert synthesis_file.exists()
    assert not simulation_file.exists()
    assert not module.register_simulation_folder.exists()

    module.get_simulation_files()
    assert simulation_file.exists()


def test_old_register_package_should_be_deleted(tmp_path):
    create_file(tmp_path / "a" / "regs_a.toml", "register.apa.mode = 'r_w'")
    regs_pkg = create_file(tmp_path / "a" / "a_regs_pkg.vhd")

    module = BaseModule(path=tmp_path / "a", library_name="a")
    module.get_synthesis_files()

    assert not regs_pkg.exists()


@pytest.fixture
def get_modules_test(tmp_path):
    class GetModulesTest:
        def __init__(self):
            create_directory(tmp_path / "a")
            create_directory(tmp_path / "b")
            create_directory(tmp_path / "c")

            self.modules_folder = tmp_path
            self.modules_folders = [self.modules_folder]

    return GetModulesTest()


# False positive for pytest fixtures
# pylint: disable=redefined-outer-name


def test_name_filtering_include(get_modules_test):
    modules = get_modules(get_modules_test.modules_folders, names_include=["a", "b"])
    assert set(module.name for module in modules) == set(["a", "b"])


def test_name_filtering_avoid(get_modules_test):
    modules = get_modules(get_modules_test.modules_folders, names_avoid=["a", "b"])
    assert set(module.name for module in modules) == set(["c"])


def test_name_filtering_include_and_avoid(get_modules_test):
    modules = get_modules(
        get_modules_test.modules_folders, names_include=["a", "c"], names_avoid=["b", "c"]
    )
    assert set(module.name for module in modules) == set(["a"])


def test_library_name_does_not_have_lib_suffix(get_modules_test):
    modules = get_modules(get_modules_test.modules_folders)
    assert set(module.library_name for module in modules) == set(["a", "b", "c"])


def test_library_name_has_lib_suffix(get_modules_test):
    modules = get_modules(get_modules_test.modules_folders, library_name_has_lib_suffix=True)
    assert set(module.library_name for module in modules) == set(["a_lib", "b_lib", "c_lib"])


def test_stray_file_can_exist_in_modules_folder_without_error(get_modules_test):
    create_file(get_modules_test.modules_folder / "text_file.txt")
    modules = get_modules(get_modules_test.modules_folders)
    assert len(modules) == 3


def test_local_override_of_module_type(get_modules_test):
    module_file_content = """
from tsfpga.module import BaseModule

class Module(BaseModule):
    def id(self):
        return """

    create_file(get_modules_test.modules_folder / "a" / "module_a.py", module_file_content + '"a"')
    create_file(get_modules_test.modules_folder / "b" / "module_b.py", module_file_content + '"b"')

    modules = get_modules(get_modules_test.modules_folders)

    assert len(modules) == 3
    for module in modules:
        if module.name == "a":
            assert module.id() == "a"
        elif module.name == "b":
            assert module.id() == "b"
        elif module.name == "c":
            assert isinstance(module, BaseModule)
        else:
            assert False


@patch("tsfpga.module.from_toml", autospec=True)
@patch("tsfpga.module.VhdlRegisterPackageGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlRecordPackageGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlSimulationReadWritePackageGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlSimulationWaitUntilPackageGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlAxiLiteWrapperGenerator.create", autospec=True)
def test_register_toml_file_parsed_only_once_when_getting_synthesis_files(
    _, __, ___, ____, _____, from_toml, tmp_path
):
    toml_file = create_file(tmp_path / "a" / "regs_a.toml")

    module = get_modules([tmp_path]).get("a")
    module.get_synthesis_files()
    module.get_synthesis_files()

    from_toml.assert_called_once_with("a", toml_file, ANY)


@patch("tsfpga.module.from_toml", autospec=True)
@patch("tsfpga.module.VhdlRegisterPackageGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlRecordPackageGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlAxiLiteWrapperGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlSimulationReadWritePackageGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlSimulationCheckPackageGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlSimulationWaitUntilPackageGenerator.create", autospec=True)
def test_register_toml_file_parsed_only_once_when_getting_simulation_files(
    _, __, ___, ____, _____, ______, from_toml, tmp_path
):
    toml_file = create_file(tmp_path / "a" / "regs_a.toml")

    module = get_modules([tmp_path]).get("a")
    module.get_simulation_files()
    module.get_simulation_files()

    from_toml.assert_called_once_with("a", toml_file, ANY)


@patch("tsfpga.module.from_toml", autospec=True)
@patch("tsfpga.module.VhdlRegisterPackageGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlRecordPackageGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlAxiLiteWrapperGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlSimulationReadWritePackageGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlSimulationCheckPackageGenerator.create", autospec=True)
@patch("tsfpga.module.VhdlSimulationWaitUntilPackageGenerator.create", autospec=True)
def test_register_toml_file_parsed_only_once_when_getting_mixed_files(
    _, __, ___, ____, _____, ______, from_toml, tmp_path
):
    toml_file = create_file(tmp_path / "a" / "regs_a.toml")

    module = get_modules([tmp_path]).get("a")
    module.get_synthesis_files()
    module.get_simulation_files()

    from_toml.assert_called_once_with("a", toml_file, ANY)
