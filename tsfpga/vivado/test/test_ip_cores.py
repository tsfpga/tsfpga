# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from unittest.mock import MagicMock, patch

# Third party libraries
import pytest

# First party libraries
from tsfpga.ip_core_file import IpCoreFile
from tsfpga.module import BaseModule, get_modules
from tsfpga.system_utils import create_file, delete
from tsfpga.vivado.ip_cores import VivadoIpCores


def test_get_ip_core_files_is_called_with_the_correct_arguments(tmp_path):
    modules = [MagicMock(spec=BaseModule)]

    with patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True):
        VivadoIpCores(modules, tmp_path, part_name="test_part")

    modules[0].get_ip_core_files.assert_called_once_with(generics={}, part="test_part")


def test_system_call_to_vivado_failing_should_raise_exception(tmp_path):
    project = VivadoIpCores(modules=[], output_path=tmp_path, part_name="test_part")

    with patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True) as create:
        create.return_value = False

        with pytest.raises(AssertionError) as exception_info:
            project.create_vivado_project_if_needed()

        assert str(exception_info.value) == "Failed to create Vivado IP core project"


@pytest.fixture
def ip_cores_test(tmp_path):
    class IpCoresTest:
        def __init__(self):
            self.project_folder = tmp_path / "ip_project"
            self.modules_folder = tmp_path / "modules"

            self.apa_tcl = create_file(self.modules_folder / "apa" / "ip_cores" / "apa.tcl", "apa")
            self.hest_tcl = create_file(
                self.modules_folder / "hest" / "ip_cores" / "hest.tcl", "hest"
            )

            modules = get_modules([self.modules_folder])
            self.vivado_ip_cores = VivadoIpCores(modules, self.project_folder, part_name="-")

            # Create initial hash and (empty) compile order file
            self.vivado_ip_cores._save_hash()  # pylint: disable=protected-access
            self.create_compile_order_file()

        def create_compile_order_file(self):
            create_file(self.vivado_ip_cores.compile_order_file)

    return IpCoresTest()


# False positive for pytest fixtures
# pylint: disable=redefined-outer-name


@patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
def test_should_not_recreate(create, ip_cores_test):
    assert not ip_cores_test.vivado_ip_cores.create_vivado_project_if_needed()
    create.assert_not_called()


@patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
def test_should_recreate_if_compile_order_file_is_missing(create, ip_cores_test):
    delete(ip_cores_test.vivado_ip_cores.compile_order_file)
    assert ip_cores_test.vivado_ip_cores.create_vivado_project_if_needed()
    create.assert_called_once()


@patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
def test_should_recreate_if_hash_file_is_missing(create, ip_cores_test):
    delete(ip_cores_test.vivado_ip_cores._hash_file)  # pylint: disable=protected-access
    assert ip_cores_test.vivado_ip_cores.create_vivado_project_if_needed()
    create.assert_called_once()


@patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
def test_should_not_recreate_if_nothing_is_changed(create, ip_cores_test):
    # This test shows that the pattern used in the upcoming tests:
    #   change something -> get modules -> create new VivadoIpCores object
    # should not result in a recreate unless we actually change something.
    modules = get_modules([ip_cores_test.modules_folder])
    vivado_ip_cores = VivadoIpCores(modules, ip_cores_test.project_folder, part_name="-")

    assert not vivado_ip_cores.create_vivado_project_if_needed()
    create.assert_not_called()


@patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
def test_should_recreate_if_ip_core_file_is_added(create, ip_cores_test):
    create_file(ip_cores_test.modules_folder / "zebra" / "ip_cores" / "zebra.tcl", "zebra")
    modules = get_modules([ip_cores_test.modules_folder])
    vivado_ip_cores = VivadoIpCores(modules, ip_cores_test.project_folder, part_name="-")

    assert vivado_ip_cores.create_vivado_project_if_needed()
    create.assert_called_once()


@patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
def test_should_recreate_if_ip_core_file_is_removed(create, ip_cores_test):
    delete(ip_cores_test.hest_tcl)
    modules = get_modules([ip_cores_test.modules_folder])
    vivado_ip_cores = VivadoIpCores(modules, ip_cores_test.project_folder, part_name="-")

    assert vivado_ip_cores.create_vivado_project_if_needed()
    create.assert_called_once()


@patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
def test_should_recreate_if_ip_core_file_is_changed(create, ip_cores_test):
    create_file(ip_cores_test.apa_tcl, "blaha blaha")
    modules = get_modules([ip_cores_test.modules_folder])
    vivado_ip_cores = VivadoIpCores(modules, ip_cores_test.project_folder, part_name="-")

    assert vivado_ip_cores.create_vivado_project_if_needed()
    create.assert_called_once()


@patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
def test_ip_core_variables(create, ip_cores_test):
    modules = [MagicMock(spec=BaseModule)]

    modules[0].get_ip_core_files.return_value = [IpCoreFile(path=ip_cores_test.apa_tcl)]

    vivado_ip_cores = VivadoIpCores(modules, ip_cores_test.project_folder, part_name="-")

    assert vivado_ip_cores.create_vivado_project_if_needed()
    assert create.call_count == 1
    ip_cores_test.create_compile_order_file()

    # Should not recreate until we change something
    assert not vivado_ip_cores.create_vivado_project_if_needed()
    assert create.call_count == 1

    # Adding variables should recreate
    modules[0].get_ip_core_files.return_value = [
        IpCoreFile(path=ip_cores_test.apa_tcl, zz="123", aa="456")
    ]

    vivado_ip_cores = VivadoIpCores(modules, ip_cores_test.project_folder, part_name="-")

    assert vivado_ip_cores.create_vivado_project_if_needed()
    assert create.call_count == 2
    ip_cores_test.create_compile_order_file()

    # Changing order of variables should not recreate
    modules[0].get_ip_core_files.return_value = [
        IpCoreFile(path=ip_cores_test.apa_tcl, aa="456", zz="123")
    ]

    vivado_ip_cores = VivadoIpCores(modules, ip_cores_test.project_folder, part_name="-")

    assert not vivado_ip_cores.create_vivado_project_if_needed()
    assert create.call_count == 2
