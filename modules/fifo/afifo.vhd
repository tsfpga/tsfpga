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
    clk_read : in std_logic;

    read_ready : in  std_logic;
    read_valid : out std_logic := '0';  -- '1' if FIFO is not empty
    read_data  : out std_logic_vector(width - 1 downto 0);
    almost_empty : out std_logic;

    clk_write : in std_logic;

    write_ready : out std_logic := '1';  -- '1' if FIFO is not full
    write_valid : in  std_logic;
    write_data  : in  std_logic_vector(width - 1 downto 0);
    almost_full : out std_logic
    );
end entity;

architecture a of afifo is

  -- Make address one bit wider than is needed to point into the memory.
  -- This is done to be able to detect if all words where written or read in
  -- one clock domain since during one cycle in the other domain
  signal read_addr, next_read_addr_reg, read_addr_reg, write_addr, read_addr_resync, write_addr_resync : integer range 0 to 2*depth - 1 := 0;
  signal clk_write_level, clk_read_level : integer range 0 to depth := 0;
  signal read_data_int : std_logic_vector(read_data'range);
begin

  assert is_power_of_two(depth) report "Depth must be a power of two, to make counter synchronization convenient";

  write_ready <= not to_sl(clk_write_level > depth-1);
  almost_full <= to_sl(clk_write_level > almost_full_level - 1);
  almost_empty <= to_sl(clk_read_level < almost_empty_level);


  ------------------------------------------------------------------------------
  read_addr_handling : process
  begin
    wait until rising_edge(clk_read);

    read_addr_reg <= read_addr;
    next_read_addr_reg <= (read_addr + 1) mod (2*depth);
  end process;

  read_addr <= next_read_addr_reg when (read_ready and read_valid) = '1' else read_addr_reg;


  ------------------------------------------------------------------------------
  write_status : process
    variable next_write_addr : integer range 0 to 2*depth-1;
    variable current_clk_write_level : integer range 0 to depth;
  begin
    wait until rising_edge(clk_write);

    next_write_addr := (write_addr + 1) mod (2*depth);

    if read_addr_resync / depth = 1 and write_addr / depth = 0 then
      -- Write address is below read address
      current_clk_write_level := (2*depth + write_addr - read_addr_resync);
    else
      current_clk_write_level := (write_addr - read_addr_resync);
    end if;
    if write_ready and write_valid then
      clk_write_level <= current_clk_write_level  + 1;
      write_addr <= next_write_addr;
    else--if write_addr /= read_addr_resync then
      clk_write_level <= current_clk_write_level;
    end if;
  end process;


  ------------------------------------------------------------------------------
  resync_write_addr : entity resync.resync_counter
    generic map (
      counter_max => 2*depth-1)
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

    clk_read_level <= (write_addr_resync - read_addr) mod depth;
  end process;


  ------------------------------------------------------------------------------
  resync_read_addr : entity resync.resync_counter
    generic map (
      counter_max => 2*depth-1)
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
