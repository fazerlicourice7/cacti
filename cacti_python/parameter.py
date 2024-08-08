import math
import re
import sys
import os
from .const import *
from .area import Area
import sympy as sp
import time


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from hw_symbols import symbol_table as sympy_var

def contains_any_symbol(expr):
    # Extract all the symbols from the dictionary
    symbols = sympy_var.values()
    
    # Check if the expression contains any of the symbols
    return any(expr.has(symbol) for symbol in symbols)

class InputParameter:
    def __init__(self):
        self.cache_sz = 0
        self.line_sz = 0
        self.assoc = 0
        self.nbanks = 0
        self.out_w = 0
        self.specific_tag = False
        self.tag_w = 0
        self.access_mode = 0
        self.obj_func_dyn_energy = 0
        self.obj_func_dyn_power = 0
        self.obj_func_leak_power = 0
        self.obj_func_cycle_t = 0
        self.F_sz_nm = 0.0
        self.F_sz_um = 0.0
        self.num_rw_ports = 0
        self.num_rd_ports = 0
        self.num_wr_ports = 0
        self.num_se_rd_ports = 0
        self.num_search_ports = 0
        self.is_main_mem = False
        self.is_3d_mem = False
        self.print_detail_debug = False
        self.is_cache = False
        self.pure_ram = False
        self.pure_cam = False
        self.rpters_in_htree = False
        self.ver_htree_wires_over_array = 0
        self.broadcast_addr_din_over_ver_htrees = 0
        self.temp = 0
        self.ram_cell_tech_type = 0
        self.peri_global_tech_type = 0
        self.data_arr_ram_cell_tech_type = 0
        self.data_arr_peri_global_tech_type = 0
        self.tag_arr_ram_cell_tech_type = 0
        self.tag_arr_peri_global_tech_type = 0
        self.burst_len = 0
        self.int_prefetch_w = 0
        self.page_sz_bits = 0
        self.num_die_3d = 0
        self.burst_depth = 0
        self.io_width = 0
        self.sys_freq_MHz = 0
        self.tsv_is_subarray_type = 0
        self.tsv_os_bank_type = 0
        self.TSV_proj_type = 0
        self.partition_gran = 0
        self.num_tier_row_sprd = 0
        self.num_tier_col_sprd = 0
        self.fine_gran_bank_lvl = False
        self.ic_proj_type = 0
        self.wire_is_mat_type = 0
        self.wire_os_mat_type = 0
        self.wt = None
        self.force_wiretype = 0
        self.print_input_args = False
        self.nuca_cache_sz = 0
        self.ndbl = 0
        self.ndwl = 0
        self.nspd = 0
        self.ndsam1 = 0
        self.ndsam2 = 0
        self.ndcm = 0
        self.force_cache_config = False
        self.cache_level = 0
        self.cores = 0
        self.nuca_bank_count = 0
        self.force_nuca_bank = 0
        self.delay_wt = 0
        self.dynamic_power_wt = 0
        self.leakage_power_wt = 0
        self.cycle_time_wt = 0
        self.area_wt = 0
        self.delay_wt_nuca = 0
        self.dynamic_power_wt_nuca = 0
        self.leakage_power_wt_nuca = 0
        self.cycle_time_wt_nuca = 0
        self.area_wt_nuca = 0
        self.delay_dev = 0
        self.dynamic_power_dev = 0
        self.leakage_power_dev = 0
        self.cycle_time_dev = 0
        self.area_dev = 0
        self.delay_dev_nuca = 0
        self.dynamic_power_dev_nuca = 0
        self.leakage_power_dev_nuca = 0
        self.cycle_time_dev_nuca = 0
        self.area_dev_nuca = 0
        self.ed = 0
        self.nuca = 0
        self.fast_access = False
        self.block_sz = 0
        self.tag_assoc = 0
        self.data_assoc = 0
        self.is_seq_acc = False
        self.fully_assoc = False
        self.nsets = 0
        self.print_detail = 0
        self.add_ecc_b_ = False
        self.throughput = 0.0
        self.latency = 0.0
        self.pipelinable = False
        self.pipeline_stages = 0
        self.per_stage_vector = 0
        self.with_clock_grid = False
        self.array_power_gated = False
        self.bitline_floating = False
        self.wl_power_gated = False
        self.cl_power_gated = False
        self.interconect_power_gated = False
        self.power_gating = False
        self.perfloss = 0.0
        self.cl_vertical = False
        self.addr_timing = 0.0
        self.duty_cycle = 0.0
        self.mem_density = 0.0
        self.bus_bw = 0.0
        self.activity_dq = 0.0
        self.activity_ca = 0.0
        self.bus_freq = 0.0
        self.mem_data_width = 0
        self.num_mem_dq = 0
        self.num_clk = 0
        self.num_ca = 0
        self.num_dqs = 0
        self.num_dq = 0
        self.rtt_value = 0.0
        self.ron_value = 0.0
        self.tflight_value = 0.0
        self.iostate = None
        self.dram_ecc = None
        self.io_type = None
        self.dram_dimm = None
        self.num_bobs = 0
        self.capacity = 0
        self.num_channels_per_bob = 0
        self.first_metric = None
        self.second_metric = None
        self.third_metric = None
        self.dimm_model = None
        self.low_power_permitted = False
        self.load = 0.0
        self.row_buffer_hit_rate = 0.0
        self.rd_2_wr_ratio = 0.0
        self.same_bw_in_bob = False
        self.mirror_in_bob = False
        self.total_power = False
        self.verbose = False

        self.repeater_spacing = 0.0
        self.repeater_size = 0.0
        

    def parse_cfg(self, in_file):
        try:
            with open(in_file, "r") as fp:
                lines = fp.readlines()

            for line in lines:
                line = line.strip()
                if line.startswith("-size"):
                    self.cache_sz = int(line.split()[-1])
                elif line.startswith("-page size"):
                    self.page_sz_bits = int(line.split()[-1])
                elif line.startswith("-burst length"):
                    self.burst_len = int(line.split()[-1])
                elif line.startswith("-internal prefetch width"):
                    self.int_prefetch_w = int(line.split()[-1])
                elif line.startswith("-block size (bytes)"):
                    self.line_sz = int(line.split()[-1])
                elif line.startswith("-associativity"):
                    self.assoc = int(line.split()[-1])
                elif line.startswith("-read-write port"):
                    self.num_rw_ports = int(line.split()[-1])
                elif line.startswith("-exclusive read port"):
                    self.num_rd_ports = int(line.split()[-1])
                elif line.startswith("-exclusive write port"):
                    self.num_wr_ports = int(line.split()[-1])
                elif line.startswith("-single"):
                    self.num_se_rd_ports = int(line.split()[-1])
                elif line.startswith("-search port"):
                    self.num_search_ports = int(line.split()[-1])
                elif line.startswith("-UCA bank"):
                    self.nbanks = int(line.split()[-1])
                elif line.startswith("-technology"):
                    self.F_sz_um = float(line.split()[-1])
                    self.F_sz_nm = self.F_sz_um * 1000
                elif line.startswith("-output/input bus"):
                    self.out_w = int(float(line.split()[-1]))
                elif line.startswith("-operating temperature"):
                    self.temp = int(line.split()[-1])
                elif line.startswith("-cache type"):
                    cache_type = line.split("\"")[1]
                    self.is_cache = "cache" in cache_type
                    self.is_main_mem = "main memory" in cache_type
                    self.is_3d_mem = "3D memory or 2D main memory" in cache_type
                    self.pure_cam = "cam" in cache_type
                    self.pure_ram = "ram" in cache_type or self.is_main_mem
                elif line.startswith("-print option"):
                    print_option = line.split("\"")[1]
                    self.print_detail_debug = "debug detail" in print_option
                elif line.startswith("-burst depth"):
                    self.burst_depth = int(line.split()[-1])
                elif line.startswith("-IO width"):
                    self.io_width = int(line.split()[-1])
                elif line.startswith("-system frequency"):
                    self.sys_freq_MHz = int(line.split()[-1])
                elif line.startswith("-stacked die"):
                    self.num_die_3d = int(line.split()[-1])
                elif line.startswith("-partitioning granularity"):
                    self.partition_gran = int(line.split()[-1])
                elif line.startswith("-TSV projection"):
                    self.TSV_proj_type = int(line.split()[-1])
                elif line.startswith("-tag size"):
                    tag_size = line.split("\"")[1]
                    if "default" in tag_size:
                        self.specific_tag = False
                        self.tag_w = 42
                    else:
                        self.specific_tag = True
                        self.tag_w = int(line.split()[-1])
                elif line.startswith("-access mode"):
                    access_mode = line.split("\"")[1]
                    # DONE
                    if "fast" in access_mode:
                        self.access_mode = 2
                    elif "sequential" in access_mode:
                        self.access_mode = 1
                    elif "normal" in access_mode:
                        self.access_mode = 0
                    else:
                        raise ValueError("Invalid access mode")
                elif line.startswith("-Data array cell type"):
                    cell_type = line.split("\"")[1]
                    if "itrs-hp" in cell_type:
                        self.data_arr_ram_cell_tech_type = 0
                    elif "itrs-lstp" in cell_type:
                        self.data_arr_ram_cell_tech_type = 1
                    elif "itrs-lop" in cell_type:
                        self.data_arr_ram_cell_tech_type = 2
                    elif "lp-dram" in cell_type:
                        self.data_arr_ram_cell_tech_type = 3
                    elif "comm-dram" in cell_type:
                        self.data_arr_ram_cell_tech_type = 4
                    else:
                        raise ValueError("Invalid data array cell type")
                elif line.startswith("-Data array peripheral type"):
                    peri_type = line.split("\"")[1]
                    if "itrs-hp" in peri_type:
                        self.data_arr_peri_global_tech_type = 0
                    elif "itrs-lstp" in peri_type:
                        self.data_arr_peri_global_tech_type = 1
                    elif "itrs-lop" in peri_type:
                        self.data_arr_peri_global_tech_type = 2
                    else:
                        raise ValueError("Invalid data array peripheral type")
                elif line.startswith("-Tag array cell type"):
                    cell_type = line.split("\"")[1]
                    if "itrs-hp" in cell_type:
                        self.tag_arr_ram_cell_tech_type = 0
                    elif "itrs-lstp" in cell_type:
                        self.tag_arr_ram_cell_tech_type = 1
                    elif "itrs-lop" in cell_type:
                        self.tag_arr_ram_cell_tech_type = 2
                    elif "lp-dram" in cell_type:
                        self.tag_arr_ram_cell_tech_type = 3
                    elif "comm-dram" in cell_type:
                        self.tag_arr_ram_cell_tech_type = 4
                    else:
                        raise ValueError("Invalid tag array cell type")
                elif line.startswith("-Tag array peripheral type"):
                    peri_type = line.split("\"")[1]
                    if "itrs-hp" in peri_type:
                        self.tag_arr_peri_global_tech_type = 0
                    elif "itrs-lstp" in peri_type:
                        self.tag_arr_peri_global_tech_type = 1
                    elif "itrs-lop" in peri_type:
                        self.tag_arr_peri_global_tech_type = 2
                    else:
                        raise ValueError("Invalid tag array peripheral type")
                elif line.startswith("-design"):
                    # DONE
                    match = re.search(r'-design objective \(weight delay, dynamic power, leakage power, cycle time, area\) (\d+):(\d+):(\d+):(\d+):(\d+)', line)
                    if match:
                        self.delay_wt = int(match.group(1))
                        self.dynamic_power_wt = int(match.group(2))
                        self.leakage_power_wt = int(match.group(3))
                        self.cycle_time_wt = int(match.group(4))
                        self.area_wt = int(match.group(5))
                        print(f"Design weights - Delay: {self.delay_wt}, Dynamic Power: {self.dynamic_power_wt}, Leakage Power: {self.leakage_power_wt}, Cycle Time: {self.cycle_time_wt}, Area: {self.area_wt}")
                elif line.startswith("-deviate"):
                    match = re.search(r'-deviate \(delay, dynamic power, leakage power, cycle time, area\) (\d+):(\d+):(\d+):(\d+):(\d+)', line)
                    if match:
                        self.delay_dev = int(match.group(1))
                        self.dynamic_power_dev = int(match.group(2))
                        self.leakage_power_dev = int(match.group(3))
                        self.cycle_time_dev = int(match.group(4))
                        self.area_dev = int(match.group(5))
                        print(f"Deviations - Delay: {self.delay_dev}, Dynamic Power: {self.dynamic_power_dev}, Leakage Power: {self.leakage_power_dev}, Cycle Time: {self.cycle_time_dev}, Area: {self.area_dev}")
                elif line.startswith("-Optimize"):
                    optimize = line.split("\"")[1]
                    if "ED^2" in optimize:
                        self.ed = 2
                    elif "ED" in optimize:
                        self.ed = 1
                    else:
                        self.ed = 0
                elif line.startswith("-NUCAdesign"):
                    match = re.search(r'-NUCAdesign objective \(weight delay, dynamic power, leakage power, cycle time, area\) (\d+):(\d+):(\d+):(\d+):(\d+)', line)
                    if match:
                        self.delay_wt_nuca = int(match.group(1))
                        self.dynamic_power_wt_nuca = int(match.group(2))
                        self.leakage_power_wt_nuca = int(match.group(3))
                        self.cycle_time_wt_nuca = int(match.group(4))
                        self.area_wt_nuca = int(match.group(5))
                        print(f"NUCA Design weights - Delay: {self.delay_wt_nuca}, Dynamic Power: {self.dynamic_power_wt_nuca}, Leakage Power: {self.leakage_power_wt_nuca}, Cycle Time: {self.cycle_time_wt_nuca}, Area: {self.area_wt_nuca}")
                elif line.startswith("-NUCAdeviate"):
                    match = re.search(r'-NUCAdeviate \(delay, dynamic power, leakage power, cycle time, area\) (\d+):(\d+):(\d+):(\d+):(\d+)', line)
                    if match:
                        self.delay_dev_nuca = int(match.group(1))
                        self.dynamic_power_dev_nuca = int(match.group(2))
                        self.leakage_power_dev_nuca = int(match.group(3))
                        self.cycle_time_dev_nuca = int(match.group(4))
                        self.area_dev_nuca = int(match.group(5))
                        print(f"NUCA Deviations - Delay: {self.delay_dev_nuca}, Dynamic Power: {self.dynamic_power_dev_nuca}, Leakage Power: {self.leakage_power_dev_nuca}, Cycle Time: {self.cycle_time_dev_nuca}, Area: {self.area_dev_nuca}")
                elif line.startswith("-Cache model"):
                    cache_model = line.split("\"")[1]
                    self.nuca = 0 if "UCA" in cache_model else 1
                elif line.startswith("-NUCA bank count"):
                    self.nuca_bank_count = int(line.split()[-1])
                    if self.nuca_bank_count != 0:
                        self.force_nuca_bank = 1
                elif line.startswith("-Wire inside mat"):
                    wire_type = line.split("\"")[1]
                    if "global" in wire_type:
                        self.wire_is_mat_type = 2
                    elif "local" in wire_type:
                        self.wire_is_mat_type = 0
                    else:
                        self.wire_is_mat_type = 1
                elif line.startswith("-Wire outside mat"):
                    wire_type = line.split("\"")[1]
                    if "global" in wire_type:
                        self.wire_os_mat_type = 2
                    else:
                        self.wire_os_mat_type = 1
                elif line.startswith("-Interconnect projection"):
                    ic_proj_type = line.split("\"")[1]
                    self.ic_proj_type = 0 if "aggressive" in ic_proj_type else 1
                elif line.startswith("-Wire signaling"):
                    wire_signaling = line.split("\"")[1]
                    if "default" in wire_signaling:
                        self.force_wiretype = 0
                        self.wt = "Global"
                    elif "Global_10" in wire_signaling:
                        self.force_wiretype = 1
                        self.wt = "Global_10"
                    elif "Global_20" in wire_signaling:
                        self.force_wiretype = 1
                        self.wt = "Global_20"
                    elif "Global_30" in wire_signaling:
                        self.force_wiretype = 1
                        self.wt = "Global_30"
                    elif "Global_5" in wire_signaling:
                        self.force_wiretype = 1
                        self.wt = "Global_5"
                    elif "Global" in wire_signaling:
                        self.force_wiretype = 1
                        self.wt = "Global"
                    elif "fullswing" in wire_signaling:
                        self.force_wiretype = 1
                        self.wt = "Full_swing"
                    elif "lowswing" in wire_signaling:
                        self.force_wiretype = 1
                        self.wt = "Low_swing"
                    else:
                        raise ValueError("Unknown wire type")
                elif line.startswith("-Core count"):
                    self.cores = int(line.split()[-1])
                    if self.cores > 16:
                        raise ValueError("No. of cores should be less than 16!")
                elif line.startswith("-Cache level"):
                    cache_level = line.split("\"")[1]
                    self.cache_level = 0 if "L2" in cache_level else 1
                elif line.startswith("-Print level"):
                    print_level = line.split("\"")[1]
                    self.print_detail = 1 if "DETAILED" in print_level else 0
                elif line.startswith("-Add ECC"):
                    add_ecc = line.split("\"")[1]
                    self.add_ecc_b_ = True if "true" in add_ecc else False
                elif line.startswith("-CLDriver vertical"):
                    cl_driver = line.split("\"")[1]
                    self.cl_vertical = True if "true" in cl_driver else False
                elif line.startswith("-Array Power Gating"):
                    array_power = line.split("\"")[1]
                    self.array_power_gated = True if "true" in array_power else False
                elif line.startswith("-Bitline floating"):
                    bitline_float = line.split("\"")[1]
                    self.bitline_floating = True if "true" in bitline_float else False
                elif line.startswith("-WL Power Gating"):
                    wl_power = line.split("\"")[1]
                    self.wl_power_gated = True if "true" in wl_power else False
                elif line.startswith("-CL Power Gating"):
                    cl_power = line.split("\"")[1]
                    self.cl_power_gated = True if "true" in cl_power else False
                elif line.startswith("-Interconnect Power Gating"):
                    interconnect_power = line.split("\"")[1]
                    self.interconect_power_gated = True if "true" in interconnect_power else False
                elif line.startswith("-Power Gating Performance Loss"):
                    val = line.split()[-1]
                    cleaned_value = val.strip('"').strip()
                    self.perfloss = float(cleaned_value)
                elif line.startswith("-Print input parameters"):
                    print_input = line.split("\"")[1]
                    self.print_input_args = True if "true" in print_input else False
                elif line.startswith("-Force cache config"):
                    force_cache = line.split("\"")[1]
                    self.force_cache_config = True if "true" in force_cache else False
                elif line.startswith("-Ndbl"):
                    self.ndbl = int(line.split()[-1])
                elif line.startswith("-Ndwl"):
                    self.ndwl = int(line.split()[-1])
                elif line.startswith("-Nspd"):
                    self.nspd = int(line.split()[-1])
                elif line.startswith("-Ndsam1"):
                    self.ndsam1 = int(line.split()[-1])
                elif line.startswith("-Ndsam2"):
                    self.ndsam2 = int(line.split()[-1])
                elif line.startswith("-Ndcm"):
                    self.ndcm = int(line.split()[-1])
                elif line.startswith("-dram_type"):
                    dram_type = line.split("\"")[1]
                    if "DDR3" in dram_type:
                        self.io_type = "DDR3"
                    elif "DDR4" in dram_type:
                        self.io_type = "DDR4"
                    elif "LPDDR2" in dram_type:
                        self.io_type = "LPDDR2"
                    elif "WideIO" in dram_type:
                        self.io_type = "WideIO"
                    elif "Low_Swing_Diff" in dram_type:
                        self.io_type = "Low_Swing_Diff"
                    elif "Serial" in dram_type:
                        self.io_type = "Serial"
                    else:
                        raise ValueError("Invalid Input for dram type")
                elif line.startswith("-io state"):
                    io_state = line.split("\"")[1]
                    if "READ" in io_state:
                        self.iostate = "READ"
                    elif "WRITE" in io_state:
                        self.iostate = "WRITE"
                    elif "IDLE" in io_state:
                        self.iostate = "IDLE"
                    elif "SLEEP" in io_state:
                        self.iostate = "SLEEP"
                    else:
                        raise ValueError("Invalid Input for io state")
                elif line.startswith("-addr_timing"):
                    self.addr_timing = float(re.search(r'-addr_timing (\d+\.\d+)', line).group(1))
                    print(f"Address Timing: {self.addr_timing}")
                elif line.startswith("-dram ecc"):
                    dram_ecc = line.split("\"")[1]
                    if "NO_ECC" in dram_ecc:
                        self.dram_ecc = "NO_ECC"
                    elif "SECDED" in dram_ecc:
                        self.dram_ecc = "SECDED"
                    elif "CHIP_KILL" in dram_ecc:
                        self.dram_ecc = "CHIP_KILL"
                    else:
                        print("Invalid Input for dram ecc")
                elif line.startswith("-dram dimm"):
                    dram_dimm = line.split("\"")[1]
                    if "UDIMM" in dram_dimm:
                        self.dram_dimm = "UDIMM"
                    elif "RDIMM" in dram_dimm:
                        self.dram_dimm = "RDIMM"
                    elif "LRDIMM" in dram_dimm:
                        self.dram_dimm = "LRDIMM"
                    else:
                        print("Invalid Input for dram dimm")
                elif line.startswith("-bus_bw"):
                    self.bus_bw = float(line.split()[-1])
                elif line.startswith("-duty_cycle"):
                    self.duty_cycle = float(line.split()[-1])
                elif line.startswith("-mem_density"):
                    self.mem_density = float(re.search(r'-mem_density (\d+)', line).group(1))
                    print(self.mem_density)
                elif line.startswith("-activity_dq"):
                    self.activity_dq = float(re.search(r'-activity_dq (\d+\.\d+)', line).group(1))
                    print(f"Activity DQ: {self.activity_dq}")
                elif line.startswith("-activity_ca"):
                    self.activity_ca = float(re.search(r'-activity_ca (\d+\.\d+)', line).group(1))
                    print(f"Activity CA: {self.activity_ca}")
                elif line.startswith("-bus_freq"):
                    self.bus_freq = float(re.search(r'-bus_freq (\d+)', line).group(1))
                    print(self.bus_freq)
                elif line.startswith("-num_dq"):
                    match = re.search(r'-num_dq (\d+)', line)
                    if match:
                        self.num_dq = int(match.group(1))
                        print(f"Number of DQ pins: {self.num_dq}")
                    if line.startswith("-num_dqs"):
                        match = re.search(r'-num_dqs (\d+)', line)
                        if match:
                            self.num_dqs = int(match.group(1))
                            print(f"Number of DQS pins: {self.num_dqs}")
                elif line.startswith("-num_ca"):
                    self.num_ca = int(re.search(r'-num_ca (\d+)', line).group(1))
                    print(f"Number of CA pins: {self.num_ca}")
                elif line.startswith("-num_clk"):
                    self.num_clk = int(re.search(r'-num_clk (\d+)', line).group(1))
                    print(f"Number of CLK pins: {self.num_clk}")
                    if self.num_clk <= 0:
                        raise ValueError("num_clk should be greater than zero!")
                elif line.startswith("-num_mem_dq"):
                    self.num_mem_dq = int(re.search(r'-num_mem_dq (\d+)', line).group(1))
                    print(f"Number of Physical Ranks: {self.num_mem_dq}")
                elif line.startswith("-mem_data_width"):
                    self.mem_data_width = int(re.search(r'-mem_data_width (\d+)', line).group(1))
                    print(f"Width of the Memory Data Bus: {self.mem_data_width}")
                elif line.startswith("-num_bobs"):
                    self.num_bobs = int(line.split()[-1])
                elif line.startswith("-capacity"):
                    self.capacity = int(line.split()[-1])
                elif line.startswith("-num_channels_per_bob"):
                    self.num_channels_per_bob = int(line.split()[-1])
                elif line.startswith("-first metric"):
                    first_metric = line.split("\"")[1]
                    if "Cost" in first_metric:
                        self.first_metric = "Cost"
                    elif "Energy" in first_metric:
                        self.first_metric = "Energy"
                    elif "Bandwidth" in first_metric:
                        self.first_metric = "Bandwidth"
                    else:
                        raise ValueError("Invalid Input for first metric")
                elif line.startswith("-second metric"):
                    second_metric = line.split("\"")[1]
                    if "Cost" in second_metric:
                        self.second_metric = "Cost"
                    elif "Energy" in second_metric:
                        self.second_metric = "Energy"
                    elif "Bandwidth" in second_metric:
                        self.second_metric = "Bandwidth"
                    else:
                        raise ValueError("Invalid Input for second metric")
                elif line.startswith("-third metric"):
                    third_metric = line.split("\"")[1]
                    if "Cost" in third_metric:
                        self.third_metric = "Cost"
                    elif "Energy" in third_metric:
                        self.third_metric = "Energy"
                    elif "Bandwidth" in third_metric:
                        self.third_metric = "Bandwidth"
                    else:
                        raise ValueError("Invalid Input for third metric")
                elif line.startswith("-DIMM model"):
                    dimm_model = line.split("\"")[1]
                    if "JUST_UDIMM" in dimm_model:
                        self.dimm_model = "JUST_UDIMM"
                    elif "JUST_RDIMM" in dimm_model:
                        self.dimm_model = "JUST_RDIMM"
                    elif "JUST_LRDIMM" in dimm_model:
                        self.dimm_model = "JUST_LRDIMM"
                    elif "ALL" in dimm_model:
                        self.dimm_model = "ALL"
                    else:
                        raise ValueError("Invalid Input for DIMM model")
                elif line.startswith("-Low Power Permitted"):
                    low_power = line.split("\"")[1]
                    self.low_power_permitted = True if "T" in low_power else False
                elif line.startswith("-load"):
                    self.load = float(line.split()[-1])
                elif line.startswith("-row_buffer_hit_rate"):
                    self.row_buffer_hit_rate = float(line.split()[-1])
                elif line.startswith("-rd_2_wr_ratio"):
                    self.rd_2_wr_ratio = float(line.split()[-1])
                elif line.startswith("-same_bw_in_bob"):
                    same_bw = line.split("\"")[1]
                    self.same_bw_in_bob = True if "T" in same_bw else False
                elif line.startswith("-mirror_in_bob"):
                    mirror = line.split("\"")[1]
                    self.mirror_in_bob = True if "T" in mirror else False
                elif line.startswith("-total_power"):
                    total_power = line.split("\"")[1]
                    self.total_power = True if "T" in total_power else False
                elif line.startswith("-verbose"):
                    verbose = line.split("\"")[1]
                    self.verbose = True if "T" in verbose else False

        except FileNotFoundError:
            print(f"{in_file} is missing!")
            exit(-1)

    def error_checking(self): 
        A = 0
        seq_access = False
        fast_access = True

        if self.access_mode == 0:
            seq_access = False
            fast_access = False
        elif self.access_mode == 1:
            seq_access = True
            fast_access = False
        elif self.access_mode == 2:
            seq_access = False
            fast_access = True

        if self.is_main_mem:
            if self.ic_proj_type == 0 and not g_ip.is_3d_mem:
                print("DRAM model supports only conservative interconnect projection!\n\n")
                return False

        B = self.line_sz

        if B < 1:
            print("Block size must >= 1")
            return False
        elif B * 8 < self.out_w:
            print(f"Block size must be at least {self.out_w / 8}")
            return False

        if self.F_sz_um <= 0:
            print("Feature size must be > 0")
            return False
        elif self.F_sz_um > 0.091:
            print("Feature size must be <= 90 nm")
            return False

        RWP = self.num_rw_ports
        ERP = self.num_rd_ports
        EWP = self.num_wr_ports
        NSER = self.num_se_rd_ports
        SCHP = self.num_search_ports

        if (RWP + ERP + EWP) < 1:
            print("Must have at least one port")
            return False

        if not is_pow2(self.nbanks):
            print("Number of subbanks should be greater than or equal to 1 and should be a power of 2")
            return False

        C = self.cache_sz / self.nbanks
        if C < 64 and not g_ip.is_3d_mem:
            print("Cache size must >=64")
            return False

        if self.is_cache and self.assoc == 0:
            self.fully_assoc = True
        else:
            self.fully_assoc = False

        if self.pure_cam and self.assoc != 0:
            print("Pure CAM must have associativity as 0")
            return False

        if self.assoc == 0 and not self.pure_cam and not self.is_cache:
            print("Only CAM or Fully associative cache can have associativity as 0")
            return False

        if (self.fully_assoc or self.pure_cam) and (
                self.data_arr_ram_cell_tech_type != self.tag_arr_ram_cell_tech_type
                or self.data_arr_peri_global_tech_type != self.tag_arr_peri_global_tech_type):
            print("CAM and fully associative cache must have same device type for both data and tag array")
            return False

        if (self.fully_assoc or self.pure_cam) and (
                self.data_arr_ram_cell_tech_type == lp_dram or self.data_arr_ram_cell_tech_type == comm_dram):
            print("DRAM based CAM and fully associative cache are not supported")
            return False

        if (self.fully_assoc or self.pure_cam) and self.is_main_mem:
            print("CAM and fully associative cache cannot be as main memory")
            return False

        if (self.fully_assoc or self.pure_cam) and SCHP < 1:
            print("CAM and fully associative must have at least 1 search port")
            return False

        if RWP == 0 and ERP == 0 and SCHP > 0 and (self.fully_assoc or self.pure_cam):
            ERP = SCHP

        if self.assoc == 0:
            A = C / B
        else:
            if self.assoc == 1:
                A = 1
            else:
                A = self.assoc
                if not is_pow2(A):
                    print("Associativity must be a power of 2")
                    return False

        if C / (B * A) <= 1 and self.assoc != 0 and not g_ip.is_3d_mem:
            print("Number of sets is too small: ")
            print(" Need to either increase cache size, or decrease associativity or block size")
            print(" (or use fully associative cache)")
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

        self.num_rw_ports = RWP
        self.num_rd_ports = ERP
        self.num_wr_ports = EWP
        self.num_se_rd_ports = NSER

        if not (self.fully_assoc or self.pure_cam):
            self.num_search_ports = 0

        self.nsets = C / (B * A)

        if self.temp < 300 or self.temp > 400 or self.temp % 10 != 0:
            print(f"{self.temp} Temperature must be between 300 and 400 Kelvin and multiple of 10.")
            return False

        if self.nsets < 1 and not g_ip.is_3d_mem:
            print("Less than one set...")
            return False

        self.power_gating = (self.array_power_gated or self.bitline_floating or self.wl_power_gated or
                            self.cl_power_gated or self.interconect_power_gated)

        return True


    def display_ip(self):
        print(f"Cache size                    : {self.cache_sz}")
        print(f"Block size                    : {self.line_sz}")
        print(f"Associativity                 : {self.assoc}")
        print(f"Read only ports               : {self.num_rd_ports}")
        print(f"Write only ports              : {self.num_wr_ports}")
        print(f"Read write ports              : {self.num_rw_ports}")
        print(f"Single ended read ports       : {self.num_se_rd_ports}")
        if self.fully_assoc or self.pure_cam:
            print(f"Search ports                  : {self.num_search_ports}")
        print(f"Cache banks (UCA)             : {self.nbanks}")
        print(f"Technology                    : {self.F_sz_um}")
        print(f"Temperature                   : {self.temp}")
        print(f"Tag size                      : {self.tag_w}")
        if self.is_cache:
            print("Array type                    : Cache")
        if self.pure_ram:
            print("Array type                    : Scratch RAM")
        if self.pure_cam:
            print("Array type                    : CAM")
        print(f"Model as memory               : {self.is_main_mem}")
        print(f"Model as 3D memory            : {self.is_3d_mem}")
        print(f"Access mode                   : {self.access_mode}")
        print(f"Data array cell type          : {self.data_arr_ram_cell_tech_type}")
        print(f"Data array peripheral type    : {self.data_arr_peri_global_tech_type}")
        print(f"Tag array cell type           : {self.tag_arr_ram_cell_tech_type}")
        print(f"Tag array peripheral type     : {self.tag_arr_peri_global_tech_type}")
        print(f"Optimization target           : {self.ed}")
        print(f"Design objective (UCA wt)     : {self.delay_wt} {self.dynamic_power_wt} {self.leakage_power_wt} {self.cycle_time_wt} {self.area_wt}")
        print(f"Design objective (UCA dev)    : {self.delay_dev} {self.dynamic_power_dev} {self.leakage_power_dev} {self.cycle_time_dev} {self.area_dev}")
        if self.nuca:
            print(f"Cores                         : {self.cores}")
            print(f"Design objective (NUCA wt)    : {self.delay_wt_nuca} {self.dynamic_power_wt_nuca} {self.leakage_power_wt_nuca} {self.cycle_time_wt_nuca} {self.area_wt_nuca}")
            print(f"Design objective (NUCA dev)   : {self.delay_dev_nuca} {self.dynamic_power_dev_nuca} {self.leakage_power_dev_nuca} {self.cycle_time_dev_nuca} {self.area_dev_nuca}")
        print(f"Cache model                   : {self.nuca}")
        print(f"Nuca bank                     : {self.nuca_bank_count}")
        print(f"Wire inside mat               : {self.wire_is_mat_type}")
        print(f"Wire outside mat              : {self.wire_os_mat_type}")
        print(f"Interconnect projection       : {self.ic_proj_type}")
        print(f"Wire signaling                : {self.force_wiretype}")
        print(f"Print level                   : {self.print_detail}")
        print(f"ECC overhead                  : {self.add_ecc_b_}")
        print(f"Page size                     : {self.page_sz_bits}")
        print(f"Burst length                  : {self.burst_len}")
        print(f"Internal prefetch width       : {self.int_prefetch_w}")
        print(f"Force cache config            : {self.force_cache_config}")
        if self.force_cache_config:
            print(f"Ndwl                          : {self.ndwl}")
            print(f"Ndbl                          : {self.ndbl}")
            print(f"Nspd                          : {self.nspd}")
            print(f"Ndcm                          : {self.ndcm}")
            print(f"Ndsam1                        : {self.ndsam1}")
            print(f"Ndsam2                        : {self.ndsam2}")
        print(f"Subarray Driver direction     : {self.cl_vertical}")

        # CACTI-I/O
        print(f"iostate                       : ", end="")
        if self.iostate == 'READ':
            print("READ")
        elif self.iostate == 'WRITE':
            print("WRITE")
        elif self.iostate == 'IDLE':
            print("IDLE")
        elif self.iostate == 'SLEEP':
            print("SLEEP")
        else:
            raise ValueError("Invalid iostate value")

        print(f"dram_ecc                      : ", end="")
        if self.dram_ecc == 'NO_ECC':
            print("NO_ECC")
        elif self.dram_ecc == 'SECDED':
            print("SECDED")
        elif self.dram_ecc == 'CHIP_KILL':
            print("CHIP_KILL")
        else:
            print("Invalid dram_ecc value")

        print(f"io_type                       : ", end="")
        if self.io_type == 'DDR3':
            print("DDR3")
        elif self.io_type == 'DDR4':
            print("DDR4")
        elif self.io_type == 'LPDDR2':
            print("LPDDR2")
        elif self.io_type == 'WideIO':
            print("WideIO")
        elif self.io_type == 'Low_Swing_Diff':
            print("Low_Swing_Diff")
        else:
            print("Invalid io_type value")

        print(f"dram_dimm                    : ", end="")
        if self.dram_dimm == 'UDIMM':
            print("UDIMM")
        elif self.dram_dimm == 'RDIMM':
            print("RDIMM")
        elif self.dram_dimm == 'LRDIMM':
            print("LRDIMM")
        else:
            print("Invalid dram_dimm value")

