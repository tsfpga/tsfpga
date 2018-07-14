from os.path import join, dirname
import sys

PATH_TO_HLD_REUSE = join(dirname(__file__), "..", "..")
sys.path.append(PATH_TO_HLD_REUSE)
import hdl_reuse
from hdl_reuse.module import get_modules
from hdl_reuse.examples import MODULE_FOLDERS
from hdl_reuse.system_utils import create_directory


def main():
    version = "0.0.0.0"
    release_dir = create_directory(join(hdl_reuse.ROOT, "fpga-" + version), empty=True)

    for module in get_modules(MODULE_FOLDERS):
        if module.registers is not None:
            module.registers.create_html_table(join(release_dir, "doc", "tables"))
            module.registers.create_html_page(join(release_dir, "doc"))


if __name__ == "__main__":
    main()
