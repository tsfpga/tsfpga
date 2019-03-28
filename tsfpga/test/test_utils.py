# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.system_utils import read_file


def file_contains_string(file, string):
    return string in read_file(file)


def file_equals(file, string):
    return string == read_file(file)
