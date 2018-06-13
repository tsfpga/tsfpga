from os import makedirs, remove
from os.path import dirname, exists, isdir
from shutil import rmtree


def create_file(file, contents=None):
    if not exists(dirname(file)):
        makedirs(dirname(file))

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


def create_directory(directory, allow_overwrite=True):
    if allow_overwrite:
        delete(directory)
    elif exists(directory):
        return directory

    makedirs(directory)
    return directory


def file_contains_string(file, string):
    with open(file) as file_handle:
        return string in file_handle.read()


def file_equals(file, string):
    with open(file) as file_handle:
        return file_handle.read() == string
