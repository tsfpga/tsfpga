# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import os
import shutil
from pathlib import Path

import pytest

from tsfpga.build_project_list import BuildProjectList, get_build_projects
from tsfpga.examples.example_env import get_tsfpga_example_modules
from tsfpga.module import get_modules
from tsfpga.system_utils import create_file
from tsfpga.test.test_utils import file_contains_string
from tsfpga.vivado.build_result_checker import (
    DspBlocks,
    EqualTo,
    Ffs,
    GreaterThan,
    LessThan,
    TotalLuts,
)
from tsfpga.yosys.common import get_ghdl_library_prefix, get_ghdl_path, get_yosys_path
from tsfpga.yosys.project import (
    YosysIntelNetlistBuild,
    YosysMicrochipNetlistBuild,
    YosysNetlistBuild,
    YosysXilinxNetlistBuild,
)

# Path to the 'ghdl-yosys-plugin' module (typically named 'ghdl.so').
# Can be left unset if the plugin is already available to Yosys without explicitly loading it
# (e.g. if it has been installed in the Yosys plugin directory).
GHDL_PLUGIN_PATH = (
    Path(os.environ["TSFPGA_GHDL_PLUGIN_PATH"]) if "TSFPGA_GHDL_PLUGIN_PATH" in os.environ else None
)

# Value for the 'GHDL_PREFIX' environment variable, see 'YosysNetlistBuild' docstring.
# Normally not needed: auto-detected via 'ghdl --disp-config'. Can be set to override, e.g. if
# auto-detection fails or picks the wrong GHDL installation.
GHDL_PREFIX = Path(os.environ["TSFPGA_GHDL_PREFIX"]) if "TSFPGA_GHDL_PREFIX" in os.environ else None

# This whole test suite requires GHDL and Yosys, with the 'ghdl-yosys-plugin', to be installed
# on the machine that runs the tests.
THIS_DIR = Path(__file__).parent


def copy_modules(name: str, tmp_path: Path) -> Path:
    """
    Copy the module sources used by a test to a writable location.

    Arguments:
        name: Name of a folder in the "modules" directory next to this file.
        tmp_path: The test's temporary directory.

    Return:
        The modules folder, as accepted by 'get_modules'.
    """
    modules_folder = tmp_path / "modules"
    shutil.copytree(THIS_DIR / "modules" / name, modules_folder)
    return modules_folder


pytestmark = pytest.mark.skipif(
    shutil.which("ghdl") is None or shutil.which("yosys") is None,
    reason="GHDL and/or Yosys is not available on the PATH",
)


def test_tools_are_found_on_the_path():
    """
    On a properly installed system, nothing needs to be configured: GHDL and Yosys are found on
    the PATH, and GHDL's library prefix is derived from the GHDL installation itself.
    """
    ghdl_path = get_ghdl_path()
    assert ghdl_path.exists(), ghdl_path
    assert ghdl_path.is_absolute(), ghdl_path

    yosys_path = get_yosys_path()
    assert yosys_path.exists(), yosys_path
    assert yosys_path.is_absolute(), yosys_path

    # Needed by the 'ghdl-yosys-plugin', which can not work it out on its own since it runs
    # inside the Yosys process. Must be found without the user supplying anything.
    library_prefix = get_ghdl_library_prefix()
    assert library_prefix is not None
    assert library_prefix.exists(), library_prefix


