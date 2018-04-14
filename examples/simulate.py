from os.path import join, dirname
import sys

PATH_TO_HLD_REUSE = join(dirname(__file__), "..")
sys.path.append(PATH_TO_HLD_REUSE)
import hdl_reuse
from hdl_reuse.module import get_modules

PATH_TO_VUNIT = join(hdl_reuse.ROOT, "..", "vunit")
sys.path.append(PATH_TO_VUNIT)
from vunit import VUnit


def main():
    vunit_proj = VUnit.from_argv()
    vunit_proj.add_verification_components()
    vunit_proj.add_random()

    for module in get_modules([hdl_reuse.HDL_REUSE_MODULES]):
        vunit_library = vunit_proj.add_library(module.library_name)
        for file in module.get_simulation_files():
            vunit_library.add_source_file(file)
        module.setup_simulations(vunit_proj)

    vunit_proj.main()


if __name__ == "__main__":
    main()
