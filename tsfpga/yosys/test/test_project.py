# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import gc
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from tsfpga.module import get_modules
from tsfpga.system_utils import create_file
from tsfpga.vivado.build_result_checker import EqualTo, Ffs, TotalLuts
from tsfpga.vivado.generics import BitVectorGenericValue, StringGenericValue
from tsfpga.yosys.project import (
    YosysIntelNetlistBuild,
    YosysMicrochipNetlistBuild,
    YosysNetlistBuild,
    YosysXilinxNetlistBuild,
    _get_ghdl_generic_value,
    _get_verilog_parameter_value,
    _suppress_stdout,
)

# ruff: noqa: ARG002


def _create_module(modules_path, module_name="apa", top_name=None):
    top_name = f"{module_name}_top" if top_name is None else top_name
    create_file(
        modules_path / module_name / "src" / f"{top_name}.vhd",
        f"""\
library ieee;
use ieee.std_logic_1164.all;

entity {top_name} is
  port (
    clk : in std_logic
  );
end entity;

architecture a of {top_name} is
begin
end architecture;
""",
    )
    return get_modules(modules_folder=modules_path)


def test_casting_to_string():
    project = YosysNetlistBuild(name="my_project", modules=[])
    assert (
        str(project)
        == """\
my_project
Type:       YosysNetlistBuild
Top level:  my_project_top
Generics:   -
"""
    )

    project = YosysNetlistBuild(
        name="my_project",
        modules=[],
        top="apa",
        generics={"hest": True, "zebra": 3, "foo": StringGenericValue("test")},
    )
    assert (
        str(project)
        == """\
my_project
Type:       YosysNetlistBuild
Top level:  apa
Generics:   hest=True, zebra=3, foo=test
"""
    )

    project = YosysNetlistBuild(name="my_project", modules=[], apa=123, hest=456)
    assert (
        str(project)
        == """\
my_project
Type:       YosysNetlistBuild
Top level:  my_project_top
Generics:   -
Arguments:  apa=123, hest=456
"""
    )


def test_modules_list_should_be_copied():
    modules = [1]
    proj = YosysNetlistBuild(name="name", modules=modules)

    modules.append(2)
    assert len(proj.modules) == 1


def test_static_generics_dictionary_should_be_copied():
    generics = {"apa": 3}
    proj = YosysNetlistBuild(name="name", modules=[], generics=generics)

    generics["apa"] = False
    assert proj.static_generics["apa"] == 3


def test_build_result_checkers_list_should_be_copied():
    checkers = [TotalLuts(EqualTo(3))]
    proj = YosysNetlistBuild(name="name", modules=[], build_result_checkers=checkers)

    checkers.append(Ffs(EqualTo(4)))
    assert len(proj.build_result_checkers) == 1


def test_vhdl_entities_list_should_be_copied():
    vhdl_entities = ["apa"]
    proj = YosysNetlistBuild(name="name", modules=[], vhdl_entities=vhdl_entities)

    vhdl_entities.append("hest")
    assert len(proj.vhdl_entities) == 1


def test_top_name():
    assert YosysNetlistBuild(name="apa", modules=[]).top == "apa_top"
    assert YosysNetlistBuild(name="apa", modules=[], top="hest").top == "hest"


def test_project_file_name_is_same_as_project_name():
    project = YosysNetlistBuild(name="apa", modules=[])
    assert project.project_file(Path("/hest")) == Path("/hest/apa.ys")


def test_xilinx_netlist_build_sets_synth_command():
    project = YosysXilinxNetlistBuild(name="apa", modules=[])
    assert project.synth_command == "synth_xilinx"
    assert project._get_synth_command() == "synth_xilinx -top apa_top -flatten"  # noqa: SLF001

    project = YosysXilinxNetlistBuild(name="apa", modules=[], family="xc7")
    assert project.synth_command == "synth_xilinx -family xc7"


def test_intel_netlist_build_sets_synth_command():
    project = YosysIntelNetlistBuild(name="apa", modules=[])
    assert project.synth_command == "synth_intel"
    # 'synth_intel' does not accept a '-flatten' flag, unlike 'synth_xilinx'.
    assert project._get_synth_command() == "synth_intel -top apa_top"  # noqa: SLF001

    project = YosysIntelNetlistBuild(name="apa", modules=[], family="cycloneiv")
    assert project.synth_command == "synth_intel -family cycloneiv"


