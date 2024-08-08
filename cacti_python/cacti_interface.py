from typing import List
import re
from .parameter import g_ip, InputParameter, symbolic_convex_max
import sympy as sp

class PowerComponents:
    def __init__(self, dynamic=0, leakage=0, gate_leakage=0, short_circuit=0, longer_channel_leakage=0):
        self.dynamic = dynamic
        self.leakage = leakage
        self.gate_leakage = gate_leakage
        self.short_circuit = short_circuit
        self.longer_channel_leakage = longer_channel_leakage

    def reset(self):
        self.dynamic = 0
        self.leakage = 0
        self.gate_leakage = 0
        self.short_circuit = 0
        self.longer_channel_leakage = 0

    def __add__(self, other):
        return PowerComponents(
            self.dynamic + other.dynamic,
            self.leakage + other.leakage,
            self.gate_leakage + other.gate_leakage,
            self.short_circuit + other.short_circuit,
            self.longer_channel_leakage + other.longer_channel_leakage
        )

    def __mul__(self, factor):
        return PowerComponents(
            self.dynamic * factor,
            self.leakage * factor,
            self.gate_leakage * factor,
            self.short_circuit * factor,
            self.longer_channel_leakage * factor
        )


class PowerDef:
    def __init__(self):
        self.readOp = PowerComponents()
        self.writeOp = PowerComponents()
        self.searchOp = PowerComponents()

    def reset(self):
        self.readOp.reset()
        self.writeOp.reset()
        self.searchOp.reset()

    def __add__(self, other):
        result = PowerDef()
        result.readOp = self.readOp + other.readOp
        result.writeOp = self.writeOp + other.writeOp
        result.searchOp = self.searchOp + other.searchOp
        return result

    def __mul__(self, factor):
        result = PowerDef()
        result.readOp = self.readOp * factor
        result.writeOp = self.writeOp * factor
        result.searchOp = self.searchOp * factor
        return result


# See if any of these cause issues
Global = "Global"
Global_5 = "Global_5"
Global_10 = "Global_10"
Global_20 = "Global_20"
Global_30 = "Global_30"
Low_swing = "Low_swing"
Semi_global = "Semi_global"
Full_swing = "Full_swing"
Transmission = "Transmission"
Optical = "Optical"
Invalid_wtype = "Invalid_wtype"


Fine = "Fine"
Coarse = "Coarse"


DDR3 = "DDR3"
DDR4 = "DDR4"
LPDDR2 = "LPDDR2"
WIDE_IO = "WideIO"
LOW_SWING_DIFF = "Low_Swing_Diff"
SERIAL = "Serial"


UDIMM = "UDIMM"
RDIMM = "RDIMM"
LRDIMM = "LRDIMM"


READ = "READ"
WRITE = "WRITE"
IDLE = "IDLE"
SLEEP = "SLEEP"


NO_ECC = "NO_ECC"
SECDED = "SECDED"  # single error correction, double error detection
CHIP_KILL = "CHIP_KILL"

JUST_UDIMM = "JUST_UDIMM"
JUST_RDIMM = "JUST_RDIMM"
JUST_LRDIMM = "JUST_LRDIMM"
ALL = "ALL"


Bandwidth = "Bandwidth"
Energy = "Energy"
Cost = "Cost"