class TechnologyParameter:
    def __init__(self):
        self.reset()

    def reset(self):
        self.ram_wl_stitching_overhead_ = 0
        self.min_w_nmos_ = 0
        self.max_w_nmos_ = 0
        self.max_w_nmos_dec = 0
        self.unit_len_wire_del = 0
        self.FO4 = 0
        self.kinv = 0
        self.vpp = 0
        self.w_sense_en = 0
        self.w_sense_n = 0
        self.w_sense_p = 0
        self.sense_delay = 0
        self.sense_dy_power = 0
        self.w_iso = 0
        self.w_poly_contact = 0
        self.spacing_poly_to_poly = 0
        self.spacing_poly_to_contact = 0
        self.tsv_pitch = 0
        self.tsv_diameter = 0
        self.tsv_length = 0
        self.tsv_dielec_thickness = 0
        self.tsv_contact_resistance = 0
        self.tsv_depletion_width = 0
        self.tsv_liner_dielectric_constant = 0
        self.tsv_parasitic_capacitance_fine = 0
        self.tsv_parasitic_resistance_fine = 0
        self.tsv_minimum_area_fine = 0
        self.tsv_parasitic_capacitance_coarse = 0
        self.tsv_parasitic_resistance_coarse = 0
        self.tsv_minimum_area_coarse = 0
        self.w_comp_inv_p1 = 0
        self.w_comp_inv_p2 = 0
        self.w_comp_inv_p3 = 0
        self.w_comp_inv_n1 = 0
        self.w_comp_inv_n2 = 0
        self.w_comp_inv_n3 = 0
        self.w_eval_inv_p = 0
        self.w_eval_inv_n = 0
        self.w_comp_n = 0
        self.w_comp_p = 0
        self.dram_cell_I_on = 0
        self.dram_cell_Vdd = 0
        self.dram_cell_I_off_worst_case_len_temp = 0
        self.dram_cell_C = 0
        self.gm_sense_amp_latch = 0
        self.w_nmos_b_mux = 0
        self.w_nmos_sa_mux = 0
        self.w_pmos_bl_precharge = 0
        self.w_pmos_bl_eq = 0
        self.MIN_GAP_BET_P_AND_N_DIFFS = 0
        self.MIN_GAP_BET_SAME_TYPE_DIFFS = 0
        self.HPOWERRAIL = 0
        self.cell_h_def = 0
        self.chip_layout_overhead = 0
        self.macro_layout_overhead = 0
        self.sckt_co_eff = 0
        self.fringe_cap = 0
        self.h_dec = 0
        self.sram_cell = DeviceType()
        self.dram_acc = DeviceType()
        self.dram_wl = DeviceType()
        self.peri_global = DeviceType()
        self.cam_cell = DeviceType()
        self.sleep_tx = DeviceType()
        self.wire_local = InterconnectType()
        self.wire_inside_mat = InterconnectType()
        self.wire_outside_mat = InterconnectType()
        self.scaling_factor = ScalingFactor()
        self.sram = MemoryType()
        self.dram = MemoryType()
        self.cam = MemoryType()

        self.dram_cell_I_on = sympy_var['dram_cell_I_on']
        self.dram_cell_Vdd = sympy_var['dram_cell_Vdd']
        self.dram_cell_C = sympy_var['dram_cell_C']
        self.dram_cell_I_off_worst_case_len_temp = sympy_var['dram_cell_I_off_worst_case_len_temp']
        self.vpp = sympy_var['vpp']
        self.sckt_co_eff = sympy_var['sckt_co_eff']
        self.chip_layout_overhead = sympy_var['chip_layout_overhead']
        self.macro_layout_overhead = sympy_var['macro_layout_overhead']

        self.sense_delay = sympy_var['sense_delay']
        self.sense_dy_power = sympy_var['sense_dy_power']
        self.sckt_co_eff = sympy_var['sckt_co_eff']
        self.chip_layout_overhead = sympy_var['chip_layout_overhead']
        self.macro_layout_overhead = sympy_var['macro_layout_overhead']
        self.dram_cell_I_on = sympy_var['dram_cell_I_on']
        self.dram_cell_Vdd = sympy_var['dram_cell_Vdd']
        self.dram_cell_C = sympy_var['dram_cell_C']
        self.dram_cell_I_off_worst_case_len_temp = sympy_var['dram_cell_I_off_worst_case_len_temp']
        self.vpp = sympy_var['vpp']

    def init_symbolic():
        return

    def find_upper_and_lower_tech(self, technology, tech_lo, in_file_lo, tech_hi, in_file_hi):
        if 179 < technology < 181:
            tech_lo = 180
            in_file_lo = "tech_params/180nm.dat"
            tech_hi = 180
            in_file_hi = "tech_params/180nm.dat"
        elif 89 < technology < 91:
            tech_lo = 90
            in_file_lo = "tech_params/90nm.dat"
            tech_hi = 90
            in_file_hi = "tech_params/90nm.dat"
        elif 64 < technology < 66:
            tech_lo = 65
            in_file_lo = "tech_params/65nm.dat"
            tech_hi = 65
            in_file_hi = "tech_params/65nm.dat"
        elif 44 < technology < 46:
            tech_lo = 45
            in_file_lo = "tech_params/45nm.dat"
            tech_hi = 45
            in_file_hi = "tech_params/45nm.dat"
        elif 31 < technology < 33:
            tech_lo = 32
            in_file_lo = "tech_params/32nm.dat"
            tech_hi = 32
            in_file_hi = "tech_params/32nm.dat"
        elif 21 < technology < 23:
            tech_lo = 22
            in_file_lo = "tech_params/22nm.dat"
            tech_hi = 22
            in_file_hi = "tech_params/22nm.dat"
        elif 90 < technology < 180:
            tech_lo = 180
            in_file_lo = "tech_params/180nm.dat"
            tech_hi = 90
            in_file_hi = "tech_params/90nm.dat"
        elif 65 < technology < 90:
            tech_lo = 90
            in_file_lo = "tech_params/90nm.dat"
            tech_hi = 65
            in_file_hi = "tech_params/65nm.dat"
        elif 45 < technology < 65:
            tech_lo = 65
            in_file_lo = "tech_params/65nm.dat"
            tech_hi = 45
            in_file_hi = "tech_params/45nm.dat"
        elif 32 < technology < 45:
            tech_lo = 45
            in_file_lo = "tech_params/45nm.dat"
            tech_hi = 32
            in_file_hi = "tech_params/32nm.dat"
        elif 22 < technology < 32:
            tech_lo = 32
            in_file_lo = "tech_params/32nm.dat"
            tech_hi = 22
            in_file_hi = "tech_params/22nm.dat"
        else:
            print("Invalid technology nodes")
            exit(0)

        in_file_lo = "cacti/" + in_file_lo
        in_file_hi = "cacti/" + in_file_hi
        return tech_lo, in_file_lo, tech_hi, in_file_hi

    def assign_tsv(self, in_file):
        for iter in range(2):  # 0:fine 1:coarse
            tsv_type = g_ip.tsv_is_subarray_type if iter == 0 else g_ip.tsv_os_bank_type
            with open(in_file, "r") as fp:
                lines = fp.readlines()

            self.tsv_pitch = sympy_var['tsv_pitch']
            self.tsv_diameter = sympy_var['tsv_diameter']
            self.tsv_length = sympy_var['tsv_length']
            self.tsv_dielec_thickness = sympy_var['tsv_dielec_thickness']
            self.tsv_contact_resistance = sympy_var['tsv_contact_resistance']
            self.tsv_depletion_width = sympy_var['tsv_depletion_width']
            self.tsv_liner_dielectric_constant = sympy_var['tsv_liner_dielectric_cons']

            # for line in lines:
            #     if line.startswith("-tsv_pitch"):
            #         self.tsv_pitch = scan_input_double_tsv_type(line, "-tsv_pitch", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            #     elif line.startswith("-tsv_diameter"):
            #         self.tsv_diameter = scan_input_double_tsv_type(line, "-tsv_diameter", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            #     elif line.startswith("-tsv_length"):
            #         self.tsv_length = scan_input_double_tsv_type(line, "-tsv_length", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            #     elif line.startswith("-tsv_dielec_thickness"):
            #         self.tsv_dielec_thickness = scan_input_double_tsv_type(line, "-tsv_dielec_thickness", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            #     elif line.startswith("-tsv_contact_resistance"):
            #         self.tsv_contact_resistance = scan_input_double_tsv_type(line, "-tsv_contact_resistance", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            #     elif line.startswith("-tsv_depletion_width"):
            #         self.tsv_depletion_width = scan_input_double_tsv_type(line, "-tsv_depletion_width", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            #     elif line.startswith("-tsv_liner_dielectric_cons"):
            #         self.tsv_liner_dielectric_constant = scan_input_double_tsv_type(line, "-tsv_liner_dielectric_cons", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            
            self.tsv_length *= g_ip.num_die_3d
            if iter == 0:
                self.tsv_parasitic_resistance_fine = tsv_resistance(BULK_CU_RESISTIVITY, self.tsv_length, self.tsv_diameter, self.tsv_contact_resistance)
                self.tsv_parasitic_capacitance_fine = tsv_capacitance(self.tsv_length, self.tsv_diameter, self.tsv_pitch, self.tsv_dielec_thickness, self.tsv_liner_dielectric_constant, self.tsv_depletion_width)
                self.tsv_minimum_area_fine = tsv_area(self.tsv_pitch)
            else:
                self.tsv_parasitic_resistance_coarse = tsv_resistance(BULK_CU_RESISTIVITY, self.tsv_length, self.tsv_diameter, self.tsv_contact_resistance)
                self.tsv_parasitic_capacitance_coarse = tsv_capacitance(self.tsv_length, self.tsv_diameter, self.tsv_pitch, self.tsv_dielec_thickness, self.tsv_liner_dielectric_constant, self.tsv_depletion_width)
                self.tsv_minimum_area_coarse = tsv_area(self.tsv_pitch)

    def init(self, technology, is_tag):
        self.reset()
        ram_cell_tech_type = g_ip.tag_arr_ram_cell_tech_type if is_tag else g_ip.data_arr_ram_cell_tech_type
        peri_global_tech_type = g_ip.tag_arr_peri_global_tech_type if is_tag else g_ip.data_arr_peri_global_tech_type
        tech_lo, tech_hi = 0, 0
        in_file_lo, in_file_hi = "", ""

        technology *= 1000.0  # in the unit of nm

        tech_lo, in_file_lo, tech_hi, in_file_hi = self.find_upper_and_lower_tech(technology, tech_lo, in_file_lo, tech_hi, in_file_hi)

        if (tech_lo == 22) and (tech_hi == 22):
            if ram_cell_tech_type == 3:
                print("current version does not support eDRAM technologies at 22nm")
                exit(0)

        alpha = 1 if tech_lo == tech_hi else (technology - tech_hi) / (tech_lo - tech_hi)
        with open(in_file_lo, "r") as fp:
            lines = fp.readlines()

        self.dram_cell_I_on = 0
        self.dram_cell_Vdd = 0
        self.dram_cell_C = 0
        self.dram_cell_I_off_worst_case_len_temp = 0
        self.vpp = 0
        self.macro_layout_overhead = 0
        self.chip_layout_overhead = 0
        self.sckt_co_eff = 0

        self.dram_cell_I_on = sympy_var['dram_cell_I_on']
        self.dram_cell_Vdd = sympy_var['dram_cell_Vdd']
        self.dram_cell_C = sympy_var['dram_cell_C']
        self.dram_cell_I_off_worst_case_len_temp = sympy_var['dram_cell_I_off_worst_case_len_temp']
        self.vpp = sympy_var['vpp']
        self.sckt_co_eff = sympy_var['sckt_co_eff']
        self.chip_layout_overhead = sympy_var['chip_layout_overhead']
        self.macro_layout_overhead = sympy_var['macro_layout_overhead']

        # for line in lines:
        #     if line.startswith("-dram_cell_I_on"):
        #         self.dram_cell_I_on += alpha * scan_five_input_double(line, "-dram_cell_I_on", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_Vdd"):
        #         self.dram_cell_Vdd += alpha * scan_five_input_double(line, "-dram_cell_Vdd", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_C"):
        #         self.dram_cell_C += alpha * scan_five_input_double(line, "-dram_cell_C", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_I_off_worst_case_len_temp"):
        #         self.dram_cell_I_off_worst_case_len_temp += alpha * scan_five_input_double(line, "-dram_cell_I_off_worst_case_len_temp", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-vpp"):
        #         self.vpp += alpha * scan_five_input_double(line, "-vpp", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-sckt_co_eff"):
        #         self.sckt_co_eff += alpha * scan_single_input_double(line, "-sckt_co_eff", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-chip_layout_overhead"):
        #         self.chip_layout_overhead += alpha * scan_single_input_double(line, "-chip_layout_overhead", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-macro_layout_overhead"):
        #         self.macro_layout_overhead += alpha * scan_single_input_double(line, "-macro_layout_overhead", "F/um", g_ip.print_detail_debug)

        peri_global_lo = DeviceType()
        peri_global_hi = DeviceType()
        peri_global_lo.assign(in_file_lo, peri_global_tech_type, g_ip.temp)
        # peri_global_lo.display()
        peri_global_hi.assign(in_file_hi, peri_global_tech_type, g_ip.temp)
        # peri_global_hi.display()
        
        self.peri_global.interpolate(alpha, peri_global_lo, peri_global_hi)
        # self.peri_global.display()

        sleep_tx_lo = DeviceType()
        sleep_tx_hi = DeviceType()
        sleep_tx_lo.assign(in_file_lo, 1, g_ip.temp)
        sleep_tx_hi.assign(in_file_hi, 1, g_ip.temp)
        self.sleep_tx.interpolate(alpha, sleep_tx_lo, sleep_tx_hi)

        sram_cell_lo = DeviceType()
        sram_cell_hi = DeviceType()
        sram_cell_lo.assign(in_file_lo, ram_cell_tech_type, g_ip.temp)
        sram_cell_hi.assign(in_file_hi, ram_cell_tech_type, g_ip.temp)
        self.sram_cell.interpolate(alpha, sram_cell_lo, sram_cell_hi)

        dram_acc_lo = DeviceType()
        dram_acc_hi = DeviceType()
        dram_acc_lo.assign(in_file_lo, ram_cell_tech_type if ram_cell_tech_type == comm_dram else dram_cell_tech_flavor, g_ip.temp)
        dram_acc_hi.assign(in_file_hi, ram_cell_tech_type if ram_cell_tech_type == comm_dram else dram_cell_tech_flavor, g_ip.temp)
        self.dram_acc.interpolate(alpha, dram_acc_lo, dram_acc_hi)
        if tech_lo <= 22:
            pass
        elif tech_lo <= 32:
            self.dram_acc.Vth = 0.44129 if ram_cell_tech_type == lp_dram else 1.0
        elif tech_lo <= 45:
            self.dram_acc.Vth = 0.44559 if ram_cell_tech_type == lp_dram else 1.0
        elif tech_lo <= 65:
            self.dram_acc.Vth = 0.43806 if ram_cell_tech_type == lp_dram else 1.0
        elif tech_lo <= 90:
            self.dram_acc.Vth = 0.4545 if ram_cell_tech_type == lp_dram else 1.0

        self.dram_acc.Vdd = 0.0
        self.dram_acc.I_on_p = 0.0
        self.dram_acc.I_off_n = 0.0
        self.dram_acc.I_off_p = 0.0
        self.dram_acc.C_ox = 0.0
        self.dram_acc.t_ox = 0.0
        self.dram_acc.n_to_p_eff_curr_drv_ratio = 0.0

        dram_wl_lo = DeviceType()
        dram_wl_hi = DeviceType()
        dram_wl_lo.assign(in_file_lo, ram_cell_tech_type if ram_cell_tech_type == comm_dram else dram_cell_tech_flavor, g_ip.temp)
        dram_wl_hi.assign(in_file_hi, ram_cell_tech_type if ram_cell_tech_type == comm_dram else dram_cell_tech_flavor, g_ip.temp)
        self.dram_wl.interpolate(alpha, dram_wl_lo, dram_wl_hi)

        self.dram_wl.Vdd = 0.0
        self.dram_wl.Vth = 0.0
        self.dram_wl.I_on_p = 0.0
        self.dram_wl.C_ox = 0.0
        self.dram_wl.t_ox = 0.0

        if ram_cell_tech_type < 3:
            self.dram_acc.reset()
            self.dram_wl.reset()

        cam_cell_lo = DeviceType()
        cam_cell_hi = DeviceType()
        cam_cell_lo.assign(in_file_lo, ram_cell_tech_type, g_ip.temp)
        cam_cell_hi.assign(in_file_hi, ram_cell_tech_type, g_ip.temp)
        self.cam_cell.interpolate(alpha, cam_cell_lo, cam_cell_hi)

        dram_lo = MemoryType()
        dram_hi = MemoryType()
        dram_lo.assign(in_file_lo, ram_cell_tech_type, 2)  # cell_type = dram(2)
        dram_hi.assign(in_file_hi, ram_cell_tech_type, 2)
        self.dram.interpolate(alpha, dram_lo, dram_hi)

        sram_lo = MemoryType()
        sram_hi = MemoryType()
        sram_lo.assign(in_file_lo, ram_cell_tech_type, 0)  # cell_type = sram(0)
        sram_hi.assign(in_file_hi, ram_cell_tech_type, 0)
        self.sram.interpolate(alpha, sram_lo, sram_hi)

        cam_lo = MemoryType()
        cam_hi = MemoryType()
        cam_lo.assign(in_file_lo, ram_cell_tech_type, 1)  # cell_type = sram(0)
        cam_hi.assign(in_file_hi, ram_cell_tech_type, 1)
        self.cam.interpolate(alpha, cam_lo, cam_hi)

        scaling_factor_lo = ScalingFactor()
        scaling_factor_hi = ScalingFactor()
        scaling_factor_lo.assign(in_file_lo)
        scaling_factor_hi.assign(in_file_hi)
        self.scaling_factor.interpolate(alpha, scaling_factor_lo, scaling_factor_hi)

        self.peri_global.Vcc_min += (alpha * peri_global_lo.Vdd + (1 - alpha) * peri_global_hi.Vdd) * 0.35
        self.sleep_tx.Vcc_min += alpha * sleep_tx_lo.Vdd + (1 - alpha) * sleep_tx_hi.Vdd
        self.sram_cell.Vcc_min += (alpha * sram_cell_lo.Vdd + (1 - alpha) * sram_cell_hi.Vdd) * 0.65

        with open(in_file_hi, "r") as fp:
            lines = fp.readlines()

        self.sense_delay = sympy_var['sense_delay']
        self.sense_dy_power = sympy_var['sense_dy_power']
        self.sckt_co_eff = sympy_var['sckt_co_eff']
        self.chip_layout_overhead = sympy_var['chip_layout_overhead']
        self.macro_layout_overhead = sympy_var['macro_layout_overhead']
        self.dram_cell_I_on = sympy_var['dram_cell_I_on']
        self.dram_cell_Vdd = sympy_var['dram_cell_Vdd']
        self.dram_cell_C = sympy_var['dram_cell_C']
        self.dram_cell_I_off_worst_case_len_temp = sympy_var['dram_cell_I_off_worst_case_len_temp']
        self.vpp = sympy_var['vpp']

        # for line in lines:
        #     if line.startswith("-sense_delay"):
        #         self.sense_delay = scan_single_input_double(line, "-sense_delay", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-sense_dy_power"):
        #         self.sense_dy_power = scan_single_input_double(line, "-sense_dy_power", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-sckt_co_eff"):
        #         self.sckt_co_eff += (1 - alpha) * scan_single_input_double(line, "-sckt_co_eff", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-chip_layout_overhead"):
        #         self.chip_layout_overhead += (1 - alpha) * scan_single_input_double(line, "-chip_layout_overhead", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-macro_layout_overhead"):
        #         self.macro_layout_overhead += (1 - alpha) * scan_single_input_double(line, "-macro_layout_overhead", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_I_on"):
        #         self.dram_cell_I_on += (1 - alpha) * scan_five_input_double(line, "-dram_cell_I_on", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_Vdd"):
        #         self.dram_cell_Vdd += (1 - alpha) * scan_five_input_double(line, "-dram_cell_Vdd", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_C"):
        #         self.dram_cell_C += (1 - alpha) * scan_five_input_double(line, "-dram_cell_C", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_I_off_worst_case_len_temp"):
        #         self.dram_cell_I_off_worst_case_len_temp += (1 - alpha) * scan_five_input_double(line, "-dram_cell_I_off_worst_case_len_temp", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-vpp"):
        #         self.vpp += (1 - alpha) * scan_five_input_double(line, "-vpp", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)

        self.w_comp_inv_p1 = 12.5 * g_ip.F_sz_um
        self.w_comp_inv_n1 = 7.5 * g_ip.F_sz_um
        self.w_comp_inv_p2 = 25 * g_ip.F_sz_um
        self.w_comp_inv_n2 = 15 * g_ip.F_sz_um
        self.w_comp_inv_p3 = 50 * g_ip.F_sz_um
        self.w_comp_inv_n3 = 30 * g_ip.F_sz_um
        self.w_eval_inv_p = 100 * g_ip.F_sz_um
        self.w_eval_inv_n = 50 * g_ip.F_sz_um
        self.w_comp_n = 12.5 * g_ip.F_sz_um
        self.w_comp_p = 37.5 * g_ip.F_sz_um
        self.MIN_GAP_BET_P_AND_N_DIFFS = 5 * g_ip.F_sz_um
        self.MIN_GAP_BET_SAME_TYPE_DIFFS = 1.5 * g_ip.F_sz_um
        self.HPOWERRAIL = 2 * g_ip.F_sz_um
        self.cell_h_def = 50 * g_ip.F_sz_um
        self.w_poly_contact = g_ip.F_sz_um
        self.spacing_poly_to_contact = g_ip.F_sz_um
        self.spacing_poly_to_poly = 1.5 * g_ip.F_sz_um
        self.ram_wl_stitching_overhead_ = 7.5 * g_ip.F_sz_um
        self.min_w_nmos_ = 3 * g_ip.F_sz_um / 2
        self.max_w_nmos_ = 100 * g_ip.F_sz_um
        self.w_iso = 12.5 * g_ip.F_sz_um
        self.w_sense_n = 3.75 * g_ip.F_sz_um
        self.w_sense_p = 7.5 * g_ip.F_sz_um
        self.w_sense_en = 5 * g_ip.F_sz_um
        self.w_nmos_b_mux = 6 * self.min_w_nmos_
        self.w_nmos_sa_mux = 6 * self.min_w_nmos_
        self.w_pmos_bl_precharge = 6 * pmos_to_nmos_sz_ratio() * self.min_w_nmos_
        self.w_pmos_bl_eq = pmos_to_nmos_sz_ratio() * self.min_w_nmos_

        if ram_cell_tech_type == comm_dram:
            self.max_w_nmos_dec = 8 * g_ip.F_sz_um
            self.h_dec = 8  # in the unit of memory cell height
        else:
            self.max_w_nmos_dec = self.max_w_nmos_
            self.h_dec = 4  # in the unit of memory cell height

        gmn_sense_amp_latch = (self.peri_global.Mobility_n / 2) * self.peri_global.C_ox * (self.w_sense_n / self.peri_global.l_elec) * self.peri_global.Vdsat
        gmp_sense_amp_latch = self.peri_global.gmp_to_gmn_multiplier * gmn_sense_amp_latch
        self.gm_sense_amp_latch = gmn_sense_amp_latch + gmp_sense_amp_latch

        wire_local_lo = InterconnectType()
        wire_local_hi = InterconnectType()
        wire_local_lo.assign(in_file_lo, g_ip.ic_proj_type, 3 if ram_cell_tech_type == comm_dram else 0)
        wire_local_hi.assign(in_file_hi, g_ip.ic_proj_type, 3 if ram_cell_tech_type == comm_dram else 0)
        self.wire_local.interpolate(alpha, wire_local_lo, wire_local_hi)

        wire_inside_mat_lo = InterconnectType()
        wire_inside_mat_hi = InterconnectType()
        wire_inside_mat_lo.assign(in_file_lo, g_ip.ic_proj_type, g_ip.wire_is_mat_type)
        wire_inside_mat_hi.assign(in_file_hi, g_ip.ic_proj_type, g_ip.wire_is_mat_type)
        self.wire_inside_mat.interpolate(alpha, wire_inside_mat_lo, wire_inside_mat_hi)

        wire_outside_mat_lo = InterconnectType()
        wire_outside_mat_hi = InterconnectType()
        wire_outside_mat_lo.assign(in_file_lo, g_ip.ic_proj_type, g_ip.wire_os_mat_type)
        wire_outside_mat_hi.assign(in_file_hi, g_ip.ic_proj_type, g_ip.wire_os_mat_type)
        self.wire_outside_mat.interpolate(alpha, wire_outside_mat_lo, wire_outside_mat_hi)

        self.unit_len_wire_del = self.wire_inside_mat.R_per_um * self.wire_inside_mat.C_per_um / 2

        self.assign_tsv(in_file_hi)

        self.fringe_cap = wire_local_hi.fringe_cap

        rd = tr_R_on(self.min_w_nmos_, NCH, 1)
        p_to_n_sizing_r = pmos_to_nmos_sz_ratio()
        c_load = gate_C(self.min_w_nmos_ * (1 + p_to_n_sizing_r), 0.0)
        tf = rd * c_load
        self.kinv = horowitz(0, tf, 0.5, 0.5, RISE)
        KLOAD = 1
        c_load = KLOAD * (drain_C_(self.min_w_nmos_, NCH, 1, 1, self.cell_h_def) +
                          drain_C_(self.min_w_nmos_ * p_to_n_sizing_r, PCH, 1, 1, self.cell_h_def) +
                          gate_C(self.min_w_nmos_ * 4 * (1 + p_to_n_sizing_r), 0.0))
        tf = rd * c_load
        self.FO4 = horowitz(0, tf, 0.5, 0.5, RISE)

    def isEqual(self, tech):
        if not is_equal(self.ram_wl_stitching_overhead_, tech.ram_wl_stitching_overhead_):
            assert False  # fs
        if not is_equal(self.min_w_nmos_, tech.min_w_nmos_):
            assert False  # fs
        if not is_equal(self.max_w_nmos_, tech.max_w_nmos_):
            assert False  # fs
        if not is_equal(self.max_w_nmos_dec, tech.max_w_nmos_dec):
            assert False  # fs + ram_cell_tech_type
        if not is_equal(self.unit_len_wire_del, tech.unit_len_wire_del):
            assert False  # wire_inside_mat
        if not is_equal(self.FO4, tech.FO4):
            assert False  # fs
        if not is_equal(self.kinv, tech.kinv):
            assert False  # fs
        if not is_equal(self.vpp, tech.vpp):
            assert False  # input 
        if not is_equal(self.w_sense_en, tech.w_sense_en):
            assert False  # fs
        if not is_equal(self.w_sense_n, tech.w_sense_n):
            assert False  # fs
        if not is_equal(self.w_sense_p, tech.w_sense_p):
            assert False  # fs
        if not is_equal(self.sense_delay, tech.sense_delay):
            PRINT("sense_delay", self.sense_delay, tech)
            assert False  # input
        if not is_equal(self.sense_dy_power, tech.sense_dy_power):
            assert False  # input
        if not is_equal(self.w_iso, tech.w_iso):
            assert False  # fs
        if not is_equal(self.w_poly_contact, tech.w_poly_contact):
            assert False  # fs
        if not is_equal(self.spacing_poly_to_poly, tech.spacing_poly_to_poly):
            assert False  # fs
        if not is_equal(self.spacing_poly_to_contact, tech.spacing_poly_to_contact):
            assert False  # fs

        # CACTI3D auxiliary variables
        # if not is_equal(self.tsv_pitch, tech.tsv_pitch):
        #     assert False
        # if not is_equal(self.tsv_diameter, tech.tsv_diameter):
        #     assert False
        # if not is_equal(self.tsv_length, tech.tsv_length):
        #     assert False
        # if not is_equal(self.tsv_dielec_thickness, tech.tsv_dielec_thickness):
        #     assert False
        # if not is_equal(self.tsv_contact_resistance, tech.tsv_contact_resistance):
        #     assert False
        # if not is_equal(self.tsv_depletion_width, tech.tsv_depletion_width):
        #     assert False
        # if not is_equal(self.tsv_liner_dielectric_constant, tech.tsv_liner_dielectric_constant):
        #     assert False

        # CACTI3DD TSV params
        if not is_equal(self.tsv_parasitic_capacitance_fine, tech.tsv_parasitic_capacitance_fine):
            PRINT("tsv_parasitic_capacitance_fine", self.tsv_parasitic_capacitance_fine, tech)
            assert False
        if not is_equal(self.tsv_parasitic_resistance_fine, tech.tsv_parasitic_resistance_fine):
            assert False
        if not is_equal(self.tsv_minimum_area_fine, tech.tsv_minimum_area_fine):
            assert False

        if not is_equal(self.tsv_parasitic_capacitance_coarse, tech.tsv_parasitic_capacitance_coarse):
            assert False
        if not is_equal(self.tsv_parasitic_resistance_coarse, tech.tsv_parasitic_resistance_coarse):
            assert False
        if not is_equal(self.tsv_minimum_area_coarse, tech.tsv_minimum_area_coarse):
            assert False

        # fs
        if not is_equal(self.w_comp_inv_p1, tech.w_comp_inv_p1):
            assert False
        if not is_equal(self.w_comp_inv_p2, tech.w_comp_inv_p2):
            assert False
        if not is_equal(self.w_comp_inv_p3, tech.w_comp_inv_p3):
            assert False
        if not is_equal(self.w_comp_inv_n1, tech.w_comp_inv_n1):
            assert False
        if not is_equal(self.w_comp_inv_n2, tech.w_comp_inv_n2):
            assert False
        if not is_equal(self.w_comp_inv_n3, tech.w_comp_inv_n3):
            assert False
        if not is_equal(self.w_eval_inv_p, tech.w_eval_inv_p):
            assert False
        if not is_equal(self.w_eval_inv_n, tech.w_eval_inv_n):
            assert False
        if not is_equal(self.w_comp_n, tech.w_comp_n):
            assert False
        if not is_equal(self.w_comp_p, tech.w_comp_p):
            assert False

        if not is_equal(self.dram_cell_I_on, tech.dram_cell_I_on):
            assert False  # ram_cell_tech_type
        if not is_equal(self.dram_cell_Vdd, tech.dram_cell_Vdd):
            assert False
        if not is_equal(self.dram_cell_I_off_worst_case_len_temp, tech.dram_cell_I_off_worst_case_len_temp):
            assert False
        if not is_equal(self.dram_cell_C, tech.dram_cell_C):
            assert False
        if not is_equal(self.gm_sense_amp_latch, tech.gm_sense_amp_latch):
            assert False  # depends on many things

        if not is_equal(self.w_nmos_b_mux, tech.w_nmos_b_mux):
            assert False  # fs
        if not is_equal(self.w_nmos_sa_mux, tech.w_nmos_sa_mux):
            assert False  # fs
        if not is_equal(self.w_pmos_bl_precharge, tech.w_pmos_bl_precharge):
            PRINT("w_pmos_bl_precharge", self.w_pmos_bl_precharge, tech)
            assert False  # fs
        if not is_equal(self.w_pmos_bl_eq, tech.w_pmos_bl_eq):
            assert False  # fs
        if not is_equal(self.MIN_GAP_BET_P_AND_N_DIFFS, tech.MIN_GAP_BET_P_AND_N_DIFFS):
            assert False  # fs
        if not is_equal(self.MIN_GAP_BET_SAME_TYPE_DIFFS, tech.MIN_GAP_BET_SAME_TYPE_DIFFS):
            assert False  # fs
        if not is_equal(self.HPOWERRAIL, tech.HPOWERRAIL):
            assert False  # fs
        if not is_equal(self.cell_h_def, tech.cell_h_def):
            assert False  # fs

        if not is_equal(self.chip_layout_overhead, tech.chip_layout_overhead):
            assert False  # input
        if not is_equal(self.macro_layout_overhead, tech.macro_layout_overhead):
            print(f"{self.macro_layout_overhead} vs. {tech.macro_layout_overhead}")
            assert False
        if not is_equal(self.sckt_co_eff, tech.sckt_co_eff):
            assert False

        if not is_equal(self.fringe_cap, tech.fringe_cap):
            PRINT("fringe_cap", self.fringe_cap, tech)
            assert False  # input

        if self.h_dec != tech.h_dec:
            assert False  # ram_cell_tech_type

        print("sram_cell")
        self.sram_cell.isEqual(tech.sram_cell)  # SRAM cell transistor
        print("dram_acc")
        self.dram_acc.isEqual(tech.dram_acc)  # DRAM access transistor
        print("dram_wl")
        self.dram_wl.isEqual(tech.dram_wl)  # DRAM wordline transistor
        print("peri_global")
        self.peri_global.isEqual(tech.peri_global)  # peripheral global
        print("cam_cell")
        self.cam_cell.isEqual(tech.cam_cell)  # SRAM cell transistor

        print("sleep_tx")
        self.sleep_tx.isEqual(tech.sleep_tx)  # Sleep transistor cell transistor

        print("wire_local")
        self.wire_local.isEqual(tech.wire_local)
        print("wire_inside_mat")
        self.wire_inside_mat.isEqual(tech.wire_inside_mat)
        print("wire_outside_mat")
        self.wire_outside_mat.isEqual(tech.wire_outside_mat)

        print("scaling_factor")
        self.scaling_factor.isEqual(tech.scaling_factor)
        print("sram:")
        self.sram.isEqual(tech.sram)
        print("dram:")
        self.dram.isEqual(tech.dram)
        print("cam:")
        self.cam.isEqual(tech.cam)

        return True

