import math

# Constants
ADDRESS_BITS = 42
EXTRA_TAG_BITS = 5
MAXDATAN = 512
MAXSUBARRAYS = 1048576
MAXDATASPD = 256
MAX_COL_MUX = 256

ROUTER_TYPES = 3
WIRE_TYPES = 6

Cpolywire = 0.0

VTHFA1 = 0.452
VTHFA2 = 0.304
VTHFA3 = 0.420
VTHFA4 = 0.413
VTHFA5 = 0.405
VTHFA6 = 0.452
VSINV = 0.452
VTHCOMPINV = 0.437
VTHMUXNAND = 0.548
VTHEVALINV = 0.452
VTHSENSEEXTDRV = 0.438

WmuxdrvNANDn = 0.0
WmuxdrvNANDp = 0.0

BIGNUM = 1e30
INF = 9999999

RISE = 1
FALL = 0
NCH = 1
PCH = 0

EPSILON = 0.5
EPSILON2 = 0.1
EPSILON3 = 0.6

MINSUBARRAYROWS = 16
MAXSUBARRAYROWS = 262144
MINSUBARRAYCOLS = 2
MAXSUBARRAYCOLS = 262144

INV = 0
NOR = 1
NAND = 2

NUMBER_TECH_FLAVORS = 4
NUMBER_INTERCONNECT_PROJECTION_TYPES = 2
NUMBER_WIRE_TYPES = 4
NUMBER_TSV_TYPES = 3

dram_cell_tech_flavor = 3

VBITSENSEMIN = 0.08

fopt = 4.0

INPUT_WIRE_TO_INPUT_GATE_CAP_RATIO = 0
BUFFER_SEPARATION_LENGTH_MULTIPLIER = 1
NUMBER_MATS_PER_REDUNDANT_MAT = 8

NUMBER_STACKED_DIE_LAYERS = 1

STACKED_DIE_LAYER_ALLOTED_AREA_mm2 = 0
MAX_PERCENT_AWAY_FROM_ALLOTED_AREA = 50
MIN_AREA_EFFICIENCY = 20

STACKED_DIE_LAYER_ASPECT_RATIO = 1
MAX_PERCENT_AWAY_FROM_ASPECT_RATIO = 101

TARGET_CYCLE_TIME_ns = 1000000000

NUMBER_PIPELINE_STAGES = 4

LENGTH_INTERCONNECT_FROM_BANK_TO_CROSSBAR = 0

IS_CROSSBAR = 0
NUMBER_INPUT_PORTS_CROSSBAR = 8
NUMBER_OUTPUT_PORTS_CROSSBAR = 8
NUMBER_SIGNALS_PER_PORT_CROSSBAR = 256

MAT_LEAKAGE_REDUCTION_DUE_TO_SLEEP_TRANSISTORS_FACTOR = 1
LEAKAGE_REDUCTION_DUE_TO_LONG_CHANNEL_HP_TRANSISTORS_FACTOR = 1

PAGE_MODE = 0

MAIN_MEM_PER_CHIP_STANDBY_CURRENT_mA = 60

VDD_STORAGE_LOSS_FRACTION_WORST = 0.125
CU_RESISTIVITY = 0.022
BULK_CU_RESISTIVITY = 0.018
PERMITTIVITY_FREE_SPACE = 8.854e-18

sram_num_cells_wl_stitching_ = 16
dram_num_cells_wl_stitching_ = 64
comm_dram_num_cells_wl_stitching_ = 256
num_bits_per_ecc_b_ = 8.0

bit_to_byte = 8.0

MAX_NUMBER_GATES_STAGE = 20
MAX_NUMBER_HTREE_NODES = 20
NAND2_LEAK_STACK_FACTOR = 0.2
NAND3_LEAK_STACK_FACTOR = 0.2
NOR2_LEAK_STACK_FACTOR = 0.2
INV_LEAK_STACK_FACTOR = 0.5
MAX_NUMBER_ARRAY_PARTITIONS = 1000000

class RamCellTechTypeNum:
    itrs_hp = 0
    itrs_lstp = 1
    itrs_lop = 2
    lp_dram = 3
    comm_dram = 4

itrs_hp = 0
itrs_lstp = 1
itrs_lop = 2
lp_dram = 3
comm_dram = 4

pppm = [1, 1, 1, 1]
pppm_lkg = [0, 1, 1, 0]
pppm_dyn = [1, 0, 0, 0]
pppm_Isub = [0, 1, 0, 0]
pppm_Ig = [0, 0, 1, 0]
pppm_sc = [0, 0, 0, 1]

nmos = "nmos"
pmos = "pmos"
inv = "inv"
nand = "nand"
nor = "nor"
tri = "tri"
tg = "tg"

Ilinear_to_Isat_ratio = 2.0

# Define helper functions for min and max
def MAX(a, b):
    return a if a > b else b

def MIN(a, b):
    return a if a < b else b