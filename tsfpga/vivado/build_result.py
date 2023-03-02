# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import json

# Local folder libraries
from .logic_level_distribution_parser import LogicLevelDistributionParser


class BuildResult:

    """
    Attributes:
        project_name (`str`): The name of the build.
        success (`bool`): True if the build and all pre- and post hooks succeeded.
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

    def __init__(self, name):
        """
        Arguments:
            name (`str`): The name of the build.
        """
        self.name = name
        self.success = True
        self.synthesis_size = None
        self.implementation_size = None
        self.logic_level_distribution = None

    def size_summary(self):
        """
        Return a string with a formatted message of the size.

        Returns:
            str: A human-readable message of the latest size. ``None`` if no size is set.
        """
        build_step = None
        size = None

        if self.implementation_size is not None:
            build_step = "implementation"
            size = self.implementation_size
        elif self.synthesis_size is not None:
            build_step = "synthesis"
            size = self.synthesis_size
        else:
            return None

        return f"Size of {self.name} after {build_step}:\n{json.dumps(size, indent=2)}"

    def report(self):
        """
        Return a report of the build result. Includes all metrics and information that has been
        extracted from the Vivado reports.

        Returns:
            str: The report.
        """
        result = self.size_summary()

        if self.logic_level_distribution is not None:
            result = f"{result}\nLogic level distribution:\n{self.logic_level_distribution}"

        return result

    @property
    def maximum_logic_level(self):
        """
        The maximum level in the the :attr:`.BuildResult.logic_level_distribution`.
        Will be ``None`` for non-netlist builds.
        Will be ``None`` if synthesis failed or did not run.

        Returns:
            int: The maximum logic level.
        """
        if self.logic_level_distribution is None:
            return None

        return LogicLevelDistributionParser.get_maximum_logic_level(
            table=self.logic_level_distribution
        )
