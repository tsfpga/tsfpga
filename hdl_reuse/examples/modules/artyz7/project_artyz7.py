from os.path import abspath, dirname, join

from hdl_reuse.vivado_project import VivadoProject
from hdl_reuse.module import get_modules
from hdl_reuse.examples import MODULE_FOLDERS
from hdl_reuse.constraint import Constraint

THIS_DIR = abspath(dirname(__file__))
THIS_FILE = abspath(__file__)


def get_projects():
    projects = []

    modules = get_modules(MODULE_FOLDERS)
    part = "xc7z020clg400-1"

    tcl_dir = join(THIS_DIR, "tcl")
    block_design = join(tcl_dir, "block_design.tcl")

    # This one creates clocks, so for other constraint files to work it has to be processed early.
    pinning = Constraint(join(tcl_dir, "artyz7_pinning.tcl"), processing_order="early")

    projects.append(VivadoProject(
        name="artyz7",
        modules=modules,
        part=part,
        tcl_sources=[block_design],
        constraints=[pinning],
        defined_at=THIS_FILE
    ))

    projects.append(SpecialVivadoProject(
        name="artyz7_hest",
        modules=modules,
        part=part,
        top="artyz7_top",
        tcl_sources=[block_design],
        constraints=[pinning],
    ))

    return projects


class SpecialVivadoProject(VivadoProject):

    def post_build(self, output_path, **kwargs):
        print("Here we can do useful things in the output path: " + output_path)
