# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import re
from collections import OrderedDict


class UtilizationParser:

    """
    Used for parsing the utilization report generated by Vivado
    """

    @staticmethod
    def get_size(report):
        """
        Takes a hierarchical utilization report as a string and returns the top level size
        for the specified run.

        Arguments:
            report (str): A string containing the entire Vivado hierarchical utilization report.
        """
        lines = report.split("\n")
        for idx, line in enumerate(lines):
            # Find the table line that is the top level
            if re.search(r"\(top\)", line):
                # Parse the report, remove uninteresting fields and create dictionary
                # Note that "|" is the column separator. Heading titles for the data is two lines
                # above the row for the top level.
                headers = [column_data.strip() for column_data in lines[idx - 2].split("|")]
                numbers = [column_data.strip() for column_data in line.split("|")]
                # The first columns contain entity name, etc. We only want the numbers
                headers = headers[3:-1]
                numbers = numbers[3:-1]
                # Convert numbers from string to integers
                numbers = [int(number) for number in numbers]
                return OrderedDict(zip(headers, numbers))

        return dict()


class LessThan:

    """
    Limit to be used with a checker to see that a resource number is less than the
    specified value.
    """

    def __init__(self, value):
        """
        Arguments:
            value (int): The result size value shall be less than this.
        """
        self.value = value

    def check(self, result_value):
        return result_value < self.value

    def __str__(self):
        return f"< {self.value}"


class EqualTo:

    """
    Limit to be used with a checker to see that a resource number is equal to the
    specified value.
    """

    def __init__(self, value):
        """
        Arguments:
            value (int): The result size value shall be equal to this.
        """
        self.value = value

    def check(self, result_value):
        return result_value == self.value

    def __str__(self):
        return str(self.value)


class SizeChecker:

    """
    Check a build result size value against a limit.

    Overload and set the correct ``resource_name``, according to the names
    in the vendor utilization report.
    """

    resource_name = ""

    def __init__(self, limit):
        """
        Arguments:
            limit: The limit that the specified resource shall be checked against. Should
                be e.g. a :class:`LessThan` object.
        """
        self.limit = limit

    def check(self, result_size):
        """
        Arguments:
            result_size (dict): A size dictionary as found in the :class:`.BuildResult`
                object.
        """
        return self._check_value(self.resource_name, result_size[self.resource_name])

    def _check_value(self, resource_name, value):
        if self.limit.check(value):
            message = f"Result size check passed for {resource_name}: {value} ({self.limit})"
            print(message)
            return True

        message = (
            f"Result size check failed for {resource_name}. " f"Got {value}, expected {self.limit}."
        )
        print(message)
        return False


class TotalLuts(SizeChecker):

    resource_name = "Total LUTs"


class LogicLuts(SizeChecker):

    resource_name = "Logic LUTs"


class LutRams(SizeChecker):

    resource_name = "LUTRAMs"


class Srls(SizeChecker):

    resource_name = "SRLs"


class Ffs(SizeChecker):

    resource_name = "FFs"


class Ramb36(SizeChecker):

    resource_name = "RAMB36"


class Ramb18(SizeChecker):

    resource_name = "RAMB18"


class DspBlocks(SizeChecker):

    """
    In Vivado pre-2020.1 the resource was called "DSP48 Blocks" in the utilization report.
    After that it is called "DSP Blocks". This class checks for both.
    """

    resource_name = "DSP Blocks"

    def check(self, result_size):
        """
        Same as parent class, but checks for the legacy name as well as the current name.
        """
        legacy_name = "DSP48 Blocks"
        if legacy_name in result_size:
            return self._check_value(legacy_name, result_size[legacy_name])

        return self._check_value(self.resource_name, result_size[self.resource_name])
