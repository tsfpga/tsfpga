# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Strategy 1 is implementation defaults, which is the default when
# omitting the -strategy flag to create_run.
set vivado_strategies [list Performance_ExplorePostRoutePhysOpt \
Area_Explore \
Congestion_SpreadLogic_medium \
Congestion_SSI_SpreadLogic_high \
Performance_WLBlockPlacementFanoutOpt \
Flow_RuntimeOptimized \
Area_ExploreSequential \
Power_ExploreArea \
Area_ExploreWithRemap \
Flow_Quick \
Flow_RunPhysOpt \
Performance_ExtraTimingOpt \
Power_DefaultOpt \
Performance_NetDelay_low \
Performance_EarlyBlockPlacement \
Performance_Auto_3 \
Performance_WLBlockPlacement \
Performance_ExploreWithRemap \
Flow_RunPostRoutePhysOpt \
Congestion_SSI_SpreadLogic_low \
Performance_Auto_1 \
Performance_Explore \
Performance_BalanceSLRs \
Performance_Retiming \
Performance_Auto_2 \
Performance_HighUtilSLRs \
Performance_BalanceSLLs \
Congestion_SpreadLogic_high \
Performance_NetDelay_high \
Performance_SpreadSLLs \
Performance_RefinePlacement \
Congestion_SpreadLogic_low]

set idx 1

create_run impl_explore_$idx -parent_run synth_1 -flow {Vivado Implementation 2021}

foreach strategy $vivado_strategies {
  incr idx
  create_run impl_explore_$idx -parent_run synth_1 -flow {Vivado Implementation 2021} -strategy $strategy
}
