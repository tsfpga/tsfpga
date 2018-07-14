import datetime

from hdl_reuse.git_utils import git_commands_are_available, get_git_commit


class Bit:

    def __init__(self, idx, name, description):
        self.idx = idx
        self.name = name
        self.description = description


class Register:

    _modes_readable = {
        "r": "Read",
        "w": "Write",
        "r_w": "Read, Write",
        "wpulse": "Write-pulse",
        "r_wpulse": "Read, Write-pulse",
    }

    def __init__(self, name, idx, mode):
        self.name = name
        self.idx = idx
        self.mode = mode
        self.description = ""
        self.bits = []

    def append_bit(self, bit_name, bit_description):
        idx = len(self.bits)
        bit = Bit(idx, bit_name, bit_description)

        self.bits.append(bit)
        return bit

    @property
    def mode_readable(self):
        return self._modes_readable[self.mode]

    @property
    def address(self):
        address_int = 4 * self.idx
        num_nibbles_needed = 4
        formatting_string = "0x{:0%iX}" % num_nibbles_needed
        return formatting_string.format(address_int)


class RegisterList:

    def __init__(self, name):
        self.name = name
        self.registers = []

    def append(self, register_name, mode):
        idx = len(self.registers)
        register = Register(register_name, idx, mode)

        self.registers.append(register)
        return register

    @staticmethod
    def generated_info():
        """
        A string informing the user that a file is automatically generated
        """
        info = "Automatically generated file"
        return info

    @staticmethod
    def generated_source_info():
        """
        A string containing info about the source of the generated register information
        """
        git_commit_info = ""
        if git_commands_are_available():
            git_commit = get_git_commit()
            git_commit_info = "from " + git_commit + " "

        time_info = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        info = f"Generated {git_commit_info}on {time_info}."
        return info