@pytest.fixture
def basic_project_test(tmp_path):
    class BasicProjectTest:
        def __init__(self):
            self.modules_folder = copy_modules("basic", tmp_path)
            self.module_folder = self.modules_folder / "apa"
            self.project_folder = tmp_path / "yosys"

            self.top_file = self.module_folder / "src" / "test_proj_top.vhd"

            self.modules = get_modules(modules_folder=self.modules_folder)
            # Target Xilinx primitives, so that the utilization report contains the LUT/FF
            # counts that the 'tsfpga.vivado.build_result_checker' checkers expect.
            self.proj = YosysXilinxNetlistBuild(
                family="xc7",
                name="test_proj",
                modules=self.modules,
                build_result_checkers=[TotalLuts(LessThan(100))],
                ghdl_plugin_path=GHDL_PLUGIN_PATH,
                ghdl_prefix=GHDL_PREFIX,
            )

        @property
        def script_file(self):
            """
            The Yosys command script that should exist after a build.
            """
            return self.proj.project_file(project_path=self.project_folder)

        @property
        def utilization_report_file(self):
            """
            The Yosys utilization report that should exist after a build.
            """
            return self.project_folder / f"{self.proj.name}_utilization.txt"

        def create_yosys_project(self):
            assert self.proj.create(self.project_folder)
            assert self._get_ghdl_workdir().exists()

        def _get_ghdl_workdir(self):
            return self.project_folder / "ghdl"

    return BasicProjectTest()


def test_create_project(basic_project_test):
    basic_project_test.create_yosys_project()


def test_synth_project(basic_project_test):
    basic_project_test.create_yosys_project()

    build_result = basic_project_test.proj.build(basic_project_test.project_folder)
    assert build_result.success
    assert basic_project_test.script_file.exists()
    assert basic_project_test.utilization_report_file.exists()
    assert build_result.synthesis_size["Total LUTs"] < 100


def test_build_without_create_should_fail(basic_project_test):
    with pytest.raises(ValueError, match="does not exist in the specified location"):
        basic_project_test.proj.build(basic_project_test.project_folder)


def test_synth_should_fail_if_source_code_does_not_compile(basic_project_test):
    create_file(
        basic_project_test.top_file,
        """
this is not valid VHDL code
""",
    )

    assert not basic_project_test.proj.create(basic_project_test.project_folder)


def test_build_result_checker_failure_should_fail_build(basic_project_test):
    basic_project_test.proj.build_result_checkers = [TotalLuts(EqualTo(0))]
    basic_project_test.create_yosys_project()

    build_result = basic_project_test.proj.build(basic_project_test.project_folder)
    assert not build_result.success
    # The report should still have been produced, even though the check failed.
    assert basic_project_test.utilization_report_file.exists()


def test_build_result_checker_success(basic_project_test):
    basic_project_test.proj.build_result_checkers = [
        TotalLuts(LessThan(100)),
        TotalLuts(GreaterThan(0)),
    ]
    basic_project_test.create_yosys_project()

    build_result = basic_project_test.proj.build(basic_project_test.project_folder)
    assert build_result.success


def test_build_with_generics(basic_project_test):
    basic_project_test.create_yosys_project()

    build_result = basic_project_test.proj.build(
        basic_project_test.project_folder, generics={"width": 4}
    )
    assert build_result.success
    assert file_contains_string(file=basic_project_test.script_file, string="-gwidth=4")


def test_building_plain_yosys_netlist_project(basic_project_test):
    """
    The base class targets generic Yosys primitives rather than Xilinx ones, so the
    'TotalLuts'/'Ffs' style checkers can not be used. The raw cell counts are still available.
    """
    project = YosysNetlistBuild(
        name="test_proj",
        modules=basic_project_test.modules,
        ghdl_plugin_path=GHDL_PLUGIN_PATH,
        ghdl_prefix=GHDL_PREFIX,
    )
    assert project.create(basic_project_test.project_folder)

    build_result = project.build(project_path=basic_project_test.project_folder)
    assert build_result.success
    assert sum(build_result.synthesis_size.values()) > 0


