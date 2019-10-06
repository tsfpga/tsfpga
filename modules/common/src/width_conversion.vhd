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
  output_valid <= to_sl(atoms >= output_atoms);


  ------------------------------------------------------------------------------
  main : process
    variable atoms_next : integer range 0 to atom_count_max;
  begin
    wait until rising_edge(clk);

    atoms_next := atoms;

    if input_ready and input_valid then
      atoms_next := atoms_next + input_atoms;
      data_shift_reg <= input_data & data_shift_reg(data_shift_reg'left downto input_data'length);
      last_shift_reg <= input_last & last_shift_reg(last_shift_reg'left downto 1);
    end if;

    if output_ready and output_valid then
      atoms_next := atoms_next - output_atoms;
    end if;

    atoms <= atoms_next;
  end process;


  ------------------------------------------------------------------------------
  slice : process(all)
    variable atom_idx : integer range 0 to atom_count_max - output_atoms;
  begin
    if atoms >= output_atoms then
      atom_idx := atom_count_max - atoms;
      output_data <= data_shift_reg((atom_idx + output_atoms) * atom_width - 1 downto atom_idx * atom_width);
    else
      output_data <= (others => '-');
    end if;

    if atoms = output_atoms then
      output_last <= last_shift_reg(last_shift_reg'high);
    else
      output_last <= '-';
    end if;
  end process;

end architecture;
