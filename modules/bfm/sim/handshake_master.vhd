-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Toggle the 'valid' signal based on probabilities set via generics.
-- This realizes a handshake master with jitter that is compliant with the AXI-Stream standard.
-- According to the standard, 'valid' may be lowered only after a transaction.
--
-- This BFM can be more convenient to use than the VUnit 'axi_stream_master' BFM in some cases.
-- Specifically when the data is not an SLV, but instead a record. When using VUnit BFMs we would need
-- to have conversion functions to and from SLV. When using this BFM instead for the handshaking,
-- the data can be handled as records in the testbench with no conversion necessary.
-- Using this simple BFM is also significantly faster.
-- A drawback of this BFM is that the tesbench code becomes more "RTL"-like compared to the VUnit
-- BFM, which results in more "high level" code.
-- See the testbench 'tb_handshake_bfm' for example usage.
--
-- This entity can also optionally perform protocol checking on the handshaking data interface.
-- This will verify that the AXI-Stream standard is followed.
-- Assign the 'data' port and set the correct 'data_width' generic in order to use this.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
context vunit_lib.vc_context;
context vunit_lib.vunit_context;

library osvvm;
use osvvm.RandomPkg.RandomPType;


entity handshake_master is
  generic (
    stall_probability_percent : natural;
    max_stall_cycles : natural;
    -- Is also used for the random seed
    logger_prefix : string := "";
    -- Assign a non-zero value in order to use the 'data' port for protocol checking
    data_width : natural := 0
  );
  port (
    clk : in std_logic;
    --
    -- Set by testbench when there is data available to push
    data_is_valid : in std_logic;
    --
    data_ready : in std_logic;
    data_valid : out std_logic := '0';
    -- Must set 'data_width' generic in order to use this for protocol checking
    data : in std_logic_vector(data_width - 1 downto 0) := (others => '0')
  );
end entity;

architecture a of handshake_master is

  signal stall_data : std_logic := '1';

begin

  data_valid <= data_is_valid and not stall_data;


  ------------------------------------------------------------------------------
  toggle_stall : process
    variable rnd : RandomPType;
  begin
    assert stall_probability_percent >= 0 and stall_probability_percent <= 100
      report "Invalid percentage: " & to_string(stall_probability_percent);

    rnd.InitSeed(rnd'instance_name & logger_prefix);

    loop
      if rnd.RandInt(1, 100) > (100 - stall_probability_percent) then
        stall_data <= '1';

        for low_cycles in 1 to rnd.FavorSmall(1, max_stall_cycles) loop
          wait until rising_edge(clk);
        end loop;
      end if;

      stall_data <= '0';
      wait until (data_ready and data_valid) = '1' and rising_edge(clk);
    end loop;
  end process;


  ------------------------------------------------------------------------------
  axi_stream_protocol_checker_inst : entity vunit_lib.axi_stream_protocol_checker
    generic map (
      protocol_checker => new_axi_stream_protocol_checker(
        logger => get_logger(logger_prefix & "handshake_master"),
        data_length => data'length
      )
    )
    port map (
      aclk => clk,
      tvalid => data_valid,
      tready => data_ready,
      tdata => data
    );

end architecture;
