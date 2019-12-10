-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- @brief Synchronous FIFO.
--
-- @details Vivado synthesis example with Zynq 7020 and the following generics
--   width: 64, depth: 1024, almost_full_level: 512, almost_empty_level: 40
-- resulted in resource utilization
--   RAMB36: 2, LUT: 62, FF: 43
-- with an estimated max frequency of 600 MHz.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library common;
use common.types_pkg.all;


entity fifo is
  generic (
    width : integer;
    depth : integer;
    almost_full_level : integer range 0 to depth - 1 := 0;
    almost_empty_level : integer range 0 to depth - 1 := 0
  );
  port (
    clk : in std_logic;
    level : out integer range 0 to depth := 0;

    read_ready : in std_logic;
    read_valid : out std_logic := '0'; -- '1' if FIFO is not empty
    read_data : out std_logic_vector(width - 1 downto 0);
    almost_empty : out std_logic;

    write_ready : out std_logic := '1'; -- '1' if FIFO is not full
    write_valid : in std_logic;
    write_data : in std_logic_vector(width - 1 downto 0);
    almost_full : out std_logic
  );
end entity;

architecture a of fifo is

  signal read_addr, read_addr_plus_1_reg, read_addr_reg, write_addr : integer range 0 to depth - 1 := 0;

begin

  -- The flags will update one cycle after the read/write that puts level over the line.
  almost_full <= to_sl(level > almost_full_level - 1); -- '1' if there are almost_full_level or more words available in the FIFO
  almost_empty <= to_sl(level < almost_empty_level); -- '1' if there are fewer than almost_empty_level words available to read


  ------------------------------------------------------------------------------
  read_addr_handling : process
  begin
    wait until rising_edge(clk);

    read_addr_reg <= read_addr;

    if read_addr = depth - 1 then
      read_addr_plus_1_reg <= 0;
    else
      read_addr_plus_1_reg <= read_addr + 1;
    end if;
  end process;

  read_addr <= read_addr_plus_1_reg when (read_ready and read_valid) = '1' else read_addr_reg;


  ------------------------------------------------------------------------------
  status : process
    variable write_addr_plus_1 : integer range 0 to depth - 1 := 0;
  begin
    wait until rising_edge(clk);

    if write_addr = depth - 1 then
      write_addr_plus_1 := 0;
    else
      write_addr_plus_1 := write_addr + 1;
    end if;

    read_valid <= to_sl(level > 0);
    if read_ready and read_valid and not (write_valid and write_ready) then
      -- Read but no write
      write_ready <= '1';
      level <= level - 1;

      if read_addr_plus_1_reg = write_addr then
        -- No data left
        read_valid <= '0';
      end if;

    elsif write_ready and write_valid and not (read_ready and read_valid) then
      -- Write but no read
      write_addr <= write_addr_plus_1;
      level <= level + 1;

      if write_addr_plus_1 = read_addr_reg then
        -- FIFO full
        write_ready <= '0';
      end if;

    elsif read_ready and read_valid and write_ready and write_valid then
      -- Write and read
      write_addr <= write_addr_plus_1;

      if read_addr = write_addr then
        -- Race condition. Need to let write data propagate into RAM before it can be read.
        read_valid <= '0';
      end if;
    end if;
  end process;


  ------------------------------------------------------------------------------
  memory : process
    subtype word_t is std_logic_vector(width - 1 downto 0);
    type mem_t is array (integer range <>) of word_t;
    variable mem : mem_t(0 to depth - 1) := (others => (others => '0'));
  begin
    wait until rising_edge(clk);

    read_data <= mem(read_addr);

    if write_ready and write_valid then
      mem(write_addr) := write_data;
    end if;
  end process;

end architecture;
