# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from pathlib import Path
import shutil
from subprocess import check_call, check_output
import sys
from xml.etree import ElementTree

from pybadges import badge

REPO_ROOT = Path(__file__).parent.parent
sys.path.append(str(REPO_ROOT))
import tsfpga
from tsfpga.system_utils import create_directory, create_file, delete, read_file


SPHINX_HTML = tsfpga.TSFPGA_GENERATED / "sphinx_html"


def main():
    generate_registers()
    generate_release_notes()
    build_sphinx()
    build_coverage_badge()
    copy_coverage_to_html_output()


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

"""

    for release, previous_release_git_tag in get_release_notes_files():
        heading = f"[{release.version}] - {release.date}"
        rst += heading + "\n"
        rst += "-" * len(heading) + "\n"
        rst += "\n"
        if previous_release_git_tag is not None:
            diff_url = f"https://gitlab.com/truestream/tsfpga/-/compare/{previous_release_git_tag}...{release.git_tag}"
            rst += f"`Changes since previous release <{diff_url}>`__\n"
        rst += "\n"
        rst += read_file(release.release_notes_file)
        rst += "\n"

    create_file(tsfpga.TSFPGA_GENERATED / "sphinx" / "release_notes.rst", rst)


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
        cmd = [
            "git",
            "show",
            "-s",
            "--format=%cd",
            "--date=short",
            tag
        ]
        return check_output(cmd).decode().strip()


def build_coverage_badge():
    pytest_coverage_xml = tsfpga.TSFPGA_GENERATED / "pytest_coverage.xml"
    assert pytest_coverage_xml.exists(), "Run pytest with coverage before building documentation"

    xml_root = ElementTree.parse(pytest_coverage_xml).getroot()
    line_coverage = int(float(xml_root.attrib["line-rate"]) * 100)
    color = "green" if line_coverage > 80 else "red"

    badge_svg = badge(
        left_text="Pytest coverage",
        right_text=str(line_coverage) + "%",
        right_color=color,
        logo="https://upload.wikimedia.org/wikipedia/commons/0/0a/Python.svg",
        embed_logo=True,
        left_link="https://truestream.gitlab.io/tsfpga/pytest_coverage_html",
        right_link="https://truestream.gitlab.io/tsfpga/pytest_coverage_html"
    )
    output_path = create_directory(SPHINX_HTML / "badges")
    create_file(output_path / "pytest_coverage.svg", badge_svg)


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


def copy_coverage_to_html_output():
    pytest_coverage_html = tsfpga.TSFPGA_GENERATED / "pytest_coverage_html"
    assert (pytest_coverage_html / "index.html").exists(), "Run pytest with coverage before building documentation"

    output_path = delete(SPHINX_HTML / "pytest_coverage_html")
    shutil.copytree(pytest_coverage_html, output_path)


if __name__ == "__main__":
    main()
