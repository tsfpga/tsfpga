# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

set first_resync_register [get_cells data_in_p1_reg]

set_false_path -setup -hold -to ${first_resync_register}
