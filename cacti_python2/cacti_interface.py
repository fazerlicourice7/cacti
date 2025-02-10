"""
cacti_interface.py
Python translation of cacti_interface.{h, cc} from CACTI 7.0
All references to external modules (e.g. basic_circuit, parameter, etc.)
should be adapted to your Python environment.
"""

from math import sqrt
# If you have a 'const' or 'basic_circuit' or 'parameter' python file, you can import them as needed:
# from .const import * 
# from .basic_circuit import MAX
# from .parameter import InputParameter

# Define Python enumerations or use simple constants for Wire_type, etc.

def symbolic_convex_max(a, b):
    """
    An approximation to the max function that plays well with numeric
    or symbolic solvers.
    """
    return 0.5 * (a + b + abs(a - b))

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

class TSV_type:
    Fine = 0
    Coarse = 1

# ali
class Mem_IO_type:
    DDR3 = 0
    DDR4 = 1
    LPDDR2 = 2
    WideIO = 3
    Low_Swing_Diff = 4
    Serial = 5

class Mem_DIMM:
    UDIMM = 0
    RDIMM = 1
    LRDIMM = 2

class Mem_state:
    READ = 0
    WRITE = 1
    IDLE = 2
    SLEEP = 3

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

# End ali enumerations/definitions.


class powerComponents:
    """
    Python version of the C++ powerComponents struct/class.
    """
    def __init__(self, dynamic=0.0, leakage=0.0, gate_leakage=0.0,
                 short_circuit=0.0, longer_channel_leakage=0.0):
        self.dynamic = dynamic
        self.leakage = leakage
        self.gate_leakage = gate_leakage
        self.short_circuit = short_circuit
        self.longer_channel_leakage = longer_channel_leakage

    def reset(self):
        self.dynamic = 0.0
        self.leakage = 0.0
        self.gate_leakage = 0.0
        self.short_circuit = 0.0
        self.longer_channel_leakage = 0.0

    def __add__(self, other):
        """
        Mimic operator+(powerComponents, powerComponents)
        """
        result = powerComponents()
        result.dynamic  = self.dynamic  + other.dynamic
        result.leakage  = self.leakage  + other.leakage
        result.gate_leakage  = self.gate_leakage + other.gate_leakage
        result.short_circuit = self.short_circuit + other.short_circuit
        result.longer_channel_leakage = (self.longer_channel_leakage +
                                         other.longer_channel_leakage)
        return result

    def __mul__(self, factor):
        """
        In C++: operator*(powerComponents, double const * const)
        We'll assume factor is just a float/double.
        """
        result = powerComponents()
        result.dynamic  = self.dynamic  * factor
        result.leakage  = self.leakage  * factor
        result.gate_leakage  = self.gate_leakage * factor
        result.short_circuit = self.short_circuit * factor
        result.longer_channel_leakage = self.longer_channel_leakage * factor
        return result


class powerDef:
    """
    Python version of the C++ powerDef class.
    Contains readOp, writeOp, searchOp (CAM or fully assoc).
    """
    def __init__(self):
        self.readOp = powerComponents()
        self.writeOp = powerComponents()
        self.searchOp = powerComponents()

    def reset(self):
        self.readOp.reset()
        self.writeOp.reset()
        self.searchOp.reset()

    def __add__(self, other):
        """
        Mimic operator+(powerDef, powerDef).
        """
        result = powerDef()
        result.readOp   = self.readOp + other.readOp
        result.writeOp  = self.writeOp + other.writeOp
        result.searchOp = self.searchOp + other.searchOp
        return result

    def __mul__(self, factor):
        """
        Mimic operator*(powerDef, double const * const).
        We'll treat factor as a float for simplicity.
        """
        result = powerDef()
        result.readOp   = self.readOp   * factor
        result.writeOp  = self.writeOp  * factor
        result.searchOp = self.searchOp * factor
        return result