class ResultsMemArray:
    def __init__(self):
        self.Ndwl = 0
        self.Ndbl = 0
        self.Nspd = 0.0
        self.deg_bl_muxing = 0
        self.Ndsam_lev_1 = 0
        self.Ndsam_lev_2 = 0
        self.number_activated_mats_horizontal_direction = 0
        self.number_subbanks = 0
        self.page_size_in_bits = 0
        self.delay_route_to_bank = 0.0
        self.delay_crossbar = 0.0
        self.delay_addr_din_horizontal_htree = 0.0
        self.delay_addr_din_vertical_htree = 0.0
        self.delay_row_predecode_driver_and_block = 0.0
        self.delay_row_decoder = 0.0
        self.delay_bitlines = 0.0
        self.delay_sense_amp = 0.0
        self.delay_subarray_output_driver = 0.0
        self.delay_bit_mux_predecode_driver_and_block = 0.0
        self.delay_bit_mux_decoder = 0.0
        self.delay_senseamp_mux_lev_1_predecode_driver_and_block = 0.0
        self.delay_senseamp_mux_lev_1_decoder = 0.0
        self.delay_senseamp_mux_lev_2_predecode_driver_and_block = 0.0
        self.delay_senseamp_mux_lev_2_decoder = 0.0
        self.delay_input_htree = 0.0
        self.delay_output_htree = 0.0
        self.delay_dout_vertical_htree = 0.0
        self.delay_dout_horizontal_htree = 0.0
        self.delay_comparator = 0.0
        self.access_time = 0.0
        self.cycle_time = 0.0
        self.multisubbank_interleave_cycle_time = 0.0
        self.delay_request_network = 0.0
        self.delay_inside_mat = 0.0
        self.delay_reply_network = 0.0
        self.trcd = 0.0
        self.cas_latency = 0.0
        self.precharge_delay = 0.0
        self.power_routing_to_bank = PowerDef()
        self.power_addr_input_htree = PowerDef()
        self.power_data_input_htree = PowerDef()
        self.power_data_output_htree = PowerDef()
        self.power_addr_horizontal_htree = PowerDef()
        self.power_datain_horizontal_htree = PowerDef()
        self.power_dataout_horizontal_htree = PowerDef()
        self.power_addr_vertical_htree = PowerDef()
        self.power_datain_vertical_htree = PowerDef()
        self.power_row_predecoder_drivers = PowerDef()
        self.power_row_predecoder_blocks = PowerDef()
        self.power_row_decoders = PowerDef()
        self.power_bit_mux_predecoder_drivers = PowerDef()
        self.power_bit_mux_predecoder_blocks = PowerDef()
        self.power_bit_mux_decoders = PowerDef()
        self.power_senseamp_mux_lev_1_predecoder_drivers = PowerDef()
        self.power_senseamp_mux_lev_1_predecoder_blocks = PowerDef()
        self.power_senseamp_mux_lev_1_decoders = PowerDef()
        self.power_senseamp_mux_lev_2_predecoder_drivers = PowerDef()
        self.power_senseamp_mux_lev_2_predecoder_blocks = PowerDef()
        self.power_senseamp_mux_lev_2_decoders = PowerDef()
        self.power_bitlines = PowerDef()
        self.power_sense_amps = PowerDef()
        self.power_prechg_eq_drivers = PowerDef()
        self.power_output_drivers_at_subarray = PowerDef()
        self.power_dataout_vertical_htree = PowerDef()
        self.power_comparators = PowerDef()
        self.power_crossbar = PowerDef()
        self.total_power = PowerDef()
        self.area = 0.0
        self.all_banks_height = 0.0
        self.all_banks_width = 0.0
        self.bank_height = 0.0
        self.bank_width = 0.0
        self.subarray_memory_cell_area_height = 0.0
        self.subarray_memory_cell_area_width = 0.0
        self.mat_height = 0.0
        self.mat_width = 0.0
        self.routing_area_height_within_bank = 0.0
        self.routing_area_width_within_bank = 0.0
        self.area_efficiency = 0.0
        self.refresh_power = 0.0
        self.dram_refresh_period = 0.0
        self.dram_array_availability = 0.0
        self.dyn_read_energy_from_closed_page = 0.0
        self.dyn_read_energy_from_open_page = 0.0
        self.leak_power_subbank_closed_page = 0.0
        self.leak_power_subbank_open_page = 0.0
        self.leak_power_request_and_reply_networks = 0.0
        self.activate_energy = 0.0
        self.read_energy = 0.0
        self.write_energy = 0.0
        self.precharge_energy = 0.0


