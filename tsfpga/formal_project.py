# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from fnmatch import fnmatch
from pathlib import Path

from vunit import VUnitCLI, VUnit
from vunit.test.list import TestList
from vunit.test.runner import TestRunner
from vunit.test.report import TestReport
from vunit.color_printer import COLOR_PRINTER, NO_COLOR_PRINTER

from tsfpga.module import BaseModule
from tsfpga.yosys_project import YosysProject


class FormalConfig:

    # pylint: disable=too-many-arguments
    def __init__(
        self, top, generics=None, engine_command="smtbmc", solver_command="z3", mode="bmc", depth=20
    ):
        """
        Arguments:
            top (str): Name of top level entity.
            generics (dict): Generics that will be applied to the top level.
            engine_command (str): Engine command, e.g. ``smtbmc --syn --nopresat``
            solver_command (str): Solver command, e.g.
                ``z3 rewriter.cache_all=true opt.enable_sat=true``
            mode (str): Typically ``bmc`` or ``prove``.
            depth (int): In ``bmc`` mode, this parameter is the depth of the bounded model
                check. In ``prove`` mode it is ignored for all engines except ``smtbmc``
                where it is used as the depth for k-induction.
        """
        self.top = top
        self.generics = None if generics is None else generics.copy()
        self.formal_settings = dict(
            engine_command=engine_command, solver_command=solver_command, mode=mode, depth=depth
        )

    @property
    def test_name(self):
        return BaseModule.test_case_name(self.top, self.generics)


class FormalProject:
    def __init__(self, project_path, modules):
        self._formal_config_list = []
        self.project_path = project_path.resolve()
        self.modules = modules

    def add_config(self, **kwargs):
        config = FormalConfig(**kwargs)
        self._formal_config_list.append(config)

    def list_tests(self, test_filters="*"):
        test_list = self._create_test_list(test_filters)
        for test in test_list:
            print(test.name)
        print(f"Listed {test_list.num_tests} tests")

    def run(self, num_threads=1, verbose=False, quiet=False, no_color=False, test_filters=None):
        # First, compile the source code and assign the compile result information to the
        # test objects.
        src_files, compiled_libraries = self._compile_source_code()
        test_list = self._create_test_list(test_filters)
        for test in test_list:
            # 'test' in this context is a TestCaseWrapper object.
            # Access the member to get the FormalTestCase object.
            # pylint: disable=protected-access
            test._test_case.set_src_files(src_files)
            # pylint: disable=protected-access
            test._test_case.set_compiled_libraries(compiled_libraries)

        if verbose:
            verbosity = TestRunner.VERBOSITY_VERBOSE
        elif quiet:
            verbosity = TestRunner.VERBOSITY_QUIET
        else:
            verbosity = TestRunner.VERBOSITY_NORMAL

        color_printer = NO_COLOR_PRINTER if no_color else COLOR_PRINTER
        report = TestReport(printer=color_printer)

        # Run all the tests
        test_runner = TestRunner(
            report=report,
            output_path=self.project_path,
            verbosity=verbosity,
            num_threads=num_threads,
            no_color=no_color,
        )
        test_runner.run(test_list)

        return report.all_ok()

    def _create_test_list(self, test_filters):
        test_list = TestList()
        for formal_config in self._formal_config_list:
            test_list.add_test(FormalTestCase(formal_config))

        def test_filter(name, attribute_names):  # pylint: disable=unused-argument
            """
            The ``attribute_names`` argument is used by VUnit in it's test filtering.
            We have no such concept, but the argument is needed so the function signature
            is correct.
            """
            return any(fnmatch(name, test_name_filter) for test_name_filter in test_filters)

        test_list.keep_matches(test_filter)

        return test_list

    def _compile_source_code(self, no_color=False):
        # Set up a VUnit project for compilation of sources
        args = VUnitCLI().parse_args(["--no-color", no_color])
        args.output_path = self.project_path / "vunit_out"
        vunit_proj = VUnit.from_args(args=args)
        vunit_proj.add_verification_components()
        vunit_proj.add_random()
        vunit_proj.add_osvvm()

        src_files = []
        compiled_libraries = []

        for module in self.modules:
            vunit_library = vunit_proj.add_library(module.library_name)
            compiled_libraries.append(args.output_path / "ghdl" / "libraries" / module.library_name)

            for hdl_file in module.get_formal_files():
                if hdl_file.is_vhdl:
                    vunit_library.add_source_file(hdl_file.path)
                else:
                    assert False, f"Can not handle this file: {hdl_file.path}"

                src_files.append(hdl_file.path)

        vunit_proj.set_compile_option("ghdl.a_flags", ["-fpsl", "-fsynopsys", "-frelaxed"])
        vunit_proj._main_compile_only()  # pylint: disable=protected-access

        return src_files, compiled_libraries


class FormalTestCase:
    def __init__(self, formal_config):
        self._formal_config = formal_config
        self._src_files = None
        self._compiled_libraries = None

        self._setup_unused_vunit_fields()

    def _setup_unused_vunit_fields(self):
        """
        Setup fields that are needed in a test case for VUnit test handling to work.
        These are unused by us. I think we are mimicking a IndependentSimTestCase object.
        """
        self.attribute_names = set()

        class TestConfiguration:

            attributes = {}

        self.test_configuration = TestConfiguration()

    @property
    def name(self):
        return self._formal_config.test_name

    def set_src_files(self, src_files):
        self._src_files = src_files

    def set_compiled_libraries(self, compiled_libraries):
        self._compiled_libraries = compiled_libraries

    def run(self, output_path, read_output):  # pylint: disable=unused-argument
        """
        VUnit test runner sends another argument "read_output" which we don't use.
        It can be used to read back the STDOUTput from a test. Typically used in a post
        test hook.
        """
        # If these have not been set there is something procedurally wrong
        if self._src_files is None:
            raise ValueError("FormalTestCase missing source files")
        if self._compiled_libraries is None:
            raise ValueError("FormalTestCase missing compiled libraries")

        output_path = Path(output_path)

        project = YosysProject(
            top=self._formal_config.top,
            generics=self._formal_config.generics,
            formal_settings=self._formal_config.formal_settings,
        )

        test_ok = project.run_formal(
            project_path=output_path,
            src_files=self._src_files,
            compiled_libraries=self._compiled_libraries,
        )

        if not test_ok:
            self._print_trace_help(output_path)

        return test_ok

    @staticmethod
    def _print_trace_help(output_path):
        """
        Prints the location of trace files, if any available.
        """
        message = "\n\nFormal test case failed. "
        vcd_files = list(output_path.glob("**/*.vcd"))
        if vcd_files:
            message += "You might want to inspect the trace file(s):"
            print(message)
            for vcd_file in vcd_files:
                print(f"  gtkwave {vcd_file} &")
        else:
            message += (
                "There does not seem to be any trace files available for inspection. "
                "Please see log output instead."
            )
            print(message)