class InputParameter:
    """
    Python version of C++ InputParameter with many fields.
    See parameter.py for an alternate or combined version.
    """
    def __init__(self):
        # We initialize with default or placeholder values
        self.cache_sz = 0
        self.line_sz  = 0
        self.assoc    = 0
        self.nbanks   = 1
        self.out_w    = 0
        self.specific_tag = False
        self.tag_w    = 42
        self.access_mode = 0
        self.obj_func_dyn_energy = 0
        self.obj_func_dyn_power = 0
        self.obj_func_leak_power = 0
        self.obj_func_cycle_t = 0

        self.F_sz_nm = 45.0
        self.F_sz_um = 0.045
        self.num_rw_ports = 1
        self.num_rd_ports = 0
        self.num_wr_ports = 0
        self.num_se_rd_ports = 0
        self.num_search_ports = 0
        self.is_main_mem = False
        self.is_3d_mem   = False
        self.print_detail_debug = False
        self.is_cache    = True
        self.pure_ram    = False
        self.pure_cam    = False
        self.rpters_in_htree = True
        self.ver_htree_wires_over_array = 0
        self.broadcast_addr_din_over_ver_htrees = 0
        self.temp        = 300
        self.ram_cell_tech_type = 0
        self.peri_global_tech_type = 0
        self.data_arr_ram_cell_tech_type = 0
        self.data_arr_peri_global_tech_type = 0
        self.tag_arr_ram_cell_tech_type = 0
        self.tag_arr_peri_global_tech_type = 0
        self.burst_len = 1
        self.int_prefetch_w = 1
        self.page_sz_bits  = 0
        self.num_die_3d    = 1
        self.burst_depth   = 1
        self.io_width      = 8
        self.sys_freq_MHz  = 2000
        self.tsv_is_subarray_type = 0
        self.tsv_os_bank_type = 0
        self.TSV_proj_type = 0
        self.partition_gran = 0
        self.num_tier_row_sprd = 1
        self.num_tier_col_sprd = 1
        self.fine_gran_bank_lvl = False
        self.ic_proj_type = 0
        self.wire_is_mat_type = 2
        self.wire_os_mat_type = 2
        self.wt = Wire_type.Global_
        self.force_wiretype = 0
        self.print_input_args = False
        self.nuca_cache_sz = 0
        self.ndbl = 1
        self.ndwl = 1
        self.nspd = 1
        self.ndsam1 = 1
        self.ndsam2 = 1
        self.ndcm = 1
        self.force_cache_config = False
        self.cache_level = 0
        self.cores = 1
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
        self.block_sz = 64
        self.tag_assoc = 1
        self.data_assoc= 1
        self.is_seq_acc = False
        self.fully_assoc = False
        self.nsets = 0
        self.print_detail = 1
        self.add_ecc_b_ = False
        self.throughput=0
        self.latency=0
        self.pipelinable=False
        self.pipeline_stages=1
        self.per_stage_vector=1
        self.with_clock_grid=True
        self.array_power_gated=False
        self.bitline_floating=False
        self.wl_power_gated=False
        self.cl_power_gated=False
        self.interconect_power_gated=False
        self.power_gating=False
        self.perfloss=0
        self.cl_vertical=False
        self.addr_timing=0
        self.duty_cycle=0
        self.mem_density=0
        self.bus_bw=0
        self.activity_dq=0
        self.activity_ca=0
        self.bus_freq=0
        self.mem_data_width=0
        self.num_mem_dq=0
        self.num_clk=0
        self.num_ca=0
        self.num_dqs=0
        self.num_dq=0
        self.rtt_value=0
        self.ron_value=0
        self.tflight_value=0
        self.iostate=Mem_state.IDLE
        self.dram_ecc=Mem_ECC.NO_ECC
        self.io_type=Mem_IO_type.DDR3
        self.dram_dimm=Mem_DIMM.UDIMM
        self.num_bobs=0
        self.capacity=0
        self.num_channels_per_bob=1
        self.first_metric=MemCad_metrics.Bandwidth
        self.second_metric=MemCad_metrics.Energy
        self.third_metric=MemCad_metrics.Cost
        self.dimm_model=DIMM_Model.ALL
        self.low_power_permitted=True
        self.load=0.5
        self.row_buffer_hit_rate=0
        self.rd_2_wr_ratio=1
        self.same_bw_in_bob=True
        self.mirror_in_bob=False
        self.total_power=False
        self.verbose=False

    def parse_cfg(self, infile):
        """
        In C++, this would parse a config file. In Python you might do:
        with open(infile) as f:
            ...
        and read lines, setting self fields.
        """
        pass  # Placeholder

    def error_checking(self):
        """
        Return False if input parameters are inconsistent, True otherwise.
        """
        # Implement any checks you need.
        return True

    def display_ip(self):
        """
        Print the input parameters for debugging.
        """
        print("InputParameter dump:")
        print(f" cache_sz={self.cache_sz}, line_sz={self.line_sz}, assoc={self.assoc}, nbanks={self.nbanks} ...")
        # etc.