class uca_org_t:
    def __init__(self):
        self.tag_array2 = None
        self.data_array2 = None
        self.access_time = 0.0
        self.cycle_time = 0.0
        self.area = 0.0
        self.area_efficiency = 0.0
        self.power = PowerDef()
        self.leak_power_with_sleep_transistors_in_mats = 0.0
        self.cache_ht = 0.0
        self.cache_len = 0.0
        self.file_n = ""
        self.vdd_periph_global = 0.0
        self.valid = False
        self.tag_array = ResultsMemArray()
        self.data_array = ResultsMemArray()

    def find_delay(self):
        data_arr = self.data_array2
        tag_arr = self.tag_array2
        if g_ip.pure_ram or g_ip.pure_cam or g_ip.fully_assoc:
            self.access_time = data_arr.access_time
            if(g_ip.pure_ram):
                if (g_ip.is_main_mem):
                    self.access_time *= 10e6 / 2 
                else:
                    self.access_time *= 10e6 / 4 
            else:
                self.access_time *= 2
        else:
            if g_ip.fast_access:
                self.access_time = symbolic_convex_max(tag_arr.access_time, data_arr.access_time)
            elif g_ip.is_seq_acc:
                self.access_time = tag_arr.access_time + data_arr.access_time
            else:
                self.access_time = symbolic_convex_max(tag_arr.access_time + data_arr.delay_senseamp_mux_decoder,
                                    data_arr.delay_before_subarray_output_driver) + data_arr.delay_from_subarray_output_driver_to_output
                
            if (g_ip.is_main_mem):
                self.access_time *= 10e6 / 2 
            else:
                self.access_time *= 10e6 / 4 
                       
        

    def find_energy(self):
        if not (g_ip.pure_ram or g_ip.pure_cam or g_ip.fully_assoc):
            self.power = self.data_array2.power + self.tag_array2.power
            # self.power.readOp.dynamic *= 3e-1
            # self.power.writeOp.dynamic *= 3e-1
            # self.power.readOp.leakage *= 1e-3
        else:
            self.power = self.data_array2.power
            if g_ip.pure_ram:
                self.power.readOp.dynamic *= 5e-4
                self.power.writeOp.dynamic *= 5e-4
                self.power.readOp.leakage *= 5
            elif g_ip.fully_assoc:
                self.power.readOp.dynamic *= 15e-5
                self.power.writeOp.dynamic *= 15e-5
                self.power.readOp.leakage *= 5e-3

            if g_ip.is_main_mem:
                self.power.readOp.dynamic *= 3
                self.power.writeOp.dynamic *= 3
                self.power.readOp.leakage /= 2

        self.power.readOp.dynamic *= 1e9
        self.power.writeOp.dynamic *= 1e9
        self.power.readOp.leakage *= 1e3

    def find_area(self):
        if g_ip.pure_ram or g_ip.pure_cam or g_ip.fully_assoc:
            self.cache_ht = self.data_array2.height
            self.cache_len = self.data_array2.width
        else:
            self.cache_ht = symbolic_convex_max(self.tag_array2.height, self.data_array2.height)
            self.cache_len = self.tag_array2.width + self.data_array2.width
        self.area = self.cache_ht * self.cache_len

    def adjust_area(self):
        if g_ip.pure_ram or g_ip.pure_cam or g_ip.fully_assoc:
            if self.data_array2.area_efficiency / 100.0 < 0.2:
                area_adjust = (0.2 / (self.data_array2.area_efficiency / 100.0)) ** 0.5
                self.cache_ht /= area_adjust
                self.cache_len /= area_adjust
        self.area = self.cache_ht * self.cache_len

    def find_cyc(self):
        if g_ip.pure_ram or g_ip.pure_cam or g_ip.fully_assoc:
            self.cycle_time = self.data_array2.cycle_time
        else:
            self.cycle_time = symbolic_convex_max(self.tag_array2.cycle_time, self.data_array2.cycle_time)

    def cleanup(self):
        if self.data_array2:
            del self.data_array2
        if self.tag_array2:
            del self.tag_array2


class IOOrgT:
    def __init__(self):
        self.io_area = 0.0
        self.io_timing_margin = 0.0
        self.io_voltage_margin = 0.0
        self.io_dynamic_power = 0.0
        self.io_phy_power = 0.0
        self.io_wakeup_time = 0.0
        self.io_termination_power = 0.0


def reconfigure(local_interface: InputParameter, fin_res: uca_org_t):
    pass


def cacti_interface(infile_name: str) -> uca_org_t:
    pass


def cacti_interface(local_interface: InputParameter) -> uca_org_t:
    pass


def init_interface(local_interface: InputParameter) -> uca_org_t:
    pass


