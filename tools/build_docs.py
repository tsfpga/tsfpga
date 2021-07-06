# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import argparse
from datetime import datetime
from pathlib import Path
import shutil
from subprocess import check_call
import sys
from xml.etree import ElementTree

from pybadges import badge
from git import Repo

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

import tsfpga
from tsfpga.about import get_short_doc, get_doc
from tsfpga.system_utils import create_directory, create_file, delete, read_file

SPHINX_HTML = tsfpga.TSFPGA_GENERATED / "sphinx_html"


def main():
    args = arguments()
    delete(SPHINX_HTML)

    generate_registers()
    generate_release_notes()
    generate_apidoc()
    generate_sphinx_index()
    build_sphinx()

    badges_path = create_directory(SPHINX_HTML / "badges")
    build_information_badges(badges_path)

    if args.skip_coverage:
        return

    build_python_coverage_badge(badges_path)
    copy_python_coverage_to_html_output()

    if not args.no_vhdl_coverage:
        build_vhdl_coverage_badges(badges_path)
        copy_vhdl_coverage_to_html_output()


def arguments():
    parser = argparse.ArgumentParser(
        "Build sphinx documentation", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--skip-coverage",
        action="store_true",
        help="skip handling of all coverage reports",
    )
    parser.add_argument(
        "--no-vhdl-coverage",
        action="store_true",
        help="skip handling of only VHDL coverage reports",
    )
    return parser.parse_args()


def generate_registers():
    cmd = [
        sys.executable,
        tsfpga.TSFPGA_EXAMPLES / "build.py",
        "--generate-registers-only",
    ]
    check_call(cmd)


def generate_release_notes():
    rst = """
Release notes
=============

Release history and changelog for the tsfpga project.

"""

    for release, previous_release_git_tag in get_release_notes_files():
        heading = f"{release.version} ({release.date})"
        rst += heading + "\n"
        rst += "-" * len(heading) + "\n"
        rst += "\n"
        if previous_release_git_tag is not None:
            diff_url = (
                "https://gitlab.com/tsfpga/tsfpga/-/compare/"
                f"{previous_release_git_tag}...{release.git_tag}"
            )
            rst += f"`Changes since previous release <{diff_url}>`__\n"
        rst += "\n"
        rst += read_file(release.release_notes_file)
        rst += "\n"

    create_file(tsfpga.TSFPGA_GENERATED / "sphinx" / "release_notes.rst", rst)


def generate_apidoc():
    output_path = delete(tsfpga.TSFPGA_GENERATED / "sphinx" / "apidoc")
    cmd = [
        sys.executable,
        "-m",
        "sphinx.ext.apidoc",
        "-o",
        str(output_path),
        "tsfpga",
        # Exclude test files
        "**/test/**",
    ]
    check_call(cmd, cwd=tsfpga.REPO_ROOT)


def generate_sphinx_index():
    """
    Generate index.rst for sphinx. Also verify that readme.rst in the project is identical.

    Rst file inclusion in readme.rst does not work on gitlab unfortunately, hence this
    cumbersome handling of syncing documentation.
    """
    rst_head = """\
About tsfpga
============

"""
    rst_head += read_file(tsfpga.TSFPGA_DOC / "readme" / "badges.rst")
    rst_head += "\n"
    rst_head += get_short_doc()
    rst_head += "\n"

    rst_index = rst_head + get_doc()
    create_file(tsfpga.TSFPGA_GENERATED / "sphinx" / "index.rst", rst_index)

    rst_readme = rst_head
    rst_readme += "**See documentation on the website**: https://tsfpga.com\n"
    rst_readme += "\n"
    rst_readme += get_doc()
    if read_file(tsfpga.REPO_ROOT / "readme.rst") != rst_readme:
        file_path = tsfpga.TSFPGA_GENERATED / "sphinx" / "readme.rst"
        create_file(file_path, rst_readme)
        assert False, f"readme.rst in repo root not correct. See file {file_path}"


def get_release_notes_files():
    release_notes_dir = tsfpga.TSFPGA_DOC / "release_notes"
    unreleased_notes_file = release_notes_dir / "unreleased.rst"

    release_notes = []

    # Get all versioned release notes files and sort them in order newest -> oldest
    for release_notes_file in release_notes_dir.glob("*.rst"):
        if not release_notes_file == unreleased_notes_file:
            release_notes.append(release_notes_file)
    release_notes.sort(reverse=True)

    # The "Unreleased" shall be first
    release_notes.insert(0, unreleased_notes_file)

    releases = [Release(release_notes_file) for release_notes_file in release_notes]

    for idx, release in enumerate(releases):
        if idx == len(releases) - 1:
            previous_release_git_tag = None
        else:
            previous_release_git_tag = releases[idx + 1].git_tag

        yield release, previous_release_git_tag