def test_microchip_netlist_build_sets_synth_command():
    project = YosysMicrochipNetlistBuild(name="apa", modules=[])
    assert project.synth_command == "synth_microchip"
    assert project._get_synth_command() == "synth_microchip -top apa_top"  # noqa: SLF001

    project = YosysMicrochipNetlistBuild(name="apa", modules=[], family="polarfire")
    assert project.synth_command == "synth_microchip -family polarfire"

    project = YosysMicrochipNetlistBuild(name="apa", modules=[], discard_ffinit=True)
    assert project.synth_command == "synth_microchip -discard-ffinit"


def test_get_ghdl_generic_value():
    assert _get_ghdl_generic_value(True) == "true"
    assert _get_ghdl_generic_value(False) == "false"
    assert _get_ghdl_generic_value(3) == "3"
    assert _get_ghdl_generic_value(3.5) == "3.5"
    assert _get_ghdl_generic_value(BitVectorGenericValue("1010")) == "1010"
    assert _get_ghdl_generic_value(StringGenericValue("hest")) == "hest"

    with pytest.raises(TypeError):
        _get_ghdl_generic_value("apa")


def test_get_read_verilog_command_returns_none_if_no_verilog_files(tmp_path):
    modules = _create_module(tmp_path)
    project = YosysNetlistBuild(name="apa", modules=modules)

    assert project._get_read_verilog_command() is None  # noqa: SLF001


def test_get_read_verilog_command_with_verilog_and_systemverilog_files(tmp_path):
    src_path = tmp_path / "apa" / "src"
    create_file(src_path / "counter.v", "module counter (); endmodule\n")
    create_file(src_path / "adder.sv", "module adder (); endmodule\n")
    create_file(src_path / "counter_defines.vh", "`define WIDTH 8\n")

    modules = _create_module(tmp_path)
    project = YosysNetlistBuild(name="apa", modules=modules)

    command = project._get_read_verilog_command()  # noqa: SLF001

    assert command is not None
    assert command.startswith("read_verilog -sv ")
    # Include directories must NOT be quoted, Yosys would treat the quotes as part of the path.
    assert f"-I{src_path.resolve().as_posix()} " in command
    assert '-I"' not in command
    assert (src_path / "counter.v").resolve().as_posix() in command
    assert (src_path / "adder.sv").resolve().as_posix() in command
    # Header files are 'include'd by the source files, not passed as source arguments themselves.
    assert "counter_defines.vh" not in command


@pytest.fixture
def yosys_project_test(tmp_path):
    class YosysProjectTest:
        def __init__(self):
            self.modules_path = tmp_path / "modules"
            self.project_path = tmp_path / "projects" / "apa" / "project"
            self.output_path = tmp_path / "projects" / "apa"
            self.build_time_generics = {"enable": True}

            self.mocked_run_ghdl = None
            self.mocked_run_yosys = None

        def create(self, project, **other_arguments):
            with patch("tsfpga.yosys.project.run_ghdl", autospec=True) as self.mocked_run_ghdl:
                self.mocked_run_ghdl.return_value = True
                return project.create(project_path=self.project_path, **other_arguments)

        def build(self, project, **other_arguments):
            with (
                patch("tsfpga.yosys.project.run_yosys", autospec=True) as self.mocked_run_yosys,
                patch(
                    "tsfpga.yosys.project.YosysNetlistBuild._get_size", autospec=True
                ) as mocked_get_size,
            ):
                self.mocked_run_yosys.return_value = True
                mocked_get_size.return_value = {"Total LUTs": 0, "FFs": 0}

                return project.build(
                    project_path=self.project_path,
                    output_path=self.output_path,
                    generics=self.build_time_generics,
                    **other_arguments,
                )

    return YosysProjectTest()


def test_default_pre_create_hook_should_pass(yosys_project_test):
    class CustomYosysNetlistBuild(YosysNetlistBuild):
        pass

    modules = _create_module(yosys_project_test.modules_path)
    project = CustomYosysNetlistBuild(name="apa", modules=modules)
    assert yosys_project_test.create(project)
    yosys_project_test.mocked_run_ghdl.assert_called_once()