def is_equal(first, second):
    if first == 0 and second == 0:
        return True

    if second == 0 or sp.is_nan(second):
        return True

    if sp.is_nan(first) or sp.is_nan(second):
        return True

    if first == 0:
        if abs(first - second) < (second * 0.000001):
            return True
    else:
        if abs(first - second) < (first * 0.000001):
            return True

    return False

class DeviceType:
    def __init__(self):
        self.C_g_ideal = 0
        self.C_fringe = 0
        self.C_overlap = 0
        self.C_junc = 0  # C_junc_area
        self.C_junc_sidewall = 0
        self.l_phy = 0
        self.l_elec = 0
        self.R_nch_on = 0
        self.R_pch_on = 0
        self.Vdd = 0
        self.Vth = 0
        self.Vcc_min = 0  # allowed min vcc; for memory cell it is the lowest vcc for data retention. for logic it is the vcc to balance the leakage reduction and wakeup latency
        self.I_on_n = 0
        self.I_on_p = 0
        self.I_off_n = 0
        self.I_off_p = 0
        self.I_g_on_n = 0
        self.I_g_on_p = 0
        self.C_ox = 0
        self.t_ox = 0
        self.n_to_p_eff_curr_drv_ratio = 0
        self.long_channel_leakage_reduction = 0
        self.Mobility_n = 0

        # self.n_to_p_eff_curr_drv_ratio = sympy_var['n2p_drv_rt']

        # auxiliary parameters
        self.Vdsat = 0
        self.gmp_to_gmn_multiplier = 0

        self.C_g_ideal = sympy_var['C_g_ideal']
        self.C_fringe = sympy_var['C_fringe']
        self.C_junc_sidewall = sympy_var['C_junc_sw']
        self.C_junc = sympy_var['C_junc']
        self.l_phy = sympy_var['l_phy']
        self.l_elec = sympy_var['l_elec']
        self.nmos_effective_resistance_multiplier = sympy_var['nmos_effective_resistance_multiplier']
        self.Vdd = sympy_var['Vdd']
        self.Vth = sympy_var['Vth']
        self.Vdsat = sympy_var['Vdsat']
        self.I_on_n = sympy_var['I_on_n']
        self.I_on_p = sympy_var['I_on_p']
        self.I_off_n = sympy_var['I_off_n']
        self.I_g_on_n = sympy_var['I_g_on_n']
        self.C_ox = sympy_var['C_ox']
        self.t_ox = sympy_var['t_ox']
        self.n_to_p_eff_curr_drv_ratio = sympy_var['n2p_drv_rt']
        self.long_channel_leakage_reduction = sympy_var['lch_lk_rdc']
        self.Mobility_n = sympy_var['Mobility_n']
        self.gmp_to_gmn_multiplier = sympy_var['gmp_to_gmn_multiplier']

        self.C_overlap = 0.2 * self.C_g_ideal
        self.I_off_p = self.I_off_n
        self.I_g_on_p = self.I_g_on_n

    def reset(self):
        self.C_g_ideal = 0
        self.C_fringe = 0
        self.C_overlap = 0
        self.C_junc = 0  # C_junc_area
        self.C_junc_sidewall = 0
        self.l_phy = 0
        self.l_elec = 0
        self.R_nch_on = 0
        self.R_pch_on = 0
        self.Vdd = 0
        self.Vth = 0
        self.Vcc_min = 0  # allowed min vcc; for memory cell it is the lowest vcc for data retention. for logic it is the vcc to balance the leakage reduction and wakeup latency
        self.I_on_n = 0
        self.I_on_p = 0
        self.I_off_n = 0
        self.I_off_p = 0
        self.I_g_on_n = 0
        self.I_g_on_p = 0
        self.C_ox = 0
        self.t_ox = 0
        self.n_to_p_eff_curr_drv_ratio = 0
        self.long_channel_leakage_reduction = 0
        self.Mobility_n = 0

        # auxiliary parameters
        self.Vdsat = 0
        self.gmp_to_gmn_multiplier = 0

        self.C_g_ideal = sympy_var['C_g_ideal']
        self.C_fringe = sympy_var['C_fringe']
        self.C_junc_sidewall = sympy_var['C_junc_sw']
        self.C_junc = sympy_var['C_junc']
        self.l_phy = sympy_var['l_phy']
        self.l_elec = sympy_var['l_elec']
        self.nmos_effective_resistance_multiplier = sympy_var['nmos_effective_resistance_multiplier']
        self.Vdd = sympy_var['Vdd']
        self.Vth = sympy_var['Vth']
        self.Vdsat = sympy_var['Vdsat']
        self.I_on_n = sympy_var['I_on_n']
        self.I_on_p = sympy_var['I_on_p']
        self.I_off_n = sympy_var['I_off_n']
        self.I_g_on_n = sympy_var['I_g_on_n']
        self.C_ox = sympy_var['C_ox']
        self.t_ox = sympy_var['t_ox']
        self.n_to_p_eff_curr_drv_ratio = sympy_var['n2p_drv_rt']
        self.long_channel_leakage_reduction = sympy_var['lch_lk_rdc']
        self.Mobility_n = sympy_var['Mobility_n']
        self.gmp_to_gmn_multiplier = sympy_var['gmp_to_gmn_multiplier']

        self.C_overlap = 0.2 * self.C_g_ideal
        self.I_off_p = self.I_off_n
        self.I_g_on_p = self.I_g_on_n

    def display(self, indent=0):
        indent_str = ' ' * indent
        print(f"{indent_str}C_g_ideal = {self.C_g_ideal} F/um")
        print(f"{indent_str}C_fringe  = {self.C_fringe} F/um")
        print(f"{indent_str}C_overlap = {self.C_overlap} F/um")
        print(f"{indent_str}C_junc    = {self.C_junc} F/um^2")
        print(f"{indent_str}C_junc_sw = {self.C_junc_sidewall} F/um^2")
        print(f"{indent_str}l_phy     = {self.l_phy} um")
        print(f"{indent_str}l_elec    = {self.l_elec} um")
        print(f"{indent_str}R_nch_on  = {self.R_nch_on} ohm-um")
        print(f"{indent_str}R_pch_on  = {self.R_pch_on} ohm-um")
        print(f"{indent_str}Vdd       = {self.Vdd} V")
        print(f"{indent_str}Vth       = {self.Vth} V")
        print(f"{indent_str}I_on_n    = {self.I_on_n} A/um")
        print(f"{indent_str}I_on_p    = {self.I_on_p} A/um")
        print(f"{indent_str}I_off_n   = {self.I_off_n} A/um")
        print(f"{indent_str}I_off_p   = {self.I_off_p} A/um")
        print(f"{indent_str}C_ox      = {self.C_ox} F/um^2")
        print(f"{indent_str}t_ox      = {self.t_ox} um")
        print(f"{indent_str}n_to_p_eff_curr_drv_ratio = {self.n_to_p_eff_curr_drv_ratio}")

    def isEqual(self, dev):
        if not is_equal(self.C_g_ideal, dev.C_g_ideal): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.C_fringe, dev.C_fringe): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.C_overlap, dev.C_overlap): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.C_junc, dev.C_junc): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.C_junc_sidewall, dev.C_junc_sidewall): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.l_phy, dev.l_phy): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.l_elec, dev.l_elec): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.R_nch_on, dev.R_nch_on): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.R_pch_on, dev.R_pch_on): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.Vdd, dev.Vdd): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.Vth, dev.Vth): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.I_on_n, dev.I_on_n): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.I_on_p, dev.I_on_p): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.I_off_n, dev.I_off_n): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.I_off_p, dev.I_off_p): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.I_g_on_n, dev.I_g_on_n): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.I_g_on_p, dev.I_g_on_p): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.C_ox, dev.C_ox): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.t_ox, dev.t_ox): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.n_to_p_eff_curr_drv_ratio, dev.n_to_p_eff_curr_drv_ratio): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.long_channel_leakage_reduction, dev.long_channel_leakage_reduction): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.Mobility_n, dev.Mobility_n): self.display(); print("\n\n\n"); dev.display(); assert False
        return True

    def assign(self, in_file, tech_flavor, temperature):
        with open(in_file, 'r') as fp:
            lines = fp.readlines()

        nmos_effective_resistance_multiplier = 0

        self.C_g_ideal = sympy_var['C_g_ideal']
        self.C_fringe = sympy_var['C_fringe']
        self.C_junc_sidewall = sympy_var['C_junc_sw']
        self.C_junc = sympy_var['C_junc']
        self.l_phy = sympy_var['l_phy']
        self.l_elec = sympy_var['l_elec']
        self.nmos_effective_resistance_multiplier = sympy_var['nmos_effective_resistance_multiplier']
        self.Vdd = sympy_var['Vdd']
        self.Vth = sympy_var['Vth']
        self.Vdsat = sympy_var['Vdsat']
        self.I_on_n = sympy_var['I_on_n']
        self.I_on_p = sympy_var['I_on_p']
        self.I_off_n = sympy_var['I_off_n']
        self.I_g_on_n = sympy_var['I_g_on_n']
        self.C_ox = sympy_var['C_ox']
        self.t_ox = sympy_var['t_ox']
        self.n_to_p_eff_curr_drv_ratio = sympy_var['n2p_drv_rt']
        self.long_channel_leakage_reduction = sympy_var['lch_lk_rdc']
        self.Mobility_n = sympy_var['Mobility_n']
        self.gmp_to_gmn_multiplier = sympy_var['gmp_to_gmn_multiplier']

        # for line in lines:
        #     if line.startswith("-C_g_ideal"):
        #         self.C_g_ideal = scan_five_input_double(line, "-C_g_ideal", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-C_fringe"):
        #         self.C_fringe = scan_five_input_double(line, "-C_fringe", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-C_junc_sw"):
        #         self.C_junc_sidewall = scan_five_input_double(line, "-C_junc_sw", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-C_junc"):
        #         self.C_junc = scan_five_input_double(line, "-C_junc", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-l_phy"):
        #         self.l_phy = scan_five_input_double(line, "-l_phy", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-l_elec"):
        #         print("HERE!")
        #         self.l_elec = scan_five_input_double(line, "-l_elec", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         print(self.l_elec)
        #         print()
        #         continue
        #     if line.startswith("-nmos_effective_resistance_multiplier"):
        #         nmos_effective_resistance_multiplier = scan_five_input_double(line, "-nmos_effective_resistance_multiplier", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-Vdd"):
        #         self.Vdd = scan_five_input_double(line, "-Vdd", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-Vth"):
        #         self.Vth = scan_five_input_double(line, "-Vth", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-Vdsat"):
        #         self.Vdsat = scan_five_input_double(line, "-Vdsat", "V", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-I_on_n"):
        #         self.I_on_n = scan_five_input_double(line, "-I_on_n", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-I_on_p"):
        #         self.I_on_p = scan_five_input_double(line, "-I_on_p", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-I_off_n"):
        #         scan_five_input_double_temperature(line, "-I_off_n", "F/um", tech_flavor, temperature, g_ip.print_detail_debug, self.I_off_n)
        #         continue
        #     if line.startswith("-I_g_on_n"):
        #         scan_five_input_double_temperature(line, "-I_g_on_n", "F/um", tech_flavor, temperature, g_ip.print_detail_debug, self.I_g_on_n)
        #         continue
        #     if line.startswith("-C_ox"):
        #         self.C_ox = scan_five_input_double(line, "-C_ox", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-t_ox"):
        #         self.t_ox = scan_five_input_double(line, "-t_ox", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-n2p_drv_rt"):
        #         self.n_to_p_eff_curr_drv_ratio = scan_five_input_double(line, "-n2p_drv_rt", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-lch_lk_rdc"):
        #         self.long_channel_leakage_reduction = scan_five_input_double(line, "-lch_lk_rdc", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-Mobility_n"):
        #         self.Mobility_n = scan_five_input_double(line, "-Mobility_n", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-gmp_to_gmn_multiplier"):
        #         self.gmp_to_gmn_multiplier = scan_five_input_double(line, "-gmp_to_gmn_multiplier", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue

        self.C_overlap = 0.2 * self.C_g_ideal
        if tech_flavor >= 3:
            self.R_nch_on = self.nmos_effective_resistance_multiplier * g_tp.vpp / self.I_on_n
        else:
            self.R_nch_on = self.nmos_effective_resistance_multiplier * self.Vdd / self.I_on_n
        # CHECKPOINT _pch_on issue
        # print(f"nmos_effective_resistance_multiplier {nmos_effective_resistance_multiplier}")
        # print(f"tech_flavor {tech_flavor}")
        # print(f"self.I_on_n {self.I_on_n}")
        # print(f"self.R_nch {self.R_nch_on}")
        self.R_pch_on = self.n_to_p_eff_curr_drv_ratio * self.R_nch_on
        self.I_off_p = self.I_off_n
        self.I_g_on_p = self.I_g_on_n
        if g_ip.print_detail_debug:
            print(f"C_overlap: {self.C_overlap} F/um")
            print(f"R_nch_on: {self.R_nch_on} ohm-micron")
            print(f"R_pch_on: {self.R_pch_on} ohm-micron")

    def interpolate(self, alpha, dev1, dev2):
        result = DeviceType()
        self.C_g_ideal = alpha * dev1.C_g_ideal + (1 - alpha) * dev2.C_g_ideal
        self.C_fringe = alpha * dev1.C_fringe + (1 - alpha) * dev2.C_fringe
        self.C_overlap = alpha * dev1.C_overlap + (1 - alpha) * dev2.C_overlap
        self.C_junc = alpha * dev1.C_junc + (1 - alpha) * dev2.C_junc
        self.l_phy = alpha * dev1.l_phy + (1 - alpha) * dev2.l_phy
        self.l_elec = alpha * dev1.l_elec + (1 - alpha) * dev2.l_elec
        self.R_nch_on = alpha * dev1.R_nch_on + (1 - alpha) * dev2.R_nch_on
        self.R_pch_on = alpha * dev1.R_pch_on + (1 - alpha) * dev2.R_pch_on
        self.Vdd = alpha * dev1.Vdd + (1 - alpha) * dev2.Vdd
        self.Vth = alpha * dev1.Vth + (1 - alpha) * dev2.Vth
        self.Vcc_min = alpha * dev1.Vcc_min + (1 - alpha) * dev2.Vcc_min
        self.I_on_n = alpha * dev1.I_on_n + (1 - alpha) * dev2.I_on_n
        self.I_on_p = alpha * dev1.I_on_p + (1 - alpha) * dev2.I_on_p
        self.I_off_n = alpha * dev1.I_off_n + (1 - alpha) * dev2.I_off_n
        self.I_off_p = alpha * dev1.I_off_p + (1 - alpha) * dev2.I_off_p
        self.I_g_on_n = alpha * dev1.I_g_on_n + (1 - alpha) * dev2.I_g_on_n
        self.I_g_on_p = alpha * dev1.I_g_on_p + (1 - alpha) * dev2.I_g_on_p
        self.C_ox = alpha * dev1.C_ox + (1 - alpha) * dev2.C_ox
        self.t_ox = alpha * dev1.t_ox + (1 - alpha) * dev2.t_ox
        self.n_to_p_eff_curr_drv_ratio = alpha * dev1.n_to_p_eff_curr_drv_ratio + (1 - alpha) * dev2.n_to_p_eff_curr_drv_ratio
        self.long_channel_leakage_reduction = alpha * dev1.long_channel_leakage_reduction + (1 - alpha) * dev2.long_channel_leakage_reduction
        self.Mobility_n = alpha * dev1.Mobility_n + (1 - alpha) * dev2.Mobility_n
        self.Vdsat = alpha * dev1.Vdsat + (1 - alpha) * dev2.Vdsat
        self.gmp_to_gmn_multiplier = alpha * dev1.gmp_to_gmn_multiplier + (1 - alpha) * dev2.gmp_to_gmn_multiplier
        self.C_junc_sidewall = dev1.C_junc_sidewall
    