class Release:
    def __init__(self, release_notes_file):
        self.release_notes_file = release_notes_file

        version = release_notes_file.stem
        if version == "unreleased":
            self.version = "Unreleased"
            self.git_tag = "master"
            self.date = "YYYY-MM-DD"
        else:
            self.version = version
            self.git_tag = "v" + self.version
            self.date = self.get_git_date_from_tag(self.git_tag)

    @staticmethod
    def get_git_date_from_tag(tag):
        timestamp = Repo(tsfpga.REPO_ROOT).tag(f"refs/tags/{tag}").commit.committed_date
        time = datetime.fromtimestamp(timestamp)
        return f"{time.day} {time:%B} {time.year}".lower()


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
    color = "green" if line_coverage > 80 else "red"

    badge_svg = badge(
        left_text="line coverage",
        right_text=f"{line_coverage}%",
        right_color=color,
        logo=str(tsfpga.TSFPGA_DOC / "sphinx" / "Python-logo-notext.svg"),
        embed_logo=True,
        left_link="https://tsfpga.com/python_coverage_html",
        right_link="https://tsfpga.com/python_coverage_html",
    )
    create_file(output_path / "python_coverage.svg", badge_svg)


def build_vhdl_coverage_badges(output_path):
    coverage_xml = tsfpga.TSFPGA_GENERATED / "vhdl_coverage.xml"
    assert coverage_xml.exists(), "Run simulate.py with GHDL coverage before building documentation"
    xml_root = ElementTree.parse(coverage_xml).getroot()

    build_vhdl_line_coverage_badge(xml_root, output_path)
    build_vhdl_branch_coverage_badge(xml_root, output_path)


def build_vhdl_line_coverage_badge(xml_root, output_path):
    line_coverage = int(round(float(xml_root.attrib["line-rate"]) * 100))
    assert line_coverage > 50, f"Coverage is way low: {line_coverage}. Something is wrong."
    color = "green" if line_coverage > 80 else "red"

    badge_svg = badge(
        left_text="line coverage",
        right_text=f"{line_coverage}%",
        right_color=color,
        logo="http://vunit.github.io/_static/VUnit_logo_420x420.png",
        embed_logo=True,
        left_link="https://tsfpga.com/vhdl_coverage_html",
        right_link="https://tsfpga.com/vhdl_coverage_html",
    )
    create_file(output_path / "vhdl_line_coverage.svg", badge_svg)


def build_vhdl_branch_coverage_badge(xml_root, output_path):
    branch_coverage = int(round(float(xml_root.attrib["branch-rate"]) * 100))
    assert branch_coverage > 50, "Coverage is way low: {line_coverage}. Something is wrong."
    color = "green" if branch_coverage > 80 else "orange"

    badge_svg = badge(
        left_text="branch coverage",
        right_text=f"{branch_coverage}%",
        right_color=color,
        logo="http://vunit.github.io/_static/VUnit_logo_420x420.png",
        embed_logo=True,
        left_link="https://tsfpga.com/vhdl_coverage_html",
        right_link="https://tsfpga.com/vhdl_coverage_html",
    )
    create_file(output_path / "vhdl_branch_coverage.svg", badge_svg)


def build_sphinx():
    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        "-EanWT",
        tsfpga.TSFPGA_DOC / "sphinx",
        SPHINX_HTML,
    ]
    check_call(cmd)
    index_html = SPHINX_HTML / "index.html"
    assert index_html.exists(), index_html
    print(f"Open with:\nfirefox {index_html} &")


def copy_python_coverage_to_html_output():
    coverage_html = tsfpga.TSFPGA_GENERATED / "python_coverage_html"
    assert (
        coverage_html / "index.html"
    ).exists(), "Run pytest with coverage before building documentation"

    shutil.copytree(coverage_html, SPHINX_HTML / "python_coverage_html")


def copy_vhdl_coverage_to_html_output():
    coverage_html = tsfpga.TSFPGA_GENERATED / "vhdl_coverage_html"
    assert (
        coverage_html / "index.html"
    ).exists(), "Run simulate.py with GHDL coverage before building documentation"

    shutil.copytree(coverage_html, SPHINX_HTML / "vhdl_coverage_html")


if __name__ == "__main__":
    main()