def test_create_with_vhdl_extension_top_level_file(yosys_project_test):
    # Regression test: the top-level file lookup used to hardcode the '.vhd' file ending,
    # which meant it failed to find a top-level file using e.g. the '.vhdl' file ending.
    create_file(
        yosys_project_test.modules_path / "apa" / "src" / "apa_top.vhdl",
        """\
library ieee;
use ieee.std_logic_1164.all;

entity apa_top is
  port (
    clk : in std_logic
  );
end entity;

architecture a of apa_top is
begin
end architecture;
""",
    )
    modules = get_modules(modules_folder=yosys_project_test.modules_path)
    project = YosysNetlistBuild(name="apa", modules=modules)

    assert yosys_project_test.create(project)
    yosys_project_test.mocked_run_ghdl.assert_called_once()


def test_project_pre_create_hook_returning_false_should_fail_and_not_call_ghdl(
    yosys_project_test,
):
    class CustomYosysNetlistBuild(YosysNetlistBuild):
        def pre_create(self, **kwargs):
            return False

    modules = _create_module(yosys_project_test.modules_path)
    project = CustomYosysNetlistBuild(name="apa", modules=modules)
    assert not yosys_project_test.create(project)
    yosys_project_test.mocked_run_ghdl.assert_not_called()


def test_create_should_call_pre_create_with_correct_parameters(yosys_project_test):
    modules = _create_module(yosys_project_test.modules_path)
    project = YosysNetlistBuild(name="apa", modules=modules, generics={"apa": 123}, hest=456)
    with patch("tsfpga.yosys.project.YosysNetlistBuild.pre_create") as mocked_pre_create:
        yosys_project_test.create(project, zebra=789)
    mocked_pre_create.assert_called_once_with(
        project_path=yosys_project_test.project_path,
        hest=456,
        zebra=789,
    )
    yosys_project_test.mocked_run_ghdl.assert_called_once()


def test_default_pre_and_post_build_hooks_should_pass(yosys_project_test):
    modules = _create_module(yosys_project_test.modules_path)
    project = YosysNetlistBuild(name="apa", modules=modules)
    yosys_project_test.create(project)

    build_result = yosys_project_test.build(project)
    assert build_result.success
    yosys_project_test.mocked_run_yosys.assert_called_once()


def test_project_pre_build_hook_returning_false_should_fail_and_not_call_yosys(
    yosys_project_test,
):
    class CustomYosysNetlistBuild(YosysNetlistBuild):
        def pre_build(self, **kwargs):
            return False

    modules = _create_module(yosys_project_test.modules_path)
    project = CustomYosysNetlistBuild(name="apa", modules=modules)
    yosys_project_test.create(project)

    build_result = yosys_project_test.build(project)
    assert not build_result.success
    yosys_project_test.mocked_run_yosys.assert_not_called()


def test_project_post_build_hook_returning_false_should_fail(yosys_project_test):
    class CustomYosysNetlistBuild(YosysNetlistBuild):
        def post_build(self, **kwargs):
            return False

    modules = _create_module(yosys_project_test.modules_path)
    project = CustomYosysNetlistBuild(name="apa", modules=modules)
    yosys_project_test.create(project)

    build_result = yosys_project_test.build(project)
    assert not build_result.success
    yosys_project_test.mocked_run_yosys.assert_called_once()


def test_module_pre_build_hook_and_create_regs_are_called(yosys_project_test):
    # Patched on the class, since 'YosysNetlistBuild' deep-copies the module list before
    # 'pre_build'/'build' is called.
    with (
        patch("tsfpga.module.BaseModule.pre_build", autospec=True) as mocked_pre_build,
        patch(
            "tsfpga.module.BaseModule.create_register_synthesis_files", autospec=True
        ) as mocked_create_register_synthesis_files,
    ):
        mocked_pre_build.return_value = True

        modules = _create_module(yosys_project_test.modules_path)
        project = YosysNetlistBuild(name="apa", modules=modules)
        yosys_project_test.create(project)

        build_result = yosys_project_test.build(project)
        assert build_result.success

    mocked_pre_build.assert_called_once()
    # Note: 'BaseModule.get_synthesis_files' also triggers register file generation as a side
    # effect, and is called a few times while resolving compile order in 'create()'. So this
    # will be called more than once, which is expected and not a problem since it is idempotent.
    mocked_create_register_synthesis_files.assert_called()


