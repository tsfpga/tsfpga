# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


class LessThan:

    """
    Limit to be used with a checker to see that a figure is less than the specified value.
    """

    def __init__(self, value):
        """
        Arguments:
            value (int): The result value shall be less than this.
        """
        self.value = value

    def check(self, result_value):
        return result_value < self.value

    def __str__(self):
        return f"< {self.value}"


class EqualTo:

    """
    Limit to be used with a checker to see that a figure is equal to the specified value.
    """

    def __init__(self, value):
        """
        Arguments:
            value (int): The result value shall be equal to this.
        """
        self.value = value

    def check(self, result_value):
        return result_value == self.value

    def __str__(self):
        return str(self.value)


class BuildResultChecker:

    """
    Check a build result value against a limit.

    Overload and implement the ``check`` method according to the resource you want to check.
    """

    def __init__(self, limit):
        """
        Arguments:
            limit: The limit that the specified resource shall be checked against. Should
                be e.g. a :class:`LessThan` object.
        """
        self.limit = limit

    def check(self, build_result):
        """
        Arguments:
            build_result (tsfpga.vivado.build_result.BuildResult): Build result that shall
                be checked.

        Returns:
            bool: True if check passed, false otherwise.
        """
        raise NotImplementedError("Implement in child class")

    def _check_value(self, name, value):
        if self.limit.check(value):
            message = f"Result check passed for {name}: {value} ({self.limit})"
            print(message)
            return True

        message = f"Result check failed for {name}. " f"Got {value}, expected {self.limit}."
        print(message)
        return False


class MaximumLogicLevel(BuildResultChecker):

    """
    Check the maximum logic level of a build result against a limit.
    """

    name = "Maximum logic level"

    def check(self, build_result):
        return self._check_value("maximum logic level", build_result.maximum_logic_level)


class SizeChecker(BuildResultChecker):

    """
    Check a build result size value against a limit.

    Overload and set the correct ``name``, according to the names
    in the vendor utilization report.

    Note that since this is to be used by netlist builds it checks the synthesized size, not
    the implemented one, even if available.
    """

    name = ""

    def check(self, build_result):
        return self._check_value(self.name, build_result.synthesis_size[self.name])


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


class Uram(SizeChecker):
    name = "URAM"


class DspBlocks(SizeChecker):

    """
    In Vivado pre-2020.1 the resource was called "DSP48 Blocks" in the utilization report.
    After that it is called "DSP Blocks". This class checks for both.
    """

    name = "DSP Blocks"

    def check(self, build_result):
        """
        Same as parent class, but checks for the legacy name as well as the current name.
        """
        legacy_name = "DSP48 Blocks"
        if legacy_name in build_result.synthesis_size:
            return self._check_value(legacy_name, build_result.synthesis_size[legacy_name])

        return self._check_value(self.name, build_result.synthesis_size[self.name])