class results_mem_array:
    """
    Python version of the struct used for storing results for a memory array
    or subarray. 
    """
    def __init__(self):
        self.Ndwl = 1
        self.Ndbl = 1
        self.Nspd = 1.0
        self.deg_bl_muxing = 1
        self.Ndsam_lev_1 = 1
        self.Ndsam_lev_2 = 1
        self.number_activated_mats_horizontal_direction = 1
        self.number_subbanks = 1
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

        self.power_routing_to_bank = powerDef()
        self.power_addr_input_htree = powerDef()
        self.power_data_input_htree = powerDef()
        self.power_data_output_htree = powerDef()
        self.power_addr_horizontal_htree = powerDef()
        self.power_datain_horizontal_htree = powerDef()
        self.power_dataout_horizontal_htree = powerDef()
        self.power_addr_vertical_htree = powerDef()
        self.power_datain_vertical_htree = powerDef()
        self.power_row_predecoder_drivers = powerDef()
        self.power_row_predecoder_blocks = powerDef()
        self.power_row_decoders = powerDef()
        self.power_bit_mux_predecoder_drivers = powerDef()
        self.power_bit_mux_predecoder_blocks = powerDef()
        self.power_bit_mux_decoders = powerDef()
        self.power_senseamp_mux_lev_1_predecoder_drivers = powerDef()
        self.power_senseamp_mux_lev_1_predecoder_blocks = powerDef()
        self.power_senseamp_mux_lev_1_decoders = powerDef()
        self.power_senseamp_mux_lev_2_predecoder_drivers = powerDef()
        self.power_senseamp_mux_lev_2_predecoder_blocks = powerDef()
        self.power_senseamp_mux_lev_2_decoders = powerDef()
        self.power_bitlines = powerDef()
        self.power_sense_amps = powerDef()
        self.power_prechg_eq_drivers = powerDef()
        self.power_output_drivers_at_subarray = powerDef()
        self.power_dataout_vertical_htree = powerDef()
        self.power_comparators = powerDef()
        self.power_crossbar = powerDef()
        self.total_power = powerDef()

        self.area = 0.0
        self.all_banks_height = 0.0
        self.all_banks_width  = 0.0
        self.bank_height      = 0.0
        self.bank_width       = 0.0
        self.subarray_memory_cell_area_height = 0.0
        self.subarray_memory_cell_area_width  = 0.0
        self.mat_height = 0.0
        self.mat_width  = 0.0
        self.routing_area_height_within_bank = 0.0
        self.routing_area_width_within_bank  = 0.0
        self.area_efficiency = 0.0
        self.refresh_power = 0.0
        self.dram_refresh_period = 0.0
        self.dram_array_availability = 1.0
        self.dyn_read_energy_from_closed_page = 0.0
        self.dyn_read_energy_from_open_page = 0.0
        self.leak_power_subbank_closed_page = 0.0
        self.leak_power_subbank_open_page = 0.0
        self.leak_power_request_and_reply_networks = 0.0
        self.activate_energy = 0.0
        self.read_energy = 0.0
        self.write_energy = 0.0
        self.precharge_energy = 0.0


