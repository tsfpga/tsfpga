from os import makedirs
from os.path import dirname, join
from shutil import rmtree
import sys
import unittest

from hdl_reuse.module import BaseModule, get_modules
from hdl_reuse.test.test_utils import create_file


THIS_DIR = dirname(__file__)


def test_default_library_name_should_have_no_suffix():
    name = "apa"
    path = join(THIS_DIR, name)

    my_module = BaseModule(path)

    assert my_module.library_name == name


def test_library_name_should_have_suffix():
    module_name = "hest"
    library_name = "hest_lib"
    path = join(THIS_DIR, module_name)

    my_module = BaseModule(path=path, library_name_has_lib_suffix=True)

    assert my_module.library_name == library_name


def test_file_list_filtering():
    module_name = "zebra"
    path = join(THIS_DIR, module_name)

    makedirs(path)
    makedirs(join(path, "folder_should_not_be_included"))

    good_file = create_file(join(path, "source_code.vhd"))
    create_file(join(path, "should_not_be_included.apa"))

    my_module = BaseModule(path)

    synthesis_files = my_module.get_synthesis_files()
    assert len(synthesis_files) == 1 and good_file in synthesis_files

    simulation_files = my_module.get_simulation_files()
    assert len(simulation_files) == 1 and good_file in simulation_files

    rmtree(path)


class TestGetModules(unittest.TestCase):

    _modules_folder = join(THIS_DIR, "modules_for_test")
    _modules_folders = [_modules_folder]

    def setUp(self):
        makedirs(self._modules_folder)
        makedirs(join(self._modules_folder, "a"))
        makedirs(join(self._modules_folder, "b"))
        makedirs(join(self._modules_folder, "c"))

    def tearDown(self):
        rmtree(self._modules_folder)

    def test_name_filtering(self):
        modules = get_modules(self._modules_folders, ["a", "b"])
        assert len(modules) == 2
        for module in modules:
            assert module.name != "c"

    def test_stray_file_can_exist_in_modules_folder_without_error(self):
        with open(join(self._modules_folder, "text_file.txt"), "w") as file_handle:
            file_handle.write("Dummy file")
        modules = get_modules(self._modules_folders)
        assert len(modules) == 3

    def test_local_override_of_module_type(self):
        module_file_content = """
from hdl_reuse.module import BaseModule

class Module(BaseModule):

    def whatever(self):
        pass
"""
        with open(join(self._modules_folder, "a", "module_a.py"), "w") as file_handle:
            file_handle.write(module_file_content)
        with open(join(self._modules_folder, "b", "module_b.py"), "w") as file_handle:
            file_handle.write(module_file_content)

        modules = get_modules(self._modules_folders)

        sys.path.append(join(self._modules_folder, "a"))
        sys.path.append(join(self._modules_folder, "b"))

        import module_a  # pylint: disable=import-error
        import module_b  # pylint: disable=import-error

        assert len(modules) == 3
        for module in modules:
            if module.name == "a":
                assert isinstance(module, module_a.Module)
            elif module.name == "b":
                assert isinstance(module, module_b.Module)
            elif module.name == "c":
                assert isinstance(module, BaseModule)
            else:
                assert False