class InterconnectType:
    def __init__(self):
        self.pitch = 0
        self.R_per_um = 0
        self.C_per_um = 0
        self.horiz_dielectric_constant = 0
        self.vert_dielectric_constant = 0
        self.aspect_ratio = 0
        self.miller_value = 0
        self.ild_thickness = 0

        # auxiliary parameters
        self.wire_width = 0
        self.wire_thickness = 0
        self.wire_spacing = 0
        self.barrier_thickness = 0
        self.dishing_thickness = 0
        self.alpha_scatter = 0
        self.fringe_cap = 0

        self.pitch = sympy_var['wire_pitch']
        self.barrier_thickness = sympy_var['barrier_thickness']
        self.dishing_thickness = sympy_var['dishing_thickness']
        self.alpha_scatter = sympy_var['alpha_scatter']
        self.aspect_ratio = sympy_var['aspect_ratio']
        self.miller_value = sympy_var['miller_value']
        self.horiz_dielectric_constant = sympy_var['horiz_dielectric_constant']
        self.vert_dielectric_constant = sympy_var['vert_dielectric_constant']
        self.ild_thickness = sympy_var['ild_thickness']
        self.fringe_cap = sympy_var['fringe_cap']
        self.R_per_um = sympy_var['wire_r_per_micron']
        self.C_per_um = sympy_var['wire_c_per_micron']
        self.resistivity = sympy_var['resistivity']
        self.pitch *= g_ip.F_sz_um
        self.wire_width = self.pitch / 2  # micron
        self.wire_thickness = self.aspect_ratio * self.wire_width  # micron
        self.wire_spacing = self.pitch - self.wire_width  # micron

        self.reset()

    def reset(self):
        self.pitch = 0
        self.R_per_um = 0
        self.C_per_um = 0
        self.horiz_dielectric_constant = 0
        self.vert_dielectric_constant = 0
        self.aspect_ratio = 0
        self.miller_value = 0
        self.ild_thickness = 0

        # auxiliary parameters
        self.wire_width = 0
        self.wire_thickness = 0
        self.wire_spacing = 0
        self.barrier_thickness = 0
        self.dishing_thickness = 0
        self.alpha_scatter = 0
        self.fringe_cap = 0

        self.pitch = sympy_var['wire_pitch']
        self.barrier_thickness = sympy_var['barrier_thickness']
        self.dishing_thickness = sympy_var['dishing_thickness']
        self.alpha_scatter = sympy_var['alpha_scatter']
        self.aspect_ratio = sympy_var['aspect_ratio']
        self.miller_value = sympy_var['miller_value']
        self.horiz_dielectric_constant = sympy_var['horiz_dielectric_constant']
        self.vert_dielectric_constant = sympy_var['vert_dielectric_constant']
        self.ild_thickness = sympy_var['ild_thickness']
        self.fringe_cap = sympy_var['fringe_cap']
        self.R_per_um = sympy_var['wire_r_per_micron']
        self.C_per_um = sympy_var['wire_c_per_micron']
        self.resistivity = sympy_var['resistivity']
        self.pitch *= g_ip.F_sz_um
        self.wire_width = self.pitch / 2  # micron
        self.wire_thickness = self.aspect_ratio * self.wire_width  # micron
        self.wire_spacing = self.pitch - self.wire_width  # micron

    def is_equal(self, inter):
        if not is_equal(self.pitch, inter.pitch): return False
        if not is_equal(self.R_per_um, inter.R_per_um): return False
        if not is_equal(self.C_per_um, inter.C_per_um): return False
        if not is_equal(self.horiz_dielectric_constant, inter.horiz_dielectric_constant): return False
        if not is_equal(self.vert_dielectric_constant, inter.vert_dielectric_constant): return False
        if not is_equal(self.aspect_ratio, inter.aspect_ratio): return False
        if not is_equal(self.miller_value, inter.miller_value): return False
        if not is_equal(self.ild_thickness, inter.ild_thickness): return False
        return True

    def display(self, indent=0):
        indent_str = ' ' * indent
        print(f"{indent_str}pitch = {self.pitch} um")
        print(f"{indent_str}R_per_um = {self.R_per_um} ohm/um")
        print(f"{indent_str}C_per_um = {self.C_per_um} F/um")
        print(f"{indent_str}horiz_dielectric_constant = {self.horiz_dielectric_constant}")
        print(f"{indent_str}vert_dielectric_constant = {self.vert_dielectric_constant}")
        print(f"{indent_str}aspect_ratio = {self.aspect_ratio}")
        print(f"{indent_str}miller_value = {self.miller_value}")
        print(f"{indent_str}ild_thickness = {self.ild_thickness} um")

    def assign(self, in_file, projection_type, tech_flavor):
        with open(in_file, 'r') as fp:
            lines = fp.readlines()

        resistivity = 0
        print_debug = g_ip.print_detail_debug

        self.pitch = sympy_var['wire_pitch']
        self.barrier_thickness = sympy_var['barrier_thickness']
        self.dishing_thickness = sympy_var['dishing_thickness']
        self.alpha_scatter = sympy_var['alpha_scatter']
        self.aspect_ratio = sympy_var['aspect_ratio']
        self.miller_value = sympy_var['miller_value']
        self.horiz_dielectric_constant = sympy_var['horiz_dielectric_constant']
        self.vert_dielectric_constant = sympy_var['vert_dielectric_constant']
        self.ild_thickness = sympy_var['ild_thickness']
        self.fringe_cap = sympy_var['fringe_cap']
        self.R_per_um = sympy_var['wire_r_per_micron']
        self.C_per_um = sympy_var['wire_c_per_micron']
        self.resistivity = sympy_var['resistivity']

        # for line in lines:
        #     if line.startswith("-wire_pitch"):
        #         self.pitch = scan_input_double_inter_type(line, "-wire_pitch", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-barrier_thickness"):
        #         self.barrier_thickness = scan_input_double_inter_type(line, "-barrier_thickness", "ohm", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-dishing_thickness"):
        #         self.dishing_thickness = scan_input_double_inter_type(line, "-dishing_thickness", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-alpha_scatter"):
        #         self.alpha_scatter = scan_input_double_inter_type(line, "-alpha_scatter", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-aspect_ratio"):
        #         self.aspect_ratio = scan_input_double_inter_type(line, "-aspect_ratio", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-miller_value"):
        #         self.miller_value = scan_input_double_inter_type(line, "-miller_value", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-horiz_dielectric_constant"):
        #         self.horiz_dielectric_constant = scan_input_double_inter_type(line, "-horiz_dielectric_constant", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-vert_dielectric_constant"):
        #         self.vert_dielectric_constant = scan_input_double_inter_type(line, "-vert_dielectric_constant", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-ild_thickness"):
        #         self.ild_thickness = scan_input_double_inter_type(line, "-ild_thickness", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-fringe_cap"):
        #         self.fringe_cap = scan_input_double_inter_type(line, "-fringe_cap", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-wire_r_per_micron"):
        #         self.R_per_um = scan_input_double_inter_type(line, "-wire_r_per_micron", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-wire_c_per_micron"):
        #         self.C_per_um = scan_input_double_inter_type(line, "-wire_c_per_micron", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-resistivity"):
        #         resistivity = scan_input_double_inter_type(line, "-resistivity", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue

        self.pitch *= g_ip.F_sz_um
        self.wire_width = self.pitch / 2  # micron
        self.wire_thickness = self.aspect_ratio * self.wire_width  # micron
        self.wire_spacing = self.pitch - self.wire_width  # micron

        if projection_type != 1 or tech_flavor != 3:
            self.R_per_um = wire_resistance(resistivity, self.wire_width,
                                            self.wire_thickness, self.barrier_thickness, self.dishing_thickness, self.alpha_scatter)  # ohm/micron
            if print_debug:
                print(f"{self.R_per_um} = wire_resistance({resistivity}, {self.wire_width}, {self.wire_thickness}, {self.barrier_thickness}, {self.dishing_thickness}, {self.alpha_scatter})")

            self.C_per_um = wire_capacitance(self.wire_width, self.wire_thickness, self.wire_spacing,
                                             self.ild_thickness, self.miller_value, self.horiz_dielectric_constant,
                                             self.vert_dielectric_constant, self.fringe_cap)  # F/micron
            if print_debug:
                print(f"{self.C_per_um} = wire_capacitance({self.wire_width}, {self.wire_thickness}, {self.wire_spacing}, {self.ild_thickness}, {self.miller_value}, {self.horiz_dielectric_constant}, {self.vert_dielectric_constant}, {self.fringe_cap})")

    def interpolate(self, alpha, inter1, inter2):
        self.pitch = alpha * inter1.pitch + (1 - alpha) * inter2.pitch
        self.R_per_um = alpha * inter1.R_per_um + (1 - alpha) * inter2.R_per_um
        self.C_per_um = alpha * inter1.C_per_um + (1 - alpha) * inter2.C_per_um
        self.horiz_dielectric_constant = alpha * inter1.horiz_dielectric_constant + (1 - alpha) * inter2.horiz_dielectric_constant
        self.vert_dielectric_constant = alpha * inter1.vert_dielectric_constant + (1 - alpha) * inter2.vert_dielectric_constant
        self.aspect_ratio = alpha * inter1.aspect_ratio + (1 - alpha) * inter2.aspect_ratio
        self.miller_value = alpha * inter1.miller_value + (1 - alpha) * inter2.miller_value
        self.ild_thickness = alpha * inter1.ild_thickness + (1 - alpha) * inter2.ild_thickness