def test_build_should_raise_exception_if_project_does_not_exist(yosys_project_test):
    modules = _create_module(yosys_project_test.modules_path)
    project = YosysNetlistBuild(name="apa", modules=modules)

    with pytest.raises(ValueError, match='Project "apa" does not exist'):
        yosys_project_test.build(project)


def test_build_result_checkers_are_run_and_can_fail_build(yosys_project_test):
    modules = _create_module(yosys_project_test.modules_path)
    project = YosysNetlistBuild(
        name="apa", modules=modules, build_result_checkers=[TotalLuts(EqualTo(0))]
    )
    yosys_project_test.create(project)

    with patch(
        "tsfpga.yosys.project.YosysNetlistBuild._get_size", autospec=True
    ) as mocked_get_size:
        mocked_get_size.return_value = {"Total LUTs": 3}
        with patch("tsfpga.yosys.project.run_yosys", autospec=True) as mocked_run_yosys:
            mocked_run_yosys.return_value = True
            (yosys_project_test.project_path / "ghdl").mkdir(parents=True, exist_ok=True)
            build_result = project.build(
                project_path=yosys_project_test.project_path,
                output_path=yosys_project_test.output_path,
            )

    assert not build_result.success
    assert build_result.synthesis_size == {"Total LUTs": 3}


def test_build_time_generics_are_copied(yosys_project_test):
    modules = _create_module(yosys_project_test.modules_path)
    project = YosysNetlistBuild(name="apa", modules=modules)

    generics = {"apa": 3}
    yosys_project_test.build_time_generics = generics
    yosys_project_test.create(project)
    yosys_project_test.build(project)

    generics["apa"] = False
    _, kwargs = yosys_project_test.mocked_run_yosys.call_args
    # Generics are baked into the script file content, not passed as an explicit argument.
    script_content = kwargs["script_file"].read_text()
    assert "-gapa=3" in script_content


def test_different_generic_combinations(yosys_project_test):
    modules = _create_module(yosys_project_test.modules_path)

    # Only build time generics
    project = YosysNetlistBuild(name="apa", modules=modules)
    yosys_project_test.build_time_generics = {"runtime": 1}
    yosys_project_test.create(project)
    yosys_project_test.build(project)
    _, kwargs = yosys_project_test.mocked_run_yosys.call_args
    assert "-gruntime=1" in kwargs["script_file"].read_text()

    # Static and build time generics
    project = YosysNetlistBuild(name="apa", modules=modules, generics={"static": 2})
    yosys_project_test.build_time_generics = {"runtime": 1}
    yosys_project_test.create(project)
    yosys_project_test.build(project)
    _, kwargs = yosys_project_test.mocked_run_yosys.call_args
    script_content = kwargs["script_file"].read_text()
    assert "-gruntime=1" in script_content
    assert "-gstatic=2" in script_content

    # Same key in both. Should prefer build time.
    project = YosysNetlistBuild(name="apa", modules=modules, generics={"common": 2})
    yosys_project_test.build_time_generics = {"common": 5}
    yosys_project_test.create(project)
    yosys_project_test.build(project)
    _, kwargs = yosys_project_test.mocked_run_yosys.call_args
    assert "-gcommon=5" in kwargs["script_file"].read_text()


def test_non_vhdl_top_with_vhdl_entities(yosys_project_test):
    modules = _create_module(yosys_project_test.modules_path, module_name="apa", top_name="sub_a")
    modules = _create_module(yosys_project_test.modules_path, module_name="apa", top_name="sub_b")

    project = YosysNetlistBuild(
        name="apa", modules=modules, top="verilog_top", vhdl_entities=["sub_a", "sub_b"]
    )

    yosys_project_test.build_time_generics = {}
    yosys_project_test.create(project)
    # One call per analyzed VHDL source file ('sub_a.vhd' and 'sub_b.vhd').
    assert yosys_project_test.mocked_run_ghdl.call_count == 2

    build_result = yosys_project_test.build(project)
    assert build_result.success

    _, kwargs = yosys_project_test.mocked_run_yosys.call_args
    script_content = kwargs["script_file"].read_text()

    assert script_content.count("ghdl --std=08") == 2
    assert script_content.splitlines()[0].endswith(" sub_a")
    assert script_content.splitlines()[1].endswith(" sub_b")
    assert "-top verilog_top" in script_content


