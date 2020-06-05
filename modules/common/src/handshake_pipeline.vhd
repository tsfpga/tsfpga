-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- @brief Handshake pipeline, aka skid-aside buffer, aka skid buffer
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;


entity handshake_pipeline is
  generic (
    data_width : integer
  );
  port (
    clk : in std_logic;
    --
    input_ready : out std_logic := '1';
    input_valid : in std_logic;
    input_last : in std_logic := '-';
    input_data : in std_logic_vector(data_width - 1 downto 0);
    --
    output_ready : in std_logic;
    output_valid : out std_logic := '0';
    output_last : out std_logic;
    output_data : out std_logic_vector(data_width - 1 downto 0)
  );
end entity;

architecture a of handshake_pipeline is

  type state_t is (wait_for_input_valid, full_throughput, wait_for_output_ready);
  signal state : state_t := wait_for_input_valid;

  signal input_data_skid : std_logic_vector(input_data'range);
  signal input_last_skid : std_logic;

begin

  main : process
  begin
    wait until rising_edge(clk);

    case state is
      when wait_for_input_valid =>
        if input_valid then
          -- input_ready is '1', so if we get here an input transaction has occured
          output_valid <= '1';
          output_data <= input_data;
          output_last <= input_last;
          state <= full_throughput;
        end if;

      when full_throughput =>
        -- input_ready and output_valid are always '1' in this state

        if input_valid and output_ready then
          -- Input and output transactions have occured. Update data register.
          output_data <= input_data;
          output_last <= input_last;
        elsif output_ready then
          -- Output transaction has occured, but no input transaction
          output_valid <= '0';
          state <= wait_for_input_valid;
        elsif input_valid then
          -- Input transaction has occured, but no output transaction
          -- Values from input transaction will be saved in the skid-aside buffer while we wait for output_ready.
          input_ready <= '0';
          state <= wait_for_output_ready;
        end if;

      when wait_for_output_ready =>
        if output_ready then
          -- output_valid is '1', so if we get here an output transaction has occured
          input_ready <= '1';
          output_data <= input_data_skid;
          output_last <= input_last_skid;
          state <= full_throughput;
        end if;
    end case;

    if input_ready and input_valid then
      input_data_skid <= input_data;
      input_last_skid <= input_last;
    end if;
  end process;

end architecture;
