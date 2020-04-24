-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- @brief Width conversion of a data bus. Can handle wide to thin or thin
-- to wide, with some restrctions.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.types_pkg.all;


entity width_conversion is
  generic (
    input_width : integer;
    output_width : integer
  );
  port (
    clk : in std_logic;
    --
    input_ready : out std_logic := '1';
    input_valid : in std_logic;
    input_last : in std_logic;
    input_data : in std_logic_vector(input_width - 1 downto 0);
    --
    output_ready : in std_logic;
    output_valid : out std_logic := '0';
    output_last : out std_logic;
    output_data : out std_logic_vector(output_width - 1 downto 0)
  );
end entity;

architecture a of width_conversion is

  constant atom_width : integer := minimum(input_width, output_width);
  constant input_atoms : integer := input_width / atom_width;
  constant output_atoms : integer := output_width / atom_width;

  constant atom_count_max : integer := input_atoms + output_atoms;
  constant data_shift_reg_width : integer := atom_count_max * atom_width;

  signal data_shift_reg : std_logic_vector(data_shift_reg_width - 1 downto 0) := (others => '0');
  signal last_shift_reg : std_logic_vector(atom_count_max - 1 downto 0) := (others => '0');

  signal atoms : integer range 0 to atom_count_max := 0;

begin

  ------------------------------------------------------------------------------
  assert input_width /= output_width
    report "Do not use this module with equal widths" severity failure;
  assert input_width mod output_width = 0 or output_width mod input_width = 0
    report "larger width has to be multiple of smaller" severity failure;


  ------------------------------------------------------------------------------
  input_ready <= to_sl(atoms <= atom_count_max - input_atoms);


  ------------------------------------------------------------------------------
  main : process
    variable atoms_next : integer range 0 to atom_count_max;
    variable padded_input_last : std_logic_vector(input_atoms - 1 downto 0);
  begin
    wait until rising_edge(clk);

    atoms_next := atoms;

    if input_ready and input_valid then
      atoms_next := atoms_next + input_atoms;
      data_shift_reg <= input_data & data_shift_reg(data_shift_reg'left downto input_data'length);

      padded_input_last := (others => '0');
      padded_input_last(padded_input_last'high) := input_last;
      last_shift_reg <= padded_input_last & last_shift_reg(last_shift_reg'left downto input_atoms);
    end if;

    if output_ready and output_valid then
      atoms_next := atoms_next - output_atoms;
    end if;

    atoms <= atoms_next;
  end process;


  ------------------------------------------------------------------------------
  slice : process(all)
    variable atom_idx : integer range 0 to atom_count_max - output_atoms;
    variable output_valid_int : std_logic;
  begin
    output_valid_int := to_sl(atoms >= output_atoms);

    if output_valid_int then
      atom_idx := atom_count_max - atoms;
      output_data <= data_shift_reg((atom_idx + output_atoms) * atom_width - 1 downto atom_idx * atom_width);
      output_last <= last_shift_reg(atom_idx + output_atoms - 1);
    else
      output_data <= (others => '-');
      output_last <= '-';
    end if;

    output_valid <= output_valid_int;
  end process;

end architecture;