class MemoryType:
    def __init__(self):
        self.b_w = 0
        self.b_h = 0
        self.cell_a_w = 0
        self.cell_pmos_w = 0
        self.cell_nmos_w = 0
        self.Vbitpre = 0
        self.Vbitfloating = 0
        self.area_cell = 0
        self.asp_ratio_cell = 0

        self.cell_a_w = sympy_var['Wmemcella']
        self.cell_pmos_w = sympy_var['Wmemcellpmos']
        self.cell_nmos_w = sympy_var['Wmemcellnmos']
        self.area_cell = sympy_var['area_cell']
        self.asp_ratio_cell = sympy_var['asp_ratio_cell']

        self.reset()

        self.cell_a_w = sympy_var['Wmemcella']
        self.cell_pmos_w = sympy_var['Wmemcellpmos']
        self.cell_nmos_w = sympy_var['Wmemcellnmos']
        self.area_cell = sympy_var['area_cell']
        self.asp_ratio_cell = sympy_var['asp_ratio_cell']
        self.cell_pmos_w *= g_ip.F_sz_um
        self.cell_nmos_w *= g_ip.F_sz_um

    def reset(self):
        self.b_w = 0
        self.b_h = 0
        self.cell_a_w = 0
        self.cell_pmos_w = 0
        self.cell_nmos_w = 0
        self.Vbitpre = 0
        self.Vbitfloating = 0
        self.area_cell = 0
        self.asp_ratio_cell = 0

        self.cell_a_w = sympy_var['Wmemcella']
        self.cell_pmos_w = sympy_var['Wmemcellpmos']
        self.cell_nmos_w = sympy_var['Wmemcellnmos']
        self.area_cell = sympy_var['area_cell']
        self.asp_ratio_cell = sympy_var['asp_ratio_cell']
        self.cell_pmos_w *= g_ip.F_sz_um
        self.cell_nmos_w *= g_ip.F_sz_um

    def assign(self, in_file, tech_flavor, cell_type):
        try:
            with open(in_file, "r") as fp:
                lines = fp.readlines()
        except FileNotFoundError:
            print(f"{in_file} is missing!")
            exit(-1)

        vdd_cell = 0
        vdd = 0

        vdd = sympy_var['Vdd']
        vdd_cell = sympy_var['vdd_cell']
        self.cell_a_w = sympy_var['Wmemcella']
        self.cell_pmos_w = sympy_var['Wmemcellpmos']
        self.cell_nmos_w = sympy_var['Wmemcellnmos']
        self.area_cell = sympy_var['area_cell']
        self.asp_ratio_cell = sympy_var['asp_ratio_cell']
        
        # for line in lines:
        #     if line.startswith("-Vdd"):
        #         vdd = scan_five_input_double(line, "-Vdd", "V", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-vdd_cell"):
        #         scan_res = scan_five_input_double_mem_type(line, "-vdd_cell", "V", tech_flavor, cell_type, g_ip.print_detail_debug)
        #         vdd_cell = scan_res if scan_res != None else vdd_cell
        #         continue
        #     if line.startswith("-Wmemcella"):
        #         scan_res = scan_five_input_double_mem_type(line, "-Wmemcella", "V", tech_flavor, cell_type, g_ip.print_detail_debug)
        #         self.cell_a_w = scan_res if scan_res != None else self.cell_a_w
        #         continue
        #     if line.startswith("-Wmemcellpmos"):
        #         scan_res = scan_five_input_double_mem_type(line, "-Wmemcellpmos", "V", tech_flavor, cell_type, g_ip.print_detail_debug)
        #         self.cell_pmos_w = scan_res if scan_res != None else self.cell_pmos_w
        #         continue
        #     if line.startswith("-Wmemcellnmos"):
        #         scan_res = scan_five_input_double_mem_type(line, "-Wmemcellnmos", "V", tech_flavor, cell_type, g_ip.print_detail_debug)
        #         self.cell_nmos_w = scan_res if scan_res != None else self.cell_nmos_w
        #         continue
        #     if line.startswith("-area_cell"):
        #         scan_res = scan_five_input_double_mem_type(line, "-area_cell", "V", tech_flavor, cell_type, g_ip.print_detail_debug)
        #         self.area_cell = scan_res if scan_res != None else self.area_cell
        #         continue
        #     if line.startswith("-asp_ratio_cell"):
        #         scan_res = scan_five_input_double_mem_type(line, "-asp_ratio_cell", "V", tech_flavor, cell_type, g_ip.print_detail_debug)
        #         self.asp_ratio_cell = scan_res if scan_res != None else self.asp_ratio_cell
        #         continue

        # print(g_ip.F_sz_um)
        # print(self.cell_pmos_w)
        if cell_type != 2:
            self.cell_a_w *= g_ip.F_sz_um
        self.cell_pmos_w *= g_ip.F_sz_um
        self.cell_nmos_w *= g_ip.F_sz_um
        if cell_type != 2:
            self.area_cell *= (g_ip.F_sz_um * g_ip.F_sz_um)

        self.b_w = sp.sqrt(self.area_cell / self.asp_ratio_cell)
        self.b_h = self.asp_ratio_cell * self.b_w
        if cell_type == 2:
            self.Vbitpre = vdd_cell
        else:
            self.Vbitpre = vdd

        self.Vbitfloating = self.Vbitpre * 0.7

    def interpolate(self, alpha, mem1, mem2):
        self.cell_a_w = alpha * mem1.cell_a_w + (1 - alpha) * mem2.cell_a_w
        self.cell_pmos_w = alpha * mem1.cell_pmos_w + (1 - alpha) * mem2.cell_pmos_w
        self.cell_nmos_w = alpha * mem1.cell_nmos_w + (1 - alpha) * mem2.cell_nmos_w
        self.area_cell = alpha * mem1.area_cell + (1 - alpha) * mem2.area_cell
        self.asp_ratio_cell = alpha * mem1.asp_ratio_cell + (1 - alpha) * mem2.asp_ratio_cell
        self.Vbitpre = mem2.Vbitpre
        self.Vbitfloating = self.Vbitpre * 0.7

        self.b_w = sp.sqrt(self.area_cell / self.asp_ratio_cell)
        self.b_h = self.asp_ratio_cell * self.b_w

    def isEqual(self, mem):
        if not is_equal(self.b_w, mem.b_w): return False
        if not is_equal(self.b_h, mem.b_h): return False
        if not is_equal(self.cell_a_w, mem.cell_a_w): return False
        if not is_equal(self.cell_pmos_w, mem.cell_pmos_w): return False
        if not is_equal(self.cell_nmos_w, mem.cell_nmos_w): return False
        if not is_equal(self.Vbitpre, mem.Vbitpre): return False
        return True

    def scan_five_input_double(self, line, name, unit_name, flavor, print_flag):
        temp = [0] * 5
        unit = ''

        pattern = re.compile(rf"{name}\s+(\S+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)")
        match = pattern.search(line)

        if match:
            unit = match.group(1)
            temp[0] = float(match.group(2))
            temp[1] = float(match.group(3))
            temp[2] = float(match.group(4))
            temp[3] = float(match.group(5))
            temp[4] = float(match.group(6))

            if print_flag:
                print(f"{name}[{flavor}]: {temp[flavor]} {unit}")
            return temp[flavor]
        return None

