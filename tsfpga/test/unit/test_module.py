# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from pathlib import Path
from unittest import mock, TestCase

import pytest

from tsfpga.module import BaseModule, get_modules
from tsfpga.system_utils import create_file, create_directory


def test_file_list_filtering(tmp_path):
    module_name = "zebra"
    path = tmp_path / module_name

    create_directory(path / "folder_should_not_be_included")
    create_file(path / "should_not_be_included.apa")

    synth_files = [create_file(path / "syn.v"),
                   create_file(path / "rtl" / "syn.v"),
                   create_file(path / "src" / "syn.vhd"),
                   create_file(path / "hdl" / "rtl" / "syn.vhd"),
                   create_file(path / "hdl" / "package" / "syn.vhd")]

    test_files = [create_file(path / "test" / "test.v"),
                  create_file(path / "rtl" / "tb" / "test.vhd")]

    sim_files = [create_file(path / "sim" / "sim.vhd")]

    my_module = BaseModule(path, "zebra")

    files = [file.path for file in my_module.get_synthesis_files()]
    assert set(files) == set(synth_files)

    files = [file.path for file in my_module.get_simulation_files()]
    assert set(files) == set(synth_files + test_files + sim_files)

    files = [file.path for file in my_module.get_simulation_files(include_tests=False)]
    assert set(files) == set(synth_files + sim_files)


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


def test_generics_to_string():
    assert BaseModule.generics_to_string(dict(apa=3, hest_zebra="foo")) == "apa_3.hest_zebra_foo"


@pytest.mark.usefixtures("fixture_tmp_path")
class TestGetModules(TestCase):

    tmp_path = None

    def setUp(self):
        create_directory(self.tmp_path / "a")
        create_directory(self.tmp_path / "b")
        create_directory(self.tmp_path / "c")

        self.modules_folders = [self.tmp_path]

    def test_name_filtering_include(self):
        modules = get_modules(self.modules_folders, names_include=["a", "b"])
        assert set(module.name for module in modules) == set(["a", "b"])

    def test_name_filtering_avoid(self):
        modules = get_modules(self.modules_folders, names_avoid=["a", "b"])
        assert set(module.name for module in modules) == set(["c"])

    def test_name_filtering_include_and_avoid(self):
        modules = get_modules(self.modules_folders,
                              names_include=["a", "c"],
                              names_avoid=["b", "c"])
        assert set(module.name for module in modules) == set(["a"])

    def test_library_name_does_not_have_lib_suffix(self):
        modules = get_modules(self.modules_folders)
        assert set(module.library_name for module in modules) == set(["a", "b", "c"])

    def test_library_name_has_lib_suffix(self):
        modules = get_modules(self.modules_folders, library_name_has_lib_suffix=True)
        assert set(module.library_name for module in modules) == set(["a_lib", "b_lib", "c_lib"])

    def test_stray_file_can_exist_in_modules_folder_without_error(self):
        create_file(self.tmp_path / "text_file.txt")
        modules = get_modules(self.modules_folders)
        assert len(modules) == 3

    def test_local_override_of_module_type(self):
        module_file_content = """
from tsfpga.module import BaseModule

class Module(BaseModule):

    def id(self):
        return """

        create_file(self.tmp_path / "a" / "module_a.py", module_file_content + "\"a\"")
        create_file(self.tmp_path / "b" / "module_b.py", module_file_content + "\"b\"")

        modules = get_modules(self.modules_folders)

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

    @mock.patch("tsfpga.module.from_json", autospec=True)
    def test_register_object_creation_synthesis(self, from_json):
        json_file = create_file(self.tmp_path / "a" / "regs_a.json")

        module = get_modules(self.modules_folders, names_include=["a"])[0]
        module.get_synthesis_files()
        module.get_synthesis_files()

        from_json.assert_called_once_with("a", json_file, mock.ANY)

    @mock.patch("tsfpga.module.from_json", autospec=True)
    def test_register_object_creation_simulation(self, from_json):
        json_file = create_file(self.tmp_path / "a" / "regs_a.json")

        module = get_modules(self.modules_folders, names_include=["a"])[0]
        module.get_simulation_files()
        module.get_simulation_files()

        from_json.assert_called_once_with("a", json_file, mock.ANY)

    @mock.patch("tsfpga.module.from_json", autospec=True)
    def test_register_object_creation_mixed(self, from_json):
        json_file = create_file(self.tmp_path / "a" / "regs_a.json")

        module = get_modules(self.modules_folders, names_include=["a"])[0]
        module.get_synthesis_files()
        module.get_simulation_files()

        from_json.assert_called_once_with("a", json_file, mock.ANY)

    def test_deprecated_register_json_file_name_should_raise_exception(self):
        json_file = create_file(self.tmp_path / "a" / "a_regs.json")

        module = get_modules(self.modules_folders, names_include=["a"])[0]
        with pytest.raises(ValueError) as exception_info:
            module.get_synthesis_files()
        assert str(exception_info.value).startswith(
            f"DEPRECATED: Using deprecated json file name: {json_file}")
