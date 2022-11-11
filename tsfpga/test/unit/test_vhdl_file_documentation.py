# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# First party libraries
from tsfpga.system_utils import create_file
from tsfpga.vhdl_file_documentation import VHDL_COMMENT_SEPARATOR, VhdlFileDocumentation


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


def run_get_symbolator_component_test(tmp_path, vhdl_code, expected):
    vhd_file_path = create_file(tmp_path / "test_entity.vhd", vhdl_code)
    got = VhdlFileDocumentation(vhd_file_path).get_symbolator_component()

    assert got == expected


def test_get_symbolator_component_simple(tmp_path):
    data = """
entity test_entity is
  generic (
    num_interfaces : positive
  );
  port (
    clk : in std_ulogic;
    --# {{}}
    input_ready : out std_ulogic := '0';
    input_valid : in std_ulogic;
    --# {{}}
    output_ready : in std_ulogic_vector(0 to num_interfaces - 1);
    output_valid : out std_ulogic_vector(0 to num_interfaces - 1) := (others => '0')
  );
end entity;
"""

    # entity->component, no ranges, and no default values.
    expected = """\
component test_entity is
  generic (
    num_interfaces : positive
  );
  port (
    clk : in std_ulogic;
    --# {{}}
    input_ready : out std_ulogic;
    input_valid : in std_ulogic;
    --# {{}}
    output_ready : in std_ulogic_vector;
    output_valid : out std_ulogic_vector
  );
end component;"""

    run_get_symbolator_component_test(tmp_path=tmp_path, vhdl_code=data, expected=expected)


def test_get_symbolator_component_complex(tmp_path):
    data = """
library common;
use common.addr_pkg.all;


entity test_entity is
  generic(
    buffer_segment_length_bytes : positive;
    dummy : positive := 10;
    -- comment
    silly : positive_vec_t(0 to 1) :=
      -- comment again
      (others => 4)
  )
  ;port(
    clk : in std_ulogic;
    --# {{}}
    request_ready : in std_ulogic := '0';
    request_valid : out std_ulogic_vector(my_range_constant) := '0';
    request_address : out addr_t(apa to hest) := (others => '0');
    request_funky : out addr_t(apa to hest) :=
      (others => '0');
    request_slinky : out addr_t(apa to hest) := (
      -- comment
      others => '0'
    );
    --# {{}}
    release_last_address : in std_ulogic_vector(enables'range)
      := '0';
    --# {{}}
    buffer_start_address : in addr_t(hest downto 0);
    buffer_last_address : in addr_t
      := (others => '0')
   );
end entity;

architecture a of test_entity is

begin

end architecture;
end;
end a;
"""

    # entity->component, no ranges, and no default values.
    expected = """\
component test_entity is
  generic(
    buffer_segment_length_bytes : positive;
    dummy : positive;
    -- comment
    silly : positive_vec_t
  );
  port (
    clk : in std_ulogic;
    --# {{}}
    request_ready : in std_ulogic;
    request_valid : out std_ulogic_vector;
    request_address : out addr_t;
    request_funky : out addr_t;
    request_slinky : out addr_t;
    --# {{}}
    release_last_address : in std_ulogic_vector;
    --# {{}}
    buffer_start_address : in addr_t;
    buffer_last_address : in addr_t
  );
end component;"""

    run_get_symbolator_component_test(tmp_path=tmp_path, vhdl_code=data, expected=expected)


def test_get_symbolator_component_no_generics(tmp_path):
    data = """
entity test_entity is
  port (
    dummy_signal : out std_ulogic_vector(my_range_constant) := '0'
  );
end entity;
"""

    # entity->component, no ranges, and no default values.
    expected = """\
component test_entity is
  port (
    dummy_signal : out std_ulogic_vector
  );
end component;"""

    run_get_symbolator_component_test(tmp_path=tmp_path, vhdl_code=data, expected=expected)