class MemArray:
    """
    Python version of the C++ MemArray class.
    Contains data about a subarray, mats, delays, energies, etc.
    """
    __slots__ = (
        'Ndcm','Ndwl','Ndbl','Nspd','deg_bl_muxing','Ndsam_lev_1','Ndsam_lev_2',
        'access_time','cycle_time','multisubbank_interleave_cycle_time','area_ram_cells','area','power',
        'delay_senseamp_mux_decoder','delay_before_subarray_output_driver','delay_from_subarray_output_driver_to_output',
        'height','width','mat_height','mat_length','subarray_length','subarray_height','delay_route_to_bank',
        'delay_input_htree','delay_row_predecode_driver_and_block','delay_row_decoder','delay_bitlines','delay_sense_amp',
        'delay_subarray_output_driver','delay_dout_htree','delay_comparator','delay_matchlines','delay_row_activate_net',
        'delay_local_wordline','delay_column_access_net','delay_column_predecoder','delay_column_decoder','delay_column_selectline',
        'delay_datapath_net','delay_global_data','delay_local_data_and_drv','delay_data_buffer',
        'energy_row_activate_net','energy_row_predecode_driver_and_block','energy_row_decoder','energy_local_wordline',
        'energy_bitlines','energy_sense_amp','energy_column_access_net','energy_column_predecoder','energy_column_decoder',
        'energy_column_selectline','energy_datapath_net','energy_global_data','energy_local_data_and_drv','energy_data_buffer',
        'energy_subarray_output_driver','all_banks_height','all_banks_width','area_efficiency','power_routing_to_bank',
        'power_addr_input_htree','power_data_input_htree','power_data_output_htree','power_htree_in_search','power_htree_out_search',
        'power_row_predecoder_drivers','power_row_predecoder_blocks','power_row_decoders','power_bit_mux_predecoder_drivers',
        'power_bit_mux_predecoder_blocks','power_bit_mux_decoders','power_senseamp_mux_lev_1_predecoder_drivers',
        'power_senseamp_mux_lev_1_predecoder_blocks','power_senseamp_mux_lev_1_decoders','power_senseamp_mux_lev_2_predecoder_drivers',
        'power_senseamp_mux_lev_2_predecoder_blocks','power_senseamp_mux_lev_2_decoders','power_bitlines','power_sense_amps',
        'power_prechg_eq_drivers','power_output_drivers_at_subarray','power_dataout_vertical_htree','power_comparators',
        'power_cam_bitline_precharge_eq_drv','power_searchline','power_searchline_precharge','power_matchlines',
        'power_matchline_precharge','power_matchline_to_wordline_drv','arr_min','wt','activate_energy','read_energy','write_energy',
        'precharge_energy','refresh_power','leak_power_subbank_closed_page','leak_power_subbank_open_page',
        'leak_power_request_and_reply_networks','precharge_delay','array_leakage','wl_leakage','cl_leakage',
        'sram_sleep_tx_width','wl_sleep_tx_width','cl_sleep_tx_width','sram_sleep_tx_area','wl_sleep_tx_area','cl_sleep_tx_area',
        'sram_sleep_wakeup_latency','wl_sleep_wakeup_latency','cl_sleep_wakeup_latency','bl_floating_wakeup_latency',
        'sram_sleep_wakeup_energy','wl_sleep_wakeup_energy','cl_sleep_wakeup_energy','bl_floating_wakeup_energy',
        'num_active_mats','num_submarray_mats','t_RCD','t_RAS','t_RC','t_CAS','t_RP','t_RRD',
        'activate_power','read_power','write_power','peak_read_power','num_row_subarray','num_col_subarray',
        'delay_TSV_tot','area_TSV_tot','dyn_pow_TSV_tot','dyn_pow_TSV_per_access','num_TSV_tot','area_lwl_drv',
        'area_row_predec_dec','area_col_predec_dec','area_subarray','area_bus','area_address_bus','area_data_bus',
        'area_data_drv','area_IOSA','area_sense_amp'
    )

    def __init__(self):
        # Initialize your fields
        self.Ndcm = 1
        self.Ndwl = 1
        self.Ndbl = 1
        self.Nspd = 1.0
        self.deg_bl_muxing = 1
        self.Ndsam_lev_1 = 1
        self.Ndsam_lev_2 = 1
        self.access_time = 0.0
        self.cycle_time = 0.0
        self.multisubbank_interleave_cycle_time = 0.0
        self.area_ram_cells = 0.0
        self.area = 0.0
        self.power = powerDef()
        self.delay_senseamp_mux_decoder = 0.0
        self.delay_before_subarray_output_driver = 0.0
        self.delay_from_subarray_output_driver_to_output = 0.0
        self.height = 0.0
        self.width  = 0.0
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
        self.all_banks_width  = 0.0
        self.area_efficiency  = 1.0

        self.power_routing_to_bank = powerDef()
        self.power_addr_input_htree = powerDef()
        self.power_data_input_htree = powerDef()
        self.power_data_output_htree = powerDef()
        self.power_htree_in_search = powerDef()
        self.power_htree_out_search = powerDef()
        self.power_row_predecoder_drivers = powerDef()
        self.power_row_predecoder_blocks = powerDef()
        self.power_row_decoders = powerDef()
        self.power_bit_mux_predecoder_drivers = powerDef()
        self.power_bit_mux_predecoder_blocks = powerDef()
        self.power_bit_mux_decoders = powerDef()
        self.power_senseamp_mux_lev_1_predecoder_drivers = powerDef()
        self.power_senseamp_mux_lev_1_predecoder_blocks = powerDef()
        self.power_senseamp_mux_lev_1_decoders = powerDef()
        self.power_senseamp_mux_lev_2_predecoder_drivers = powerDef()
        self.power_senseamp_mux_lev_2_predecoder_blocks = powerDef()
        self.power_senseamp_mux_lev_2_decoders = powerDef()
        self.power_bitlines = powerDef()
        self.power_sense_amps = powerDef()
        self.power_prechg_eq_drivers = powerDef()
        self.power_output_drivers_at_subarray = powerDef()
        self.power_dataout_vertical_htree = powerDef()
        self.power_comparators = powerDef()

        self.power_cam_bitline_precharge_eq_drv = powerDef()
        self.power_searchline = powerDef()
        self.power_searchline_precharge = powerDef()
        self.power_matchlines = powerDef()
        self.power_matchline_precharge = powerDef()
        self.power_matchline_to_wordline_drv = powerDef()

        self.arr_min = None
        self.wt      = Wire_type.Global_

        # DRAM stats
        self.activate_energy = 0.0
        self.read_energy     = 0.0
        self.write_energy    = 0.0
        self.precharge_energy= 0.0
        self.refresh_power   = 0.0
        self.leak_power_subbank_closed_page = 0.0
        self.leak_power_subbank_open_page   = 0.0
        self.leak_power_request_and_reply_networks = 0.0
        self.precharge_delay = 0.0
        self.array_leakage   = 0.0
        self.wl_leakage      = 0.0
        self.cl_leakage      = 0.0

        self.sram_sleep_tx_width = 0.0
        self.wl_sleep_tx_width   = 0.0
        self.cl_sleep_tx_width   = 0.0
        self.sram_sleep_tx_area  = 0.0
        self.wl_sleep_tx_area    = 0.0
        self.cl_sleep_tx_area    = 0.0
        self.sram_sleep_wakeup_latency = 0.0
        self.wl_sleep_wakeup_latency   = 0.0
        self.cl_sleep_wakeup_latency   = 0.0
        self.bl_floating_wakeup_latency= 0.0
        self.sram_sleep_wakeup_energy  = 0.0
        self.wl_sleep_wakeup_energy    = 0.0
        self.cl_sleep_wakeup_energy    = 0.0
        self.bl_floating_wakeup_energy = 0.0

        self.num_active_mats= 1
        self.num_submarray_mats= 1

        # CACTI3DD 3d dram stats
        self.t_RCD = 0.0
        self.t_RAS = 0.0
        self.t_RC  = 0.0
        self.t_CAS = 0.0
        self.t_RP  = 0.0
        self.t_RRD = 0.0
        self.activate_power = 0.0
        self.read_power     = 0.0
        self.write_power    = 0.0
        self.peak_read_power= 0.0
        self.num_row_subarray= 0
        self.num_col_subarray= 0
        self.delay_TSV_tot=0.0
        self.area_TSV_tot=0.0
        self.dyn_pow_TSV_tot=0.0
        self.dyn_pow_TSV_per_access=0.0
        self.num_TSV_tot=0
        self.area_lwl_drv=0.0
        self.area_row_predec_dec=0.0
        self.area_col_predec_dec=0.0
        self.area_subarray=0.0
        self.area_bus=0.0
        self.area_address_bus=0.0
        self.area_data_bus=0.0
        self.area_data_drv=0.0
        self.area_IOSA=0.0
        self.area_sense_amp=0.0

    @staticmethod
    def lt(m1, m2):
        """
        Equivalent to the static bool MemArray::lt(...) in the C++ code.
        Compare for a custom ordering. 
        """
        if m1.Nspd < m2.Nspd: return True
        elif m1.Nspd > m2.Nspd: return False
        elif m1.Ndwl < m2.Ndwl: return True
        elif m1.Ndwl > m2.Ndwl: return False
        elif m1.Ndbl < m2.Ndbl: return True
        elif m1.Ndbl > m2.Ndbl: return False
        elif m1.deg_bl_muxing < m2.deg_bl_muxing: return True
        elif m1.deg_bl_muxing > m2.deg_bl_muxing: return False
        elif m1.Ndsam_lev_1 < m2.Ndsam_lev_1: return True
        elif m1.Ndsam_lev_1 > m2.Ndsam_lev_1: return False
        elif m1.Ndsam_lev_2 < m2.Ndsam_lev_2: return True
        else:
            return False


