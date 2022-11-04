# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import re


class LogicLevelDistributionParser:

    """
    Used for parsing the ``report_design_analysis -logic_level_distribution`` report generated
    by Vivado.

    This code is very hard coded for how the report and table is formatted. See the unit tests
    for examples of this formatting.
    """

    @staticmethod
    def get_table(report):
        """
        Takes a report as a string and returns the table.

        Arguments:
            report (str): A string containing the entire Vivado
                ``report_design_analysis -logic_level_distribution`` report.
        """
        table_regexp = re.compile(r"\n(\+--.*-\+)\n", re.DOTALL)
        match = table_regexp.search(report)
        if match:
            return match.group(1)

        raise ValueError(f"Could not find table in report: {report}")

    @staticmethod
    def get_maximum_logic_level(table):
        """
        Returns the maximum logic level in the table.

        Arguments:
            table (str): The table as returned by :meth:`.get_table`.

        Returns:
            int: The maximum logic level.
        """
        header_line = table.split("\n")[1]
        # First and last items are empty, due to leading and trailing "|" in the table
        headings = header_line.split("|")

        if len(headings) <= 4:
            # Nothing in table. Happens if there are no paths in the design.
            # 4 elements in list means two headings, i.e. no integer levels.
            # See unit test for examples of how this looks.
            return 0

        right_most_heading = headings[-2]
        return int(right_most_heading.strip())
