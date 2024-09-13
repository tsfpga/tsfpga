# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import shutil
import sys
from pathlib import Path

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install.
THIS_DIR = Path(__file__).parent
REPO_ROOT = THIS_DIR.parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

# First party libraries
from tsfpga.about import REPOSITORY_URL
from tsfpga.examples.example_env import TSFPGA_EXAMPLES_TEMP_DIR, get_tsfpga_example_modules
from tsfpga.module_documentation import ModuleDocumentation
from tsfpga.system_utils import create_file
from tsfpga.tools.sphinx_doc import build_sphinx

GENERATED_SPHINX_RST = TSFPGA_EXAMPLES_TEMP_DIR / "example_sphinx_rst"
GENERATED_SPHINX_HTML = TSFPGA_EXAMPLES_TEMP_DIR / "example_sphinx_html"


def main() -> None:
    generate_documentation()

    shutil.copyfile(THIS_DIR / "conf.py", GENERATED_SPHINX_RST / "conf.py")
    build_sphinx(build_path=GENERATED_SPHINX_RST, output_path=GENERATED_SPHINX_HTML)


def generate_documentation() -> None:
    index_rst = """
Documentation of example modules
================================

.. toctree::
  :caption: Modules
  :hidden:

"""

    for module in get_tsfpga_example_modules():
        output_path = GENERATED_SPHINX_RST / "modules" / module.name

        index_rst += f"  modules/{module.name}/{module.name}\n"

        ModuleDocumentation(
            module=module,
            repository_url=f"{REPOSITORY_URL}/tree/main/{module.path.relative_to(REPO_ROOT)}",
            repository_name="GitHub",
        ).create_rst_document(output_path=output_path)

    create_file(GENERATED_SPHINX_RST / "index.rst", contents=index_rst)


if __name__ == "__main__":
    main()
