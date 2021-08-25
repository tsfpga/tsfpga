# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from tsfpga import DEFAULT_FILE_ENCODING


class SbyWriter:
    """
    Writes a SymbiYosys script file
    """

    @staticmethod
    def write_sby(output_path, top, formal_settings, compiled_libraries, src_files, generics=None):
        """
        Create SymbiYosys script. This script will run ghdl --synth
        """

        # Validate formal_settings
        valid_keys = set(["mode", "depth", "engine_command", "solver_command"])
        if set(formal_settings.keys()) != valid_keys:
            raise ValueError(
                f"Unexpected keys. Got {formal_settings.keys()}, expected one of {valid_keys}"
            )

        p_args = [f"-P{compiled_library}" for compiled_library in compiled_libraries]
        g_args = []
        if generics is not None:
            for key in iter(generics):
                g_args.append(f"-g{key}={generics[key]}")

        # Assume that the top entity name is the same as file name
        ghdl_synth_cmd = ["ghdl", "--std=08", "-fpsl"] + p_args + g_args + [top + ".vhd", "-e", top]

        sby = ""
        sby += "[options]\n"
        sby += f"mode {formal_settings['mode']} \n"
        sby += f"depth {str(formal_settings['depth'])} \n"
        sby += "\n"
        sby += "[engines]\n"
        sby += f"{formal_settings['engine_command']} {formal_settings['solver_command']}\n"
        sby += "\n"
        sby += "[script]\n"
        sby += f"{' '.join(ghdl_synth_cmd)} \n"
        sby += f"prep -top {top} \n"
        sby += "\n"
        sby += "[files]\n"
        sby += "\n".join([str(src_file) for src_file in src_files])
        sby += "\n"

        with open(output_path, "w", encoding=DEFAULT_FILE_ENCODING) as file_handle:
            file_handle.write(sby)
