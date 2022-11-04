# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import importlib.util
import os
import subprocess
from os.path import commonpath, relpath
from pathlib import Path
from platform import system
from shutil import rmtree

# First party libraries
from tsfpga import DEFAULT_FILE_ENCODING


def create_file(file, contents=None):
    create_directory(file.parent, empty=False)

    contents = "" if contents is None else contents
    with open(file, "w", encoding=DEFAULT_FILE_ENCODING) as file_handle:
        file_handle.write(contents)

    return file


def read_file(file):
    with open(file, encoding=DEFAULT_FILE_ENCODING) as file_handle:
        return file_handle.read()


def read_last_lines_of_file(file, num_lines):
    """
    Read a number of lines from the end of a file, without buffering the whole file.
    Similar to unix ``tail`` command.

    Arguments:
        file (pathlib.Path): The file that shall be read.
        num_lines (int): The number of lines to read.

    Return:
        str: The last lines of the file.
    """
    result_lines = []
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


def delete(path, wait_until_deleted=False):
    """
    Delete a file or directory from the filesystem.

    Arguments:
        path (pathlib.Path): The file/directory to be deleted.
        wait_until_deleted (bool): When set to ``True``, the function will poll the filesystem
            after initiating the deletion, and not return until the path is in fact deleted.
            Is needed on some filesystems/mounts in a situation where we delete a path and
            then directly want to write to it afterwards.

    Returns:
        pathlib.Path: The path that was deleted (i.e. the original ``path`` argument).
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


def create_directory(directory, empty=True):
    if empty:
        delete(directory)
    elif directory.exists():
        return directory

    directory.mkdir(parents=True)
    return directory


def file_is_in_directory(file_path, directories):
    """
    Check if the file is in any of the directories.

    Arguments:
        file_path (pathlib.Path): The file to be checked.
        directories (list(pathlib.Path)): The directories to be controlled.

    Returns:
        bool: True if there is a common path.
    """
    for directory in directories:
        if commonpath([str(file_path), str(directory)]) == str(directory):
            return True
    return False


def path_relative_to(path, other):
    """
    Note Path.relative_to() does not support the use case where e.g. readme.md should get
    relative path "../readme.md". Hence we have to use os.path.
    """
    assert path.exists(), path
    return Path(relpath(str(path), str(other)))


def run_command(cmd, cwd=None, env=None):
    if not isinstance(cmd, list):
        raise ValueError("Must be called with a list, not a string")

    subprocess.check_call(cmd, cwd=cwd, env=env)


def load_python_module(file):
    python_module_name = file.stem

    spec = importlib.util.spec_from_file_location(python_module_name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def system_is_windows():
    return system() == "Windows"