class uca_org_t:
    """
    Python version of the C++ uca_org_t class.
    """
    def __init__(self, g_ip, g_tp):
        self.tag_array2 = None
        self.data_array2 = None
        self.access_time = 0.0
        self.cycle_time = 0.0
        self.area = 0.0
        self.area_efficiency = 0.0
        self.power = powerDef()
        self.leak_power_with_sleep_transistors_in_mats = 0.0
        self.cache_ht = 0.0
        self.cache_len = 0.0
        self.file_n = ""
        self.vdd_periph_global = 0.0
        self.valid = True
        self.tag_array = results_mem_array()
        self.data_array= results_mem_array()

        self.g_ip = g_ip
        self.g_tp = g_tp

    def symbolic_convex_max(self, a, b):
        """
        An approximation to the max function that plays well with numeric
        or symbolic solvers.
        """
        return 0.5 * (a + b + abs(a - b))

    def find_delay(self):
        """
        Python version of uca_org_t::find_delay()
        """
        g_ip = self.g_ip
        g_tp = self.g_tp

        data_arr = self.data_array2
        tag_arr  = self.tag_array2
        # Replace usage of "g_ip->..."
        # Suppose we have a global "g_ip" or pass it in. We'll stub for now:
        from .parameter import g_ip  # or however you do it

        if g_ip.pure_ram or g_ip.pure_cam or g_ip.fully_assoc:
            self.access_time = data_arr.access_time
        elif g_ip.fast_access == True:
            self.access_time = self.symbolic_convex_max(tag_arr.access_time, data_arr.access_time)
        elif g_ip.is_seq_acc == True:
            self.access_time = tag_arr.access_time + data_arr.access_time
        else:
            self.access_time = self.symbolic_convex_max(tag_arr.access_time + data_arr.delay_senseamp_mux_decoder,
                                   data_arr.delay_before_subarray_output_driver) + \
                               data_arr.delay_from_subarray_output_driver_to_output

    def find_energy(self):
        g_ip = self.g_ip
        g_tp = self.g_tp

        if not(g_ip.pure_ram or g_ip.pure_cam or g_ip.fully_assoc):
            self.power = self.data_array2.power + self.tag_array2.power
        else:
            self.power = self.data_array2.power

    def find_area(self):
        g_ip = self.g_ip
        g_tp = self.g_tp

        if (g_ip.pure_ram or g_ip.pure_cam or g_ip.fully_assoc):
            self.cache_ht  = self.data_array2.height
            self.cache_len = self.data_array2.width
        else:
            self.cache_ht  = symbolic_convex_max(self.tag_array2.height, self.data_array2.height)
            self.cache_len = self.tag_array2.width + self.data_array2.width
        self.area = self.cache_ht * self.cache_len

    def adjust_area(self):
        """
        For McPAT only to adjust routing overhead
        """
        g_ip = self.g_ip
        g_tp = self.g_tp

        if (g_ip.pure_ram or g_ip.pure_cam or g_ip.fully_assoc):
            # Example from cacti code
            if (self.data_array2.area_efficiency/100.0 < 0.2):
                area_adjust = sqrt(0.2/(self.data_array2.area_efficiency/100.0))
                self.cache_ht  /= area_adjust
                self.cache_len /= area_adjust
        self.area = self.cache_ht * self.cache_len

    def find_cyc(self):
        g_ip = self.g_ip
        g_tp = self.g_tp

        if (g_ip.pure_ram or g_ip.pure_cam or g_ip.fully_assoc):
            self.cycle_time = self.data_array2.cycle_time
        else:
            self.cycle_time = symbolic_convex_max(self.tag_array2.cycle_time,
                                  self.data_array2.cycle_time)
            
    def find_IO(self):
        from .extio import Extio
        from .extio_technology import IOTechParam

        iot = IOTechParam(self.g_ip, self.g_ip.io_type, self.g_ip.num_mem_dq, self.g_ip.mem_data_width, self.g_ip.num_dq, self.g_ip.dram_dimm, 1, self.g_ip.bus_freq)
        testextio = Extio(self.g_ip, iot)

        self.io_area = testextio.extio_area()
        self.io_timing_margin = testextio.extio_eye()
        self.io_dynamic_power = testextio.extio_power_dynamic()
        self.io_phy_power = testextio.extio_power_phy()
        self.io_termination_power = testextio.extio_power_term()

    def cleanup(self):
        # In C++ we do: delete data_array2, tag_array2
        # In Python, garbage collection is automatic. 
        self.data_array2 = None
        self.tag_array2  = None

