"""
io.py
Direct Python translation of partial io.{h,cc} from CACTI code.
This snippet provides logical and functional equivalency.
"""

import sys
import math

#
# You would import or define the following classes and enumerations
# based on the rest of your Python CACTI codebase:
#
#   from cacti_interface import (
#       powerComponents, powerDef, uca_org_t, InputParameter,
#       cacti_interface_from_inputparam, init_tech_params, Wire, solve, solve_memcad
#       # or whichever Python modules hold these classes/functions
#   )
#
# Here, for completeness of the example, we define placeholders and
# stubs to replicate the code snippet from io.cc exactly.
#

# Enums from "cacti_interface.h" or "parameter.h" or "const.h" (simplified):
class Wire_type:
    Global_ = 0
    Global_5 = 1
    Global_10 = 2
    Global_20 = 3
    Global_30 = 4
    Low_swing = 5
    Semi_global = 6
    Full_swing = 7
    Transmission = 8
    Optical = 9
    Invalid_wtype = 10

class Mem_IO_type:
    DDR3 = 0
    DDR4 = 1
    LPDDR2 = 2
    WideIO = 3
    Low_Swing_Diff = 4
    Serial = 5

class Mem_state:
    READ = 0
    WRITE = 1
    IDLE = 2
    SLEEP = 3

class Mem_DIMM:
    UDIMM = 0
    RDIMM = 1
    LRDIMM = 2

class Mem_ECC:
    NO_ECC = 0
    SECDED = 1
    CHIP_KILL = 2

class DIMM_Model:
    JUST_UDIMM = 0
    JUST_RDIMM = 1
    JUST_LRDIMM = 2
    ALL = 3

class MemCad_metrics:
    Bandwidth = 0
    Energy = 1
    Cost = 2

# Global pointer (mimicking "g_ip")
g_ip = None


# The partial stubs for other objects or methods used within io.cc:
def init_tech_params(feature_size_um, is_tag):
    """
    Stub for technology initialization logic.
    (Equivalent to the real 'init_tech_params' in CACTI.)
    """
    pass

class Wire:
    """
    Stub for the Wire logic from CACTI.
    The constructor or other methods might do the needed wire initialization.
    """
    def __init__(self):
        # in C++: Wire winit; // Do not delete this line. It initializes wires.
        pass

class TSV:
    """
    Stub for TSV (through-silicon-via).
    """
    def __init__(self, tsv_type):
        pass

    def print_TSV(self):
        pass

def solve(fin_res):
    """
    Stub for the 'solve' function in CACTI which does the main memory/circuit solution.
    """
    # In real code, it would fill 'fin_res' with computed results.
    fin_res.valid = True

def solve_memcad(memcad_params):
    """
    Stub for 'solve_memcad' used at the end of cacti_interface() in the partial snippet.
    """
    pass

class IOTechParam:
    """
    Stub class in place of 'IOTechParam iot(g_ip, ...)' used in cacti_interface.
    """
    def __init__(self, local_ip, io_type, num_mem_dq, mem_data_width, num_dq, dram_dimm, dummy, bus_freq):
        pass

class Extio:
    """
    Stub class in place of the extio usage in cacti_interface.
    """
    def __init__(self, iot):
        pass

    def extio_area(self):
        pass

    def extio_eye(self):
        pass

    def extio_power_dynamic(self):
        pass

    def extio_power_phy(self):
        pass

    def extio_power_term(self):
        pass

# The data structures for power computations, as in cacti_interface or basic_circuit:
class powerComponents:
    def __init__(self, dynamic=0.0, leakage=0.0, gate_leakage=0.0, short_circuit=0.0, longer_channel_leakage=0.0):
        self.dynamic = dynamic
        self.leakage = leakage
        self.gate_leakage = gate_leakage
        self.short_circuit = short_circuit
        self.longer_channel_leakage = longer_channel_leakage

    def __add__(self, other):
        z = powerComponents()
        z.dynamic = self.dynamic + other.dynamic
        z.leakage = self.leakage + other.leakage
        z.gate_leakage = self.gate_leakage + other.gate_leakage
        z.short_circuit = self.short_circuit + other.short_circuit
        z.longer_channel_leakage = self.longer_channel_leakage + other.longer_channel_leakage
        return z

    def __mul__(self, factor):
        """
        The snippet in io.cc has:
            powerComponents operator*(const powerComponents & x, double const * const y)
        that uses y[0..3 or 4].
        For direct equivalency, we show a separate function or a 4-element factor approach.

        But if we assume a simple scalar multiply, do the standard approach:
        """
        # You can do normal scalar multiply here. 
        # If you want an array-based approach (like the snippet), define a separate function or handle it:
        if isinstance(factor, float) or isinstance(factor, int):
            # Simple scalar multiply
            z = powerComponents()
            z.dynamic = self.dynamic * factor
            z.leakage = self.leakage * factor
            z.gate_leakage = self.gate_leakage * factor
            z.short_circuit = self.short_circuit * factor
            z.longer_channel_leakage = self.longer_channel_leakage * factor
            return z

        # If factor is a list or tuple with the same indexing used in the snippet:
        # z.dynamic = x.dynamic*y[0]
        # z.leakage = x.leakage*y[1]
        # z.gate_leakage  = x.gate_leakage*y[2]
        # z.short_circuit = x.short_circuit*y[3]
        # z.longer_channel_leakage = x.longer_channel_leakage*y[1]
        if isinstance(factor, (list, tuple)):
            z = powerComponents()
            z.dynamic = self.dynamic * factor[0]
            z.leakage = self.leakage * factor[1]
            z.gate_leakage = self.gate_leakage * factor[2]
            z.short_circuit = self.short_circuit * factor[3]
            # longer_channel_leakage uses factor[1] too
            z.longer_channel_leakage = self.longer_channel_leakage * factor[1]
            return z

        # otherwise fallback
        raise ValueError("Unsupported multiplication factor")