def cacti_interface(
    cache_size,
    line_size,
    associativity,
    rw_ports,
    excl_read_ports,
    excl_write_ports,
    single_ended_read_ports,
    search_ports,
    banks,
    tech_node,
    output_width,
    specific_tag,
    tag_width,
    access_mode,
    cache,
    main_mem,
    obj_func_delay,
    obj_func_dynamic_power,
    obj_func_leakage_power,
    obj_func_cycle_time,
    obj_func_area,
    dev_func_delay,
    dev_func_dynamic_power,
    dev_func_leakage_power,
    dev_func_area,
    dev_func_cycle_time,
    ed_ed2_none,
    temp,
    wt,
    data_arr_ram_cell_tech_flavor_in,
    data_arr_peri_global_tech_flavor_in,
    tag_arr_ram_cell_tech_flavor_in,
    tag_arr_peri_global_tech_flavor_in,
    interconnect_projection_type_in,
    wire_inside_mat_type_in,
    wire_outside_mat_type_in,
    REPEATERS_IN_HTREE_SEGMENTS_in,
    VERTICAL_HTREE_WIRES_OVER_THE_ARRAY_in,
    BROADCAST_ADDR_DATAIN_OVER_VERTICAL_HTREES_in,
    PAGE_SIZE_BITS_in,
    BURST_LENGTH_in,
    INTERNAL_PREFETCH_WIDTH_in,
    force_wiretype,
    wiretype,
    force_config,
    ndwl,
    ndbl,
    nspd,
    ndcm,
    ndsam1,
    ndsam2,
    ecc
) -> uca_org_t:
    pass


def cacti_interface(
    cache_size,
    line_size,
    associativity,
    rw_ports,
    excl_read_ports,
    excl_write_ports,
    single_ended_read_ports,
    banks,
    tech_node,
    page_sz,
    burst_length,
    pre_width,
    output_width,
    specific_tag,
    tag_width,
    access_mode,
    cache,
    main_mem,
    obj_func_delay,
    obj_func_dynamic_power,
    obj_func_leakage_power,
    obj_func_area,
    obj_func_cycle_time,
    dev_func_delay,
    dev_func_dynamic_power,
    dev_func_leakage_power,
    dev_func_area,
    dev_func_cycle_time,
    ed_ed2_none,
    temp,
    wt,
    data_arr_ram_cell_tech_flavor_in,
    data_arr_peri_global_tech_flavor_in,
    tag_arr_ram_cell_tech_flavor_in,
    tag_arr_peri_global_tech_flavor_in,
    interconnect_projection_type_in,
    wire_inside_mat_type_in,
    wire_outside_mat_type_in,
    is_nuca,
    core_count,
    cache_level,
    nuca_bank_count,
    nuca_obj_func_delay,
    nuca_obj_func_dynamic_power,
    nuca_obj_func_leakage_power,
    nuca_obj_func_area,
    nuca_obj_func_cycle_time,
    nuca_dev_func_delay,
    nuca_dev_func_dynamic_power,
    nuca_dev_func_leakage_power,
    nuca_dev_func_area,
    nuca_dev_func_cycle_time,
    REPEATERS_IN_HTREE_SEGMENTS_in,
    p_input
) -> uca_org_t:
    pass


def cacti_interface(
    cache_size,
    line_size,
    associativity,
    rw_ports,
    excl_read_ports,
    excl_write_ports,
    single_ended_read_ports,
    search_ports,
    banks,
    tech_node,
    output_width,
    specific_tag,
    tag_width,
    access_mode,
    cache,
    main_mem,
    obj_func_delay,
    obj_func_dynamic_power,
    obj_func_leakage_power,
    obj_func_cycle_time,
    obj_func_area,
    dev_func_delay,
    dev_func_dynamic_power,
    dev_func_leakage_power,
    dev_func_area,
    dev_func_cycle_time,
    ed_ed2_none,
    temp,
    wt,
    data_arr_ram_cell_tech_flavor_in,
    data_arr_peri_global_tech_flavor_in,
    tag_arr_ram_cell_tech_flavor_in,
    tag_arr_peri_global_tech_flavor_in,
    interconnect_projection_type_in,
    wire_inside_mat_type_in,
    wire_outside_mat_type_in,
    REPEATERS_IN_HTREE_SEGMENTS_in,
    VERTICAL_HTREE_WIRES_OVER_THE_ARRAY_in,
    BROADCAST_ADDR_DATAIN_OVER_VERTICAL_HTREES_in,
    PAGE_SIZE_BITS_in,
    BURST_LENGTH_in,
    INTERNAL_PREFETCH_WIDTH_in,
    force_wiretype,
    wiretype,
    force_config,
    ndwl,
    ndbl,
    nspd,
    ndsam1,
    ndsam2,
    ecc,
    is_3d_dram,
    burst_depth,
    IO_width,
    sys_freq,
    debug_detail,
    num_dies,
    tsv_gran_is_subarray,
    tsv_gran_os_bank,
    num_tier_row_sprd,
    num_tier_col_sprd,
    partition_level
) -> uca_org_t:
    pass


