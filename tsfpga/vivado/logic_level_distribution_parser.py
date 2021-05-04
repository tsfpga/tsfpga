# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

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
        right_most_heading = header_line.split("|")[-2]
        maximum_logic_level = int(right_most_heading.strip())
        return maximum_logic_level
