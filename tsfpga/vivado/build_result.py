# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

from .logic_level_distribution_parser import LogicLevelDistributionParser


class BuildResult:
    """
    Attributes:
        name (`str`): The name of the build.
        success (`bool`): True if the build and all pre- and post hooks succeeded.
        synthesis_run_name (`str`): The name of the Vivado synthesis run that produced this result
            (e.g. ``synth_2``).
        implementation_run_name (`str`): The name of the Vivado implementation run that produced
            this result (e.g. ``impl_2``).
        synthesis_size (`dict`): A dictionary with the utilization of primitives for the
            synthesized design.
            Will be ``None`` if synthesis failed or did not run.
        implementation_size (`dict`): A dictionary with the utilization of primitives for
            the implemented design.
            Will be ``None`` if implementation failed or did not run.
        logic_level_distribution (str): A table with logic level distribution as reported by Vivado.
            Will be ``None`` for non-netlist builds.
            Will be ``None`` if synthesis failed or did not run.
    """

    def __init__(self, name: str, synthesis_run_name: str) -> None:
        """
        Arguments:
            name: The name of the build.
            synthesis_run_name: The name of the Vivado run that produced this result
                (e.g. ``synth_2``).
        """
        self.name = name
        self.success: bool = True

        self.synthesis_run_name = synthesis_run_name
        self.implementation_run_name: str | None = None

        self.synthesis_size: dict[str, int] | None = None
        self.implementation_size: dict[str, int] | None = None

        self.logic_level_distribution: str | None = None

        self.maximum_synthesis_frequency_hz: float | None = None

    def size_summary(self) -> str | None:
        """
        Return a string with a formatted message of the size.

        Return:
            A human-readable message of the latest size.
            ``None`` if no size is set.
        """
        build_step = None
        size = None

        if self.implementation_size:
            build_step = "implementation"
            size = self.implementation_size

        elif self.synthesis_size:
            build_step = "synthesis"
            size = self.synthesis_size

        else:
            return None

        values = [(key, _to_thousands_separated_string(value)) for key, value in size.items()]
        max_key_length = max(len(key) for key, _ in values)
        max_value_length = max(len(value) for _, value in values)

        result = f"Size of {self.name} after {build_step}:"
        for key, value in values:
            pad = " " * (max_key_length - len(key) + max_value_length - len(value))
            result += f"\n - {key}: {pad}{value}"

        return result

    def report(self) -> str | None:
        """
        Return a report of the build result. Includes all metrics and information that has been
        extracted from the Vivado reports.
        """
        result = self.size_summary()
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
    def maximum_logic_level(self) -> None | int:
        """
        The maximum level in the the :attr:`.BuildResult.logic_level_distribution`.
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


def _to_engineering_string(value: float) -> str:
    """
    Returns float/int value formatted with an SI prefix, for printing with a unit.
    For example, ``1.5625e8`` becomes ``156.25 M``.
    """
    if value == 0:
        return "0 "

    sign = ""
    if value < 0:
        value = -value
        sign = "-"

    exponent = 0

    while value < 1:
        value *= 1000
        exponent -= 1
    while value >= 1000:
        value /= 1000
        exponent += 1

    prefix = "" if exponent == 0 else "yzafpnum*kMGTPEZY"[exponent + 8]

    return f"{sign}{value:.2f} {prefix}"


def _to_thousands_separated_string(value: int) -> str:
    """
    Returns an integer formatted with thousand separators, for printing.
    For example, ``156250000`` becomes ``156 250 000``.
    """
    return f"{value:_}".replace("_", " ")