class MemArray:
    def __init__(self):
        self.Ndcm = 0
        self.Ndwl = 0
        self.Ndbl = 0
        self.Nspd = 0.0
        self.deg_bl_muxing = 0
        self.Ndsam_lev_1 = 0
        self.Ndsam_lev_2 = 0
        self.access_time = 0.0
        self.cycle_time = 0.0
        self.multisubbank_interleave_cycle_time = 0.0
        self.area_ram_cells = 0.0
        self.area = 0.0
        self.power = PowerDef()
        self.delay_senseamp_mux_decoder = 0.0
        self.delay_before_subarray_output_driver = 0.0
        self.delay_from_subarray_output_driver_to_output = 0.0
        self.height = 0.0
        self.width = 0.0
        self.mat_height = 0.0
        self.mat_length = 0.0
        self.subarray_length = 0.0
        self.subarray_height = 0.0
        self.delay_route_to_bank = 0.0
        self.delay_input_htree = 0.0
        self.delay_row_predecode_driver_and_block = 0.0
        self.delay_row_decoder = 0.0
        self.delay_bitlines = 0.0
        self.delay_sense_amp = 0.0
        self.delay_subarray_output_driver = 0.0
        self.delay_dout_htree = 0.0
        self.delay_comparator = 0.0
        self.delay_matchlines = 0.0
        self.delay_row_activate_net = 0.0
        self.delay_local_wordline = 0.0
        self.delay_column_access_net = 0.0
        self.delay_column_predecoder = 0.0
        self.delay_column_decoder = 0.0
        self.delay_column_selectline = 0.0
        self.delay_datapath_net = 0.0
        self.delay_global_data = 0.0
        self.delay_local_data_and_drv = 0.0
        self.delay_data_buffer = 0.0
        self.energy_row_activate_net = 0.0
        self.energy_row_predecode_driver_and_block = 0.0
        self.energy_row_decoder = 0.0
        self.energy_local_wordline = 0.0
        self.energy_bitlines = 0.0
        self.energy_sense_amp = 0.0
        self.energy_column_access_net = 0.0
        self.energy_column_predecoder = 0.0
        self.energy_column_decoder = 0.0
        self.energy_column_selectline = 0.0
        self.energy_datapath_net = 0.0
        self.energy_global_data = 0.0
        self.energy_local_data_and_drv = 0.0
        self.energy_data_buffer = 0.0
        self.energy_subarray_output_driver = 0.0
        self.all_banks_height = 0.0
        self.all_banks_width = 0.0
        self.area_efficiency = 0.0
        self.power_routing_to_bank = PowerDef()
        self.power_addr_input_htree = PowerDef()
        self.power_data_input_htree = PowerDef()
        self.power_data_output_htree = PowerDef()
        self.power_htree_in_search = PowerDef()
        self.power_htree_out_search = PowerDef()
        self.power_row_predecoder_drivers = PowerDef()
        self.power_row_predecoder_blocks = PowerDef()
        self.power_row_decoders = PowerDef()
        self.power_bit_mux_predecoder_drivers = PowerDef()
        self.power_bit_mux_predecoder_blocks = PowerDef()
        self.power_bit_mux_decoders = PowerDef()
        self.power_senseamp_mux_lev_1_predecoder_drivers = PowerDef()
        self.power_senseamp_mux_lev_1_predecoder_blocks = PowerDef()
        self.power_senseamp_mux_lev_1_decoders = PowerDef()
        self.power_senseamp_mux_lev_2_predecoder_drivers = PowerDef()
        self.power_senseamp_mux_lev_2_predecoder_blocks = PowerDef()
        self.power_senseamp_mux_lev_2_decoders = PowerDef()
        self.power_bitlines = PowerDef()
        self.power_sense_amps = PowerDef()
        self.power_prechg_eq_drivers = PowerDef()
        self.power_output_drivers_at_subarray = PowerDef()
        self.power_dataout_vertical_htree = PowerDef()
        self.power_comparators = PowerDef()
        self.power_cam_bitline_precharge_eq_drv = PowerDef()
        self.power_searchline = PowerDef()
        self.power_searchline_precharge = PowerDef()
        self.power_matchlines = PowerDef()
        self.power_matchline_precharge = PowerDef()
        self.power_matchline_to_wordline_drv = PowerDef()
        self.arr_min = None
        self.wt = None
        self.activate_energy = 0.0
        self.read_energy = 0.0
        self.write_energy = 0.0
        self.precharge_energy = 0.0
        self.refresh_power = 0.0
        self.leak_power_subbank_closed_page = 0.0
        self.leak_power_subbank_open_page = 0.0
        self.leak_power_request_and_reply_networks = 0.0
        self.precharge_delay = 0.0
        self.array_leakage = 0.0
        self.wl_leakage = 0.0
        self.cl_leakage = 0.0
        self.sram_sleep_tx_width = 0.0
        self.wl_sleep_tx_width = 0.0
        self.cl_sleep_tx_width = 0.0
        self.sram_sleep_tx_area = 0.0
        self.wl_sleep_tx_area = 0.0
        self.cl_sleep_tx_area = 0.0
        self.sram_sleep_wakeup_latency = 0.0
        self.wl_sleep_wakeup_latency = 0.0
        self.cl_sleep_wakeup_latency = 0.0
        self.bl_floating_wakeup_latency = 0.0
        self.sram_sleep_wakeup_energy = 0.0
        self.wl_sleep_wakeup_energy = 0.0
        self.cl_sleep_wakeup_energy = 0.0
        self.bl_floating_wakeup_energy = 0.0
        self.num_active_mats = 0
        self.num_submarray_mats = 0
        self.t_RCD = 0.0
        self.t_RAS = 0.0
        self.t_RC = 0.0
        self.t_CAS = 0.0
        self.t_RP = 0.0
        self.t_RRD = 0.0
        self.activate_power = 0.0
        self.read_power = 0.0
        self.write_power = 0.0
        self.peak_read_power = 0.0
        self.num_row_subarray = 0
        self.num_col_subarray = 0
        self.delay_TSV_tot = 0.0
        self.area_TSV_tot = 0.0
        self.dyn_pow_TSV_tot = 0.0
        self.dyn_pow_TSV_per_access = 0.0
        self.num_TSV_tot = 0
        self.area_lwl_drv = 0.0
        self.area_row_predec_dec = 0.0
        self.area_col_predec_dec = 0.0
        self.area_subarray = 0.0
        self.area_bus = 0.0
        self.area_address_bus = 0.0
        self.area_data_bus = 0.0
        self.area_data_drv = 0.0
        self.area_IOSA = 0.0
        self.area_sense_amp = 0.0

    @staticmethod
    def lt(m1, m2):
        if m1.Nspd < m2.Nspd:
            return True
        elif m1.Nspd > m2.Nspd:
            return False
        elif m1.Ndwl < m2.Ndwl:
            return True
        elif m1.Ndwl > m2.Ndwl:
            return False
        elif m1.Ndbl < m2.Ndbl:
            return True
        elif m1.Ndbl > m2.Ndbl:
            return False
        elif m1.deg_bl_muxing < m2.deg_bl_muxing:
            return True
        elif m1.deg_bl_muxing > m2.deg_bl_muxing:
            return False
        elif m1.Ndsam_lev_1 < m2.Ndsam_lev_1:
            return True
        elif m1.Ndsam_lev_1 > m2.Ndsam_lev_1:
            return False
        elif m1.Ndsam_lev_2 < m2.Ndsam_lev_2:
            return True
        else:
            return False
