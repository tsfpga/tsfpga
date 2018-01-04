from os.path import join

from vunit import VUnit

from hdl_reuse import ROOT
from hdl_reuse.module import get_modules


def main():
    vunit_proj = VUnit.from_argv()
    vunit_proj.add_com()
    vunit_proj.add_verification_components()
    vunit_proj.add_osvvm()

    module_folders = [join(ROOT, "modules")]
    for module in get_modules(module_folders):
        vunit_library = vunit_proj.add_library(module.library_name)
        for file in module.get_simulation_files():
            vunit_library.add_source_file(file)
        module.setup_simulations(vunit_proj)

    vunit_proj.main()


if __name__ == "__main__":
    main()
