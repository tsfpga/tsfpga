import tsfpga
from os.path import join, dirname


TSFPGA_EXAMPLE_MODULES = join(dirname(__file__), "modules")
MODULE_FOLDERS = [TSFPGA_EXAMPLE_MODULES, tsfpga.TSFPGA_MODULES]

# Can only be used with a commercial simulator
MODULE_FOLDERS_WITH_IP = MODULE_FOLDERS + [join(dirname(__file__), "modules_with_ip")]