def test_non_vhdl_top_with_vhdl_entity_not_found_should_raise_exception(yosys_project_test):
    modules = _create_module(yosys_project_test.modules_path)
    project = YosysNetlistBuild(
        name="apa", modules=modules, top="verilog_top", vhdl_entities=["non_existent"]
    )

    yosys_project_test.build_time_generics = {}
    yosys_project_test.create(project)

    with pytest.raises(
        ValueError, match='Could not find a VHDL source file for entity "non_existent"'
    ):
        yosys_project_test.build(project)


def test_non_vhdl_top_with_generics_sets_verilog_parameters(yosys_project_test):
    modules = _create_module(yosys_project_test.modules_path)
    project = YosysNetlistBuild(
        name="apa", modules=modules, top="verilog_top", generics={"width": 16}
    )

    yosys_project_test.create(project)

    yosys_project_test.build_time_generics = {"enable": True}
    build_result = yosys_project_test.build(project)
    assert build_result.success

    _, kwargs = yosys_project_test.mocked_run_yosys.call_args
    script_content = kwargs["script_file"].read_text()

    # Static and build-time generics both end up as Verilog parameters on the top level.
    assert "hierarchy -top verilog_top " in script_content
    assert "-chparam width 16" in script_content
    assert "-chparam enable 1" in script_content
    # The parameters must be set before synthesis.
    assert script_content.index("hierarchy -top") < script_content.index(
        "-top verilog_top -flatten"
    )


def test_vhdl_top_with_generics_does_not_set_verilog_parameters(yosys_project_test):
    modules = _create_module(yosys_project_test.modules_path)
    project = YosysNetlistBuild(name="apa", modules=modules, generics={"width": 16})

    yosys_project_test.create(project)
    yosys_project_test.build(project)

    _, kwargs = yosys_project_test.mocked_run_yosys.call_args
    script_content = kwargs["script_file"].read_text()

    # Generics go to GHDL for a VHDL top level, not to a Yosys 'hierarchy' command.
    assert "hierarchy" not in script_content
    assert "-gwidth=16" in script_content


def test_suppress_stdout_is_serialized():
    """
    Netlist builds are created from VUnit test-runner worker threads. Two threads inside the
    global 'sys.stdout' swap at the same time interleave their save/restore, and the last one
    out installs an already-closed file as 'sys.stdout'. So it must be mutually exclusive.
    """
    original_stdout = sys.stdout
    num_inside = 0
    max_num_inside = 0
    counter_lock = threading.Lock()

    def worker():
        nonlocal num_inside, max_num_inside
        for _ in range(20):
            with _suppress_stdout():
                with counter_lock:
                    num_inside += 1
                    max_num_inside = max(max_num_inside, num_inside)

                # Widen the window, so that a missing lock is detected reliably.
                time.sleep(0.001)

                with counter_lock:
                    num_inside -= 1

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert max_num_inside == 1, "Global 'sys.stdout' swap was not serialized"
    assert sys.stdout is original_stdout
    assert not sys.stdout.closed


def test_get_verilog_parameter_value():
    assert _get_verilog_parameter_value(True) == "1"
    assert _get_verilog_parameter_value(False) == "0"
    assert _get_verilog_parameter_value(3) == "3"
    assert _get_verilog_parameter_value(3.5) == "3.5"
    assert _get_verilog_parameter_value(BitVectorGenericValue("1010")) == "4'b1010"

    # Yosys can not set string parameters.
    with pytest.raises(TypeError, match="can not set string parameters"):
        _get_verilog_parameter_value(StringGenericValue("hest"))


def test_vunit_output_directory_is_removed_with_the_project(yosys_project_test):
    """
    The VUnit project is only used to resolve compile order, and its output is throwaway. It
    used to be created with 'mkdtemp', which never removes anything, so every netlist build
    left a directory behind in the system temp directory forever.
    """
    project = YosysNetlistBuild(name="apa", modules=_create_module(yosys_project_test.modules_path))

    project._get_vunit_project()  # noqa: SLF001
    output_directory = Path(project._vunit_output_dir.name)  # noqa: SLF001
    assert output_directory.exists()

    # Dropping the last reference must take the directory with it. 'gc.collect()' rather than
    # relying on refcounting alone, since the VUnit object graph can contain cycles.
    del project
    gc.collect()

    assert not output_directory.exists()
