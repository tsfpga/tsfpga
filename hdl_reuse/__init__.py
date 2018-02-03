"""
A set of reusable functions for working with HDL projects.
"""


from os.path import dirname, abspath, join
import test


ROOT = abspath(join(dirname(__file__), ".."))  # Root of the git repo
HDL_REUSE_TCL = join(dirname(__file__), "tcl")
HDL_REUSE_MODULES = join(ROOT, "modules")
