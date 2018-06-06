from os.path import join, exists, basename, splitext
import subprocess
import importlib.util

from hdl_reuse import ROOT


def find_git_files(file_ending=None):
    command = ["git", "ls-files"]
    output = subprocess.check_output(command, cwd=ROOT, universal_newlines=True)
    ls_files = output.split("\n")

    # subprocess.check_output() returns a trailing "\n". The split() call will make that an empty object at the end of the list.
    ls_files = ls_files[:-1]

    files = []
    for file in ls_files:
        if file_ending is None or file.endswith(file_ending):
            # git ls-files returns paths relative to the working directory where it's called. Hence we prepend the cwd used.
            file = join(ROOT, file)
            files.append(file)
            assert exists(file)  # Make sure concatenation of relative path worked

    return files


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
