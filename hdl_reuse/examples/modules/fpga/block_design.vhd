library ieee;
use ieee.std_logic_1164.all;

library axi;
use axi.axi_pkg.all;

library common;
use common.common_pkg.all;


entity block_design is
  port (
    clk_hpm0 : in std_logic;
    hpm0_m2s : out axi_m2s_t;
    hpm0_s2m : in axi_s2m_t;

    clk_hp0 : in std_logic;
    hp0_m2s : in axi_m2s_t;
    hp0_s2m : out axi_s2m_t;

    pl_clk0 : out std_logic
  );
end entity;

architecture a of block_design is

begin

  block_design_inst : if in_simulation generate
    block_design_mock_inst : entity work.block_design_mock
    port map (
      clk_hpm0 => clk_hpm0,
      hpm0_m2s => hpm0_m2s,
      hpm0_s2m => hpm0_s2m,

      pl_clk0 => pl_clk0
    );

  else generate

    -- Inst real block_design_wrapper from Vivado

  end generate;

end architecture;
