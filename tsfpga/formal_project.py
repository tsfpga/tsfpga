# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import sys

from vunit import VUnitCLI, VUnit

from tsfpga.yosys_project import YosysProject

from tsfpga.module import BaseModule


class FormalConfig:

    # pylint: disable=too-many-arguments
    def __init__(
            self,
            top,
            generics,
            engine_command="smtbmc z3",
            mode="bmc",
            depth=20
    ):
        self.top = top
        self.generics = generics
        self.formal_settings = dict(engine_command=engine_command, mode=mode, depth=depth)

    @property
    def test_name(self):
        return BaseModule.test_case_name(self.top, self.generics)


class FormalProject:

    def __init__(self, project_path, modules):
        self.config_list = []
        self.project_path = project_path
        self.modules = modules

    def add_config(self, **kwargs):
        config = FormalConfig(**kwargs)
        self.config_list.append(config)

    def list_tests(self):
        print(80 * "=")
        print("Available tests:")
        for config in self.config_list:
            print(config.test_name)
        print(80 * "=")

    def run(self):
        # Set up a VUnit project for compilation of sources
        args = VUnitCLI().parse_args([])
        args.output_path = self.project_path / "vunit_out"
        vunit_proj = VUnit.from_args(args=args)
        vunit_proj.enable_location_preprocessing()
        vunit_proj.enable_check_preprocessing()

        for module in self.modules:
            vunit_library = vunit_proj.add_library(module.library_name)
            for hdl_file in module.get_synthesis_files():
                if hdl_file.is_vhdl:
                    vunit_library.add_source_file(hdl_file.path)
                else:
                    assert False, "Can not handle this file: " + hdl_file.path

        vunit_proj.set_compile_option("ghdl.a_flags", ["-fpsl"])
        vunit_proj._main_compile_only()  # pylint: disable=protected-access

        src_files = []
        compilation_outputs = []
        for module in self.modules:
            src_files += [src_file.path for src_file in module.get_synthesis_files()]
            compilation_outputs += [args.output_path / "ghdl" / "libraries" / module.library_name]

        result = 0
        for config in self.config_list:
            project = YosysProject(
                modules=self.modules,
                top=config.top,
                generics=config.generics,
                formal_settings=config.formal_settings
            )

            yosys_project_path = self.project_path / config.test_name
            result += project.run_formal(
                project_path=yosys_project_path,
                src_files=src_files,
                compilation_outputs=compilation_outputs)

        if result == 0:
            print("All tests passed")
        else:
            print("One or more tests failed")

        sys.exit(result)
