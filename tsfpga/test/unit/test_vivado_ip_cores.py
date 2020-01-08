# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import dirname, join
from unittest import mock, TestCase

from tsfpga.module import get_modules
from tsfpga.system_utils import create_file, delete
from tsfpga.vivado_ip_cores import VivadoIpCores


THIS_DIR = dirname(__file__)


class TestVivadoIpCores(TestCase):

    project_folder = join(THIS_DIR, "ip_project")
    modules_folder = join(THIS_DIR, "modules")

    def setUp(self):
        delete(self.project_folder)
        delete(self.modules_folder)

        self.apa_tcl = create_file(join(self.modules_folder, "apa", "ip_cores", "apa.tcl"), "apa")
        self.hest_tcl = create_file(join(self.modules_folder, "hest", "ip_cores", "hest.tcl"), "hest")

        modules = get_modules([self.modules_folder])
        self.vivado_ip_cores = VivadoIpCores(modules, self.project_folder)

        # Create inital hash and (empty) compile order file
        self.vivado_ip_cores._save_hash()  # pylint: disable=protected-access
        create_file(self.vivado_ip_cores.compile_order_file)

    @mock.patch("tsfpga.vivado_ip_cores.VivadoProject.create", autospec=True)
    def test_should_not_recreate(self, create):
        assert not self.vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_not_called()

    @mock.patch("tsfpga.vivado_ip_cores.VivadoProject.create", autospec=True)
    def test_should_recreate_if_compile_order_file_is_missing(self, create):
        delete(self.vivado_ip_cores.compile_order_file)
        assert self.vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_called_once()

    @mock.patch("tsfpga.vivado_ip_cores.VivadoProject.create", autospec=True)
    def test_should_recreate_if_hash_file_is_missing(self, create):
        delete(self.vivado_ip_cores._hash_file)  # pylint: disable=protected-access
        assert self.vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_called_once()

    @mock.patch("tsfpga.vivado_ip_cores.VivadoProject.create", autospec=True)
    def test_should_not_recreate_if_nothing_is_changed(self, create):
        # This test shows that the pattern used in the upcoming tests:
        #   change something -> get modules -> create new VivadoIpCores object
        # should not result in a recreate unless we actually change something.
        modules = get_modules([self.modules_folder])
        vivado_ip_cores = VivadoIpCores(modules, self.project_folder)

        assert not vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_not_called()

    @mock.patch("tsfpga.vivado_ip_cores.VivadoProject.create", autospec=True)
    def test_should_recreate_if_ip_core_file_is_added(self, create):
        create_file(join(self.modules_folder, "zebra", "ip_cores", "zebra.tcl"), "zebra")
        modules = get_modules([self.modules_folder])
        vivado_ip_cores = VivadoIpCores(modules, self.project_folder)

        assert vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_called_once()

    @mock.patch("tsfpga.vivado_ip_cores.VivadoProject.create", autospec=True)
    def test_should_recreate_if_ip_core_file_is_removed(self, create):
        delete(self.hest_tcl)
        modules = get_modules([self.modules_folder])
        vivado_ip_cores = VivadoIpCores(modules, self.project_folder)

        assert vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_called_once()

    @mock.patch("tsfpga.vivado_ip_cores.VivadoProject.create", autospec=True)
    def test_should_recreate_if_ip_core_file_is_changed(self, create):
        create_file(self.apa_tcl, "blaha blaha")
        modules = get_modules([self.modules_folder])
        vivado_ip_cores = VivadoIpCores(modules, self.project_folder)

        assert vivado_ip_cores.create_vivado_project_if_needed()
        create.assert_called_once()