# Additional classes
class IO_org_t:
    """
    The I/O organization class from the .h file
    """
    def __init__(self):
        self.io_area = 0.0
        self.io_timing_margin = 0.0
        self.io_voltage_margin = 0.0
        self.io_dynamic_power = 0.0
        self.io_phy_power = 0.0
        self.io_wakeup_time = 0.0
        self.io_termination_power = 0.0


def reconfigure(local_interface, fin_res):
    """
    Python version of the C++ reconfigure(...) function.
    Adjust 'fin_res' based on 'local_interface' if needed.
    """
    pass  # placeholder

def cacti_interface(infile_name):
    """
    Python version of cacti_interface(const string & infile_name)
    """
    # Step 1: parse input
    ip = InputParameter()
    ip.parse_cfg(infile_name)
    # Step 2: do error checking
    if not ip.error_checking():
        print("Input parameter error!")
    # Step 3: call internal cacti logic, produce results in a uca_org_t
    uca = uca_org_t()
    # ...
    return uca

def cacti_interface_from_inputparam(local_interface):
    """
    McPAT's plain interface: cacti_interface(InputParameter * const local_interface)
    """
    # replicate the logic of cacti_interface, but using local_interface
    uca = uca_org_t()
    # ...
    return uca

def init_interface(local_interface):
    """
    Also from the C++ code: init_interface
    """
    # ...
    return cacti_interface_from_inputparam(local_interface)

# Then you would add the other cacti_interface(...) overloads as separate Python functions:
# def cacti_interface( ... list of parameters ... ):
#     ...
#     return uca_org_t()

# For example (shortened stub):
def cacti_interface_long_params(*args, **kwargs):
    """
    Python stub for the very long cacti_interface(...) signature.
    You can parse arguments or do all your logic here.
    """
    uca = uca_org_t()
    # ...
    return uca
