# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from typing import Any

from tsfpga.hdl_file import HdlFile
from tsfpga.module import BaseModule


class Module(BaseModule):
    def get_simulation_files(
        self,
        include_ip_cores: bool,
        **kwargs: Any,  # noqa: ANN401
    ) -> list[HdlFile]:
        """
        Exclude files that depend on IP cores, if instructed to by the simulation script.
        """
        files_that_depend_on_ip_cores = {
            self.path / "src" / "multiplication.vhd",
            self.path / "test" / "tb_multiplication.vhd",
        }
        files_avoid = None if include_ip_cores else files_that_depend_on_ip_cores

        return super().get_simulation_files(files_avoid=files_avoid, **kwargs)
