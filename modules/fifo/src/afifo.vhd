-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- @brief Asynchronous FIFO.
--
-- @details Vivado synthesis example with Zynq 7020 and the following generics
--   width: 64, depth: 1024, almost_full_level: 512, almost_empty_level: 40
-- resulted in resource utilization
--   RAMB36: 2, LUT: 138 , FF: 109
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library common;
use common.types_pkg.all;
use common.attribute_pkg.all;

library math;
use math.math_pkg.all;

library resync;


entity afifo is
  generic (
    width : integer;
    depth : integer;
    almost_full_level : integer range 0 to depth := depth / 2;
    almost_empty_level : integer range 0 to depth := depth / 2
  );
  port (
    -- Read data interface
    clk_read : in std_logic;
    read_ready : in  std_logic;
    read_valid : out std_logic := '0';  -- '1' if FIFO is not empty
    read_data  : out std_logic_vector(width - 1 downto 0);
    -- Status signals on the read side. Updated one clock cycle after read transactions.
    -- Updated "a while" after write transactions (not deterministic).
    read_level : out integer range 0 to depth := 0;
    read_almost_empty : out std_logic;
    -- Write data interface
    clk_write : in std_logic;
    write_ready : out std_logic := '1';  -- '1' if FIFO is not full
    write_valid : in  std_logic;
    write_data  : in  std_logic_vector(width - 1 downto 0);
    -- Status signals on the write side. Updated one clock cycle after write transactions.
    -- Updated "a while" after read transactions (not deterministic).
    write_level : out integer range 0 to depth := 0;
    write_almost_full : out std_logic
  );
end entity;

architecture a of afifo is

  -- Make address one bit wider than is needed to point into the memory.
  -- This is done to be able to detect if all words were written or read in
  -- one clock domain during one cycle in the other domain
  subtype fifo_addr_t is integer range 0 to 2 * depth - 1;
  signal read_addr, next_read_addr_reg, read_addr_reg, write_addr, read_addr_resync, write_addr_resync : fifo_addr_t := 0;
  signal read_data_int : std_logic_vector(read_data'range);
begin

  assert is_power_of_two(depth) report "Depth must be a power of two, to make counter synchronization convenient";

  write_ready <= not to_sl(write_level > depth - 1);
  write_almost_full <= to_sl(write_level > almost_full_level - 1);
  read_almost_empty <= to_sl(read_level < almost_empty_level);


  ------------------------------------------------------------------------------
  read_addr_handling : process
  begin
    wait until rising_edge(clk_read);

    read_addr_reg <= read_addr;
    next_read_addr_reg <= (read_addr + 1) mod (2 * depth);
  end process;

  read_addr <= next_read_addr_reg when (read_ready and read_valid) = '1' else read_addr_reg;


  ------------------------------------------------------------------------------
  write_status : process
    variable next_write_addr : fifo_addr_t;
    variable current_write_level : integer range 0 to depth;
  begin
    wait until rising_edge(clk_write);

    next_write_addr := (write_addr + 1) mod (2 * depth);
    current_write_level := (write_addr - read_addr_resync) mod (2 * depth);

    if write_ready and write_valid then
      write_level <= current_write_level  + 1;
      write_addr <= next_write_addr;
    else
      write_level <= current_write_level;
    end if;
  end process;


  ------------------------------------------------------------------------------
  resync_write_addr : entity resync.resync_counter
    generic map (
      counter_max => fifo_addr_t'high)
    port map (
      clk_in      => clk_write,
      counter_in  => write_addr,
      clk_out     => clk_read,
      counter_out => write_addr_resync
      );


  ------------------------------------------------------------------------------
  read_status : process
  begin
    wait until rising_edge(clk_read);
    if write_addr_resync /= read_addr then
      read_valid <= '1';
      -- TODO: Add check for case when all fifo is written on one clk_read cycle.
    else
      read_valid <= '0';
    end if;

    read_level <= (write_addr_resync - read_addr) mod (2 * depth);
  end process;


  ------------------------------------------------------------------------------
  resync_read_addr : entity resync.resync_counter
    generic map (
      counter_max => fifo_addr_t'high)
    port map (
      clk_in      => clk_read,
      counter_in  => read_addr,
      clk_out     => clk_write,
      counter_out => read_addr_resync
      );


  ------------------------------------------------------------------------------
  memory : block
    subtype word_t is std_logic_vector(width - 1 downto 0);
    type mem_t is array (integer range <>) of word_t;

    signal mem : mem_t(0 to depth - 1) := (others => (others => '0'));
  begin
    write_memory : process
    begin
      wait until rising_edge(clk_write);

      if write_ready and write_valid then
        mem(write_addr mod depth) <= write_data;
      end if;
    end process;

    read_memory : process
    begin
      wait until rising_edge(clk_read);

      read_data_int <= mem(read_addr mod depth);
    end process;
    read_data <= read_data_int;
  end block;

end architecture;