def test_building_intel_netlist_project(basic_project_test):
    """
    Build a Yosys netlist project targeting Intel primitives, using 'YosysIntelNetlistBuild'.
    Uses the same resource name conventions ('Total LUTs', 'FFs') as the Xilinx flow, so the
    same build result checkers can be reused.
    """
    project = YosysIntelNetlistBuild(
        name="test_proj",
        modules=basic_project_test.modules,
        build_result_checkers=[TotalLuts(GreaterThan(0)), Ffs(GreaterThan(0))],
        ghdl_plugin_path=GHDL_PLUGIN_PATH,
        ghdl_prefix=GHDL_PREFIX,
    )
    assert project.create(basic_project_test.project_folder)

    build_result = project.build(project_path=basic_project_test.project_folder)
    assert build_result.success
    assert build_result.synthesis_size["Total LUTs"] > 0
    assert build_result.synthesis_size["FFs"] > 0


def test_building_microchip_netlist_project(basic_project_test):
    """
    Build a Yosys netlist project targeting Microchip primitives, using
    'YosysMicrochipNetlistBuild'.
    """
    project = YosysMicrochipNetlistBuild(
        name="test_proj",
        modules=basic_project_test.modules,
        # The top level has a signal with an initial value, which is not supported by the
        # Microchip flip-flop mapping unless explicitly discarded.
        discard_ffinit=True,
        build_result_checkers=[TotalLuts(GreaterThan(0)), Ffs(GreaterThan(0))],
        ghdl_plugin_path=GHDL_PLUGIN_PATH,
        ghdl_prefix=GHDL_PREFIX,
    )
    assert project.create(basic_project_test.project_folder)

    build_result = project.build(project_path=basic_project_test.project_folder)
    assert build_result.success
    assert build_result.synthesis_size["Total LUTs"] > 0
    assert build_result.synthesis_size["FFs"] > 0


def test_building_mixed_vhdl_and_verilog_netlist_project(tmp_path):
    """
    Build a Yosys netlist project where the VHDL top level instantiates a Verilog submodule.
    Verifies that Verilog source files, which are not analyzed by GHDL, are picked up by Yosys
    directly via a 'read_verilog' command, and bound to the unbound VHDL component instantiation
    by name.
    """
    modules_folder = copy_modules("mixed", tmp_path)

    modules = get_modules(modules_folder=modules_folder)
    project = YosysNetlistBuild(
        name="test_proj",
        modules=modules,
        ghdl_plugin_path=GHDL_PLUGIN_PATH,
        ghdl_prefix=GHDL_PREFIX,
    )

    project_path = tmp_path / "yosys"
    assert project.create(project_path)

    build_result = project.build(project_path)
    assert build_result.success
    assert sum(build_result.synthesis_size.values()) > 0


def test_building_verilog_top_with_vhdl_entities(tmp_path):
    """
    Build a Yosys netlist project where a Verilog top level instantiates VHDL entities.
    Since there is no VHDL top level to automatically resolve dependencies from, the VHDL
    entities are listed explicitly via the 'vhdl_entities' argument. Verifies that they are
    elaborated by GHDL and bound to the unbound Verilog module instantiations by name.
    """
    modules_folder = copy_modules("verilog_top", tmp_path)

    modules = get_modules(modules_folder=modules_folder)
    project = YosysNetlistBuild(
        name="test_proj",
        modules=modules,
        top="test_proj_top",
        vhdl_entities=["counter_a", "counter_b"],
        ghdl_plugin_path=GHDL_PLUGIN_PATH,
        ghdl_prefix=GHDL_PREFIX,
    )

    project_path = tmp_path / "yosys"
    assert project.create(project_path)

    build_result = project.build(project_path)
    assert build_result.success
    assert sum(build_result.synthesis_size.values()) > 0


