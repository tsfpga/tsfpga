from os import makedirs, remove
from os.path import basename, splitext, dirname, isdir, exists, abspath
import subprocess
import importlib.util
from shutil import rmtree


def create_file(file, contents=None):
    create_directory(dirname(file), empty=False)

    contents = "" if contents is None else contents
    with open(file, "w") as file_handle:
        file_handle.write(contents)

    return file


def delete(path):
    if exists(path):
        if isdir(path):
            rmtree(path)
        else:
            remove(path)


def create_directory(directory, empty=True):
    if empty:
        delete(directory)
    elif exists(directory):
        return directory

    makedirs(abspath(directory))
    return directory


def run_command(cmd, cwd=None):
    if not isinstance(cmd, list):
        raise ValueError("Must be called with a list, not a string")

    subprocess.check_call(cmd, cwd=cwd)


def load_python_module(file):
    python_module_name = splitext(basename(file))[0]

    spec = importlib.util.spec_from_file_location(python_module_name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module
