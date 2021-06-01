# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import os
import unittest

import pytest

from vunit import VUnitCLI

from examples.simulate import setup_vunit_project


class TestCompilation(unittest.TestCase):

    tmp_path = None

    def setUp(self):
        self.old_environ = os.environ
        self.cli = VUnitCLI()
        self.argv = ["--compile", "--clean"]
        self.argv = ["--compile", "--clean", "--output-path", str(self.tmp_path)]
        self.args = self.cli.parse_args(argv=self.argv)
        self.args.vivado_skip = True

    def tearDown(self):
        # Set old environment again
        os.environ = self.old_environ

    def test_modelsim(self):
        os.environ["VUNIT_SIMULATOR"] = "modelsim"
        vunit_proj, _, _ = setup_vunit_project(self.args)
        with pytest.raises(SystemExit) as exit_code:
            vunit_proj.main()

        assert exit_code.type == SystemExit
        assert exit_code.value.code == 0
