from os.path import join, dirname
import sys

PATH_TO_TSFPGA = join(dirname(__file__), "..", "..")
sys.path.append(PATH_TO_TSFPGA)
import tsfpga
from tsfpga.module import get_modules
from tsfpga.examples import MODULE_FOLDERS

PATH_TO_VUNIT = join(tsfpga.ROOT, "..", "vunit")
sys.path.append(PATH_TO_VUNIT)
from vunit import VUnit


def main():
    vunit_proj = VUnit.from_argv()
    vunit_proj.add_verification_components()
    vunit_proj.add_random()

    for module in get_modules(MODULE_FOLDERS):
        vunit_library = vunit_proj.add_library(module.library_name)
        for file in module.get_simulation_files():
            vunit_library.add_source_file(file)
        module.setup_simulations(vunit_proj)

    vunit_proj.main()


if __name__ == "__main__":
    main()
