from os import makedirs
from os.path import dirname, exists
from shutil import rmtree


def create_file(file, contents=None):
    if not exists(dirname(file)):
        makedirs(dirname(file))

    contents = "" if contents is None else contents
    with open(file, "w") as file_handle:
        file_handle.write(contents)

    return file


def delete_directory(directory):
    if exists(directory):
        rmtree(directory)


def create_directory(directory, allow_overwrite=True):
    if exists(directory):
        if allow_overwrite:
            rmtree(directory)
        else:
            return directory

    makedirs(directory)
    return directory