def test_get_symbolator_component_last_port_no_newline(tmp_path):
    data = """
entity test_entity is
  generic (
    buffer_segment_length_bytes : positive_vec_t(0 to 1));
  port (
    dummy_signal : out std_ulogic_vector(my_range_constant) := '0');end entity;
"""

    # entity->component, no ranges, and no default values.
    expected = """\
component test_entity is
  generic (
    buffer_segment_length_bytes : positive_vec_t
  );
  port (
    dummy_signal : out std_ulogic_vector
  );
end component;"""

    run_get_symbolator_component_test(tmp_path=tmp_path, vhdl_code=data, expected=expected)


def test_get_symbolator_component_last_port_parenthesis_on_same_line(tmp_path):
    data = """
entity test_entity is
  generic (
    buffer_segment_length_bytes : positive_vec_t(0 to 1) := (1, 2)  )
  ;
  port (
    dummy_signal : out std_ulogic_vector(my_range_constant) := '0'  )
  ;
end entity;
"""

    # entity->component, no ranges, and no default values.
    expected = """\
component test_entity is
  generic (
    buffer_segment_length_bytes : positive_vec_t
  );
  port (
    dummy_signal : out std_ulogic_vector
  );
end component;"""

    run_get_symbolator_component_test(tmp_path=tmp_path, vhdl_code=data, expected=expected)


def run_get_symbolator_component_end_test(tmp_path, end_statement):
    data = f"""
entity test_entity is
  port (
    clk : in std_ulogic;
    dummy_signal : out std_ulogic_vector(my_range_constant) := '0'
   );
{end_statement};

architecture a of test_entity is
begin

end architecture;
end;
end a;
"""

    # entity->component, no ranges, and no default values.
    expected = """\
component test_entity is
  port (
    clk : in std_ulogic;
    dummy_signal : out std_ulogic_vector
  );
end component;"""

    run_get_symbolator_component_test(tmp_path=tmp_path, vhdl_code=data, expected=expected)


def run_get_symbolator_component_end_test_with_whitespace(tmp_path, end_statement):
    # As above but with lots of whitespace around the keywords.
    data = f"""
entity
 test_entity
  is

  port (
    clk : in std_ulogic;
    dummy_signal : out std_ulogic_vector(my_range_constant) := '0'
  )
   ;


 {end_statement}
  ;

architecture a of test_entity is
begin

end architecture;
end;
end a;
"""

    # entity->component, no ranges, and no default values.
    expected = """\
component test_entity is
  port (
    clk : in std_ulogic;
    dummy_signal : out std_ulogic_vector
  );
end component;"""

    run_get_symbolator_component_test(tmp_path=tmp_path, vhdl_code=data, expected=expected)


def test_get_symbolator_component_end_only_keyword(tmp_path):
    end_statement = "end"
    run_get_symbolator_component_end_test(tmp_path=tmp_path, end_statement=end_statement)


def test_get_symbolator_component_no_end_entity_with_whitespace(tmp_path):
    end_statement = "end   \n"
    run_get_symbolator_component_end_test_with_whitespace(
        tmp_path=tmp_path, end_statement=end_statement
    )


def test_get_symbolator_component_end_name(tmp_path):
    end_statement = "end test_entity"
    run_get_symbolator_component_end_test(tmp_path=tmp_path, end_statement=end_statement)


def test_get_symbolator_component_end_name_with_whitespace(tmp_path):
    end_statement = "end \n  test_entity  \n"
    run_get_symbolator_component_end_test_with_whitespace(
        tmp_path=tmp_path, end_statement=end_statement
    )


def test_get_symbolator_component_end_entity_name(tmp_path):
    end_statement = "end entity test_entity"
    run_get_symbolator_component_end_test(tmp_path=tmp_path, end_statement=end_statement)


def test_get_symbolator_component_end_entity_name_with_whitespace(tmp_path):
    end_statement = "end \n  entity  \n test_entity  \n"
    run_get_symbolator_component_end_test_with_whitespace(
        tmp_path=tmp_path, end_statement=end_statement
    )
