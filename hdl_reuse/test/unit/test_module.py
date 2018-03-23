from os.path import dirname, join
from shutil import rmtree
import sys
import unittest

from hdl_reuse.module import BaseModule, get_modules
from hdl_reuse.test import create_file, create_directory, delete


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

    create_directory(join(path, "folder_should_not_be_included"))
    create_file(join(path, "should_not_be_included.apa"))
    good_file = create_file(join(path, "source_code.vhd"))

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
        delete(self._modules_folder)
        create_directory(join(self._modules_folder, "a"))
        create_directory(join(self._modules_folder, "b"))
        create_directory(join(self._modules_folder, "c"))

    def test_name_filtering(self):
        modules = get_modules(self._modules_folders, ["a", "b"])
        assert len(modules) == 2
        for module in modules:
            assert module.name != "c"

    def test_stray_file_can_exist_in_modules_folder_without_error(self):
        create_file(join(self._modules_folder, "text_file.txt"))
        modules = get_modules(self._modules_folders)
        assert len(modules) == 3

    def test_local_override_of_module_type(self):
        module_file_content = """
from hdl_reuse.module import BaseModule

class Module(BaseModule):

    def whatever(self):
        pass
"""
        create_file(join(self._modules_folder, "a", "module_a.py"), module_file_content)
        create_file(join(self._modules_folder, "b", "module_b.py"), module_file_content)

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
