# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from abc import ABC, abstractmethod
from typing import Union

# Local folder libraries
from .build_result import BuildResult


class Limit(ABC):
    """
    Base class for limit checks.
    Inherit and implement the check in subclass.
    """

    def __init__(self, value: int) -> None:
        """
        Arguments:
            value: The result value shall be compared with this number.
        """
        self.value = value

    @abstractmethod
    def check(self, result_value: Union[int, float]) -> bool:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


class LessThan(Limit):
    """
    Limit to be used with a checker to see that a figure is less than the specified value.
    """

    def check(self, result_value: Union[int, float]) -> bool:
        return result_value < self.value

    def __str__(self) -> str:
        return f"< {self.value}"


class EqualTo(Limit):
    """
    Limit to be used with a checker to see that a figure is equal to the specified value.
    """

    def check(self, result_value: Union[int, float]) -> bool:
        return result_value == self.value

    def __str__(self) -> str:
        return str(self.value)


class GreaterThan(Limit):
    """
    Limit to be used with a checker to see that a figure is greater than the specified value.
    """

    def check(self, result_value: Union[int, float]) -> bool:
        return result_value > self.value

    def __str__(self) -> str:
        return f"> {self.value}"


class BuildResultChecker(ABC):
    """
    Base class for build result checkers that check a certain build result value against a limit.

    Overload in subclass and implement the ``check`` method according to the resource you want
    to check.
    """

    def __init__(self, limit: Limit):
        """
        Arguments:
            limit: The limit that the specified resource shall be checked against.
        """
        self.limit = limit

    @abstractmethod
    def check(self, build_result: BuildResult) -> bool:
        """
        Arguments:
            build_result: Build result that shall be checked. Should come from a successful build.

        Return:
            True if check passed, false otherwise.
        """

    def _check_result_value(self, name: str, result_value: Union[int, float]) -> bool:
        if result_value is not None and self.limit.check(result_value=result_value):
            print(f"Result check passed for {name}: {result_value} ({self.limit})")
            return True

        print(f"Result check failed for {name}. Got {result_value}, expected {self.limit}.")
        return False


class MaximumLogicLevel(BuildResultChecker):
    """
    Check the maximum logic level of a build result against a limit.
    """

    name = "Maximum logic level"

    def check(self, build_result: BuildResult) -> bool:
        value = build_result.maximum_logic_level
        if value is None:
            raise ValueError("Should only call after successful synthesis")

        return self._check_result_value(name="maximum logic level", result_value=value)


class SizeChecker(BuildResultChecker):
    """
    Check a build result size value against a limit.

    Overload and set the correct ``name``, according to the names
    in the vendor utilization report.

    Note that since this is to be used by netlist builds it checks the synthesized size, not
    the implemented one, even if available.
    """

    name: str

    def check(self, build_result: BuildResult) -> bool:
        if build_result.synthesis_size is None:
            raise ValueError("Should only call after successful synthesis")

        if self.name not in build_result.synthesis_size:
            raise ValueError(
                f'Synthesis result size does not contain the requested resource: "{self.name}"'
            )

        return self._check_result_value(
            name=self.name, result_value=build_result.synthesis_size[self.name]
        )


class TotalLuts(SizeChecker):
    name = "Total LUTs"


class LogicLuts(SizeChecker):
    name = "Logic LUTs"


class LutRams(SizeChecker):
    name = "LUTRAMs"


class Srls(SizeChecker):
    name = "SRLs"


class Ffs(SizeChecker):
    name = "FFs"


class Ramb36(SizeChecker):
    name = "RAMB36"


class Ramb18(SizeChecker):
    name = "RAMB18"


class Ramb(SizeChecker):
    """
    Combined checker for RAMB36 and RAMB18 count.
    Each RAMB18 counts as half a RAMB36.
    """

    name = "RAMB"

    def check(self, build_result: BuildResult) -> bool:
        """
        Similar to super class, but takes out two result values.
        """
        ramb36_value = self._get_result_value(build_result=build_result, name=Ramb36.name)
        ramb18_value = self._get_result_value(build_result=build_result, name=Ramb18.name)

        value = ramb36_value + ramb18_value / 2

        return self._check_result_value(name=self.name, result_value=value)

    @staticmethod
    def _get_result_value(build_result: BuildResult, name: str) -> int:
        if build_result.synthesis_size is None:
            raise ValueError("Should only call after successful synthesis")

        if name not in build_result.synthesis_size:
            raise ValueError(
                f'Synthesis result size does not contain the requested resource: "{name}"'
            )

        return build_result.synthesis_size[name]


class Uram(SizeChecker):
    name = "URAM"


class DspBlocks(SizeChecker):
    """
    In Vivado pre-2020.1 the resource was called "DSP48 Blocks" in the utilization report.
    After that it is called "DSP Blocks". This class checks for both.
    """

    name = "DSP Blocks"

    def check(self, build_result: BuildResult) -> bool:
        """
        Same as super class, but checks for the legacy name as well as the current name.
        """
        if build_result.synthesis_size is None:
            raise ValueError("Should only call after successful synthesis")

        legacy_name = "DSP48 Blocks"

        if legacy_name in build_result.synthesis_size:
            value = build_result.synthesis_size[legacy_name]
        else:
            value = build_result.synthesis_size[self.name]

        return self._check_result_value(name=self.name, result_value=value)
