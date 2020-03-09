# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import subprocess
import importlib.util
from shutil import rmtree
from platform import system


def create_file(file, contents=None):
    create_directory(file.parent, empty=False)

    contents = "" if contents is None else contents
    with file.open("w") as file_handle:
        file_handle.write(contents)

    return file


def read_file(file):
    with file.open() as file_handle:
        return file_handle.read()


def delete(path):
    if path.exists():
        if path.is_dir():
            rmtree(path)
        else:
            path.unlink()
    return path


def create_directory(directory, empty=True):
    if empty:
        delete(directory)
    elif directory.exists():
        return directory

    directory.mkdir(parents=True)
    return directory


def run_command(cmd, cwd=None):
    if not isinstance(cmd, list):
        raise ValueError("Must be called with a list, not a string")

    subprocess.check_call(cmd, cwd=cwd)


def load_python_module(file):
    python_module_name = file.stem

    spec = importlib.util.spec_from_file_location(python_module_name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def system_is_windows():
    return system() == "Windows"
