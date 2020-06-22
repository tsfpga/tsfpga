-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Synchronous FIFO.
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
    -- Changing these levels from default value will increase logic footprint
    almost_full_level : integer range 0 to depth := depth;
    almost_empty_level : integer range 0 to depth := 0;
    -- If enabled, read_valid will not be asserted until a full packet is available in
    -- FIFO. I.e. when write_last has been received.
    enable_packet_mode : boolean := false;
    -- Set to true in order to use read_last and write_last
    enable_last : boolean := enable_packet_mode;
    ram_type : ram_style_t := ram_style_auto
  );
  port (
    clk : in std_logic;
    level : out integer range 0 to depth := 0;

    read_ready : in std_logic;
    -- '1' if FIFO is not empty
    read_valid : out std_logic := '0';
    read_data : out std_logic_vector(width - 1 downto 0);
    -- Must set enable_last generic in order to use this
    read_last : out std_logic := '0';
    -- '1' if there are almost_empty_level or fewer words available to read
    almost_empty : out std_logic;

    -- '1' if FIFO is not full
    write_ready : out std_logic := '1';
    write_valid : in std_logic;
    write_data : in std_logic_vector(width - 1 downto 0);
    -- Must set enable_last generic in order to use this
    write_last : in std_logic := '-';
    -- '1' if there are almost_full_level or more words available in the FIFO
    almost_full : out std_logic
  );
end entity;

architecture a of fifo is

  constant enable_last_int : boolean := enable_last or enable_packet_mode;

  -- Need one extra bit in the addresses to be able to make the distinction if the FIFO
  -- is full or empty (where the addresses would otherwise be equal).
  subtype fifo_addr_t is unsigned(num_bits_needed(2 * depth - 1) - 1 downto 0);
  signal read_addr_next, read_addr, write_addr : fifo_addr_t := (others => '0');

  -- The part of the address that actually goes to the BRAM address port
  subtype bram_addr_range is integer range num_bits_needed(depth - 1) - 1 downto 0;

  signal num_lasts_in_fifo : integer range 0 to depth := 0;

begin

  assert is_power_of_two(depth) report "Depth must be a power of two" severity failure;

  assert enable_last or (not enable_packet_mode) report "Must set enable_last for packet mode" severity failure;

  -- The flags will update one cycle after the write/read that puts them over/below the line.
  -- Except for almost_empty when almost_empty_level is zero.
  -- In that case, when a write puts it over the line there will be a two cycle latency, since
  -- that write must propagate into the RAM before the data is valid to read.
  -- For a read that puts it below the line there is always one cycle latency.

  assign_almost_full : if almost_full_level = depth generate
    almost_full <= not write_ready;
  else generate
    almost_full <= to_sl(level > almost_full_level - 1);
  end generate;

  assign_almost_empty : if almost_empty_level = 0 generate
    almost_empty <= not read_valid;
  else generate
    almost_empty <= to_sl(level < almost_empty_level + 1);
  end generate;


  ------------------------------------------------------------------------------
  status : process
    variable write_addr_next : fifo_addr_t := (others => '0');
    variable num_lasts_in_fifo_next : integer range 0 to depth := 0;
  begin
    wait until rising_edge(clk);

    level <= level + to_int(write_valid and write_ready) - to_int(read_ready and read_valid);

    write_addr_next := write_addr + to_int(write_ready and write_valid);

    write_ready <= to_sl(
      read_addr_next(bram_addr_range) /= write_addr_next(bram_addr_range)
      or read_addr_next(read_addr_next'high) =  write_addr_next(write_addr_next'high));

    if enable_packet_mode then
      num_lasts_in_fifo_next := num_lasts_in_fifo
        + to_int(write_ready and write_valid and write_last)
        - to_int(read_ready and read_valid and read_last);
      read_valid <= to_sl(read_addr_next /= write_addr and num_lasts_in_fifo_next /= 0);
    else
      read_valid <= to_sl(read_addr_next /= write_addr);
    end if;

    read_addr <= read_addr_next;
    write_addr <= write_addr_next;
    num_lasts_in_fifo <= num_lasts_in_fifo_next;
  end process;

  read_addr_next <= read_addr + to_int(read_ready and read_valid);


  ------------------------------------------------------------------------------
  memory : block
    constant memory_word_width : integer := width + to_int(enable_last_int);
    subtype word_t is std_logic_vector(memory_word_width - 1 downto 0);
    type mem_t is array (integer range <>) of word_t;

    signal mem : mem_t(0 to depth - 1) := (others => (others => '0'));
    attribute ram_style of mem : signal is to_attribute(ram_type);

    signal memory_read_data, memory_write_data : word_t;
  begin

    read_data <= memory_read_data(read_data'range);
    memory_write_data(write_data'range) <= write_data;

    assign_data : if enable_last_int generate
      read_last <= memory_read_data(memory_read_data'high);
      memory_write_data(memory_write_data'high) <= write_last;
    end generate;

    memory : process
    begin
      wait until rising_edge(clk);

      memory_read_data <= mem(to_integer(read_addr_next) mod depth);

      if write_ready and write_valid then
        mem(to_integer(write_addr) mod depth) <= memory_write_data;
      end if;
    end process;
  end block;

end architecture;
