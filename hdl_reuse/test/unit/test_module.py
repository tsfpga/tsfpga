from os.path import dirname, join
from shutil import rmtree
import unittest

from hdl_reuse.module import BaseModule, get_modules
from hdl_reuse.test import create_file, create_directory, delete


THIS_DIR = dirname(__file__)


def test_file_list_filtering():
    module_name = "zebra"
    path = join(THIS_DIR, module_name)

    create_directory(join(path, "folder_should_not_be_included"))
    create_file(join(path, "should_not_be_included.apa"))

    syn_files = [create_file(join(path, "syn.vhd")),
                 create_file(join(path, "hdl", "rtl", "syn.vhd")),
                 create_file(join(path, "hdl", "package", "syn.vhd"))]

    test_files = [create_file(join(path, "test", "test.vhd")),
                  create_file(join(path, "rtl", "tb", "test.vhd"))]

    sim_files = [create_file(join(path, "sim", "sim.vhd"))]

    my_module = BaseModule(path)

    files = my_module.get_synthesis_files()
    assert set(files) == set(syn_files)

    files = my_module.get_simulation_files()
    assert set(files) == set(syn_files + test_files + sim_files)

    files = my_module.get_simulation_files(include_tests=False)
    assert set(files) == set(syn_files + sim_files)

    rmtree(path)


class TestGetModules(unittest.TestCase):

    _modules_folder = join(THIS_DIR, "modules_for_test")
    _modules_folders = [_modules_folder]

    def setUp(self):
        delete(self._modules_folder)
        create_directory(join(self._modules_folder, "a"))
        create_directory(join(self._modules_folder, "b"))
        create_directory(join(self._modules_folder, "c"))

    def test_name_filtering(self):
        modules = get_modules(self._modules_folders, names=["a", "b"])
        assert len(modules) == 2
        for module in modules:
            assert module.name != "c"

    def test_library_name_does_not_have_lib_suffix(self):
        modules = get_modules(self._modules_folders)
        for module in modules:
            assert len(module.library_name) == 1  # I.e. does not end with "_lib"

    def test_library_name_has_lib_suffix(self):
        modules = get_modules(self._modules_folders, library_name_has_lib_suffix=True)
        for module in modules:
            assert module.library_name in ["a_lib", "b_lib", "c_lib"]

    def test_stray_file_can_exist_in_modules_folder_without_error(self):
        create_file(join(self._modules_folder, "text_file.txt"))
        modules = get_modules(self._modules_folders)
        assert len(modules) == 3

    def test_local_override_of_module_type(self):
        module_file_content = """
from hdl_reuse.module import BaseModule

class Module(BaseModule):

    def id(self):
        return """

        create_file(join(self._modules_folder, "a", "module_a.py"), module_file_content + "\"a\"")
        create_file(join(self._modules_folder, "b", "module_b.py"), module_file_content + "\"b\"")

        modules = get_modules(self._modules_folders)

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
