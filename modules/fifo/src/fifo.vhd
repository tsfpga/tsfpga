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
    width : positive;
    depth : positive;
    -- Must set to '1' for "level" port to be valid
    include_level_counter : boolean := false;
    almost_full_level : integer range 0 to depth := depth;
    almost_empty_level : integer range 0 to depth := 0;
    ram_type : string := "auto"
  );
  port (
    clk : in std_logic;
    -- Must set "include_level_counter" to true for this value to be vaLid
    level : out integer range 0 to depth := 0;

    read_ready : in std_logic;
    -- '1' if FIFO is not empty
    read_valid : out std_logic := '0';
    read_data : out std_logic_vector(width - 1 downto 0);
    -- '1' if there are almost_empty_level or fewer words available to read
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
  constant almost_empty_level_has_non_default_value : boolean := almost_empty_level /= 0;
  constant include_level_counter_int : boolean :=
    include_level_counter
    or almost_full_level_has_non_default_value
    or almost_empty_level_has_non_default_value;

  -- Need one extra bit in the addresses to be able to make the distinction if the FIFO
  -- is full or empty (where the addresses would otherwise be equal).
  subtype fifo_addr_t is unsigned(num_bits_needed(2 * depth - 1) - 1 downto 0);
  signal read_addr_next, read_addr, write_addr : fifo_addr_t := (others => '0');

  -- The part of the address that actually goes to the BRAM address port
  subtype bram_addr_range is integer range num_bits_needed(depth - 1) - 1 downto 0;

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

  assign_almost_empty : if almost_empty_level = 0 generate
    almost_empty <= not read_valid;
    assert not almost_empty_level_has_non_default_value severity failure;
  else generate
    almost_empty <= to_sl(level < almost_empty_level + 1);
    assert almost_empty_level_has_non_default_value severity failure;
    assert include_level_counter_int severity failure;
  end generate;


  ------------------------------------------------------------------------------
  read_addr_update : process(all)
  begin
    read_addr_next <= read_addr + to_int(read_ready and read_valid);
  end process;


  ------------------------------------------------------------------------------
  status : process
    variable write_addr_next : fifo_addr_t := (others => '0');
  begin
    wait until rising_edge(clk);

    write_addr_next := write_addr + to_int(write_ready and write_valid);

    if read_addr_next(bram_addr_range) /= write_addr_next(bram_addr_range) then
      read_valid <= '1';
      write_ready <= '1';
    else
      if read_addr_next(read_addr_next'high) /=  write_addr_next(write_addr_next'high) then
        -- Write address has wrapped around but read pointer has not. FIFO is full.
        read_valid <= '1';
        write_ready <= '0';
      else
        -- FIFO is empty
        read_valid <= '0';
        write_ready <= '1';
      end if;
    end if;

    -- Race condition that happens when writing and reading at the same time to FIFO of level 1.
    -- Need to let data propagate into RAM before it can be read.
    if (write_ready and write_valid) = '1' and read_addr_next(bram_addr_range) = write_addr(bram_addr_range) then
      read_valid <= '0';
    end if;

    if include_level_counter_int then
      level <= level + to_int(write_valid and write_ready) - to_int(read_ready and read_valid);
    end if;

    read_addr <= read_addr_next;
    write_addr <= write_addr_next;
  end process;


  ------------------------------------------------------------------------------
  memory : block
    subtype word_t is std_logic_vector(width - 1 downto 0);
    type mem_t is array (integer range <>) of word_t;

    signal mem : mem_t(0 to depth - 1) := (others => (others => '0'));
    attribute ram_style of mem : signal is ram_type;
  begin
    memory : process
    begin
      wait until rising_edge(clk);

      read_data <= mem(to_integer(read_addr_next) mod depth);

      if write_ready and write_valid then
        mem(to_integer(write_addr) mod depth) <= write_data;
      end if;
    end process;
  end block;
end architecture;
