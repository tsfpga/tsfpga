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
