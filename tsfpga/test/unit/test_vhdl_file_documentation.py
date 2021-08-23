# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from tsfpga.system_utils import create_file

from tsfpga.vhdl_file_documentation import VhdlFileDocumentation, VHDL_COMMENT_SEPARATOR


def test_documentation_header(tmp_path):
    data = f"""\
{VHDL_COMMENT_SEPARATOR}
-- Copyright bla bla
{VHDL_COMMENT_SEPARATOR}
-- This is my documentation
--
--     with
--     indentation
--
-- And empty lines.
{VHDL_COMMENT_SEPARATOR}

"""
    expected = """\
This is my documentation

    with
    indentation

And empty lines.
"""

    vhd_file = create_file(tmp_path / "file_for_test.vhd", data)
    assert VhdlFileDocumentation(vhd_file).get_header_rst() == expected


def test_only_copyright_header_should_return_no_documentation_header(tmp_path):
    data = f"""\
{VHDL_COMMENT_SEPARATOR}
-- Copyright bla bla
{VHDL_COMMENT_SEPARATOR}

"""

    vhd_file = create_file(tmp_path / "file_for_test.vhd", data)
    assert VhdlFileDocumentation(vhd_file).get_header_rst() is None


def test_get_symbolator_component(tmp_path):
    data = """
library common;
use common.addr_pkg.all;


entity test_entity is
  generic (
    buffer_segment_length_bytes : positive
  );
  port (
    clk : in std_logic;
    --# {{}}
    request_ready : in std_logic := '0';
    request_valid : out std_logic_vector(my_range_constant) := '0';
    request_address : out addr_t(apa to hest) := (others => '0');
    request_funky : out addr_t(apa to hest) :=
      (others => '0');
    request_slinky : out addr_t(apa to hest)
      := (others => '0');
    --# {{}}
    release_last_address : in std_logic_vector(enables'range) := '0';
    --# {{}}
    buffer_start_address : in addr_t(hest downto 0);
    buffer_last_address : in addr_t := (others => '0')
   );
end entity;

architecture a of test_entity is

begin
"""

    # entity->component, no ranges, and no default values.
    expected = """\
component test_entity is
  generic (
    buffer_segment_length_bytes : positive
  );
  port (
    clk : in std_logic;
    --# {{}}
    request_ready : in std_logic;
    request_valid : out std_logic_vector;
    request_address : out addr_t;
    request_funky : out addr_t;
    request_slinky : out addr_t;
    --# {{}}
    release_last_address : in std_logic_vector;
    --# {{}}
    buffer_start_address : in addr_t;
    buffer_last_address : in addr_t
   );
end component;"""

    vhd_file = create_file(tmp_path / "test_entity.vhd", data)
    got = VhdlFileDocumentation(vhd_file).get_symbolator_component()

    assert got == expected
