# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


class SbyWriter:
    """
    Writes a Symbioyosys script file
    """

    # pylint: disable=too-many-arguments
    @staticmethod
    def write_sby(
            output_path,
            top,
            generics,
            formal_settings,
            compilation_outputs,
            src_files):
        """
        Create Symbiyosys script. This script will run ghdl --synth
        """

        p_args = [f"-P{compilation_output}" for compilation_output in compilation_outputs]
        g_args = []
        for key in iter(generics):
            g_args.append("-g" + str(key) + "=" + str(generics[key]))

        # Assume that the top name is the same as file name
        ghdl_synth_cmd = ["ghdl", "--std=08", "-fpsl"] + p_args + g_args + [top + ".vhd", "-e", top]

        sby = ""
        sby += "[options]\n"
        sby += f"mode {formal_settings['mode']} \n"
        sby += f"depth {str(formal_settings['depth'])} \n"
        sby += "\n"
        sby += "[engines]\n"
        sby += f"{formal_settings['engine_command']} \n"
        sby += "\n"
        sby += "[script]\n"
        sby += f"{' '.join(ghdl_synth_cmd)} \n"
        sby += f"prep -top {top} \n"
        sby += "\n"
        sby += "[files]\n"
        sby += "\n".join([str(src_file) for src_file in src_files])
        sby += "\n"

        with open(output_path, "w") as file_handle:
            file_handle.write(sby)
