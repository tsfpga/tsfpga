# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from fnmatch import fnmatch
from pathlib import Path

from vunit import VUnitCLI, VUnit
from vunit.test.list import TestList
from vunit.test.runner import TestRunner
from vunit.test.report import TestReport

from tsfpga.yosys_project import YosysProject

from tsfpga.module import BaseModule


class FormalConfig:

    # pylint: disable=too-many-arguments
    def __init__(
            self,
            top,
            generics,
            engine_command="smtbmc",
            solver_command="z3",
            mode="bmc",
            depth=20
    ):
        """
        Args:
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
        self.generics = generics
        self.formal_settings = dict(
            engine_command=engine_command,
            solver_command=solver_command,
            mode=mode,
            depth=depth)

    @property
    def test_name(self):
        return BaseModule.test_case_name(self.top, self.generics)


class FormalProject:

    def __init__(self, project_path, modules):
        self._formal_config_list = []
        self.project_path = project_path
        self.modules = modules

    def add_config(self, **kwargs):
        config = FormalConfig(**kwargs)
        self._formal_config_list.append(config)

    def list_tests(self, test_filters):
        test_list = self._create_test_list(test_filters)
        for test in test_list:
            print(test.name)
        print(f"Listed {test_list.num_tests} tests")

    def run(self, num_threads, verbose, quiet, test_filters):
        # First, compile the source code and assign the compile result information to the
        # test objects.
        src_files, compiled_libraries = self._compile_source_code()
        test_list = self._create_test_list(test_filters)
        for test in test_list:
            # 'test' in this context is a TestCaseWrapper object.
            # Access the member to get the FormalTestCase object.
            test._test_case.set_src_files(src_files)  # pylint: disable=protected-access
            test._test_case.set_compiled_libraries(compiled_libraries)  # pylint: disable=protected-access

        if verbose:
            verbosity = TestRunner.VERBOSITY_VERBOSE
        elif quiet:
            verbosity = TestRunner.VERBOSITY_QUIET
        else:
            verbosity = TestRunner.VERBOSITY_NORMAL

        # Then run all the tests
        report = TestReport()
        test_runner = TestRunner(
            report=report,
            output_path=self.project_path,
            verbosity=verbosity,
            num_threads=num_threads)
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

    def _compile_source_code(self):
        # Set up a VUnit project for compilation of sources
        args = VUnitCLI().parse_args([])
        args.output_path = self.project_path / "vunit_out"
        vunit_proj = VUnit.from_args(args=args)

        for module in self.modules:
            vunit_library = vunit_proj.add_library(module.library_name)
            for hdl_file in module.get_synthesis_files():
                if hdl_file.is_vhdl:
                    vunit_library.add_source_file(hdl_file.path)
                else:
                    assert False, f"Can not handle this file: {hdl_file.path}"

        vunit_proj.set_compile_option("ghdl.a_flags", ["-fpsl"])
        vunit_proj._main_compile_only()  # pylint: disable=protected-access

        src_files = []
        compiled_libraries = []
        for module in self.modules:
            src_files += [src_file.path for src_file in module.get_synthesis_files()]
            compiled_libraries += [args.output_path / "ghdl" / "libraries" / module.library_name]

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

            attributes = dict()

        self.test_configuration = TestConfiguration()

    def set_src_files(self, src_files):
        self._src_files = src_files

    def set_compiled_libraries(self, compiled_libraries):
        self._compiled_libraries = compiled_libraries

    def run(self, output_path, read_output):  # pylint: disable=unused-argument
        """
        VUnit test runner sends another argument "read_output" which we don't use.
        It can be usd to read back the STDOUTput from a test. Typically used in a post
        test hook.
        """
        # If these have not been set there is something procedurally wrong
        assert self._src_files
        assert self._compiled_libraries

        output_path = Path(output_path)

        project = YosysProject(
            top=self._formal_config.top,
            generics=self._formal_config.generics,
            formal_settings=self._formal_config.formal_settings
        )

        return project.run_formal(
            project_path=output_path,
            src_files=self._src_files,
            compiled_libraries=self._compiled_libraries)

    @property
    def name(self):
        return self._formal_config.test_name
