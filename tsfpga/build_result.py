# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations


class BuildResult:
    """
    The result of a build, in a backend-agnostic form.
    Each build backend has its own subclass, which is what is actually returned by the build
    methods: :class:`.VivadoBuildResult` and :class:`.YosysBuildResult`.

    Attributes:
        name (`str`): The name of the build.
        success (`bool`): True if the build and all pre- and post hooks succeeded.
        synthesis_size (`dict`): A dictionary with the utilization of primitives for the
            synthesized design.
            Will be ``None`` if synthesis failed or did not run.
    """

    def __init__(self, name: str) -> None:
        """
        Arguments:
            name: The name of the build.
        """
        self.name = name
        self.success: bool = True

        self.synthesis_size: dict[str, int] | None = None

    def _get_size_to_report(self) -> tuple[str, dict[str, int]] | None:
        """
        Return:
            The name of the build step, and the size that shall be reported for it.
            ``None`` if no size is set.
        """
        if self.synthesis_size:
            return "synthesis", self.synthesis_size

        return None

    def size_summary(self) -> str | None:
        """
        Return a string with a formatted message of the size.

        Return:
            A human-readable message of the latest size.
            ``None`` if no size is set.
        """
        size_to_report = self._get_size_to_report()
        if size_to_report is None:
            return None

        build_step, size = size_to_report

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
        extracted from the build tool's reports.
        """
        return self.size_summary()


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
