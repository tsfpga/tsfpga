# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from unittest import TestCase
from unittest.mock import MagicMock, patch

# Third party libraries
import pytest

# First party libraries
from tsfpga.ip_core_file import IpCoreFile
from tsfpga.module import BaseModule, get_modules
from tsfpga.system_utils import create_file, delete

# pylint: disable=unused-import
from tsfpga.test.conftest import fixture_tmp_path  # noqa: F401
from tsfpga.vivado.ip_cores import VivadoIpCores


def test_get_ip_core_files_is_called_with_the_correct_arguments(tmp_path):
    modules = [MagicMock(spec=BaseModule)]

    with patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True):
        VivadoIpCores(modules, tmp_path, part_name="test_part")

    modules[0].get_ip_core_files.assert_called_once_with(generics={}, part="test_part")


@pytest.mark.usefixtures("fixture_tmp_path")
class TestVivadoIpCores(TestCase):
    tmp_path = None

    def setUp(self):
        self.project_folder = self.tmp_path / "ip_project"
        self.modules_folder = self.tmp_path / "modules"

        self.apa_tcl = create_file(self.modules_folder / "apa" / "ip_cores" / "apa.tcl", "apa")
        self.hest_tcl = create_file(self.modules_folder / "hest" / "ip_cores" / "hest.tcl", "hest")

        modules = get_modules([self.modules_folder])
        self.vivado_ip_cores = VivadoIpCores(modules, self.project_folder, part_name="-")

        # Create initial hash and (empty) compile order file
        self.vivado_ip_cores._save_hash()  # pylint: disable=protected-access
        self._create_compile_order_file()

    def _create_compile_order_file(self):
        create_file(self.vivado_ip_cores.compile_order_file)

    @patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
    def test_should_not_recreate(self, create):
        assert not self.vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_not_called()

    @patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
    def test_should_recreate_if_compile_order_file_is_missing(self, create):
        delete(self.vivado_ip_cores.compile_order_file)
        assert self.vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_called_once()

    @patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
    def test_should_recreate_if_hash_file_is_missing(self, create):
        delete(self.vivado_ip_cores._hash_file)  # pylint: disable=protected-access
        assert self.vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_called_once()

    @patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
    def test_should_not_recreate_if_nothing_is_changed(self, create):
        # This test shows that the pattern used in the upcoming tests:
        #   change something -> get modules -> create new VivadoIpCores object
        # should not result in a recreate unless we actually change something.
        modules = get_modules([self.modules_folder])
        vivado_ip_cores = VivadoIpCores(modules, self.project_folder, part_name="-")

        assert not vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_not_called()

    @patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
    def test_should_recreate_if_ip_core_file_is_added(self, create):
        create_file(self.modules_folder / "zebra" / "ip_cores" / "zebra.tcl", "zebra")
        modules = get_modules([self.modules_folder])
        vivado_ip_cores = VivadoIpCores(modules, self.project_folder, part_name="-")

        assert vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_called_once()

    @patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
    def test_should_recreate_if_ip_core_file_is_removed(self, create):
        delete(self.hest_tcl)
        modules = get_modules([self.modules_folder])
        vivado_ip_cores = VivadoIpCores(modules, self.project_folder, part_name="-")

        assert vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_called_once()

    @patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
    def test_should_recreate_if_ip_core_file_is_changed(self, create):
        create_file(self.apa_tcl, "blaha blaha")
        modules = get_modules([self.modules_folder])
        vivado_ip_cores = VivadoIpCores(modules, self.project_folder, part_name="-")

        assert vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_called_once()

    @patch("tsfpga.vivado.ip_cores.VivadoIpCoreProject.create", autospec=True)
    def test_ip_core_variables(self, create):
        modules = [MagicMock(spec=BaseModule)]

        modules[0].get_ip_core_files.return_value = [IpCoreFile(path=self.apa_tcl)]

        vivado_ip_cores = VivadoIpCores(modules, self.project_folder, part_name="-")

        assert vivado_ip_cores.create_vivado_project_if_needed()
        assert create.call_count == 1
        self._create_compile_order_file()

        # Should not recreate until we change something
        assert not vivado_ip_cores.create_vivado_project_if_needed()
        assert create.call_count == 1

        # Adding variables should recreate
        modules[0].get_ip_core_files.return_value = [
            IpCoreFile(path=self.apa_tcl, zz="123", aa="456")
        ]

        vivado_ip_cores = VivadoIpCores(modules, self.project_folder, part_name="-")

        assert vivado_ip_cores.create_vivado_project_if_needed()
        assert create.call_count == 2
        self._create_compile_order_file()

        # Changing order of variables should not recreate
        modules[0].get_ip_core_files.return_value = [
            IpCoreFile(path=self.apa_tcl, aa="456", zz="123")
        ]

        vivado_ip_cores = VivadoIpCores(modules, self.project_folder, part_name="-")

        assert not vivado_ip_cores.create_vivado_project_if_needed()
        assert create.call_count == 2