def test_building_verilog_top_with_parameters(tmp_path):
    """
    Build a Yosys netlist project where the top level is a Verilog module with a parameter.
    Verifies that generics are applied as Verilog parameters, via a Yosys 'hierarchy -chparam'
    command, when the top level is not a VHDL entity.
    """
    modules_folder = copy_modules("verilog_parameters", tmp_path)
    modules = get_modules(modules_folder=modules_folder)

    def build_with_width(width):
        project = YosysXilinxNetlistBuild(
            family="xc7",
            name=f"test_proj_{width}",
            modules=modules,
            top="test_proj_top",
            generics={"WIDTH": width},
            ghdl_plugin_path=GHDL_PLUGIN_PATH,
            ghdl_prefix=GHDL_PREFIX,
        )
        project_path = tmp_path / f"yosys_{width}"
        assert project.create(project_path)

        build_result = project.build(project_path)
        assert build_result.success
        return build_result

    # The counter register is 'WIDTH' bits wide, so a wider parameter must give more flip flops.
    assert build_with_width(24).synthesis_size["FFs"] > build_with_width(8).synthesis_size["FFs"]


def test_intel_dsp_count_of_a_single_multiplier(tmp_path):
    """
    One mapped multiplier yields both a "*_mac_mult" and a "*_mac_out" cell in the Yosys report,
    but is one DSP block. Verified against real Yosys output rather than a handwritten report.
    """
    modules_folder = copy_modules("multiplier", tmp_path)
    modules = get_modules(modules_folder=modules_folder)

    project = YosysIntelNetlistBuild(
        family="max10",
        name="test_proj",
        modules=modules,
        build_result_checkers=[DspBlocks(EqualTo(1))],
        ghdl_plugin_path=GHDL_PLUGIN_PATH,
        ghdl_prefix=GHDL_PREFIX,
    )

    project_path = tmp_path / "yosys"
    assert project.create(project_path)

    build_result = project.build(project_path)
    # The checker above fails the build if the count is not exactly one.
    assert build_result.success
    assert build_result.synthesis_size["DSP Blocks"] == 1


def test_building_resource_counter_example_module_netlist_projects(tmp_path):
    """
    Build the netlist projects defined by the 'resource_counter' example module, to make sure
    that this real-world usage example (see 'module_resource_counter.py') keeps working.
    """
    module = get_tsfpga_example_modules(names_include={"resource_counter"}).get("resource_counter")

    for project in module.get_build_projects():
        # These are 'None' by default in the example module, since a standard system installation
        # of GHDL/Yosys/ghdl-yosys-plugin would not need them. Set here to work on this test
        # machine's non-standard installation.
        project._ghdl_plugin_path = GHDL_PLUGIN_PATH  # noqa: SLF001
        project._ghdl_prefix = GHDL_PREFIX  # noqa: SLF001

        project_path = tmp_path / project.name
        assert project.create(project_path)

        build_result = project.build(project_path)
        assert build_result.success, project.name


def test_building_resource_counter_example_module_netlist_projects_via_build_project_list(
    tmp_path,
):
    """
    Same as ``test_building_resource_counter_example_module_netlist_projects`` above, but drives
    the build through :class:`.BuildProjectList` and the module-level :func:`.get_build_projects`
    helper, exactly like ``tsfpga/examples/build_fpga.py`` does for a real project.
    This proves that ``YosysNetlistBuild`` projects (netlist-only, no place & route) can be mixed
    into the same generic build flow as ``VivadoProject`` projects, with no special-casing needed
    by the caller.
    """
    modules = get_tsfpga_example_modules(names_include={"resource_counter"})

    projects = get_build_projects(
        modules=modules, project_filters=[], include_netlist_not_full_builds=True
    )
    assert projects, "Did not find the expected netlist build projects"

    for project in projects:
        # See note in the test above about why this is needed on this particular test machine.
        project._ghdl_plugin_path = GHDL_PLUGIN_PATH  # noqa: SLF001
        project._ghdl_prefix = GHDL_PREFIX  # noqa: SLF001

    project_list = BuildProjectList(projects=projects)

    assert project_list.create(projects_path=tmp_path, num_parallel_builds=2)
    assert project_list.build(
        projects_path=tmp_path, num_parallel_builds=2, num_threads_per_build=1
    )

    for project in projects:
        project_path = BuildProjectList.get_build_project_path(
            project=project, projects_path=tmp_path
        )
        assert project_path.exists()