class ScalingFactor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.logic_scaling_co_eff = 0
        self.core_tx_density = 0
        self.long_channel_leakage_reduction = 0

        self.logic_scaling_co_eff = sympy_var['logic_scaling_co_eff']
        self.core_tx_density = sympy_var['core_tx_density']

    def assign(self, in_file):
        try:
            with open(in_file, "r") as fp:
                lines = fp.readlines()
        except FileNotFoundError:
            print(f"{in_file} is missing!")
            exit(-1)

        self.logic_scaling_co_eff = sympy_var['logic_scaling_co_eff']
        self.core_tx_density = sympy_var['core_tx_density']

        # for line in lines:
        #     if line.startswith("-logic_scaling_co_eff"):
        #         self.logic_scaling_co_eff = scan_single_input_double(line, "-logic_scaling_co_eff", "F/um", g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-core_tx_density"):
        #         self.core_tx_density = scan_single_input_double(line, "-core_tx_density", "F/um", g_ip.print_detail_debug)
        #         continue

    def interpolate(self, alpha, dev1, dev2):
        self.logic_scaling_co_eff = alpha * dev1.logic_scaling_co_eff + (1 - alpha) * dev2.logic_scaling_co_eff
        self.core_tx_density = alpha * dev1.core_tx_density + (1 - alpha) * dev2.core_tx_density

    def isEqual(self, scal):
        if not is_equal(self.logic_scaling_co_eff, scal.logic_scaling_co_eff):
            self.display(0)
            assert False
        if not is_equal(self.core_tx_density, scal.core_tx_density):
            self.display(0)
            assert False
        if not is_equal(self.long_channel_leakage_reduction, scal.long_channel_leakage_reduction):
            self.display(0)
            assert False
        return True

    def display(self, indent=0):
        indent_str = ' ' * indent
        print(f"{indent_str}logic_scaling_co_eff = {self.logic_scaling_co_eff}")
        print(f"{indent_str}core_tx_density = {self.core_tx_density}")
        print(f"{indent_str}long_channel_leakage_reduction = {self.long_channel_leakage_reduction}")

# class Area:
#     h: float = 0.0
#     w: float = 0.0

