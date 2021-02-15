# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from pathlib import Path

from tsfpga.formal_project import FormalProject


def test_generics_dict_should_be_copied():
    """
    It should be possible to update the original dict object without affecting the already-created
    formal test case
    """
    formal_project = FormalProject(project_path=Path(), modules=[])

    generics = dict(a=1)
    formal_project.add_config(top="apa", generics=generics)

    generics.update(a=2)
    formal_project.add_config(top="hest", generics=generics)

    formal_project.add_config(top="zebra")

    # pylint: disable=protected-access
    assert formal_project._formal_config_list[0].top == "apa"
    assert formal_project._formal_config_list[0].generics == dict(a=1)
    assert formal_project._formal_config_list[1].top == "hest"
    assert formal_project._formal_config_list[1].generics == dict(a=2)
    assert formal_project._formal_config_list[2].top == "zebra"
    assert formal_project._formal_config_list[2].generics is None
