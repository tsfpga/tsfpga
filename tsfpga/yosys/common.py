# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from shutil import which

from vunit.ostools import Process

from tsfpga.system_utils import safe_print


def run_ghdl(ghdl_path: Path | None, arguments: list[str], cwd: Path) -> bool:
    """
    Run GHDL with the given arguments.
    Used for analyzing VHDL source files into an on-disk library, which can later be picked up
    by the ``ghdl-yosys-plugin`` when running :func:`run_yosys`.

    Setting ``cwd`` ensures that any files produced (e.g. GHDL library files) end up in a
    well-known location.

    Arguments:
        ghdl_path: Path to the GHDL executable. Can be set to ``None``
            to use whatever version is in ``PATH``.
        arguments: Arguments that shall be passed on to GHDL.
        cwd: The GHDL process will be executed with this as the working directory.

    Return:
        True if everything went well.
    """
    cmd = [str(get_ghdl_path(ghdl_path)), *arguments]

    try:
        Process(args=cmd, cwd=cwd).consume_output(callback=safe_print)
    except Process.NonZeroExitCode:
        return False
    return True


def run_yosys(
    yosys_path: Path | None,
    ghdl_plugin_path: Path | None,
    script_file: Path,
    cwd: Path,
    ghdl_path: Path | None = None,
    ghdl_prefix: Path | None = None,
) -> bool:
    """
    Run Yosys with the given script.

    Setting ``cwd`` ensures that any files produced (e.g. reports, netlists) end up in a
    well-known location.

    Arguments:
        yosys_path: Path to the Yosys executable. Can be set to ``None``
            to use whatever version is in ``PATH``.
        ghdl_plugin_path: Path to the ``ghdl-yosys-plugin`` module (typically named ``ghdl.so``).
            Can be set to ``None`` if the plugin is already available to Yosys without explicitly
            loading it (e.g. if it has been installed in the Yosys plugin directory).
        script_file: Path to a file containing the Yosys commands that shall be executed.
        cwd: The Yosys process will be executed with this as the working directory.
        ghdl_path: Path to the GHDL executable, used only to auto-detect 'ghdl_prefix' below
            when it is not given explicitly. Can be set to ``None`` to use whatever version is
            in ``PATH``.
        ghdl_prefix: Value to set the ``GHDL_PREFIX`` environment variable to for this process.
            The ``ghdl-yosys-plugin`` module is loaded as part of the Yosys process, and hence
            can not find the GHDL standard libraries (``std``, ``ieee``, ...) on its own the
            way the standalone ``ghdl`` executable can.
            Corresponds to the "library prefix" printed by ``ghdl --disp-config``.
            If left as ``None``, this method will try to find a value automatically by calling
            ``ghdl --disp-config`` (see 'ghdl_path' above) and parsing its output.
            Set explicitly to override the auto-detected value, or if auto-detection fails.

    Return:
        True if everything went well.
    """
    cmd = [str(get_yosys_path(yosys_path))]

    if ghdl_plugin_path is not None:
        cmd += ["-m", str(ghdl_plugin_path.resolve())]

    cmd += ["-s", str(script_file.resolve())]

    resolved_ghdl_prefix = (
        ghdl_prefix if ghdl_prefix is not None else get_ghdl_library_prefix(ghdl_path)
    )

    env = None
    if resolved_ghdl_prefix is not None:
        env = dict(os.environ)
        env["GHDL_PREFIX"] = str(resolved_ghdl_prefix.resolve())

    try:
        Process(args=cmd, cwd=cwd, env=env).consume_output(callback=safe_print)
    except Process.NonZeroExitCode:
        return False
    return True


def get_ghdl_path(ghdl_path: Path | None = None) -> Path:
    """
    Wrapper to get a path to the GHDL executable.

    Arguments:
        ghdl_path: Path to the GHDL executable.
            Leave as ``None`` to use whatever is available in the system ``PATH``.
    """
    if ghdl_path is not None:
        return ghdl_path.resolve()

    which_ghdl = which("ghdl")
    if which_ghdl is None:
        raise FileNotFoundError("Could not find ghdl on PATH")

    return Path(which_ghdl).resolve()


def get_ghdl_library_prefix(ghdl_path: Path | None = None) -> Path | None:
    """
    Try to automatically find the GHDL "library prefix", i.e. the location where the
    ``std``/``ieee`` standard libraries are installed, by parsing the output of
    ``ghdl --disp-config``.

    GHDL can normally find this on its own, by looking at the path of its own executable.
    This does however not work when GHDL is used as a library, e.g. via the
    ``ghdl-yosys-plugin`` module loaded into Yosys (see :func:`run_yosys`), since there is no
    ``ghdl`` executable path to derive the prefix from in that case.
    Calling this function against the standalone ``ghdl`` executable lets us find the prefix
    anyway, so it can be forwarded explicitly.

    Arguments:
        ghdl_path: Path to the GHDL executable. Can be set to ``None``
            to use whatever version is in ``PATH``.

    Return:
        The library prefix, or ``None`` if it could not be determined.
    """
    try:
        cmd = [str(get_ghdl_path(ghdl_path)), "--disp-config"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603
    except (OSError, subprocess.CalledProcessError):
        return None

    match = re.search(r"^library prefix:\s*(.+)$", result.stdout, flags=re.MULTILINE)
    if match is None:
        return None

    return Path(match.group(1).strip())


def to_yosys_path(path: Path) -> str:
    """
    Return a path string in a format suitable to embed in a Yosys command script.
    """
    return str(path.resolve()).replace("\\", "/")


def get_yosys_path(yosys_path: Path | None = None) -> Path:
    """
    Wrapper to get a path to the Yosys executable.

    Arguments:
        yosys_path: Path to the Yosys executable.
            Leave as ``None`` to use whatever is available in the system ``PATH``.
    """
    if yosys_path is not None:
        return yosys_path.resolve()

    which_yosys = which("yosys")
    if which_yosys is None:
        raise FileNotFoundError("Could not find yosys on PATH")

    return Path(which_yosys).resolve()
