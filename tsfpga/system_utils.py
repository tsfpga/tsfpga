# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import importlib.util
import os
import subprocess
from os.path import commonpath, relpath
from pathlib import Path
from platform import system
from shutil import rmtree
from typing import Any, Optional

# First party libraries
from tsfpga import DEFAULT_FILE_ENCODING


def create_file(file: Path, contents: Optional[str] = None) -> Path:
    """
    Create the ``file`` and any parent directories that do not exist.
    File will be empty unless ``contents`` is specified.

    Return:
        The path to the file that was created (i.e. the original ``file`` argument).
    """
    # Create directory unless it already exists. Do not delete anything if it exists.
    create_directory(directory=file.parent, empty=False)

    contents = "" if contents is None else contents
    with open(file, "w", encoding=DEFAULT_FILE_ENCODING) as file_handle:
        file_handle.write(contents)

    return file


def read_file(file: Path) -> str:
    """
    Read and return the file contents.
    """
    with open(file, encoding=DEFAULT_FILE_ENCODING) as file_handle:
        return file_handle.read()


def read_last_lines_of_file(file: Path, num_lines: int) -> str:
    """
    Read a number of lines from the end of a file, without buffering the whole file.
    Similar to unix ``tail`` command.

    Arguments:
        file: The file that shall be read.
        num_lines: The number of lines to read.

    Return:
        The last lines of the file.
    """
    result_lines: list[str] = []
    blocks_to_read = 0

    with open(file, encoding=DEFAULT_FILE_ENCODING) as file_handle:
        while len(result_lines) < num_lines:
            # Since we do not know the line lengths, there is some guessing involved. Keep reading
            # larger and larger blocks until we have all the lines that are requested.
            blocks_to_read += 1

            try:
                # Read a block from the end
                file_handle.seek(-blocks_to_read * 4096, os.SEEK_END)
            except IOError:
                # Tried to read more data than what is available. Read whatever we have and return
                # to user.
                file_handle.seek(0)
                result_lines = file_handle.readlines()
                break

            result_lines = file_handle.readlines()

    result = "".join(result_lines[-num_lines:])
    return result


def delete(path: Path, wait_until_deleted: bool = False) -> Path:
    """
    Delete a file or directory from the filesystem.

    Arguments:
        path: The file/directory to be deleted.
        wait_until_deleted: When set to ``True``, the function will poll the filesystem
            after initiating the deletion, and not return until the path is in fact deleted.
            Is needed on some filesystems/mounts in a situation where we delete a path and
            then directly want to write to it afterwards.

    Return:
        The path that was deleted (i.e. the original ``path`` argument).
    """
    if path.exists():
        if path.is_dir():
            rmtree(path)
        else:
            path.unlink()

    if wait_until_deleted:
        while path.exists():
            pass

    return path


def create_directory(directory: Path, empty: bool = True) -> Path:
    """
    Create a directory.

    Arguments:
        directory: Path to the directory.
        empty: If true and the directory already exists, all existing files/folders in it will
            be deleted.
            If false, this function will do nothing, since the directory already exists.

    Return:
        The path that was created (i.e. the original ``directory`` argument).
    """
    if empty:
        delete(directory)
    elif directory.exists():
        return directory

    directory.mkdir(parents=True)
    return directory


def file_is_in_directory(file_path: Path, directories: list[Path]) -> bool:
    """
    Check if the file is in any of the directories.

    Arguments:
        file_path: The file to be checked.
        directories: The directories to be controlled.

    Return:
        True if there is a common path.
    """
    for directory in directories:
        if commonpath([str(file_path), str(directory)]) == str(directory):
            return True

    return False


def path_relative_to(path: Path, other: Path) -> Path:
    """
    Return a relative path from ``other`` to ``path``.
    This function works even if ``path`` is not inside a ``other`` folder.

    Note Path.relative_to() does not support the use case where e.g. readme.md should get
    relative path "../readme.md". Hence we have to use os.path.
    """
    assert path.exists(), path
    return Path(relpath(str(path), str(other)))


def run_command(
    cmd: list[str],
    cwd: Optional[Path] = None,
    env: Optional[dict[str, str]] = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """
    Will raise ``CalledProcessError`` if the command fails.

    Arguments:
        cmd: The command to run.
        cwd: The working directory where the command shall be executed.
        env: Environment variables to set.
        capture_output: Enable capturing of STDOUT and STDERR.

    Return:
        Returns the subprocess completed process object, which contains useful information.
        If ``capture_output`` is set, the ``stdout`` and ``stderr`` members of this object can
        be inspected.
    """
    if not isinstance(cmd, list):
        raise ValueError("Must be called with a list, not a string")

    return subprocess.run(
        args=cmd,
        cwd=cwd,
        env=env,
        check=True,
        encoding=DEFAULT_FILE_ENCODING,
        capture_output=capture_output,
    )


def load_python_module(file: Path) -> Any:
    """
    Load the specified Python module.
    Note that in Python nomenclature, a module is a source code file.

    On the returned object, you can call functions or instantiate classes that are in the module.
    """
    python_module_name = file.stem

    spec = importlib.util.spec_from_file_location(name=python_module_name, location=file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load the Python module: {file}")

    module = importlib.util.module_from_spec(spec=spec)
    spec.loader.exec_module(module=module)

    return module


def system_is_windows() -> bool:
    """
    Return True if the script is being executed on a computer running the Windows operating system.
    """
    return system() == "Windows"
