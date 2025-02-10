import math
from enum import IntEnum

# ----------------------------
# Direct translation of const.h
# ----------------------------

# 1) Basic integer constants
ADDRESS_BITS          = 42
EXTRA_TAG_BITS        = 5

MAXDATAN              = 512       # maximum for Ndwl and Ndbl
MAXSUBARRAYS          = 1048576   # maximum subarrays for data and tag arrays
MAXDATASPD            = 256       # maximum for Nspd
MAX_COL_MUX           = 256

# 2) Misc constants
ROUTER_TYPES          = 3
WIRE_TYPES            = 6
Cpolywire             = 0.0

# Threshold voltages (as a proportion of Vdd)
VTHFA1                = 0.452
VTHFA2                = 0.304
VTHFA3                = 0.420
VTHFA4                = 0.413
VTHFA5                = 0.405
VTHFA6                = 0.452
VSINV                 = 0.452
VTHCOMPINV            = 0.437
VTHMUXNAND            = 0.548  # TODO : this constant must be revisited
VTHEVALINV            = 0.452
VTHSENSEEXTDRV        = 0.438

# WmuxdrvNANDn/WmuxdrvNANDp are set to 0 in the original code
WmuxdrvNANDn          = 0.0
WmuxdrvNANDp          = 0.0

# 3) BIGNUM, INF, macros for MAX, MIN
BIGNUM                = 1e30
INF                   = 9999999

def MAX(a, b):
    # return a if a > b else b
    return 0.5 * (a + b + abs(a - b))

def MIN(a, b):
    # return a if a < b else b
    return 0.5 * (a + b - abs(a - b))

# 4) Constants used in the Horowitz model / logic
RISE                  = 1
FALL                  = 0
NCH                   = 1
PCH                   = 0

# 5) Epsilon definitions
EPSILON               = 0.5
EPSILON2              = 0.1
EPSILON3              = 0.6

# 6) Limits on subarray rows/cols
MINSUBARRAYROWS       = 16
MAXSUBARRAYROWS       = 262144
MINSUBARRAYCOLS       = 2
MAXSUBARRAYCOLS       = 262144

# 7) Gate types
INV                   = 0
NOR                   = 1
NAND                  = 2

NMOS                  = 3
PMOS                  = 4

TRI                   = 5
TG                    = 6

# CHECK
inv                   = 0
nor                   = 1
nand                  = 2

nmos                  = 3
pmos                  = 4

tri                   = 5
tg                    = 6


# 8) Various enumerations or numeric definitions
NUMBER_TECH_FLAVORS                   = 4
NUMBER_INTERCONNECT_PROJECTION_TYPES  = 2  # 0=aggressive, 1=conservative
NUMBER_WIRE_TYPES                     = 4  # local, semi-global, global...
NUMBER_TSV_TYPES                      = 3  # 0=ITRS fine, 1=industrial large, 2=TBD
dram_cell_tech_flavor                 = 3

# 9) Sense voltage
VBITSENSEMIN          = 0.08

# 10) fopt
fopt                  = 4.0

# 11) Additional constants
INPUT_WIRE_TO_INPUT_GATE_CAP_RATIO          = 0
BUFFER_SEPARATION_LENGTH_MULTIPLIER         = 1
NUMBER_MATS_PER_REDUNDANT_MAT               = 8
NUMBER_STACKED_DIE_LAYERS                   = 1
STACKED_DIE_LAYER_ALLOTED_AREA_mm2          = 0
MAX_PERCENT_AWAY_FROM_ALLOTED_AREA          = 50
MIN_AREA_EFFICIENCY                         = 20
STACKED_DIE_LAYER_ASPECT_RATIO              = 1
MAX_PERCENT_AWAY_FROM_ASPECT_RATIO          = 101
TARGET_CYCLE_TIME_ns                        = 1000000000
NUMBER_PIPELINE_STAGES                      = 4
LENGTH_INTERCONNECT_FROM_BANK_TO_CROSSBAR   = 0
IS_CROSSBAR                                 = 0
NUMBER_INPUT_PORTS_CROSSBAR                 = 8
NUMBER_OUTPUT_PORTS_CROSSBAR                = 8
NUMBER_SIGNALS_PER_PORT_CROSSBAR            = 256

MAT_LEAKAGE_REDUCTION_DUE_TO_SLEEP_TRANSISTORS_FACTOR    = 1
LEAKAGE_REDUCTION_DUE_TO_LONG_CHANNEL_HP_TRANSISTORS_FACTOR = 1
PAGE_MODE                                     = 0
MAIN_MEM_PER_CHIP_STANDBY_CURRENT_mA          = 60

# 12) Resistivity / etc.
VDD_STORAGE_LOSS_FRACTION_WORST              = 0.125
CU_RESISTIVITY                               = 0.022  # ohm-micron
BULK_CU_RESISTIVITY                          = 0.018  # ohm-micron
PERMITTIVITY_FREE_SPACE                      = 8.854e-18  # F/micron

# 13) WL stitching
sram_num_cells_wl_stitching_                 = 16
dram_num_cells_wl_stitching_                 = 64
comm_dram_num_cells_wl_stitching_            = 256
num_bits_per_ecc_b_                          = 8.0

bit_to_byte                                  = 8.0

MAX_NUMBER_GATES_STAGE                       = 20
MAX_NUMBER_HTREE_NODES                       = 20
NAND2_LEAK_STACK_FACTOR                      = 0.2
NAND3_LEAK_STACK_FACTOR                      = 0.2
NOR2_LEAK_STACK_FACTOR                       = 0.2
INV_LEAK_STACK_FACTOR                        = 0.5
MAX_NUMBER_ARRAY_PARTITIONS                  = 1000000

# 14) Enumerations:
class ram_cell_tech_type_num(IntEnum):
    itrs_hp   = 0
    itrs_lstp = 1
    itrs_lop  = 2
    lp_dram   = 3
    comm_dram = 4

# CHECK CONST
itrs_hp   = 0
itrs_lstp = 1
itrs_lop  = 2
lp_dram   = 3
comm_dram = 4

# 15) Arrays pppm
pppm       = (1.0, 1.0, 1.0, 1.0)
pppm_lkg   = (0.0, 1.0, 1.0, 0.0)
pppm_dyn   = (1.0, 0.0, 0.0, 0.0)
pppm_Isub  = (0.0, 1.0, 0.0, 0.0)
pppm_Ig    = (0.0, 0.0, 1.0, 0.0)
pppm_sc    = (0.0, 0.0, 0.0, 1.0)

Ilinear_to_Isat_ratio = 2.0

# ERROR: Check added here from basic cricuit Wire Placement
class Wire_placement(IntEnum):
    outside_mat = 0
    inside_mat = 1
    local_wires = 2
    
outside_mat = 0
inside_mat = 1
local_wires = 2

# htree2:
class Htree_type(IntEnum):
    Add_htree       = 0
    Data_in_htree   = 1
    Data_out_htree  = 2
    Search_in_htree = 3
    Search_out_htree= 4

Add_htree       = 0
Data_in_htree   = 1
Data_out_htree  = 2
Search_in_htree = 3
Search_out_htree= 4

# memory_bus
class Memorybus_type(IntEnum):
    Row_add_path = 0
    Col_add_path = 1
    Data_path    = 2
    # in_network  = 3  # Commented out like in the original C++ code
    # out_network = 4  # Commented out like in the original C++ code

Row_add_path = 0
Col_add_path = 1
Data_path    = 2

# crossbar
ASPECT_THRESHOLD = .8
ADJ = 1 # CHECK IF ERROR