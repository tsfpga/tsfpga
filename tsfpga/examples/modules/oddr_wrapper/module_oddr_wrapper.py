# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING

from tsfpga.module import BaseModule

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any


class Module(BaseModule):
    def get_simulation_files(
        self,
        files_avoid: set[Path] | None = None,
        include_unisim: bool = True,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """
        Exclude files that depend on unisim.
        """
        files_to_avoid = {self.path / "src" / "oddr_primitive.vhd"}

        if not include_unisim:
            files_avoid = files_to_avoid if files_avoid is None else files_avoid | files_to_avoid

        return super().get_simulation_files(
            files_avoid=files_avoid, include_unisim=include_unisim, **kwargs
        )