class DynamicParameter:
    def __init__(self, is_tag_=False, pure_ram_=0, pure_cam_=0, Nspd_=1.0, Ndwl_=1, Ndbl_=1, Ndcm_=1, Ndsam_lev_1_=1, Ndsam_lev_2_=1, wt=None, is_main_mem_=False):
        self.is_tag = is_tag_
        self.pure_ram = pure_ram_
        self.pure_cam = pure_cam_
        self.fully_assoc = False
        self.tagbits = 0
        self.num_subarrays = 0
        self.num_mats = 0
        self.Nspd = Nspd_
        self.Ndwl = Ndwl_
        self.Ndbl = Ndbl_
        self.Ndcm = Ndcm_
        self.deg_bl_muxing = 0
        self.deg_senseamp_muxing_non_associativity = 0
        self.Ndsam_lev_1 = Ndsam_lev_1_
        self.Ndsam_lev_2 = Ndsam_lev_2_
        self.wtype = wt
        self.number_addr_bits_mat = 0
        self.number_subbanks_decode = 0
        self.num_di_b_bank_per_port = 0
        self.num_do_b_bank_per_port = 0
        self.num_di_b_mat = 0
        self.num_do_b_mat = 0
        self.num_di_b_subbank = 0
        self.num_do_b_subbank = 0
        self.num_si_b_mat = 0
        self.num_so_b_mat = 0
        self.num_si_b_subbank = 0
        self.num_so_b_subbank = 0
        self.num_si_b_bank_per_port = 0
        self.num_so_b_bank_per_port = 0
        self.number_way_select_signals_mat = 0
        self.num_act_mats_hor_dir = 0
        self.num_act_mats_hor_dir_sl = 0
        self.is_dram = False
        self.V_b_sense = 0.0
        self.num_r_subarray = 0
        self.num_c_subarray = 0
        self.tag_num_r_subarray = 0
        self.tag_num_c_subarray = 0
        self.data_num_r_subarray = 0
        self.data_num_c_subarray = 0
        self.num_mats_h_dir = 0
        self.num_mats_v_dir = 0
        self.ram_cell_tech_type = 0
        self.dram_refresh_period = 0.0
        self.use_inp_params = 0
        self.num_rw_ports = 0
        self.num_rd_ports = 0
        self.num_wr_ports = 0
        self.num_se_rd_ports = 0
        self.num_search_ports = 0
        self.out_w = 0
        self.is_main_mem = is_main_mem_
        self.cell = Area()
        self.cam_cell = Area()
        self.is_valid = False
        self.init_parameters()

    def init_parameters(self):
        self.ram_cell_tech_type = g_ip.tag_arr_ram_cell_tech_type if self.is_tag else g_ip.data_arr_ram_cell_tech_type
        self.is_dram = (self.ram_cell_tech_type == lp_dram or self.ram_cell_tech_type == comm_dram)
        self.fully_assoc = bool(g_ip.fully_assoc)
        capacity_per_die = g_ip.cache_sz / NUMBER_STACKED_DIE_LAYERS
        wire_local = g_tp.wire_local

        if self.pure_cam:
            self.init_CAM()
            return

        if self.fully_assoc:
            self.init_FA()
            return

        if not self.calc_subarr_rc(capacity_per_die):
            return

        if self.is_tag:
            self.cell.h = g_tp.sram.b_h + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + g_ip.num_rd_ports + g_ip.num_wr_ports)
            self.cell.w = g_tp.sram.b_w + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + g_ip.num_wr_ports + (g_ip.num_rd_ports - g_ip.num_se_rd_ports)) + wire_local.pitch * g_ip.num_se_rd_ports
        else:
            if self.is_dram:
                self.cell.h = g_tp.dram.b_h
                self.cell.w = g_tp.dram.b_w
            else:
                self.cell.h = g_tp.sram.b_h + 2 * wire_local.pitch * (g_ip.num_wr_ports + g_ip.num_rw_ports - 1 + g_ip.num_rd_ports)
                self.cell.w = g_tp.sram.b_w + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + (g_ip.num_rd_ports - g_ip.num_se_rd_ports) + g_ip.num_wr_ports) + g_tp.wire_local.pitch * g_ip.num_se_rd_ports

        c_b_metal = self.cell.h * wire_local.C_per_um

        if self.is_dram:
            self.deg_bl_muxing = 1
            if self.ram_cell_tech_type == comm_dram:
                Cbitrow_drain_cap = drain_C_(g_tp.dram.cell_a_w, NCH, 1, 0, self.cell.w, True, True) / 2.0
                C_bl = self.num_r_subarray * (Cbitrow_drain_cap + c_b_metal)
                self.V_b_sense = (g_tp.dram_cell_Vdd / 2) * g_tp.dram_cell_C / (g_tp.dram_cell_C + C_bl)
                if self.V_b_sense < VBITSENSEMIN and not (g_ip.is_3d_mem and g_ip.force_cache_config):
                    return
                self.dram_refresh_period = 64e-3
            else:
                Cbitrow_drain_cap = drain_C_(g_tp.dram.cell_a_w, NCH, 1, 0, self.cell.w, True, True) / 2.0
                C_bl = self.num_r_subarray * (Cbitrow_drain_cap + c_b_metal)
                self.V_b_sense = (g_tp.dram_cell_Vdd / 2) * g_tp.dram_cell_C / (g_tp.dram_cell_C + C_bl)
                if self.V_b_sense < VBITSENSEMIN:
                    return
                self.V_b_sense = VBITSENSEMIN
                self.dram_refresh_period = 0.9 * g_tp.dram_cell_C * VDD_STORAGE_LOSS_FRACTION_WORST * g_tp.dram_cell_Vdd / g_tp.dram_cell_I_off_worst_case_len_temp
        else:
            self.V_b_sense = symbolic_convex_max(0.05 * g_tp.sram_cell.Vdd, VBITSENSEMIN)
            self.deg_bl_muxing = self.Ndcm
            Cbitrow_drain_cap = drain_C_(g_tp.sram.cell_a_w, NCH, 1, 0, self.cell.w, False, True) / 2.0
            C_bl = self.num_r_subarray * (Cbitrow_drain_cap + c_b_metal)
            self.dram_refresh_period = 0

        # RECENT CHANGE
        self.num_mats_h_dir = max(self.Ndwl // 2, 1)
        self.num_mats_v_dir = max(self.Ndbl // 2, 1)

        self.num_mats = self.num_mats_h_dir * self.num_mats_v_dir
        self.num_do_b_mat = symbolic_convex_max((self.num_subarrays / self.num_mats) * self.num_c_subarray / (self.deg_bl_muxing * self.Ndsam_lev_1 * self.Ndsam_lev_2), 1)

        if not (self.fully_assoc or self.pure_cam) and self.num_do_b_mat < (self.num_subarrays / self.num_mats):
            return

        if not self.is_tag:
            if self.is_main_mem:
                self.num_do_b_subbank = g_ip.int_prefetch_w * g_ip.out_w
                if g_ip.is_3d_mem:
                    self.num_do_b_subbank = g_ip.page_sz_bits
                deg_sa_mux_l1_non_assoc = self.Ndsam_lev_1
            else:
                if g_ip.fast_access:
                    self.num_do_b_subbank = g_ip.out_w * g_ip.data_assoc
                    deg_sa_mux_l1_non_assoc = self.Ndsam_lev_1
                else:
                    self.num_do_b_subbank = g_ip.out_w
                    deg_sa_mux_l1_non_assoc = self.Ndsam_lev_1 / g_ip.data_assoc
                    if deg_sa_mux_l1_non_assoc < 1:
                        return
        else:
            self.num_do_b_subbank = self.tagbits * g_ip.tag_assoc
            if self.num_do_b_mat < self.tagbits:
                return
            deg_sa_mux_l1_non_assoc = self.Ndsam_lev_1

        self.deg_senseamp_muxing_non_associativity = deg_sa_mux_l1_non_assoc
        self.num_act_mats_hor_dir = self.num_do_b_subbank // self.num_do_b_mat
        if g_ip.is_3d_mem and self.num_act_mats_hor_dir == 0:
            self.num_act_mats_hor_dir = 1
        if self.num_act_mats_hor_dir == 0:
            return

        if self.is_tag:
            if not (self.fully_assoc or self.pure_cam):
                self.num_do_b_mat = g_ip.tag_assoc // self.num_act_mats_hor_dir
                self.num_do_b_subbank = self.num_act_mats_hor_dir * self.num_do_b_mat

        if (not g_ip.is_cache and self.is_main_mem) or (PAGE_MODE == 1 and self.is_dram):
            if self.num_act_mats_hor_dir * self.num_do_b_mat * self.Ndsam_lev_1 * self.Ndsam_lev_2 != int(g_ip.page_sz_bits):
                return

        if (not self.is_tag) and (g_ip.is_main_mem) and (self.num_act_mats_hor_dir * self.num_do_b_mat * self.Ndsam_lev_1 * self.Ndsam_lev_2 < int(g_ip.out_w * g_ip.burst_len * g_ip.data_assoc)):
            return

        if self.num_act_mats_hor_dir > self.num_mats_h_dir:
            return

        if not self.is_tag:
            if g_ip.fast_access:
                self.num_di_b_mat = self.num_do_b_mat // g_ip.data_assoc
            else:
                self.num_di_b_mat = self.num_do_b_mat
        else:
            self.num_di_b_mat = self.tagbits

        self.num_di_b_subbank = self.num_di_b_mat * self.num_act_mats_hor_dir
        self.num_si_b_subbank = self.num_si_b_mat

        num_addr_b_row_dec = _log2(self.num_r_subarray)
        if self.fully_assoc or self.pure_cam:
            num_addr_b_row_dec += _log2(self.num_subarrays // self.num_mats)
        number_subbanks = self.num_mats // self.num_act_mats_hor_dir
        self.number_subbanks_decode = _log2(number_subbanks)

        self.num_rw_ports = g_ip.num_rw_ports
        self.num_rd_ports = g_ip.num_rd_ports
        self.num_wr_ports = g_ip.num_wr_ports
        self.num_se_rd_ports = g_ip.num_se_rd_ports
        self.num_search_ports = g_ip.num_search_ports

        if self.is_dram and self.is_main_mem:
            self.number_addr_bits_mat = symbolic_convex_max(num_addr_b_row_dec, _log2(self.deg_bl_muxing) + _log2(deg_sa_mux_l1_non_assoc) + _log2(self.Ndsam_lev_2))
            if g_ip.print_detail_debug:
                print(f"parameter.cc: number_addr_bits_mat = {num_addr_b_row_dec}")
                print(f"parameter.cc: num_addr_b_row_dec = {num_addr_b_row_dec}")
                print(f"parameter.cc: num_addr_b_mux_sel = {_log2(self.deg_bl_muxing) + _log2(deg_sa_mux_l1_non_assoc) + _log2(self.Ndsam_lev_2)}")
        else:
            self.number_addr_bits_mat = num_addr_b_row_dec + _log2(self.deg_bl_muxing) + _log2(deg_sa_mux_l1_non_assoc) + _log2(self.Ndsam_lev_2)

        if self.is_tag:
            self.num_di_b_bank_per_port = self.tagbits
            self.num_do_b_bank_per_port = g_ip.data_assoc
        else:
            self.num_di_b_bank_per_port = g_ip.out_w + g_ip.data_assoc
            self.num_do_b_bank_per_port = g_ip.out_w

        if not self.is_tag and g_ip.data_assoc > 1 and not g_ip.fast_access:
            self.number_way_select_signals_mat = g_ip.data_assoc

        if g_ip.add_ecc_b_:
            self.ECC_adjustment()

        self.is_valid = True

    def init_CAM(self):
        wire_local = g_tp.wire_local
        capacity_per_die = g_ip.cache_sz / NUMBER_STACKED_DIE_LAYERS

        if self.Ndwl != 1 or self.Ndcm != 1 or self.Nspd < 1 or self.Nspd > 1 or self.Ndsam_lev_1 != 1 or self.Ndsam_lev_2 != 1 or self.Ndbl < 2:
            return

        if g_ip.specific_tag:
            self.tagbits = math.ceil(g_ip.tag_w / 8.0) * 8
        else:
            self.tagbits = math.ceil((ADDRESS_BITS + EXTRA_TAG_BITS) / 8.0) * 8

        self.tag_num_r_subarray = math.ceil(capacity_per_die / (g_ip.nbanks * self.tagbits / 8.0 * self.Ndbl))
        self.tag_num_c_subarray = self.tagbits

        if self.tag_num_r_subarray == 0 or self.tag_num_r_subarray > MAXSUBARRAYROWS or self.tag_num_c_subarray < MINSUBARRAYCOLS or self.tag_num_c_subarray > MAXSUBARRAYCOLS:
            return

        self.num_r_subarray = self.tag_num_r_subarray
        self.num_subarrays = self.Ndwl * self.Ndbl

        self.cam_cell.h = g_tp.cam.b_h + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + g_ip.num_rd_ports + g_ip.num_wr_ports) + 2 * wire_local.pitch * (g_ip.num_search_ports - 1) + wire_local.pitch * g_ip.num_se_rd_ports
        self.cam_cell.w = g_tp.cam.b_w + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + g_ip.num_rd_ports + g_ip.num_wr_ports) + 2 * wire_local.pitch * (g_ip.num_search_ports - 1) + wire_local.pitch * g_ip.num_se_rd_ports

        self.cell.h = g_tp.sram.b_h + 2 * wire_local.pitch * (g_ip.num_wr_ports + g_ip.num_rw_ports - 1 + g_ip.num_rd_ports) + 2 * wire_local.pitch * (g_ip.num_search_ports - 1)
        self.cell.w = g_tp.sram.b_w + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + (g_ip.num_rd_ports - g_ip.num_se_rd_ports) + g_ip.num_wr_ports) + g_tp.wire_local.pitch * g_ip.num_se_rd_ports + 2 * wire_local.pitch * (g_ip.num_search_ports - 1)

        c_b_metal = self.cell.h * wire_local.C_per_um
        c_b_metal = self.cam_cell.h * wire_local.C_per_um
        self.V_b_sense = max(0.05 * g_tp.sram_cell.Vdd, VBITSENSEMIN)
        self.deg_bl_muxing = 1

        Cbitrow_drain_cap = drain_C_(g_tp.cam.cell_a_w, NCH, 1, 0, self.cam_cell.w, False, True) / 2.0
        self.dram_refresh_period = 0

        if self.Ndbl == 0:
            print("   Invalid Ndbl \n")
            exit(0)
        elif self.Ndbl == 1:
            self.num_mats_h_dir = 1
            self.num_mats_v_dir = 1
        elif self.Ndbl == 2:
            self.num_mats_h_dir = 1
            self.num_mats_v_dir = 1
        else:
            self.num_mats_h_dir = math.floor(sp.sqrt(self.Ndbl / 4.0))
            self.num_mats_v_dir = int(self.Ndbl / 4.0 / self.num_mats_h_dir)

        self.num_mats = self.num_mats_h_dir * self.num_mats_v_dir

        self.num_so_b_mat = math.ceil(_log2(self.num_r_subarray)) + math.ceil(_log2(self.num_subarrays))
        self.num_do_b_mat = self.tagbits

        deg_sa_mux_l1_non_assoc = 1

        self.num_so_b_subbank = math.ceil(_log2(self.num_r_subarray)) + math.ceil(_log2(self.num_subarrays))
        self.num_do_b_subbank = self.tag_num_c_subarray

        self.deg_senseamp_muxing_non_associativity = deg_sa_mux_l1_non_assoc

        self.num_act_mats_hor_dir = 1
        self.num_act_mats_hor_dir_sl = self.num_mats_h_dir

        if self.num_act_mats_hor_dir > self.num_mats_h_dir:
            return

        self.num_di_b_mat = self.tagbits
        self.num_si_b_mat = self.tagbits

        self.num_di_b_subbank = self.num_di_b_mat * self.num_act_mats_hor_dir
        self.num_si_b_subbank = self.num_si_b_mat

        num_addr_b_row_dec = _log2(self.num_r_subarray)
        num_addr_b_row_dec += _log2(self.num_subarrays / self.num_mats)
        number_subbanks = self.num_mats / self.num_act_mats_hor_dir
        self.number_subbanks_decode = _log2(number_subbanks)

        self.num_rw_ports = g_ip.num_rw_ports
        self.num_rd_ports = g_ip.num_rd_ports
        self.num_wr_ports = g_ip.num_wr_ports
        self.num_se_rd_ports = g_ip.num_se_rd_ports
        self.num_search_ports = g_ip.num_search_ports

        self.number_addr_bits_mat = num_addr_b_row_dec + _log2(self.deg_bl_muxing) + _log2(deg_sa_mux_l1_non_assoc) + _log2(self.Ndsam_lev_2)

        self.num_di_b_bank_per_port = self.tagbits
        self.num_si_b_bank_per_port = self.tagbits
        self.num_do_b_bank_per_port = self.tagbits
        self.num_so_b_bank_per_port = math.ceil(_log2(self.num_r_subarray)) + math.ceil(_log2(self.num_subarrays))

        if not self.is_tag and g_ip.data_assoc > 1 and not g_ip.fast_access:
            self.number_way_select_signals_mat = g_ip.data_assoc

        if g_ip.add_ecc_b_:
            self.ECC_adjustment()

        self.is_valid = True

    def init_FA(self):
        wire_local = g_tp.wire_local
        assert NUMBER_STACKED_DIE_LAYERS == 1
        capacity_per_die = g_ip.cache_sz

        if self.Ndwl != 1 or self.Ndcm != 1 or self.Nspd < 1 or self.Nspd > 1 or self.Ndsam_lev_1 != 1 or self.Ndsam_lev_2 != 1 or self.Ndbl < 2:
            return

        if g_ip.specific_tag:
            self.tagbits = g_ip.tag_w
        else:
            self.tagbits = ADDRESS_BITS + EXTRA_TAG_BITS - _log2(g_ip.block_sz)
        self.tagbits = (((self.tagbits + 3) >> 2) << 2)

        self.tag_num_r_subarray = math.ceil(capacity_per_die / (g_ip.nbanks * g_ip.block_sz * self.Ndbl))
        self.tag_num_c_subarray = math.ceil((self.tagbits * self.Nspd / self.Ndwl))

        if self.tag_num_r_subarray == 0:
            return
        if self.tag_num_r_subarray > MAXSUBARRAYROWS:
            return
        if self.tag_num_c_subarray < MINSUBARRAYCOLS:
            return
        if self.tag_num_c_subarray > MAXSUBARRAYCOLS:
            return

        self.data_num_r_subarray = self.tag_num_r_subarray
        self.data_num_c_subarray = 8 * g_ip.block_sz
        if self.data_num_r_subarray == 0:
            return
        if self.data_num_r_subarray > MAXSUBARRAYROWS:
            return
        if self.data_num_c_subarray < MINSUBARRAYCOLS:
            return
        if self.data_num_c_subarray > MAXSUBARRAYCOLS:
            return
        self.num_r_subarray = self.tag_num_r_subarray

        self.num_subarrays = self.Ndwl * self.Ndbl

        self.cam_cell.h = g_tp.cam.b_h + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + g_ip.num_rd_ports + g_ip.num_wr_ports) + 2 * wire_local.pitch * (g_ip.num_search_ports - 1) + wire_local.pitch * g_ip.num_se_rd_ports
        self.cam_cell.w = g_tp.cam.b_w + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + g_ip.num_rd_ports + g_ip.num_wr_ports) + 2 * wire_local.pitch * (g_ip.num_search_ports - 1) + wire_local.pitch * g_ip.num_se_rd_ports

        self.cell.h = g_tp.sram.b_h + 2 * wire_local.pitch * (g_ip.num_wr_ports + g_ip.num_rw_ports - 1 + g_ip.num_rd_ports) + 2 * wire_local.pitch * (g_ip.num_search_ports - 1)
        self.cell.w = g_tp.sram.b_w + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + (g_ip.num_rd_ports - g_ip.num_se_rd_ports) + g_ip.num_wr_ports) + g_tp.wire_local.pitch * g_ip.num_se_rd_ports + 2 * wire_local.pitch * (g_ip.num_search_ports - 1)

        c_b_metal = self.cam_cell.h * wire_local.C_per_um
        self.V_b_sense = symbolic_convex_max(0.05 * g_tp.sram_cell.Vdd, VBITSENSEMIN)
        self.deg_bl_muxing = 1

        Cbitrow_drain_cap = drain_C_(g_tp.cam.cell_a_w, NCH, 1, 0, self.cam_cell.w, False, True) / 2.0
        self.dram_refresh_period = 0

        if self.Ndbl == 0:
            print("   Invalid Ndbl \n")
            exit(0)
        elif self.Ndbl == 1:
            self.num_mats_h_dir = 1
            self.num_mats_v_dir = 1
        elif self.Ndbl == 2:
            self.num_mats_h_dir = 1
            self.num_mats_v_dir = 1
        else:
            self.num_mats_h_dir = math.floor(sp.sqrt(self.Ndbl / 4.0))
            self.num_mats_v_dir = int(self.Ndbl / 4.0 / self.num_mats_h_dir)

        self.num_mats = self.num_mats_h_dir * self.num_mats_v_dir

        self.num_so_b_mat = self.data_num_c_subarray
        self.num_do_b_mat = self.data_num_c_subarray + self.tagbits

        deg_sa_mux_l1_non_assoc = 1
        self.num_so_b_subbank = 8 * g_ip.block_sz
        self.num_do_b_subbank = self.num_so_b_subbank + self.tag_num_c_subarray

        self.deg_senseamp_muxing_non_associativity = deg_sa_mux_l1_non_assoc
        self.num_act_mats_hor_dir = 1
        self.num_act_mats_hor_dir_sl = self.num_mats_h_dir

        if self.num_act_mats_hor_dir > self.num_mats_h_dir:
            return

        if self.fully_assoc:
            self.num_di_b_mat = self.num_do_b_mat
            self.num_si_b_mat = self.tagbits
        self.num_di_b_subbank = self.num_di_b_mat * self.num_act_mats_hor_dir
        self.num_si_b_subbank = self.num_si_b_mat

        num_addr_b_row_dec = _log2(self.num_r_subarray)
        num_addr_b_row_dec += _log2(self.num_subarrays / self.num_mats)
        number_subbanks = self.num_mats / self.num_act_mats_hor_dir
        self.number_subbanks_decode = _log2(number_subbanks)

        self.num_rw_ports = g_ip.num_rw_ports
        self.num_rd_ports = g_ip.num_rd_ports
        self.num_wr_ports = g_ip.num_wr_ports
        self.num_se_rd_ports = g_ip.num_se_rd_ports
        self.num_search_ports = g_ip.num_search_ports

        self.number_addr_bits_mat = num_addr_b_row_dec + _log2(self.deg_bl_muxing) + _log2(deg_sa_mux_l1_non_assoc) + _log2(self.Ndsam_lev_2)

        self.num_di_b_bank_per_port = g_ip.out_w + self.tagbits
        self.num_si_b_bank_per_port = self.tagbits
        self.num_do_b_bank_per_port = g_ip.out_w + self.tagbits
        self.num_so_b_bank_per_port = g_ip.out_w

        if not self.is_tag and g_ip.data_assoc > 1 and not g_ip.fast_access:
            self.number_way_select_signals_mat = g_ip.data_assoc

        if g_ip.add_ecc_b_:
            self.ECC_adjustment()

        self.is_valid = True


    def ECC_adjustment(self):
        self.num_do_b_mat += int(math.ceil(self.num_do_b_mat / num_bits_per_ecc_b_))
        self.num_di_b_mat += int(math.ceil(self.num_di_b_mat / num_bits_per_ecc_b_))
        self.num_di_b_subbank += int(math.ceil(self.num_di_b_subbank / num_bits_per_ecc_b_))
        self.num_do_b_subbank += int(math.ceil(self.num_do_b_subbank / num_bits_per_ecc_b_))
        self.num_di_b_bank_per_port += int(math.ceil(self.num_di_b_bank_per_port / num_bits_per_ecc_b_))
        self.num_do_b_bank_per_port += int(math.ceil(self.num_do_b_bank_per_port / num_bits_per_ecc_b_))

        self.num_so_b_mat += int(math.ceil(self.num_so_b_mat / num_bits_per_ecc_b_))
        self.num_si_b_mat += int(math.ceil(self.num_si_b_mat / num_bits_per_ecc_b_))
        self.num_si_b_subbank += int(math.ceil(self.num_si_b_subbank / num_bits_per_ecc_b_))
        self.num_so_b_subbank += int(math.ceil(self.num_so_b_subbank / num_bits_per_ecc_b_))
        self.num_si_b_bank_per_port += int(math.ceil(self.num_si_b_bank_per_port / num_bits_per_ecc_b_))
        self.num_so_b_bank_per_port += int(math.ceil(self.num_so_b_bank_per_port / num_bits_per_ecc_b_))


    def calc_subarr_rc(self, capacity_per_die):
        if self.Ndwl < 2 or self.Ndbl < 2:
            print("Ndwl and Ndbl set less than 2 parameter.py")
            return False

        if self.is_dram and not self.is_tag and self.Ndcm > 1:
            return False

        if self.is_tag:
            if g_ip.specific_tag:
                self.tagbits = g_ip.tag_w
            else:
                self.tagbits = ADDRESS_BITS + EXTRA_TAG_BITS - math.log2(capacity_per_die) + _log2(g_ip.tag_assoc * 2 - 1)

            self.num_r_subarray = math.ceil(capacity_per_die / (g_ip.nbanks * g_ip.block_sz * g_ip.tag_assoc * self.Ndbl * self.Nspd))
            self.num_c_subarray = math.ceil((self.tagbits * g_ip.tag_assoc * self.Nspd / self.Ndwl))
        else:
            self.num_r_subarray = math.ceil(capacity_per_die / (g_ip.nbanks * g_ip.block_sz * g_ip.data_assoc * self.Ndbl * self.Nspd))
            self.num_c_subarray = math.ceil((8 * g_ip.block_sz * g_ip.data_assoc * self.Nspd / self.Ndwl))
            if g_ip.is_3d_mem:
                capacity_per_die_double = float(g_ip.cache_sz) / g_ip.num_die_3d
                self.num_c_subarray = g_ip.page_sz_bits / self.Ndwl
                self.num_r_subarray = 1 << int(math.floor(math.log2(float(g_ip.cache_sz) / g_ip.num_die_3d / self.num_c_subarray / g_ip.nbanks / self.Ndbl / self.Ndwl * 1024 * 1024 * 1024) + 0.5))
                if g_ip.print_detail_debug:
                    print(f"parameter.cc: capacity_per_die_double = {capacity_per_die_double} Gbit")
                    print(f"parameter.cc: g_ip.nbanks * Ndbl * Ndwl = {g_ip.nbanks * self.Ndbl * self.Ndwl}")
                    print(f"parameter.cc: num_r_subarray = {self.num_r_subarray}")
                    print(f"parameter.cc: num_c_subarray = {self.num_c_subarray}")

        if self.num_r_subarray < MINSUBARRAYROWS or self.num_r_subarray == 0 or self.num_r_subarray > MAXSUBARRAYROWS:
            return False
        if self.num_c_subarray < MINSUBARRAYCOLS or self.num_c_subarray > MAXSUBARRAYCOLS:
            return False

        self.num_subarrays = self.Ndwl * self.Ndbl
        return True
    









# HELPERS
# CHECK THESE
def PRINT(A, X, tech):
    print(f"{A}: {X} , {tech.X}")

def scan_single_input_double(line, name, unit_name, print_output):
    match = re.search(f"{name}\s+([^\s]+)\s+([^\s]+)", line)
    if match:
        unit = match.group(1)
        temp = float(match.group(2))
        if print_output:
            print(f"{name}: {temp} {unit}")
        return temp
    return 0.0

def scan_five_input_double(line, name, unit_name, flavor, print_output):
    match = re.search(f"{name}\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)", line)
    if match:
        unit = match.group(1)
        temp = [float(match.group(i)) for i in range(2, 7)]
        if print_output:
            print(f"{name}[{flavor}]: {temp[flavor]} {unit}")
        return temp[flavor]
    return 0.0

def scan_five_input_double_temperature(line, name, unit_name, flavor, temperature, print_output, result):
    match = re.search(f"{name}\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)", line)
    if match:
        unit = match.group(1)
        thermal_temp = int(match.group(2))
        temp = [float(match.group(i)) for i in range(3, 8)]
        if thermal_temp == (temperature - 300):
            if print_output:
                print(f"{name}: {temp[flavor]} {unit}")
            result = temp[flavor]

def scan_input_double_inter_type(line, name, unit_name, proj_type, tech_flavor, print_output):
    assert proj_type < NUMBER_INTERCONNECT_PROJECTION_TYPES
    index = proj_type * NUMBER_WIRE_TYPES + tech_flavor
    match = re.search(f"{name}\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)", line)
    if match:
        unit = match.group(1)
        temp = [float(match.group(i)) for i in range(2, 10)]
        if print_output:
            print(f"{name} {temp[index]} {unit}")
        return temp[index]
    return 0.0

