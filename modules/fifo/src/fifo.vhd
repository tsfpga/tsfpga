-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Synchronous FIFO.
--
-- The smallest resource footprint will happen if:
-- * include_level_counter is set to false.
-- * almost_full_level and almost_empty_level have their default value.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library common;
use common.attribute_pkg.all;
use common.types_pkg.all;

library math;
use math.math_pkg.all;


entity fifo is
  generic (
    width : integer;
    depth : integer;
    -- Must set to '1' for "level" port to be valid
    include_level_counter : boolean := false;
    almost_full_level : integer range 0 to depth := depth;
    almost_empty_level : integer range 0 to depth := 1;
    ram_type : string := "auto"
  );
  port (
    clk : in std_logic;
    -- Must set "include_level_counter" to True for this value to be vaLid
    level : out integer range 0 to depth := 0;

    read_ready : in std_logic;
    -- '1' if FIFO is not empty
    read_valid : out std_logic := '0';
    read_data : out std_logic_vector(width - 1 downto 0);
    -- '1' if there are fewer than almost_empty_level words available to read
    almost_empty : out std_logic;

    -- '1' if FIFO is not full
    write_ready : out std_logic := '1';
    write_valid : in std_logic;
    write_data : in std_logic_vector(width - 1 downto 0);
    -- '1' if there are almost_full_level or more words available in the FIFO
    almost_full : out std_logic
  );
end entity;

architecture a of fifo is

  -- Default full/empty levels are chosen so that we can use the handshake signals.
  -- If they do not have the default value, then we need to maintain a level counter.
  constant almost_full_level_has_non_default_value : boolean := almost_full_level /= depth;
  constant almost_empty_level_has_non_default_value : boolean := almost_empty_level /= 1;
  constant include_level_counter_int : boolean :=
    include_level_counter
    or almost_full_level_has_non_default_value
    or almost_empty_level_has_non_default_value;

  function max_addr return integer is
  begin
    if include_level_counter_int then
      return depth - 1;
    end if;
    -- If we do not have a level counter we must have one extra bit in the addresses to be able to make
    -- the distinction if the fifo is full or empty (where the addresses would otherwise be equal).
    return 2 * depth - 1;
  end function;

  subtype fifo_addr_t is integer range 0 to max_addr;
  signal read_addr, read_addr_plus_1_reg, read_addr_reg, write_addr : fifo_addr_t := 0;

begin

  assert is_power_of_two(depth) report "Depth must be a power of two" severity failure;

  -- The flags will update one cycle after the write/read that puts them over/below the line.
  -- Except for almost_empty when almost_empty_level is zero.
  -- In that case, when a write puts it over the line there will be a two cycle latency, since
  -- that write must propagate into the RAM before the data is valid to read.
  -- For a read that puts it below the line there is always one cycle latency.

  assign_almost_full : if almost_full_level = depth generate
    almost_full <= not write_ready;
    assert not almost_full_level_has_non_default_value severity failure;
  else generate
    almost_full <= to_sl(level > almost_full_level - 1);
    assert almost_full_level_has_non_default_value severity failure;
    assert include_level_counter_int severity failure;
  end generate;

  assign_almost_empty : if almost_empty_level = 1 generate
    almost_empty <= not read_valid;
    assert not almost_empty_level_has_non_default_value severity failure;
  else generate
    almost_empty <= to_sl(level < almost_empty_level);
    assert almost_empty_level_has_non_default_value severity failure;
    assert include_level_counter_int severity failure;
  end generate;


  ------------------------------------------------------------------------------
  read_addr_handling : process
  begin
    wait until rising_edge(clk);

    read_addr_reg <= read_addr;
    read_addr_plus_1_reg <= (read_addr + 1) mod (fifo_addr_t'high + 1);
  end process;

  read_addr <= read_addr_plus_1_reg when (read_ready and read_valid) = '1' else read_addr_reg;


  ------------------------------------------------------------------------------
  status : process
    variable write_addr_plus_1 : fifo_addr_t := 0;
  begin
    wait until rising_edge(clk);

    write_addr_plus_1 := (write_addr + 1) mod (fifo_addr_t'high + 1);

    if include_level_counter_int then
      -- If we have the level it is cheaper to compare it with zero, rather than the address comparison below
      read_valid <= to_sl(level /= 0);
      level <= level + to_int(write_valid and write_ready) - to_int(read_ready and read_valid);
    else
      read_valid <= to_sl(read_addr /= write_addr);
    end if;

    if read_ready and read_valid and not (write_valid and write_ready) then
      -- Read but no write
      write_ready <= '1';

      if read_addr_plus_1_reg mod depth = write_addr mod depth then
        -- No data left
        read_valid <= '0';
      end if;

    elsif write_ready and write_valid and not (read_ready and read_valid) then
      -- Write but no read
      write_addr <= write_addr_plus_1;

      if write_addr_plus_1 mod depth = read_addr_reg mod depth then
        -- FIFO full
        write_ready <= '0';
      end if;

    elsif read_ready and read_valid and write_ready and write_valid then
      -- Write and read
      write_addr <= write_addr_plus_1;

      -- Race condition when reading and writing to fifo of level 1. Need to let write
      -- data propagate into RAM before it can be read.
      if include_level_counter_int then
        if level = 1 then
          read_valid <= '0';
        end if;
      else
        if read_addr mod depth = write_addr mod depth then
          read_valid <= '0';
        end if;
      end if;
    end if;
  end process;


  ------------------------------------------------------------------------------
  memory : process
    subtype word_t is std_logic_vector(width - 1 downto 0);
    type mem_t is array (integer range <>) of word_t;
    variable mem : mem_t(0 to depth - 1) := (others => (others => '0'));
    attribute ram_style of mem : variable is ram_type;
  begin
    wait until rising_edge(clk);

    read_data <= mem(read_addr mod depth);

    if write_ready and write_valid then
      mem(write_addr mod depth) := write_data;
    end if;
  end process;

end architecture;
