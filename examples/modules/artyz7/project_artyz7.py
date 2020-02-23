# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from pathlib import Path

from tsfpga.constraint import Constraint
from tsfpga.vivado_project import VivadoProject

from tsfpga_example_env import get_tsfpga_modules

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent


def get_projects():
    projects = []

    modules = get_tsfpga_modules()
    part = "xc7z020clg400-1"

    tcl_dir = THIS_DIR / "tcl"
    pinning = Constraint(tcl_dir / "artyz7_pinning.tcl")
    block_design = tcl_dir / "block_design.tcl"

    projects.append(VivadoProject(
        name="artyz7",
        modules=modules,
        part=part,
        tcl_sources=[block_design],
        constraints=[pinning],
        defined_at=THIS_FILE
    ))

    projects.append(SpecialVivadoProject(
        name="artyz7_dummy",
        modules=modules,
        part=part,
        top="artyz7_top",
        generics=dict(dummy=True, values=123),
        constraints=[pinning],
        tcl_sources=[block_design]
    ))

    return projects


class SpecialVivadoProject(VivadoProject):

    def post_build(self, output_path, **kwargs):
        print(f"We can do useful things here. In the output path {output_path} for example")