def scan_five_input_double_mem_type(line, name, unit_name, flavor, cell_type, print_flag):
    temp = [0.0] * 5
    unit = ""
    
    # Extract the relevant part of the line
    relevant_line = line[len(name):].strip()

    # print(line)
    # print(relevant_line)
    
    # Scan the input line and extract values
    parts = relevant_line.split()
    # print(parts)
    # print(cell_type)
    
    unit = parts[0]
    cell_type_temp = int(parts[1])
    temp[0] = float(parts[2])
    temp[1] = float(parts[3])
    temp[2] = float(parts[4])
    temp[3] = float(parts[5])
    temp[4] = float(parts[6])
    
    result = None
    if cell_type_temp == cell_type:
        if print_flag:
            print(f"{name}: {temp[flavor]} {unit}")
        result = temp[flavor]
    
    return result

def scan_input_double_tsv_type(line, name, unit_name, proj_type, tsv_type, print_flag):
    assert proj_type < NUMBER_INTERCONNECT_PROJECTION_TYPES
    index = proj_type * NUMBER_TSV_TYPES + tsv_type
    temp = [0.0] * 6
    unit = ""
    
    # Extracting the values using regular expressions
    match = re.search(rf"{name}\s+(\S+)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)", line)
    
    if match:
        unit = match.group(1)
        temp[0] = float(match.group(2))
        temp[1] = float(match.group(3))
        temp[2] = float(match.group(4))
        temp[3] = float(match.group(5))
        temp[4] = float(match.group(6))
        temp[5] = float(match.group(7))
        
        if print_flag:
            print(f"{name}: {temp[index]} {unit}")
            
        return temp[index]
    else:
        raise ValueError("Line does not match the expected format")




### basic_circuit.py
#### TO AVOID CIRCULAR DEPENDNCY
UNI_LEAK_STACK_FACTOR = 0.43

def powers(base, n):
    p = 1
    for i in range(1, n + 1):
        p *= base
    return p

def is_pow2(val):
    if val <= 0:
        return False
    elif val == 1:
        return True
    else:
        return (_log2(val) != _log2(val - 1))

def _log2(num):
    num = int(num)
    if num == 0:
        num = 1
    log2 = 0
    while num > 1:
        num >>= 1
        log2 += 1
    return log2

def factorial(n, m=1):
    fa = m
    for i in range(m + 1, n + 1):
        fa *= i
    return fa

def combination(n, m):
    return factorial(n, m + 1) // factorial(n - m)


outside_mat = "outside_mat"
inside_mat = "inside_mat"
local_wires = "local_wires"


Add_htree = "Add_htree"
Data_in_htree = "Data_in_htree"
Data_out_htree = "Data_out_htree"
Search_in_htree = "Search_in_htree"
Search_out_htree = "Search_out_htree"


Row_add_path = "Row_add_path"
Col_add_path = "Col_add_path"
Data_path = "Data_path"


nmos = "nmos"
pmos = "pmos"
inv = "inv"
nand = "nand"
nor = "nor"
tri = "tri"
tg = "tg"

parallel = "parallel"
series = "series"

class WirePlacement:
    outside_mat = "outside_mat"
    inside_mat = "inside_mat"
    local_wires = "local_wires"

class HtreeType:
    Add_htree = "Add_htree"
    Data_in_htree = "Data_in_htree"
    Data_out_htree = "Data_out_htree"
    Search_in_htree = "Search_in_htree"
    Search_out_htree = "Search_out_htree"

class MemorybusType:
    Row_add_path = "Row_add_path"
    Col_add_path = "Col_add_path"
    Data_path = "Data_path"

class GateType:
    nmos = "nmos"
    pmos = "pmos"
    inv = "inv"
    nand = "nand"
    nor = "nor"
    tri = "tri"
    tg = "tg"

class HalfNetTopology:
    parallel = "parallel"
    series = "series"

def logtwo(x):
    assert x > 0
    return sp.log(x) / sp.log(2.0)

def gate_C(width, wirelength, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_sram:
        dt = g_tp.dram_acc  # DRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif not _is_dram and _is_sram:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global
    
    return (dt.C_g_ideal + dt.C_overlap + 3 * dt.C_fringe) * width + dt.l_phy * Cpolywire

def gate_C_pass(width, wirelength, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    return gate_C(width, wirelength, _is_dram, _is_sram, _is_wl_tr, _is_sleep_tx)

def drain_C_(width, nchannel, stack, next_arg_thresh_folding_width_or_height_cell, fold_dimension, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_sram:
        dt = g_tp.dram_acc  # DRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif not _is_dram and _is_sram:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global

    c_junc_area = dt.C_junc
    c_junc_sidewall = dt.C_junc_sidewall
    c_fringe = 2 * dt.C_fringe
    c_overlap = 2 * dt.C_overlap

    if next_arg_thresh_folding_width_or_height_cell == 0:
        w_folded_tr = fold_dimension
    else:
        h_tr_region = fold_dimension - 2 * g_tp.HPOWERRAIL
        ratio_p_to_n = 2.0 / (2.0 + 1.0)
        if nchannel:
            w_folded_tr = (1 - ratio_p_to_n) * (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS)
        else:
            w_folded_tr = ratio_p_to_n * (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS)
        
    num_folded_tr = sp.ceiling(width / w_folded_tr)
    w_folded_tr = sp.Piecewise((width, num_folded_tr < 2), (w_folded_tr, True))

    total_drain_w = (g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact) + (stack - 1) * g_tp.spacing_poly_to_poly
    total_drain_w = sp.Piecewise(
        (total_drain_w, num_folded_tr <= 1),
        (total_drain_w + (num_folded_tr - 2) * (g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact) + (num_folded_tr - 1) * ((stack - 1) * g_tp.spacing_poly_to_poly), True)
    )

    drain_h_for_sidewall = sp.Piecewise((w_folded_tr, num_folded_tr <= 1), (0, num_folded_tr > 1))
    
    total_drain_height_for_cap_wrt_gate = w_folded_tr + 2 * w_folded_tr * (stack - 1)
    total_drain_height_for_cap_wrt_gate = sp.Piecewise(
        (total_drain_height_for_cap_wrt_gate, num_folded_tr <= 1),
        (total_drain_height_for_cap_wrt_gate * num_folded_tr, True)
    )

    drain_C_metal_connecting_folded_tr = sp.Piecewise(
        (0, num_folded_tr <= 1),
        (g_tp.wire_local.C_per_um * total_drain_w, True)
    )

    drain_C_area = c_junc_area * total_drain_w * w_folded_tr
    drain_C_sidewall = c_junc_sidewall * (drain_h_for_sidewall + 2 * total_drain_w)
    drain_C_wrt_gate = (c_fringe + c_overlap) * total_drain_height_for_cap_wrt_gate

    return drain_C_area + drain_C_sidewall + drain_C_wrt_gate + drain_C_metal_connecting_folded_tr



def tr_R_on(width, nchannel, stack, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_sram:
        dt = g_tp.dram_acc  # DRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif not _is_dram and _is_sram:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global

    restrans = dt.R_nch_on if nchannel else dt.R_pch_on
    return stack * restrans / width

def R_to_w(res, nchannel, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_sram:
        dt = g_tp.dram_acc  # DRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif not _is_dram and _is_sram:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global

    restrans = dt.R_nch_on if nchannel else dt.R_pch_on
    return restrans / res

def pmos_to_nmos_sz_ratio(_is_dram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_wl_tr:
        return g_tp.dram_wl.n_to_p_eff_curr_drv_ratio
    elif _is_sleep_tx:
        return g_tp.sleep_tx.n_to_p_eff_curr_drv_ratio
    else:
        return g_tp.peri_global.n_to_p_eff_curr_drv_ratio

def horowitz(inputramptime, tf, vs1, vs2, rise):
    if inputramptime == 0 and vs1 == vs2:
        return tf * sp.Piecewise((-sp.log(vs1), vs1 < 1), (sp.log(vs1), vs1 >= 1))

    a = inputramptime / tf
    if rise == RISE:
        b = 0.5
        td = tf * sp.sqrt(sp.log(vs1) ** 2 + 2 * a * b * (1.0 - vs1)) + tf * (sp.log(vs1) - sp.log(vs2))
    else:
        b = 0.4
        td = tf * sp.sqrt(sp.log(1.0 - vs1) ** 2 + 2 * a * b * vs1) + tf * (sp.log(1.0 - vs1) - sp.log(1.0 - vs2))
    return td


def cmos_Ileak(nWidth, pWidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return nWidth * dt.I_off_n + pWidth * dt.I_off_p

def simplified_nmos_Isat(nwidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return nwidth * dt.I_on_n

def simplified_pmos_Isat(pwidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return pwidth * dt.I_on_n / dt.n_to_p_eff_curr_drv_ratio

def simplified_nmos_leakage(nwidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return nwidth * dt.I_off_n

def simplified_pmos_leakage(pwidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return pwidth * dt.I_off_p

def cmos_Ig_n(nWidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return nWidth * dt.I_g_on_n

def cmos_Ig_p(pWidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return pWidth * dt.I_g_on_p

def cmos_Isub_leakage(nWidth, pWidth, fanin, g_type, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False, topo=series):
    assert fanin >= 1
    nmos_leak = simplified_nmos_leakage(nWidth, _is_dram, _is_cell, _is_wl_tr, _is_sleep_tx)
    pmos_leak = simplified_pmos_leakage(pWidth, _is_dram, _is_cell, _is_wl_tr, _is_sleep_tx)
    Isub = 0
    num_states = int(sp.Pow(2.0, fanin))

    if g_type == nmos:
        if fanin == 1:
            Isub = nmos_leak / num_states
        else:
            if topo == parallel:
                Isub = nmos_leak * fanin / num_states
            else:
                for num_off_tx in range(1, fanin + 1):
                    Isub += nmos_leak * sp.Pow(UNI_LEAK_STACK_FACTOR, (num_off_tx - 1)) * combination(fanin, num_off_tx)
                Isub /= num_states

    elif g_type == pmos:
        if fanin == 1:
            Isub = pmos_leak / num_states
        else:
            if topo == parallel:
                Isub = pmos_leak * fanin / num_states
            else:
                for num_off_tx in range(1, fanin + 1):
                    Isub += pmos_leak * sp.Pow(UNI_LEAK_STACK_FACTOR, (num_off_tx - 1)) * combination(fanin, num_off_tx)
                Isub /= num_states

    elif g_type == inv:
        Isub = (nmos_leak + pmos_leak) / 2

    elif g_type == nand:
        Isub += fanin * pmos_leak
        for num_off_tx in range(1, fanin + 1):
            Isub += nmos_leak * sp.Pow(UNI_LEAK_STACK_FACTOR, (num_off_tx - 1)) * combination(fanin, num_off_tx)
        Isub /= num_states

    elif g_type == nor:
        for num_off_tx in range(1, fanin + 1):
            Isub += pmos_leak * sp.Pow(UNI_LEAK_STACK_FACTOR, (num_off_tx - 1)) * combination(fanin, num_off_tx)
        Isub += fanin * nmos_leak
        Isub /= num_states

    elif g_type == tri:
        Isub += (nmos_leak + pmos_leak) / 2
        Isub += nmos_leak * UNI_LEAK_STACK_FACTOR
        Isub /= 2

    elif g_type == tg:
        Isub = (nmos_leak + pmos_leak) / 2

    else:
        raise ValueError("Invalid gate type")

    return Isub

def cmos_Ig_leakage(nWidth, pWidth, fanin, g_type, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False, topo=series):
    assert fanin >= 1
    nmos_leak = cmos_Ig_n(nWidth, _is_dram, _is_cell, _is_wl_tr, _is_sleep_tx)
    pmos_leak = cmos_Ig_p(pWidth, _is_dram, _is_cell, _is_wl_tr, _is_sleep_tx)
    Ig_on = 0
    
    num_states = int(sp.Pow(2.0, fanin))

    if g_type == nmos:
        if fanin == 1:
            Ig_on = nmos_leak / num_states
        else:
            if topo == parallel:
                for num_on_tx in range(1, fanin + 1):
                    Ig_on += nmos_leak * combination(fanin, num_on_tx) * num_on_tx
            else:
                Ig_on += nmos_leak * fanin
                for num_on_tx in range(1, fanin):
                    Ig_on += nmos_leak * combination(fanin, num_on_tx) * num_on_tx / 2
                Ig_on /= num_states

    elif g_type == pmos:
        if fanin == 1:
            Ig_on = pmos_leak / num_states
        else:
            if topo == parallel:
                for num_on_tx in range(1, fanin + 1):
                    Ig_on += pmos_leak * combination(fanin, num_on_tx) * num_on_tx
            else:
                Ig_on += pmos_leak * fanin
                for num_on_tx in range(1, fanin):
                    Ig_on += pmos_leak * combination(fanin, num_on_tx) * num_on_tx / 2
                Ig_on /= num_states

    elif g_type == inv:
        Ig_on = (nmos_leak + pmos_leak) / 2

    elif g_type == nand:
        for num_on_tx in range(1, fanin + 1):
            Ig_on += pmos_leak * combination(fanin, num_on_tx) * num_on_tx
        Ig_on += nmos_leak * fanin
        for num_on_tx in range(1, fanin):
            Ig_on += nmos_leak * combination(fanin, num_on_tx) * num_on_tx / 2
        Ig_on /= num_states

    elif g_type == nor:
        Ig_on += pmos_leak * fanin
        for num_on_tx in range(1, fanin):
            Ig_on += pmos_leak * combination(fanin, num_on_tx) * num_on_tx / 2
        for num_on_tx in range(1, fanin + 1):
            Ig_on += nmos_leak * combination(fanin, num_on_tx) * num_on_tx
        Ig_on /= num_states

    elif g_type == tri:
        Ig_on += (2 * nmos_leak + 2 * pmos_leak) / 2
        Ig_on += (nmos_leak + pmos_leak) / 2
        Ig_on /= 2

    elif g_type == tg:
        Ig_on = (nmos_leak + pmos_leak) / 2

    else:
        raise ValueError("Invalid gate type")

    return Ig_on

def shortcircuit_simple(vt, velocity_index, c_in, c_out, w_nmos, w_pmos, i_on_n, i_on_p, i_on_n_in, i_on_p_in, vdd):
    fo_n = i_on_n / i_on_n_in
    fo_p = i_on_p / i_on_p_in
    fanout = c_out / c_in
    beta_ratio = i_on_p / i_on_n
    vt_to_vdd_ratio = vt / vdd

    p_short_circuit_discharge_low = (10 / 3) * (pow((vdd - vt) - vt_to_vdd_ratio, 3.0) / pow(velocity_index, 2.0) / pow(2.0, 3 * vt_to_vdd_ratio * vt_to_vdd_ratio)) * c_in * vdd * vdd * fo_p * fo_p / fanout / beta_ratio
    p_short_circuit_charge_low = (10 / 3) * (pow((vdd - vt) - vt_to_vdd_ratio, 3.0) / pow(velocity_index, 2.0) / pow(2.0, 3 * vt_to_vdd_ratio * vt_to_vdd_ratio)) * c_in * vdd * vdd * fo_n * fo_n / fanout * beta_ratio

    p_short_circuit_discharge = p_short_circuit_discharge_low
    p_short_circuit_charge = p_short_circuit_charge_low
    p_short_circuit = (p_short_circuit_discharge + p_short_circuit_charge) / 2

    return p_short_circuit

def shortcircuit(vt, velocity_index, c_in, c_out, w_nmos, w_pmos, i_on_n, i_on_p, i_on_n_in, i_on_p_in, vdd):
    fo_p = i_on_p / i_on_p_in
    fanout = 1
    beta_ratio = i_on_p / i_on_n
    e = 2.71828
    f_alpha = 1 / (velocity_index + 2) - velocity_index / (2 * (velocity_index + 3)) + velocity_index / (velocity_index + 4) * (velocity_index / 2 - 1)
    k_v = 0.9 / 0.8 + (vdd - vt) / 0.8 * sp.log(10 * (vdd - vt) / e)
    g_v_alpha = (velocity_index + 1) * pow((1 - velocity_index), velocity_index) * pow((1 - velocity_index), velocity_index / 2) / f_alpha / pow((1 - velocity_index - velocity_index), (velocity_index / 2 + velocity_index + 2))
    h_v_alpha = pow(2, velocity_index) * (velocity_index + 1) * pow((1 - velocity_index), velocity_index) / pow((1 - velocity_index - velocity_index), (velocity_index + 1))

    p_short_circuit_discharge = k_v * vdd * vdd * c_in * fo_p * fo_p / ((vdd - vt) * g_v_alpha * fanout * beta_ratio / 2 / k_v + h_v_alpha * fo_p)
    return p_short_circuit_discharge

def wire_resistance(resistivity, wire_width, wire_thickness, barrier_thickness, dishing_thickness, alpha_scatter):
    resistance = alpha_scatter * resistivity / ((wire_thickness - barrier_thickness - dishing_thickness) * (wire_width - 2 * barrier_thickness))
    return resistance

def wire_capacitance(wire_width, wire_thickness, wire_spacing, ild_thickness, miller_value, horiz_dielectric_constant, vert_dielectric_constant, fringe_cap):
    vertical_cap = 2 * PERMITTIVITY_FREE_SPACE * vert_dielectric_constant * wire_width / ild_thickness
    sidewall_cap = 2 * PERMITTIVITY_FREE_SPACE * miller_value * horiz_dielectric_constant * wire_thickness / wire_spacing
    total_cap = vertical_cap + sidewall_cap + fringe_cap
    return total_cap

def tsv_resistance(resistivity, tsv_len, tsv_diam, tsv_contact_resistance):
    resistance = resistivity * tsv_len / (math.pi * (tsv_diam / 2) ** 2) + tsv_contact_resistance
    return resistance

def tsv_capacitance(tsv_len, tsv_diam, tsv_pitch, dielec_thickness, liner_dielectric_constant, depletion_width):
    e_si = PERMITTIVITY_FREE_SPACE * 11.9
    PI = math.pi
    lateral_coupling_constant = 4.1
    diagonal_coupling_constant = 5.3

    liner_cap = 2 * PI * PERMITTIVITY_FREE_SPACE * liner_dielectric_constant * tsv_len / sp.log(1 + dielec_thickness / (tsv_diam / 2))
    depletion_cap = 2 * PI * e_si * tsv_len / sp.log(1 + depletion_width / (dielec_thickness + tsv_diam / 2))
    self_cap = 1 / (1 / liner_cap + 1 / depletion_cap)

    lateral_coupling_cap = 0.4 * (0.225 * sp.log(0.97 * tsv_len / tsv_diam) + 0.53) * e_si / (tsv_pitch - tsv_diam) * PI * tsv_diam * tsv_len
    diagonal_coupling_cap = 0.4 * (0.225 * sp.log(0.97 * tsv_len / tsv_diam) + 0.53) * e_si / (1.414 * tsv_pitch - tsv_diam) * PI * tsv_diam * tsv_len

    total_cap = self_cap + lateral_coupling_constant * lateral_coupling_cap + diagonal_coupling_constant * diagonal_coupling_cap
    return total_cap

def tsv_area(tsv_pitch):
    return tsv_pitch ** 2

def symbolic_convex_max(a, b):
    """
    An approximation to the max function that plays well with these numeric solvers.
    """
    return 0.5 * (a + b + abs(a - b))

g_ip = InputParameter()
g_tp = TechnologyParameter()
