from os.path import abspath, dirname, join

from hdl_reuse.vivado_project import VivadoProject
from hdl_reuse.module import get_modules
from hdl_reuse.examples import MODULE_FOLDERS
from hdl_reuse.constraints import Constraint

THIS_DIR = abspath(dirname(__file__))
THIS_FILE = abspath(__file__)


def get_projects():
    projects = []

    modules = get_modules(MODULE_FOLDERS)
    part = "xczu3eg-sfva625-1-i"

    tcl_dir = join(THIS_DIR, "tcl")
    block_design = join(tcl_dir, "block_design.tcl")
    constraints = [Constraint(join(tcl_dir, "fpga_pinning.tcl"))]

    projects.append(VivadoProject(
        name="fpga",
        modules=modules,
        part=part,
        block_design=block_design,
        constraints=constraints,
        defined_at=THIS_FILE
    ))

    projects.append(VivadoProject(
        name="fpga_hest",
        modules=modules,
        part=part,
        top="fpga_top",
        block_design=block_design,
        constraints=constraints,
    ))

    return projects
