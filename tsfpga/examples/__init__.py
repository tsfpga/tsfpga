import tsfpga
from os.path import join, dirname


TSFPGA_EXAMPLE_MODULES = join(dirname(__file__), "modules")
MODULE_FOLDERS = [TSFPGA_EXAMPLE_MODULES, tsfpga.TSFPGA_MODULES]
