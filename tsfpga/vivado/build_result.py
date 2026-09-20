# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

from tsfpga.build_result import BuildResult as BaseBuildResult
from tsfpga.build_result import _to_engineering_string

from .logic_level_distribution_parser import LogicLevelDistributionParser


class VivadoBuildResult(BaseBuildResult):
    """
    The result of a Vivado build.

    Attributes:
        synthesis_run_name (`str`): The name of the Vivado synthesis run that produced this
            result (e.g. ``synth_2``).
        implementation_run_name (`str`): The name of the Vivado implementation run that produced
            this result (e.g. ``impl_2``). Will be ``None`` for netlist (synthesis-only) builds,
            since those have no implementation step.
        implementation_size (`dict`): A dictionary with the utilization of primitives for
            the implemented design.
            Will be ``None`` if implementation failed or did not run.
        logic_level_distribution (str): A table with logic level distribution as reported by
            Vivado. Will be ``None`` for non-netlist builds.
            Will be ``None`` if synthesis failed or did not run.
    """

    def __init__(self, name: str, synthesis_run_name: str) -> None:
        """
        Arguments:
            name: The name of the build.
            synthesis_run_name: The name of the Vivado run that produced this result
                (e.g. ``synth_2``).
        """
        super().__init__(name=name)

        self.synthesis_run_name = synthesis_run_name
        self.implementation_run_name: str | None = None

        self.implementation_size: dict[str, int] | None = None

        self.logic_level_distribution: str | None = None

        self.maximum_synthesis_frequency_hz: float | None = None

    def _get_size_to_report(self) -> tuple[str, dict[str, int]] | None:
        if self.implementation_size:
            return "implementation", self.implementation_size

        return super()._get_size_to_report()

    def report(self) -> str | None:
        """
        Return a report of the build result. Includes all metrics and information that has been
        extracted from the Vivado reports.
        """
        result = super().report()
        if result is None:
            return None

        if self.maximum_synthesis_frequency_hz:
            result += (
                f"\nMaximum synthesis frequency estimate: "
                f"{_to_engineering_string(value=self.maximum_synthesis_frequency_hz)}Hz"
            )

        if self.logic_level_distribution:
            result += f"\nLogic level distribution:\n{self.logic_level_distribution}"

        return result

    @property
    def maximum_logic_level(self) -> int | None:
        """
        The maximum level in the the :attr:`.VivadoBuildResult.logic_level_distribution`.
        Will be ``None`` for non-netlist builds.
        Will be ``None`` if synthesis failed or did not run.

        Return:
            The maximum logic level.
        """
        if not self.logic_level_distribution:
            return None

        return LogicLevelDistributionParser.get_maximum_logic_level(
            table=self.logic_level_distribution
        )


#: The class that used to live in this module, under this name.
#: Kept so that existing code that imports and instantiates it keeps working.
#: Code that wants the backend-agnostic type shall use :class:`tsfpga.build_result.BuildResult`.
BuildResult = VivadoBuildResult
