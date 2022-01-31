# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import argparse
from pathlib import Path
import shutil
from subprocess import check_call
import sys
from xml.etree import ElementTree

from pybadges import badge

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

import tsfpga
from tsfpga.about import get_readme_rst
from tsfpga.system_utils import create_directory, create_file, delete
from tsfpga.tools.sphinx_doc import build_sphinx, generate_release_notes

GENERATED_SPHINX = tsfpga.TSFPGA_GENERATED / "sphinx_rst"
GENERATED_SPHINX_HTML = tsfpga.TSFPGA_GENERATED / "sphinx_html"
SPHINX_DOC = tsfpga.TSFPGA_DOC / "sphinx"


def main():
    args = arguments()

    generate_registers()

    rst = generate_release_notes(
        repo_root=tsfpga.REPO_ROOT,
        release_notes_directory=tsfpga.TSFPGA_DOC / "release_notes",
        project_name="tsfpga",
    )
    create_file(GENERATED_SPHINX / "release_notes.rst", rst)

    generate_apidoc()

    generate_sphinx_index()

    build_sphinx(build_path=SPHINX_DOC, output_path=GENERATED_SPHINX_HTML)

    badges_path = create_directory(GENERATED_SPHINX_HTML / "badges")
    build_information_badges(badges_path)

    if args.skip_coverage:
        return

    build_python_coverage_badge(badges_path)
    copy_python_coverage_to_html_output()


def arguments():
    parser = argparse.ArgumentParser(
        "Build sphinx documentation", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--skip-coverage",
        action="store_true",
        help="skip handling of all coverage reports",
    )
    return parser.parse_args()


def generate_registers():
    cmd = [
        sys.executable,
        tsfpga.TSFPGA_EXAMPLES / "build.py",
        "--generate-registers-only",
    ]
    check_call(cmd)


def generate_apidoc():
    output_path = delete(GENERATED_SPHINX / "apidoc")

    cmd = [
        sys.executable,
        "-m",
        "sphinx.ext.apidoc",
        # Place module documentation before submodule documentation
        "--module-first",
        "--output-dir",
        str(output_path),
        # module path
        "tsfpga",
        # exclude pattern
        "**/test/**",
    ]
    check_call(cmd, cwd=tsfpga.REPO_ROOT)


def generate_sphinx_index():
    """
    Generate index.rst for sphinx. Also verify that readme.rst in the project is identical.

    Rst file inclusion in readme.rst does not work on gitlab unfortunately, hence this
    cumbersome handling of syncing documentation.
    """
    rst = get_readme_rst(include_website_link=False, verify=True)
    create_file(GENERATED_SPHINX / "index.rst", rst)


def build_information_badges(output_path):
    badge_svg = badge(left_text="pip install", right_text="tsfpga", right_color="blue")
    create_file(output_path / "pip_install.svg", badge_svg)

    badge_svg = badge(left_text="license", right_text="BSD 3-Clause", right_color="blue")
    create_file(output_path / "license.svg", badge_svg)

    badge_svg = badge(
        left_text="",
        right_text="tsfpga/tsfpga",
        left_color="grey",
        right_color="grey",
        logo="https://about.gitlab.com/images/press/press-kit-icon.svg",
        embed_logo=True,
    )
    create_file(output_path / "gitlab.svg", badge_svg)

    badge_svg = badge(
        left_text="",
        right_text="tsfpga.com",
        left_color="grey",
        right_color="grey",
        logo="https://design.firefox.com/product-identity/firefox/firefox/firefox-logo.svg",
        embed_logo=True,
    )
    create_file(output_path / "website.svg", badge_svg)


def build_python_coverage_badge(output_path):
    coverage_xml = tsfpga.TSFPGA_GENERATED / "python_coverage.xml"
    assert coverage_xml.exists(), "Run pytest with coverage before building documentation"

    xml_root = ElementTree.parse(coverage_xml).getroot()
    line_coverage = int(round(float(xml_root.attrib["line-rate"]) * 100))
    assert line_coverage > 50, f"Coverage is way low: {line_coverage}. Something is wrong."
    color = "red" if line_coverage < 80 else "green"

    badge_svg = badge(
        left_text="line coverage",
        right_text=f"{line_coverage}%",
        right_color=color,
        logo=str(SPHINX_DOC / "Python-logo-notext.svg"),
        embed_logo=True,
        left_link="https://tsfpga.com/python_coverage_html",
        right_link="https://tsfpga.com/python_coverage_html",
    )
    create_file(output_path / "python_coverage.svg", badge_svg)


def copy_python_coverage_to_html_output():
    html_output_path = GENERATED_SPHINX_HTML / "python_coverage_html"
    delete(html_output_path)

    coverage_html = tsfpga.TSFPGA_GENERATED / "python_coverage_html"
    assert (
        coverage_html / "index.html"
    ).exists(), "Run pytest with coverage before building documentation"

    shutil.copytree(coverage_html, html_output_path)


if __name__ == "__main__":
    main()