class powerDef:
    def __init__(self):
        self.readOp = powerComponents()
        self.writeOp = powerComponents()
        self.searchOp = powerComponents()

    def __add__(self, other):
        z = powerDef()
        z.readOp   = self.readOp + other.readOp
        z.writeOp  = self.writeOp + other.writeOp
        z.searchOp = self.searchOp + other.searchOp
        return z

    def __mul__(self, factor):
        # same logic as above with the factor array approach
        if isinstance(factor, float) or isinstance(factor, int):
            z = powerDef()
            z.readOp   = self.readOp   * factor
            z.writeOp  = self.writeOp  * factor
            z.searchOp = self.searchOp * factor
            return z

        if isinstance(factor, (list, tuple)):
            z = powerDef()
            z.readOp   = self.readOp   * factor
            z.writeOp  = self.writeOp  * factor
            z.searchOp = self.searchOp * factor
            return z

        raise ValueError("Unsupported multiplication factor")

class uca_org_t:
    """
    Python version of the c++ struct/class uca_org_t
    This holds final results from the CACTI run.
    """
    def __init__(self):
        self.valid = False
        # In c++ code there are many more fields; omitted for brevity.
        # Keep only a few to match usage in the snippet.


#
# The partial InputParameter Python version, matching the snippet from io.cc
#
class InputParameter:
    def __init__(self):
        # Default constructor logic from snippet:
        self.array_power_gated = False
        self.bitline_floating = False
        self.wl_power_gated = False
        self.cl_power_gated = False
        self.interconect_power_gated = False
        self.power_gating = False
        self.cl_vertical = True

        # The rest of the fields (initialized as in the snippet):
        self.cache_sz = 0
        self.page_sz_bits = 0
        self.burst_len = 0
        self.int_prefetch_w = 0
        self.line_sz = 0
        self.assoc = 0
        self.num_rw_ports = 0
        self.num_rd_ports = 0
        self.num_wr_ports = 0
        self.num_se_rd_ports = 0
        self.num_search_ports = 0
        self.nbanks = 1
        self.F_sz_um = 0.0
        self.F_sz_nm = 0.0
        self.out_w = 0
        self.temp = 300
        self.is_cache = False
        self.is_main_mem = False
        self.is_3d_mem = False
        self.print_detail_debug = False
        self.burst_depth = 0
        self.io_width = 0
        self.sys_freq_MHz = 0
        self.num_die_3d = 1
        self.partition_gran = 1
        self.TSV_proj_type = 0
        self.num_tier_row_sprd = 1  # forced by snippet
        self.num_tier_col_sprd = 1  # forced by snippet
        self.specific_tag = False
        self.tag_w = 42
        self.access_mode = 0
        self.data_arr_ram_cell_tech_type = 0
        self.data_arr_peri_global_tech_type = 0
        self.tag_arr_ram_cell_tech_type = 0
        self.tag_arr_peri_global_tech_type = 0
        self.delay_wt = 0
        self.dynamic_power_wt = 0
        self.leakage_power_wt = 0
        self.cycle_time_wt = 0
        self.area_wt = 0
        self.delay_dev = 0
        self.dynamic_power_dev = 0
        self.leakage_power_dev = 0
        self.cycle_time_dev = 0
        self.area_dev = 0
        self.ed = 0
        self.delay_wt_nuca = 0
        self.dynamic_power_wt_nuca = 0
        self.leakage_power_wt_nuca = 0
        self.cycle_time_wt_nuca = 0
        self.area_wt_nuca = 0
        self.delay_dev_nuca = 0
        self.dynamic_power_dev_nuca = 0
        self.leakage_power_dev_nuca = 0
        self.cycle_time_dev_nuca = 0
        self.area_dev_nuca = 0
        self.nuca = 0
        self.nuca_bank_count = 0
        self.force_nuca_bank = 0
        self.wire_is_mat_type = 0
        self.wire_os_mat_type = 0
        self.ic_proj_type = 0
        self.force_wiretype = 0
        self.wt = Wire_type.Global_
        self.cores = 1
        self.cache_level = 0
        self.print_detail = 0
        self.add_ecc_b_ = False
        self.array_power_gated = False
        self.bitline_floating = False
        self.wl_power_gated = False
        self.cl_power_gated = False
        self.interconect_power_gated = False
        self.perfloss = 0.0
        self.print_input_args = False
        self.force_cache_config = False
        self.ndbl = 0
        self.ndwl = 0
        self.nspd = 0
        self.ndsam1 = 0
        self.ndsam2 = 0
        self.ndcm = 0

        # Off-chip interconnect:
        self.io_type = Mem_IO_type.DDR3
        self.iostate = Mem_state.IDLE
        self.addr_timing = 0.0
        self.dram_ecc = Mem_ECC.NO_ECC
        self.dram_dimm = Mem_DIMM.UDIMM
        self.bus_bw = 0.0
        self.duty_cycle = 0.0
        self.mem_density = 0.0
        self.activity_dq = 0.0
        self.activity_ca = 0.0
        self.bus_freq = 0.0
        self.num_dq = 0
        self.num_dqs = 0
        self.num_ca = 0
        self.num_clk = 0
        self.num_mem_dq = 0
        self.mem_data_width = 0

        # MemCad
        self.num_bobs = 0
        self.capacity = 0
        self.num_channels_per_bob = 0
        self.first_metric = MemCad_metrics.Bandwidth
        self.second_metric = MemCad_metrics.Energy
        self.third_metric = MemCad_metrics.Cost
        self.dimm_model = DIMM_Model.ALL
        self.low_power_permitted = False
        self.load = 0.0
        self.row_buffer_hit_rate = 0.0
        self.rd_2_wr_ratio = 0.0
        self.same_bw_in_bob = False
        self.mirror_in_bob = False
        self.total_power = False
        self.verbose = False

        # Derived fields
        self.rpters_in_htree = True
        self.fully_assoc = False
        self.pure_cam = False
        self.pure_ram = False

        # Additional
        self.fast_access = True
        self.tag_assoc = 0
        self.data_assoc = 0
        self.is_seq_acc = False
        self.nsets = 0
        self.block_sz = 0

    def parse_cfg(self, in_file: str):
        """
        Python equivalent of:
           void InputParameter::parse_cfg(const string & in_file)
        scanning each line for parameters.
        """
        try:
            fp = open(in_file, "r")
        except FileNotFoundError:
            print(f"{in_file} is missing!")
            sys.exit(1)

        lines = fp.read().splitlines()
        fp.close()

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Because the snippet uses "strncmp" and "sscanf", replicate carefully:
            # We'll do a series of if line.startswith(...) then parse with splitted tokens:

            # The snippet has many checks. We'll replicate them:

            if line.startswith("-size"):
                # e.g. "-size XsomeprefixY <num>"
                # Then do: cache_sz = <num>
                tokens = line.split()
                # example: ["-size", "(GB)", "8"] or something
                # The snippet: sscanf(line, "-size %[(:-~)*]%u", jk, &(cache_sz));
                # We'll do a simpler approach: get last token:
                self.cache_sz = int(tokens[-1])
                if self.print_detail_debug:
                    print("cache size:", self.cache_sz, "GB")
                continue

            if line.startswith("-page size"):
                tokens = line.split()
                self.page_sz_bits = int(tokens[-1])
                continue

            if line.startswith("-burst length"):
                tokens = line.split()
                self.burst_len = int(tokens[-1])
                continue

            if line.startswith("-internal prefetch width"):
                tokens = line.split()
                self.int_prefetch_w = int(tokens[-1])
                continue

            if line.startswith("-block size"):
                # e.g. "-block size (bytes) 64"
                tokens = line.split()
                self.line_sz = int(tokens[-1])
                continue

            if line.startswith("-associativity"):
                tokens = line.split()
                self.assoc = int(tokens[-1])
                continue

            if line.startswith("-read-write"):
                tokens = line.split()
                self.num_rw_ports = int(tokens[-1])
                continue

            if line.startswith("-exclusive read"):
                tokens = line.split()
                self.num_rd_ports = int(tokens[-1])
                continue

            if line.startswith("-exclusive write"):
                tokens = line.split()
                self.num_wr_ports = int(tokens[-1])
                continue

            if line.startswith("-single ended"):
                tokens = line.split()
                self.num_se_rd_ports = int(tokens[-1])
                continue

            if line.startswith("-search port"):
                tokens = line.split()
                self.num_search_ports = int(tokens[-1])
                continue

            if line.startswith("-UCA bank"):
                tokens = line.split()
                self.nbanks = int(tokens[-1])
                continue

            if line.startswith("-technology"):
                # -technology (u) ...
                tokens = line.split()
                val = float(tokens[-1])
                self.F_sz_um = val
                self.F_sz_nm = self.F_sz_um*1000
                continue

            if line.startswith("-output/input"):
                tokens = line.split()
                self.out_w = int(tokens[-1])
                continue

            if line.startswith("-operating temperature"):
                tokens = line.split()
                self.temp = int(tokens[-1])
                continue

            if line.startswith("-cache type"):
                # parse out the quoted string
                # -cache type "<string>"
                # snippet checks for "cache", "main memory", "3D memory or 2D main memory", "cam", "ram"
                # We'll do a simpler parse:
                # e.g. line = -cache type "3D memory or 2D main memory"
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()

                if "cache" in temp_var:
                    self.is_cache = True
                else:
                    self.is_cache = False

                if "main memory" in temp_var:
                    self.is_main_mem = True
                else:
                    self.is_main_mem = False

                if "3D memory or 2D main memory" in temp_var:
                    self.is_3d_mem = True
                    self.is_main_mem = True
                else:
                    self.is_3d_mem = False

                if "cam" in temp_var:
                    self.pure_cam = True
                else:
                    self.pure_cam = False

                if "ram" in temp_var:
                    self.pure_ram = True
                else:
                    # note snippet sets pure_ram = false unless is_main_mem is true
                    if not self.is_main_mem:
                        self.pure_ram = False
                    else:
                        self.pure_ram = True

                continue

            if line.startswith("-print option"):
                # -print option "<string>"
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if "debug detail" in temp_var:
                    self.print_detail_debug = True
                else:
                    self.print_detail_debug = False
                continue

            if line.startswith("-burst depth"):
                tokens = line.split()
                self.burst_depth = int(tokens[-1])
                continue

            if line.startswith("-IO width"):
                tokens = line.split()
                self.io_width = int(tokens[-1])
                continue

            if line.startswith("-system frequency"):
                tokens = line.split()
                self.sys_freq_MHz = int(tokens[-1])
                if self.print_detail_debug:
                    print("system frequency:", self.sys_freq_MHz)
                continue

            if line.startswith("-stacked die"):
                tokens = line.split()
                self.num_die_3d = int(tokens[-1])
                if self.print_detail_debug:
                    print("num_die_3d:", self.num_die_3d)
                continue

            if line.startswith("-partitioning granularity"):
                tokens = line.split()
                self.partition_gran = int(tokens[-1])
                if self.print_detail_debug:
                    print("partitioning granularity:", self.partition_gran)
                continue

            if line.startswith("-TSV projection"):
                tokens = line.split()
                self.TSV_proj_type = int(tokens[-1])
                if self.print_detail_debug:
                    print("TSV projection:", self.TSV_proj_type)
                continue

            if line.startswith("-tag size"):
                # -tag size "<string>"
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if "default" in temp_var:
                    self.specific_tag = False
                    self.tag_w = 42
                else:
                    self.specific_tag = True
                    # parse out the integer
                    # e.g. line might be: -tag size (b) 64
                    tokens = line.split()
                    self.tag_w = int(tokens[-1])
                continue

            if line.startswith("-access mode"):
                # parse out "fast", "sequential", or "normal"
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "fast":
                    self.access_mode = 2
                elif temp_var == "sequential":
                    self.access_mode = 1
                elif temp_var == "normal":
                    self.access_mode = 0
                else:
                    print("ERROR: Invalid access mode!")
                    sys.exit(1)
                continue

            if line.startswith("-Data array cell type"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "itrs-hp":
                    self.data_arr_ram_cell_tech_type = 0
                elif temp_var == "itrs-lstp":
                    self.data_arr_ram_cell_tech_type = 1
                elif temp_var == "itrs-lop":
                    self.data_arr_ram_cell_tech_type = 2
                elif temp_var == "lp-dram":
                    self.data_arr_ram_cell_tech_type = 3
                elif temp_var == "comm-dram":
                    self.data_arr_ram_cell_tech_type = 4
                else:
                    print("ERROR: Invalid type!")
                    sys.exit(1)
                continue

            if line.startswith("-Data array peripheral type"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "itrs-hp":
                    self.data_arr_peri_global_tech_type = 0
                elif temp_var == "itrs-lstp":
                    self.data_arr_peri_global_tech_type = 1
                elif temp_var == "itrs-lop":
                    self.data_arr_peri_global_tech_type = 2
                else:
                    print("ERROR: Invalid type!")
                    sys.exit(1)
                continue

            if line.startswith("-Tag array cell type"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "itrs-hp":
                    self.tag_arr_ram_cell_tech_type = 0
                elif temp_var == "itrs-lstp":
                    self.tag_arr_ram_cell_tech_type = 1
                elif temp_var == "itrs-lop":
                    self.tag_arr_ram_cell_tech_type = 2
                elif temp_var == "lp-dram":
                    self.tag_arr_ram_cell_tech_type = 3
                elif temp_var == "comm-dram":
                    self.tag_arr_ram_cell_tech_type = 4
                else:
                    print("ERROR: Invalid type!")
                    sys.exit(1)
                continue

            if line.startswith("-Tag array peripheral type"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "itrs-hp":
                    self.tag_arr_peri_global_tech_type = 0
                elif temp_var == "itrs-lstp":
                    self.tag_arr_peri_global_tech_type = 1
                elif temp_var == "itrs-lop":
                    self.tag_arr_peri_global_tech_type = 2
                else:
                    print("ERROR: Invalid type!")
                    sys.exit(1)
                continue

            if line.startswith("-design objective (weight delay, dynamic power, leakage power, cycle time, area)"):
                # example: -design objective (weight delay, dynamic power, leakage power, cycle time, area) 1:1:1:1:1
                # parse out the 5 integers
                # in snippet it does: sscanf(...) -> delay_wt, dynamic_power_wt, ...
                # we can do:
                parts = line.split()  # last part has "1:1:1:1:1"
                design_vals = parts[-1].split(":")
                self.delay_wt = int(design_vals[0])
                self.dynamic_power_wt = int(design_vals[1])
                self.leakage_power_wt = int(design_vals[2])
                self.cycle_time_wt = int(design_vals[3])
                self.area_wt = int(design_vals[4])
                continue

            if line.startswith("-deviate (delay, dynamic power, leakage power, cycle time, area)"):
                parts = line.split()  # last part might be "1:1:1:1:1"
                dev_vals = parts[-1].split(":")
                self.delay_dev = int(dev_vals[0])
                self.dynamic_power_dev = int(dev_vals[1])
                self.leakage_power_dev = int(dev_vals[2])
                self.cycle_time_dev = int(dev_vals[3])
                self.area_dev = int(dev_vals[4])
                continue

            if line.startswith("-Optimize"):
                # parse the quoted string "ED^2", "ED", or others
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "ED^2":
                    self.ed = 2
                elif temp_var == "ED":
                    self.ed = 1
                else:
                    self.ed = 0
                continue

            if line.startswith("-NUCAdesign objective (weight delay, dynamic power, leakage power, cycle time, area)"):
                parts = line.split()
                design_vals = parts[-1].split(":")
                self.delay_wt_nuca = int(design_vals[0])
                self.dynamic_power_wt_nuca = int(design_vals[1])
                self.leakage_power_wt_nuca = int(design_vals[2])
                self.cycle_time_wt_nuca = int(design_vals[3])
                self.area_wt_nuca = int(design_vals[4])
                continue

            if line.startswith("-NUCAdeviate (delay, dynamic power, leakage power, cycle time, area)"):
                parts = line.split()
                dev_vals = parts[-1].split(":")
                self.delay_dev_nuca = int(dev_vals[0])
                self.dynamic_power_dev_nuca = int(dev_vals[1])
                self.leakage_power_dev_nuca = int(dev_vals[2])
                self.cycle_time_dev_nuca = int(dev_vals[3])
                self.area_dev_nuca = int(dev_vals[4])
                continue

            if line.startswith("-Cache model"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "UCA":
                    self.nuca = 0
                else:
                    self.nuca = 1
                continue

            if line.startswith("-NUCA bank count"):
                tokens = line.split()
                self.nuca_bank_count = int(tokens[-1])
                if self.nuca_bank_count != 0:
                    self.force_nuca_bank = 1
                continue

            if line.startswith("-Wire inside mat"):
                # parse out "global", "local", or default
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "global":
                    self.wire_is_mat_type = 2
                elif temp_var == "local":
                    self.wire_is_mat_type = 0
                else:
                    self.wire_is_mat_type = 1
                continue

            if line.startswith("-Wire outside mat"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "global":
                    self.wire_os_mat_type = 2
                else:
                    self.wire_os_mat_type = 1
                continue

            if line.startswith("-Interconnect projection"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "aggressive":
                    self.ic_proj_type = 0
                else:
                    self.ic_proj_type = 1
                continue

            if line.startswith("-Wire signaling"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "default":
                    self.force_wiretype = 0
                    self.wt = Wire_type.Global_
                elif temp_var == "Global_10":
                    self.force_wiretype = 1
                    self.wt = Wire_type.Global_10
                elif temp_var == "Global_20":
                    self.force_wiretype = 1
                    self.wt = Wire_type.Global_20
                elif temp_var == "Global_30":
                    self.force_wiretype = 1
                    self.wt = Wire_type.Global_30
                elif temp_var == "Global_5":
                    self.force_wiretype = 1
                    self.wt = Wire_type.Global_5
                elif temp_var == "Global":
                    self.force_wiretype = 1
                    self.wt = Wire_type.Global_
                elif temp_var == "fullswing":
                    self.force_wiretype = 1
                    self.wt = Wire_type.Full_swing
                elif temp_var == "lowswing":
                    self.force_wiretype = 1
                    self.wt = Wire_type.Low_swing
                else:
                    print("Unknown wire type!")
                    sys.exit(1)
                continue

            if line.startswith("-Core count"):
                tokens = line.split()
                self.cores = int(tokens[-1])
                if self.cores > 16:
                    print("No. of cores should be less than 16!")
                continue

            if line.startswith("-Cache level"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "L2":
                    self.cache_level = 0
                else:
                    self.cache_level = 1
                continue

            if line.startswith("-Print level"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "DETAILED":
                    self.print_detail = 1
                else:
                    self.print_detail = 0
                continue

            if line.startswith("-Add ECC"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "true":
                    self.add_ecc_b_ = True
                else:
                    self.add_ecc_b_ = False
                continue

            if line.startswith("-CLDriver vertical"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "true":
                    self.cl_vertical = True
                else:
                    self.cl_vertical = False
                continue

            if line.startswith("-Array Power Gating"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "true":
                    self.array_power_gated = True
                else:
                    self.array_power_gated = False
                continue

            if line.startswith("-Bitline floating"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "true":
                    self.bitline_floating = True
                else:
                    self.bitline_floating = False
                continue

            if line.startswith("-WL Power Gating"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "true":
                    self.wl_power_gated = True
                else:
                    self.wl_power_gated = False
                continue

            if line.startswith("-CL Power Gating"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "true":
                    self.cl_power_gated = True
                else:
                    self.cl_power_gated = False
                continue

            if line.startswith("-Interconnect Power Gating"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "true":
                    self.interconect_power_gated = True
                else:
                    self.interconect_power_gated = False
                continue

            if line.startswith("-Power Gating Performance Loss"):
                tokens = line.split()
                self.perfloss = float(tokens[-1])
                continue

            if line.startswith("-Print input parameters"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "true":
                    self.print_input_args = True
                else:
                    self.print_input_args = False
                continue

            if line.startswith("-Force cache config"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "true":
                    self.force_cache_config = True
                else:
                    self.force_cache_config = False
                continue

            if line.startswith("-Ndbl"):
                tokens = line.split()
                self.ndbl = int(tokens[-1])
                continue

            if line.startswith("-Ndwl"):
                tokens = line.split()
                self.ndwl = int(tokens[-1])
                continue

            if line.startswith("-Nspd"):
                tokens = line.split()
                self.nspd = int(tokens[-1])
                continue

            if line.startswith("-Ndsam1"):
                tokens = line.split()
                self.ndsam1 = int(tokens[-1])
                continue

            if line.startswith("-Ndsam2"):
                tokens = line.split()
                self.ndsam2 = int(tokens[-1])
                continue

            if line.startswith("-Ndcm"):
                tokens = line.split()
                self.ndcm = int(tokens[-1])
                continue

            if line.startswith("-dram type"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "DDR3":
                    self.io_type = Mem_IO_type.DDR3
                elif temp_var == "DDR4":
                    self.io_type = Mem_IO_type.DDR4
                elif temp_var == "LPDDR2":
                    self.io_type = Mem_IO_type.LPDDR2
                elif temp_var == "WideIO":
                    self.io_type = Mem_IO_type.WideIO
                elif temp_var == "Low_Swing_Diff":
                    self.io_type = Mem_IO_type.Low_Swing_Diff
                elif temp_var == "Serial":
                    self.io_type = Mem_IO_type.Serial
                else:
                    print("Invalid Input for dram type!")
                    sys.exit(1)
                continue

            if line.startswith("-io state"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "READ":
                    self.iostate = Mem_state.READ
                elif temp_var == "WRITE":
                    self.iostate = Mem_state.WRITE
                elif temp_var == "IDLE":
                    self.iostate = Mem_state.IDLE
                elif temp_var == "SLEEP":
                    self.iostate = Mem_state.SLEEP
                else:
                    print("Invalid Input for io state!")
                    sys.exit(1)
                continue

            if line.startswith("-addr_timing"):
                tokens = line.split()
                self.addr_timing = float(tokens[-1])
                continue

            if line.startswith("-dram ecc"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "NO_ECC":
                    self.dram_ecc = Mem_ECC.NO_ECC
                elif temp_var == "SECDED":
                    self.dram_ecc = Mem_ECC.SECDED
                elif temp_var == "CHIP_KILL":
                    self.dram_ecc = Mem_ECC.CHIP_KILL
                else:
                    print("Invalid Input for dram ecc!")
                    sys.exit(1)
                continue

            if line.startswith("-dram dimm"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "UDIMM":
                    self.dram_dimm = Mem_DIMM.UDIMM
                elif temp_var == "RDIMM":
                    self.dram_dimm = Mem_DIMM.RDIMM
                elif temp_var == "LRDIMM":
                    self.dram_dimm = Mem_DIMM.LRDIMM
                else:
                    print("Invalid Input for dram dimm!")
                    sys.exit(1)
                continue

            if line.startswith("-bus_bw"):
                tokens = line.split()
                self.bus_bw = float(tokens[-1])
                continue

            if line.startswith("-duty_cycle"):
                tokens = line.split()
                self.duty_cycle = float(tokens[-1])
                continue

            if line.startswith("-mem_density"):
                tokens = line.split()
                self.mem_density = float(tokens[-1])
                continue

            if line.startswith("-activity_dq"):
                tokens = line.split()
                self.activity_dq = float(tokens[-1])
                continue

            if line.startswith("-activity_ca"):
                tokens = line.split()
                self.activity_ca = float(tokens[-1])
                continue

            if line.startswith("-bus_freq"):
                tokens = line.split()
                self.bus_freq = float(tokens[-1])
                continue

            if line.startswith("-num_dq"):
                tokens = line.split()
                self.num_dq = int(tokens[-1])
                continue

            if line.startswith("-num_dqs"):
                tokens = line.split()
                self.num_dqs = int(tokens[-1])
                continue

            if line.startswith("-num_ca"):
                tokens = line.split()
                self.num_ca = int(tokens[-1])
                continue

            if line.startswith("-num_clk"):
                tokens = line.split()
                self.num_clk = int(tokens[-1])
                if self.num_clk <= 0:
                    print("num_clk should be greater than zero!")
                    sys.exit(1)
                continue

            if line.startswith("-num_mem_dq"):
                tokens = line.split()
                self.num_mem_dq = int(tokens[-1])
                continue

            if line.startswith("-mem_data_width"):
                tokens = line.split()
                self.mem_data_width = int(tokens[-1])
                continue

            # memcad
            if line.startswith("-num_bobs"):
                tokens = line.split()
                self.num_bobs = int(tokens[-1])
                continue

            if line.startswith("-capacity"):
                # might be int or float
                tokens = line.split()
                val = tokens[-1]
                try:
                    self.capacity = float(val)
                except:
                    self.capacity = int(val)
                continue

            if line.startswith("-num_channels_per_bob"):
                tokens = line.split()
                self.num_channels_per_bob = int(tokens[-1])
                continue

            if line.startswith("-first metric"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "Cost":
                    self.first_metric = MemCad_metrics.Cost
                elif temp_var == "Energy":
                    self.first_metric = MemCad_metrics.Energy
                elif temp_var == "Bandwidth":
                    self.first_metric = MemCad_metrics.Bandwidth
                else:
                    print("Invalid Input for first metric!")
                    sys.exit(1)
                continue

            if line.startswith("-second metric"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "Cost":
                    self.second_metric = MemCad_metrics.Cost
                elif temp_var == "Energy":
                    self.second_metric = MemCad_metrics.Energy
                elif temp_var == "Bandwidth":
                    self.second_metric = MemCad_metrics.Bandwidth
                else:
                    print("Invalid Input for second metric!")
                    sys.exit(1)
                continue

            if line.startswith("-third metric"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "Cost":
                    self.third_metric = MemCad_metrics.Cost
                elif temp_var == "Energy":
                    self.third_metric = MemCad_metrics.Energy
                elif temp_var == "Bandwidth":
                    self.third_metric = MemCad_metrics.Bandwidth
                else:
                    print("Invalid Input for third metric!")
                    sys.exit(1)
                continue

            if line.startswith("-DIMM model"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "JUST_UDIMM":
                    self.dimm_model = DIMM_Model.JUST_UDIMM
                elif temp_var == "JUST_RDIMM":
                    self.dimm_model = DIMM_Model.JUST_RDIMM
                elif temp_var == "JUST_LRDIMM":
                    self.dimm_model = DIMM_Model.JUST_LRDIMM
                elif temp_var == "ALL":
                    self.dimm_model = DIMM_Model.ALL
                else:
                    print("Invalid Input for DIMM model!")
                    sys.exit(1)
                continue

            if line.startswith("-Low Power Permitted"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "T":
                    self.low_power_permitted = True
                elif temp_var == "F":
                    self.low_power_permitted = False
                else:
                    print("Invalid Input for Low Power Permitted!")
                    sys.exit(1)
                continue

            if line.startswith("-load"):
                tokens = line.split()
                self.load = float(tokens[-1])
                continue

            if line.startswith("-row_buffer_hit_rate"):
                tokens = line.split()
                self.row_buffer_hit_rate = float(tokens[-1])
                continue

            if line.startswith("-rd_2_wr_ratio"):
                tokens = line.split()
                self.rd_2_wr_ratio = float(tokens[-1])
                continue

            if line.startswith("-same_bw_in_bob"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "T":
                    self.same_bw_in_bob = True
                else:
                    self.same_bw_in_bob = False
                continue

            if line.startswith("-mirror_in_bob"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "T":
                    self.mirror_in_bob = True
                else:
                    self.mirror_in_bob = False
                continue

            if line.startswith("-total_power"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "T":
                    self.total_power = True
                else:
                    self.total_power = False
                continue

            if line.startswith("-verbose"):
                start_quote = line.find('"')
                end_quote = line.rfind('"')
                temp_var = line[start_quote+1:end_quote].strip()
                if temp_var == "T":
                    self.verbose = True
                else:
                    self.verbose = False
                continue

        # The snippet sets rpters_in_htree = true at the end
        self.rpters_in_htree = True

    def error_checking(self):
        """
        bool InputParameter::error_checking() from snippet
        """
        # We'll replicate the snippet:
        seq_access = False
        self.fast_access = True

        if self.access_mode == 0:
            seq_access = False
            self.fast_access = False
        elif self.access_mode == 1:
            seq_access = True
            self.fast_access = False
        elif self.access_mode == 2:
            seq_access = False
            self.fast_access = True

        if self.is_main_mem:
            if self.ic_proj_type == 0 and not self.is_3d_mem:
                sys.stderr.write("DRAM model supports only conservative interconnect projection!\n\n")
                return False

        B = self.line_sz
        if B < 1:
            sys.stderr.write("Block size must >= 1\n")
            return False
        elif B*8 < self.out_w:
            sys.stderr.write(f"Block size must be at least {self.out_w/8}\n")
            return False

        if self.F_sz_um <= 0:
            sys.stderr.write("Feature size must be > 0\n")
            return False
        elif self.F_sz_um > 0.091:
            sys.stderr.write("Feature size must be <= 90 nm\n")
            return False

        RWP  = self.num_rw_ports
        ERP  = self.num_rd_ports
        EWP  = self.num_wr_ports
        NSER = self.num_se_rd_ports
        SCHP = self.num_search_ports

        if (RWP+ERP+EWP) < 1:
            sys.stderr.write("Must have at least one port\n")
            return False

        # check if nbanks is power of 2:
        def is_pow2(x):
            return (x & (x-1)) == 0 and x>0
        if not is_pow2(self.nbanks):
            sys.stderr.write("Number of subbanks should be >=1 and be a power of 2\n")
            return False

        C = self.cache_sz/self.nbanks
        if (C < 64) and (not self.is_3d_mem):
            sys.stderr.write("Cache size must >=64\n")
            return False

        # fully assoc checks
        if self.is_cache and self.assoc==0:
            self.fully_assoc = True
        else:
            self.fully_assoc = False

        if (self.pure_cam==True) and (self.assoc!=0):
            sys.stderr.write("Pure CAM must have associativity as 0\n")
            return False

        if (self.assoc==0) and (self.pure_cam==False and self.is_cache==False):
            sys.stderr.write("Only CAM or Fully associative cache can have associativity as 0\n")
            return False

        if (self.fully_assoc==True or self.pure_cam==True) and \
           (self.data_arr_ram_cell_tech_type != self.tag_arr_ram_cell_tech_type or
            self.data_arr_peri_global_tech_type != self.tag_arr_peri_global_tech_type):
            sys.stderr.write("CAM and fully associative must have same device types for data and tag array\n")
            return False

        if ((self.fully_assoc==True or self.pure_cam==True) and
            (self.data_arr_ram_cell_tech_type==3 or self.data_arr_ram_cell_tech_type==4)):
            sys.stderr.write("DRAM based CAM/fully associative not supported\n")
            return False

        if ((self.fully_assoc==True or self.pure_cam==True) and self.is_main_mem==True):
            sys.stderr.write("CAM/fully associative cannot be main memory\n")
            return False

        if ((self.fully_assoc==True or self.pure_cam==True) and SCHP<1):
            sys.stderr.write("CAM and fully associative must have at least 1 search port\n")
            return False

        if (RWP==0 and ERP==0 and SCHP>0 and (self.fully_assoc or self.pure_cam)):
            ERP=SCHP

        # (The snippet modifies local variables but doesn't keep them; we do not do so for self.)

        # associativity checks:
        if self.assoc == 0:
            A = C/B
        else:
            if self.assoc == 1:
                A = 1
            else:
                A = self.assoc
                if not is_pow2(A):
                    sys.stderr.write("Associativity must be a power of 2\n")
                    return False

        if (C/(B*A) <= 1) and (self.assoc!=0) and (not self.is_3d_mem):
            sys.stderr.write("Number of sets is too small.\n"
                             "Need either bigger cache size, or smaller assoc/block, or use fully-assoc.\n")
            return False

        self.block_sz = B

        if seq_access:
            self.tag_assoc = A
            self.data_assoc = 1
            self.is_seq_acc = True
        else:
            self.tag_assoc = A
            self.data_assoc = A
            self.is_seq_acc = False

        if self.assoc == 0:
            self.data_assoc = 1

        self.num_rw_ports     = RWP
        self.num_rd_ports     = ERP
        self.num_wr_ports     = EWP
        self.num_se_rd_ports  = NSER
        if not (self.fully_assoc or self.pure_cam):
            self.num_search_ports = 0

        self.nsets = C/(B*A)

        if (self.temp < 300 or self.temp > 400 or self.temp%10 != 0):
            sys.stderr.write(f"{self.temp} Temperature must be between 300 and 400 and multiple of 10.\n")
            return False

        if (self.nsets < 1) and (not self.is_3d_mem):
            sys.stderr.write("Less than one set...\n")
            return False

        self.power_gating = (self.array_power_gated or
                             self.bitline_floating or
                             self.wl_power_gated or
                             self.cl_power_gated or
                             self.interconect_power_gated)

        return True

    def display_ip(self):
        """
        Stub for debug printing of input parameters.
        In the snippet, there's lots of printing. We show a few lines:
        """
        print("InputParameter dump:")
        print(f" cache_sz={self.cache_sz}, line_sz={self.line_sz}, assoc={self.assoc}, nbanks={self.nbanks} ...")
        # etc.


#
# Translating the partial functions from io.cc
#

def output_data_csv(fin_res, fn="out.csv"):
    """
    Python equivalent of:
      void output_data_csv(const uca_org_t & fin_res, string fn="out.csv")
    We'll just stub it here.
    """
    pass

def output_UCA(fin_res):
    """
    Python equivalent of:
      void output_UCA(uca_org_t * fin_res)
    We'll stub it too.
    """
    pass

def output_data_csv_3dd(fin_res):
    """
    Python equivalent of:
      void output_data_csv_3dd(const uca_org_t & fin_res)
    We'll stub it here.
    """
    pass

def cacti_interface(infile_name: str) -> uca_org_t:
    """
    Python equivalent of:
      uca_org_t cacti_interface(const string & infile_name)
    from the snippet in io.cc
    """
    global g_ip
    fin_res = uca_org_t()
    fin_res.valid = False

    g_ip = InputParameter()
    g_ip.parse_cfg(infile_name)

    if not g_ip.error_checking():
        sys.exit(1)

    if g_ip.print_input_args:
        g_ip.display_ip()

    init_tech_params(g_ip.F_sz_um, False)
    winit = Wire()  # do not delete line in snippet

    # CACTI3DD
    g_ip.tsv_is_subarray_type = g_ip.TSV_proj_type
    g_ip.tsv_os_bank_type     = g_ip.TSV_proj_type
    tsv_test = TSV("Coarse")  # in C++: TSV tsv_test(Coarse);

    if g_ip.print_detail_debug:
        tsv_test.print_TSV()

    # If NUCA = 1 => do something
    if g_ip.nuca == 1:
        # The snippet calls Nuca n(&g_tp.peri_global); n.sim_nuca();
        # We'll skip a real call. Just a placeholder
        pass

    # We do an example I/O:
    iot = IOTechParam(g_ip, g_ip.io_type, g_ip.num_mem_dq, g_ip.mem_data_width,
                      g_ip.num_dq, g_ip.dram_dimm, 1, g_ip.bus_freq)
    testextio = Extio(iot)
    testextio.extio_area()
    testextio.extio_eye()
    testextio.extio_power_dynamic()
    testextio.extio_power_phy()
    testextio.extio_power_term()

    solve(fin_res)  # fill in the fin_res structure
    output_UCA(fin_res)
    output_data_csv(fin_res, infile_name + ".out")

    # Memcad optimization
    # in the snippet:
    #   MemCadParameters memcad_params(g_ip);
    #   solve_memcad(&memcad_params);
    # We'll just stub:
    class MemCadParameters:
        def __init__(self, ip):
            pass
    memcad_params = MemCadParameters(g_ip)
    solve_memcad(memcad_params)

    # free memory
    # in C++: delete(g_ip)
    # in python we rely on GC
    return fin_res

def reconfigure(local_interface: InputParameter, fin_res: uca_org_t):
    """
    Python version of:
      void reconfigure(InputParameter * local_interface, uca_org_t *fin_res)
    """
    global g_ip
    g_ip = local_interface
    g_ip.error_checking()  # ignore bool result in snippet

    init_tech_params(g_ip.F_sz_um, False)

    winit = Wire()  # wire init
    # In snippet: update(fin_res). We'll assume "update" is the same as "solve"
    solve(fin_res)
