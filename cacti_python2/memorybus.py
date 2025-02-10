# memory_bus.py (updated)

import math
from .component import Component
from .cacti_interface import powerDef
from .const import *
from .wire import Wire
from .decoder import Driver, Decoder, PredecBlk, PredecBlkDrv, Predec

from .basic_circuit import (
    is_pow2, _log2, is_equal,
    wire_resistance, wire_capacitance, tsv_resistance, tsv_capacitance, tsv_area,
    pmos_to_nmos_sz_ratio, gate_C, gate_C_pass, tr_R_on, drain_C_, cmos_Ig_leakage,
    horowitz, cmos_Isub_leakage, simplified_nmos_Isat
)

class Memorybus(Component):
    """
    Python version of the C++ Memorybus class, adapted from memory_bus.h and memory_bus.cc.
    Inherits from Component (so it has self.area, self.power, etc.).
    """

    def __init__(self,
                 g_ip,
                 g_tp,
                 wire_model,               # enum Wire_type
                 mat_w: float,
                 mat_h: float,
                 subarray_w: float,
                 subarray_h: float,
                 row_add_bits: int,
                 col_add_bits: int,
                 data_bits: int,
                 ndbl: int,
                 ndwl: int,
                 membus_type,             # enum Memorybus_type
                 dp,                      # DynamicParameter reference
                 dt=None):
        super().__init__()
        self.g_ip = g_ip
        self.g_tp = g_tp
        self.dp   = dp

        if dt is None:
            dt = self.g_tp.peri_global

        self.deviceType = dt
        self.membus_type = membus_type
        self.mat_width     = mat_w
        self.mat_height    = mat_h
        self.subarray_width= subarray_w
        self.subarray_height= subarray_h
        self.row_add_bits  = row_add_bits
        self.col_add_bits  = col_add_bits
        self.data_bits     = data_bits
        self.ndbl          = ndbl
        self.ndwl          = ndwl
        self.wt            = wire_model
        self.dp            = dp
        self.is_dram       = dp.is_dram

        # Some of these fields will be set later in Network()
        self.center_stripe = None
        self.bank_bus      = None
        self.global_WL     = None
        self.column_sel    = None
        self.local_data    = None
        self.global_data   = None
        self.out_seg       = None

        self.lwl_drv       = None
        self.local_data_drv= None
        self.global_data_drv= None
        self.add_dec       = None
        self.add_predec    = None

        self.in_rise_time  = 0.0
        self.out_rise_time = 0.0
        self.delay = 0.0

        self.max_unpipelined_link_delay = 0.0

        self.min_w_nmos = g_tp.min_w_nmos_
        self.min_w_pmos = dt.n_to_p_eff_curr_drv_ratio * self.min_w_nmos

        self.semi_repeated_global_line = 0
        self.cell = Component()
        self.cell.h = self.g_tp.dram.b_h
        self.cell.w = self.g_tp.dram.b_w

        # Additional power/area fields from memorybus.h
        self.power_bit    = powerDef()
        self.power_bus    = powerDef()
        self.power_lwl_drv= powerDef()
        self.power_add_decoders    = powerDef()
        self.power_global_WL       = powerDef()
        self.power_local_WL        = powerDef()
        self.power_add_predecoder  = powerDef()
        self.power_burst           = powerDef()
        self.power_col_sel         = powerDef()
        self.power_local_data      = powerDef()
        self.power_global_data     = powerDef()

        self.delay_bus         = 0.0
        self.delay_add_predecoder=0.0
        self.delay_add_decoder = 0.0
        self.delay_lwl_drv     = 0.0
        self.delay_global_data = 0.0
        self.delay_local_data  = 0.0
        self.delay_data_buffer = 0.0

        # area-related
        self.area_sense_amp  = 0.0
        self.area_subarray   = 0.0
        self.area_bus        = 0.0
        self.area_address_bus= 0.0
        self.area_data_bus   = 0.0
        self.area_data_drv   = 0.0
        self.area_IOSA       = 0.0
        self.area_local_dataline = 0.0

        self.area_row_predec_dec = 0.0
        self.area_col_predec_dec = 0.0
        self.area_lwl_drv        = 0.0
        self.area_subarray       = 0.0
        self.area_bus            = 0.0
        self.area_address_bus    = 0.0
        self.area_data_bus       = 0.0
        self.area_data_drv       = 0.0
        self.area_IOSA           = 0.0
        self.area_local_dataline = 0.0
        self.area_sense_amp      = 0.0

        # Possibly adjust ndwl, ndbl for 3D
        if not self.g_ip.is_3d_mem:
            if not (self.ndbl >= 2 and self.ndwl >= 2):
                raise ValueError("Memorybus: ndbl/ndwl must be >=2 unless 3D memory is used.")

        # For debugging
        if self.g_ip.print_detail_debug:
            print("memorybus.cc: membus_type = ", self.membus_type)
            print("burst length: ", self.g_ip.burst_depth)
            print("output width:", self.g_ip.io_width)

        self.chip_IO_width = self.g_ip.io_width
        self.burst_length  = self.g_ip.burst_depth
        self.data_bits     = self.chip_IO_width * self.burst_length

        # re-store row_add_bits, col_add_bits from constructor
        self.row_add_bits  = row_add_bits
        self.col_add_bits  = col_add_bits

        self.ndwl = ndwl // self.g_ip.num_tier_row_sprd
        self.ndbl = ndbl // self.g_ip.num_tier_col_sprd
        self.num_subarray_global_IO = self.ndbl if self.ndbl <= 16 else 16

        # Decide action based on membus_type
        if self.membus_type == Memorybus_type.Data_path:
            self.data_bits = self.chip_IO_width * self.burst_length
            self.Network()

        elif self.membus_type == Memorybus_type.Row_add_path:
            self.add_bits = self.row_add_bits
            self.num_dec_signals = self.dp.num_r_subarray * self.ndbl
            self.Network()

        elif self.membus_type == Memorybus_type.Col_add_path:
            self.add_bits = self.col_add_bits
            if self.data_bits != 0:
                self.num_dec_signals = (self.dp.num_c_subarray * self.ndwl) // self.data_bits
            else:
                self.num_dec_signals = 0
            self.Network()
        else:
            raise ValueError("Memorybus: invalid membus_type")

        # sanity checks
        if self.power.readOp.dynamic < 0 or self.power.readOp.leakage < 0:
            raise ValueError("Memorybus constructor => negative power values??")

    def Network(self):
        """
        Translated from the newly provided snippet in memory_bus.cc.
        """
        # local references
        g_ip = self.g_ip
        g_tp = self.g_tp
        dp   = self.dp

        R_wire_dec_out   = 0.0
        C_ld_dec_out     = 0.0
        bank_bus_length  = 0.0
        area_bank_vertical_peripheral_circuitry = 0.0
        area_bank_horizontal_peripheral_circuitry=0.0

        # initial area_sense_amp, area_subarray
        self.area_sense_amp = ((self.mat_height - self.subarray_height)
                               * self.mat_width * self.ndbl * self.ndwl)
        self.area_subarray  = (self.subarray_height * self.subarray_width
                               * self.ndbl * self.ndwl)

        # For 3D DRAM, mat only has one subarray, but we do:
        self.subarray_height = self.mat_height
        self.subarray_width  = self.mat_width

        # Partition gran => determines how we set bus overhead
        if g_ip.partition_gran == 0:  # Coarse_rank_level
            self.height_bank = (self.subarray_height*self.ndbl
                                + (self.col_add_bits + self.row_add_bits)*g_tp.wire_outside_mat.pitch/2
                                + self.data_bits*g_tp.wire_outside_mat.pitch)
            self.length_bank = (self.subarray_width*self.ndwl
                                + (self.col_add_bits + self.row_add_bits)*g_tp.wire_outside_mat.pitch/2
                                + self.data_bits*g_tp.wire_outside_mat.pitch)
            self.area_address_bus = ((self.row_add_bits + self.col_add_bits)
                                     * g_tp.wire_outside_mat.pitch
                                     * math.sqrt(self.length_bank * self.height_bank))
            self.area_data_bus = (self.data_bits * g_tp.wire_outside_mat.pitch
                                  * math.sqrt(self.length_bank * self.height_bank))

        elif g_ip.partition_gran == 1:  # Fine_rank_level => address bus replaced by TSV
            self.height_bank = self.subarray_height*self.ndbl
            self.length_bank = self.subarray_width*self.ndwl
            self.area_address_bus = 0.0
            self.area_data_bus = (self.data_bits*g_tp.wire_outside_mat.pitch
                                  * math.sqrt(self.length_bank*self.height_bank))

        elif g_ip.partition_gran == 2:  # Coarse_bank_level => address/data bus replaced by TSV
            self.height_bank = self.subarray_height*self.ndbl
            self.length_bank = self.subarray_width*self.ndwl
            self.area_address_bus = 0.0
            self.area_data_bus = 0.0

        if g_ip.print_detail_debug:
            print("memorybus.cc: N subarrays per mat =", dp.num_subarrays/dp.num_mats)
            print("memorybus.cc: g_tp.wire_local.pitch =", g_tp.wire_local.pitch/1e3, "mm")
            print("memorybus.cc: subarray_width =", self.subarray_width/1e3, "mm")
            print("memorybus.cc: subarray_height=", self.subarray_height/1e3, "mm")
            print("memorybus.cc: mat_height=", self.mat_height/1e3, "mm")
            print("memorybus.cc: mat_width=", self.mat_width/1e3, "mm")
            print("memorybus.cc: height_bank=", self.height_bank/1e3, "mm")
            print("memorybus.cc: length_bank=", self.length_bank/1e3, "mm")

        # compute # banks horizontally/vertically for some global bus usage
        num_banks_hor_dir = 1 << int(math.ceil((_log2(g_ip.nbanks*g_ip.num_tier_row_sprd))/2.0))
        num_banks_ver_dir = 1 << int(math.ceil((_log2(g_ip.nbanks*g_ip.num_tier_col_sprd*g_ip.num_tier_row_sprd
                                                     / num_banks_hor_dir))))

        if g_ip.print_detail_debug:
            print("horz bank #:", num_banks_hor_dir)
            print("vert bank #:", num_banks_ver_dir)
            print("g_ip->nbanks=", g_ip.nbanks)
            print("num_banks_hor_dir=", num_banks_hor_dir)

        # center_stripe wire length
        center_stripe_length = 0.5 * float(num_banks_hor_dir)* self.height_bank
        if g_ip.print_detail_debug:
            print("memorybus.cc: center_stripe wire length =", center_stripe_length, "um")
        self.center_stripe = Wire(g_ip, g_tp,
                                  wire_model=self.wt,
                                  wire_length=center_stripe_length) # length in microns

        self.area_bus = (2.0 * center_stripe_length
                         * (self.row_add_bits + self.col_add_bits + self.data_bits)
                         * g_tp.wire_outside_mat.pitch / g_ip.nbanks)

        # If we have a row_add_path
        if self.membus_type == Memorybus_type.Row_add_path:
            # create a global_WL wire
            self.global_WL = Wire(g_ip, g_tp,
                                  wire_model=self.wt,
                                  wire_length=self.length_bank,  # in microns
                                  nsense=1,
                                  width_scaling=1.0,
                                  spacing_scaling=1.0,
                                  wire_placement=Wire_placement.inside_mat,
                                  resistivity=CU_RESISTIVITY,
                                  deviceType=g_tp.peri_global)

            # We'll approximate num_lwl_per_gwl=4 from code
            num_lwl_per_gwl = 4
            self.num_lwl_drv = self.ndwl

            # If semi_repeated_global_line => do smaller expression
            if self.semi_repeated_global_line:
                self.C_GWL = (float(num_lwl_per_gwl)*gate_C(g_tp.min_w_nmos_+self.min_w_pmos, 0)
                              + g_tp.wire_inside_mat.C_per_um*(self.subarray_width+ g_tp.wire_local.pitch))
                self.R_GWL = g_tp.wire_inside_mat.R_per_um*(self.subarray_width+ g_tp.wire_local.pitch)
            else:
                self.C_GWL = (float(self.num_lwl_drv)*num_lwl_per_gwl
                              * gate_C(g_tp.min_w_nmos_+self.min_w_pmos, 0)
                              + g_tp.wire_inside_mat.C_per_um*self.length_bank)
                self.R_GWL = self.length_bank*g_tp.wire_inside_mat.R_per_um

            # lwl driver loads
            self.lwl_driver_c_gate_load = (dp.num_c_subarray *
                                           gate_C_pass(g_tp.dram.cell_a_w, g_tp.dram.b_w,
                                                       is_dram=True, is_cell=True))
            self.lwl_driver_c_wire_load = (dp.num_c_subarray
                                           * g_tp.dram.b_w
                                           * g_tp.wire_local.C_per_um)
            self.lwl_driver_r_wire_load = (dp.num_c_subarray
                                           * g_tp.dram.b_w
                                           * g_tp.wire_local.R_per_um)

            self.C_LWL = self.lwl_driver_c_gate_load + self.lwl_driver_c_wire_load

            # create lwl_drv
            self.lwl_drv = Driver(g_ip=g_ip,
                                  g_tp=g_tp,
                                  c_gate_load=self.lwl_driver_c_gate_load,
                                  c_wire_load=self.lwl_driver_c_wire_load,
                                  r_wire_load=self.lwl_driver_r_wire_load,
                                  is_dram_=self.is_dram)
            self.lwl_drv.compute_area()

            # decide whether to load or not
            if not g_ip.fine_gran_bank_lvl:
                C_ld_dec_out = self.C_GWL
                R_wire_dec_out= self.R_GWL
            else:
                C_ld_dec_out = gate_C(g_tp.min_w_nmos_+self.min_w_pmos, 0)
                R_wire_dec_out= 0

            # bank_bus
            bank_bus_length = float(num_banks_ver_dir)*0.5*max(self.length_bank, self.height_bank)
            self.bank_bus = Wire(g_ip, g_tp, wire_model=self.wt, wire_length=bank_bus_length)

        elif self.membus_type == Memorybus_type.Col_add_path:
            # create column_sel wire
            self.column_sel = Wire(g_ip, g_tp,
                                   wire_model=self.wt,
                                   wire_length=math.sqrt(self.length_bank*self.height_bank),
                                   nsense=1,
                                   width_scaling=1.0,
                                   spacing_scaling=1.0,
                                   wire_placement=Wire_placement.outside_mat,
                                   resistivity=CU_RESISTIVITY,
                                   deviceType=g_tp.peri_global)

            if self.semi_repeated_global_line:
                self.C_colsel = (g_tp.wire_inside_mat.C_per_um
                                 * (self.subarray_height + g_tp.wire_local.pitch))
                self.R_colsel = (g_tp.wire_inside_mat.R_per_um
                                 * (self.subarray_height + g_tp.wire_local.pitch))
            else:
                # from c++ code:
                self.C_colsel = (self.column_sel.repeater_size*
                                 gate_C(g_tp.min_w_nmos_+self.min_w_pmos, 0)
                                 + (self.column_sel.repeater_spacing
                                    if self.column_sel.repeater_spacing< self.height_bank
                                    else self.height_bank)
                                 * g_tp.wire_outside_mat.C_per_um)
                self.R_colsel = ((self.column_sel.repeater_spacing
                                  if self.column_sel.repeater_spacing< self.height_bank
                                  else self.height_bank)
                                 * g_tp.wire_outside_mat.R_per_um)

            if not g_ip.fine_gran_bank_lvl:
                C_ld_dec_out = self.C_colsel
                R_wire_dec_out= self.R_colsel
            else:
                C_ld_dec_out = gate_C(g_tp.min_w_nmos_+self.min_w_pmos,0)
                R_wire_dec_out= 0

            bank_bus_length = float(num_banks_ver_dir)*0.5* max(self.length_bank, self.height_bank)
            self.bank_bus   = Wire(g_ip, g_tp, wire_model=self.wt, wire_length=bank_bus_length)

        elif self.membus_type == Memorybus_type.Data_path:
            # local_data, global_data wires
            self.local_data = Wire(g_ip, g_tp,
                                   wire_model=self.wt,
                                   wire_length=self.subarray_width,
                                   nsense=1,
                                   width_scaling=1.0,
                                   spacing_scaling=1.0,
                                   wire_placement=Wire_placement.inside_mat,
                                   resistivity=CU_RESISTIVITY,
                                   deviceType=g_tp.peri_global)

            self.global_data= Wire(g_ip, g_tp,
                                   wire_model=self.wt,
                                   wire_length=math.sqrt(self.length_bank*self.height_bank),
                                   nsense=1,
                                   width_scaling=1.0,
                                   spacing_scaling=1.0,
                                   wire_placement=Wire_placement.outside_mat,
                                   resistivity=CU_RESISTIVITY,
                                   deviceType=g_tp.peri_global)
            if self.semi_repeated_global_line:
                self.C_global_data= g_tp.wire_inside_mat.C_per_um *(self.subarray_height + g_tp.wire_local.pitch)
                self.R_global_data= g_tp.wire_inside_mat.R_per_um *(self.subarray_height + g_tp.wire_local.pitch)
            else:
                self.C_global_data= g_tp.wire_inside_mat.C_per_um* self.height_bank/2.0
                self.R_global_data= g_tp.wire_inside_mat.R_per_um* self.height_bank/2.0

            self.global_data_drv = Driver(g_ip=g_ip,
                                          g_tp=g_tp,
                                          c_gate_load=0,
                                          c_wire_load=self.C_global_data,
                                          r_wire_load=self.R_global_data,
                                          is_dram_=self.is_dram)
            self.global_data_drv.compute_delay(0)
            self.global_data_drv.compute_area()

            # local data line loads
            local_data_c_gate_load = (dp.num_c_subarray
                                      * drain_C_(g_tp,
                                                 g_tp.w_nmos_sa_mux,
                                                 0.0,  # pwidth unused
                                                 NCH, 1, 0, self.cell.w,
                                                 self.is_dram))
            local_data_c_wire_load = (dp.num_c_subarray
                                      * g_tp.dram.b_w
                                      * g_tp.wire_inside_mat.C_per_um)
            local_data_r_wire_load = (dp.num_c_subarray
                                      * g_tp.dram.b_w
                                      * g_tp.wire_inside_mat.R_per_um)
            local_data_r_gate_load = 0.0

            tf = (local_data_c_gate_load + local_data_c_wire_load)*(local_data_r_wire_load + local_data_r_gate_load)
            this_delay = horowitz(0.0, tf, 0.5, 0.5, RISE)
            # We won't store local_data->delay etc., as in the code, it's commented out

            data_drv_c_gate_load  = local_data_c_gate_load
            data_drv_c_wire_load  = local_data_c_wire_load
            data_drv_r_wire_load  = local_data_r_gate_load + local_data_r_wire_load

            self.local_data_drv   = Driver(g_ip=g_ip,
                                           g_tp=g_tp,
                                           c_gate_load=data_drv_c_gate_load,
                                           c_wire_load=data_drv_c_wire_load,
                                           r_wire_load=data_drv_r_wire_load,
                                           is_dram_=self.is_dram)
            self.local_data_drv.compute_delay(0)
            self.local_data_drv.compute_area()

            if g_ip.print_detail_debug:
                print("C:", local_data_c_gate_load+ local_data_c_wire_load, "F")
                print("R:", local_data_r_gate_load+ local_data_r_wire_load, "Ohm")
                print("this_delay:", this_delay*1e9, "ns")
                print("local_data_drv delay:", self.local_data_drv.delay*1e9, "ns")

            # final bank_bus
            bank_bus_length = float(num_banks_ver_dir)*0.5* max(self.length_bank, self.height_bank)
            self.bank_bus = Wire(g_ip, g_tp,
                                 wire_model=self.wt,
                                 wire_length=bank_bus_length)

            if g_ip.print_detail_debug:
                print("memorybus.cc: bank_bus_length=", bank_bus_length)

            # out_seg wire
            self.out_seg = Wire(g_ip, g_tp,
                                wire_model=self.wt,
                                wire_length= 0.25* float(num_banks_hor_dir)*(
                                    self.length_bank + (self.row_add_bits+self.col_add_bits+self.data_bits)* g_tp.wire_outside_mat.pitch))

            # area overhead
            self.area_IOSA = (875 + 500)* g_ip.F_sz_um*g_ip.F_sz_um * self.data_bits
            self.area_data_drv = self.local_data_drv.area.get_area()* self.data_bits
            if self.ndbl>16:
                factor = float(self.ndbl)/16.0
                self.area_IOSA *= factor
                self.area_data_drv *= factor
            self.area_local_dataline = (self.data_bits
                                        * self.subarray_width
                                        * g_tp.wire_local.pitch
                                        * self.ndbl)

        # if row_add_path or col_add_path => build dec + predec
        if (self.membus_type == Memorybus_type.Row_add_path
            or self.membus_type == Memorybus_type.Col_add_path):
            if g_ip.print_detail_debug:
                print("memorybus.cc: num_dec_signals=", self.num_dec_signals)
                print("memorybus.cc: C_ld_dec_out=", C_ld_dec_out)
                print("memorybus.cc: R_wire_dec_out=", R_wire_dec_out)
                print("memorybus.cc: is_dram=", self.is_dram)
                print("memorybus.cc: cell.h=", self.cell.h)

            # The decoder
            signals_for_decoder = max(self.num_dec_signals, 16)
            self.add_dec = Decoder(
                signals_for_decoder,
                flag_way_select=False,
                C_ld_dec_out=C_ld_dec_out,
                R_wire_dec_out=R_wire_dec_out,
                fully_assoc=False,
                is_dram_=self.is_dram,
                is_wl_tr_=(True if self.membus_type==Memorybus_type.Row_add_path else False),
                cell_=self.cell
            )

            # Predec blocks
            C_wire_predec_blk_out = 0.0
            R_wire_predec_blk_out = 0.0
            num_dec_per_predec    = 1

            add_predec_blk1 = PredecBlk(num_dec_signals=self.num_dec_signals,
                                        dec=self.add_dec,
                                        C_wire_predec_blk_out=C_wire_predec_blk_out,
                                        R_wire_predec_blk_out=R_wire_predec_blk_out,
                                        num_dec_per_predec=num_dec_per_predec,
                                        is_dram_=self.is_dram,
                                        is_blk1=True)

            add_predec_blk2 = PredecBlk(num_dec_signals=self.num_dec_signals,
                                        dec=self.add_dec,
                                        C_wire_predec_blk_out=C_wire_predec_blk_out,
                                        R_wire_predec_blk_out=R_wire_predec_blk_out,
                                        num_dec_per_predec=num_dec_per_predec,
                                        is_dram_=self.is_dram,
                                        is_blk1=False)

            add_predec_blk_drv1= PredecBlkDrv(0, add_predec_blk1, self.is_dram)
            add_predec_blk_drv2= PredecBlkDrv(0, add_predec_blk2, self.is_dram)

            self.add_predec = Predec(add_predec_blk_drv1, add_predec_blk_drv2)

            if self.membus_type == Memorybus_type.Row_add_path:
                self.area_row_predec_dec = (add_predec_blk_drv1.area.get_area()
                                            + add_predec_blk_drv2.area.get_area()
                                            + add_predec_blk1.area.get_area()
                                            + add_predec_blk2.area.get_area()
                                            + self.num_dec_signals*self.add_dec.area.get_area())

                # area for lwl driver
                # num_lwl_drv/2.0 * dp.num_r_subarray * ndbl => from C++ code
                # lwl_drv->area => self.lwl_drv.area
                self.area_lwl_drv = (float(self.num_lwl_drv)/2.0
                                     * dp.num_r_subarray
                                     * float(self.ndbl)
                                     * self.lwl_drv.area.get_area())

                if g_ip.print_detail_debug:
                    print("area_bank_vertical_peripheral_circuitry?? Not yet set, ignoring in debug.")
                    print("lwl drv area =", self.lwl_drv.area.get_area())
                    print("total lwl drv area =",
                          (self.num_lwl_drv*dp.num_r_subarray*self.ndbl*self.lwl_drv.area.get_area()))
            elif self.membus_type == Memorybus_type.Col_add_path:
                self.area_col_predec_dec = (add_predec_blk_drv1.area.get_area()
                                            + add_predec_blk_drv2.area.get_area()
                                            + add_predec_blk1.area.get_area()
                                            + add_predec_blk2.area.get_area()
                                            + self.num_dec_signals*self.add_dec.area.get_area())
                if self.ndbl>16:
                    factor = float(self.ndbl)/16.0
                    self.area_col_predec_dec *= factor

            # Summation for final area (vertical/horizontal)
            area_bank_vertical_peripheral_circuitry = (self.area_row_predec_dec + self.area_lwl_drv
                                                       + self.area_address_bus + self.area_data_bus)
            area_bank_horizontal_peripheral_circuitry= (self.area_col_predec_dec + self.area_data_drv
                                                        + (self.area_bus + self.area_IOSA)/ g_ip.nbanks)

            # final 'area' dimension
            self.area.h = ((self.height_bank
                            + area_bank_horizontal_peripheral_circuitry/self.length_bank)
                           * num_banks_ver_dir)
            self.area.w = ((self.length_bank
                            + area_bank_vertical_peripheral_circuitry/self.height_bank)
                           * num_banks_hor_dir)

            if g_ip.partition_gran == 0:
                self.area.h += (g_tp.wire_outside_mat.pitch
                                * float(self.add_bits + self.add_bits + self.data_bits))
                self.area.w += (g_tp.wire_outside_mat.pitch
                                * float(self.add_bits + self.add_bits + self.data_bits))

            if g_ip.print_detail_debug:
                print("memorybus.cc: circuit height =",
                      area_bank_horizontal_peripheral_circuitry/self.length_bank/1e3,"mm")
                print("memorybus.cc: circuit length =",
                      area_bank_vertical_peripheral_circuitry/self.height_bank/1e3,"mm")
                print("memorybus.cc: area.h=", self.area.h/1e3,"mm")
                print("memorybus.cc: area.w=", self.area.w/1e3,"mm")
                print("memorybus.cc: area=", self.area.get_area()/1e6,"mm2")

        # Finally, call the bus-level compute_delays and compute_power_energy
        self.compute_delays(0.0)
        self.compute_power_energy()

    def compute_delays(self, inrisetime: float) -> float:
        """
        Final part from memory_bus.cc snippet #3.
        """
        # We'll replicate the logic:
        predec_outrisetime = 0.0
        add_dec_outrisetime= 0.0
        lwl_drv_outrisetime= 0.0
        self.delay = 0.0

        if self.membus_type == Memorybus_type.Data_path:
            self.delay_bus = ( (self.center_stripe.delay if self.center_stripe else 0.0)
                             + (self.bank_bus.delay       if self.bank_bus       else 0.0) )
            self.delay += self.delay_bus

            # No explicit local_data_drv->compute_delay(inrisetime) used, but in C++ code we store local_data_drv->delay
            self.delay_global_data = 0.0
            if self.semi_repeated_global_line > 0:
                self.delay_global_data = (self.global_data_drv.delay
                                          * self.num_subarray_global_IO)
            else:
                # global_data_drv->delay + global_data->delay
                gd_delay = self.global_data_drv.delay if self.global_data_drv else 0.0
                gw_delay = self.global_data.delay     if self.global_data else 0.0
                self.delay_global_data = gd_delay + gw_delay

            if (self.g_ip.partition_gran==0 or self.g_ip.partition_gran==1):
                self.delay += self.delay_global_data

            self.delay_local_data = (self.local_data_drv.delay
                                     if self.local_data_drv else 0.0)
            self.delay += self.delay_local_data

            # Add the "delay_data_buffer" = 2 *1e-6 / freq
            self.delay_data_buffer = 2e-6 / float(self.g_ip.sys_freq_MHz)
            self.delay += self.delay_data_buffer

            if self.g_ip.print_detail_debug:
                print("memorybus.cc: data path delay =", self.delay)
            self.out_rise_time = 0.0

        else:
            # row_add_path or col_add_path
            self.delay_bus = ((self.center_stripe.delay if self.center_stripe else 0.0)
                              + (self.bank_bus.delay if self.bank_bus else 0.0))
            self.delay += self.delay_bus

            # predec/delay
            predec_outrisetime = self.add_predec.compute_delays(inrisetime) if self.add_predec else 0.0
            add_dec_outrisetime= self.add_dec.compute_delays(predec_outrisetime) if self.add_dec else 0.0
            self.delay_add_predecoder = (self.add_predec.delay if self.add_predec else 0.0)
            self.delay += self.delay_add_predecoder

            if self.membus_type == Memorybus_type.Row_add_path:
                if self.semi_repeated_global_line:
                    # add_dec->delay * ndwl
                    base_delay = self.add_dec.delay if self.add_dec else 0.0
                    self.delay_add_decoder = base_delay * float(self.ndwl)
                    if self.g_ip.page_sz_bits > 8192:
                        self.delay_add_decoder /= (float(self.g_ip.page_sz_bits)/8192.0)
                else:
                    self.delay_add_decoder = (self.add_dec.delay if self.add_dec else 0.0)

                self.delay += self.delay_add_decoder

                # lwl_drv->compute_delay
                if self.lwl_drv:
                    lwl_drv_outrisetime = self.lwl_drv.compute_delay(add_dec_outrisetime)
                    self.delay_lwl_drv = self.lwl_drv.delay
                    if not self.g_ip.fine_gran_bank_lvl:
                        self.delay += self.delay_lwl_drv

                if self.g_ip.print_detail_debug:
                    print("memorybus.cc: row add path delay =", self.delay)
                self.out_rise_time = lwl_drv_outrisetime

            elif self.membus_type == Memorybus_type.Col_add_path:
                if self.semi_repeated_global_line:
                    self.delay_add_decoder = (self.add_dec.delay if self.add_dec else 0.0)* float(self.num_subarray_global_IO)
                else:
                    # plus column_sel->delay
                    if self.column_sel:
                        self.delay += self.column_sel.delay
                    self.delay_add_decoder = (self.add_dec.delay if self.add_dec else 0.0)
                self.delay += self.delay_add_decoder

                self.out_rise_time = 0.0
                if self.g_ip.print_detail_debug:
                    print("memorybus.cc: column add path delay =", self.delay)
            else:
                raise ValueError("Memorybus: invalid membus_type in else block")

        # final out_rise_time in c++ code => delay/(1-0.5)
        # but that might be a single-latch style. We'll replicate exactly:
        self.out_rise_time = self.delay / 0.5
        return self.out_rise_time

    def compute_power_energy(self):
        """
        Final from memory_bus.cc snippet #3.
        """
        # define arrays
        coeff1 = [float(self.add_bits)]*4
        coeff2 = [float(self.data_bits)]*4
        coeff3 = [float(self.num_lwl_drv)]*4
        coeff4 = [float(self.burst_length*self.chip_IO_width)]*4
        coeff5 = [float(self.ndwl)]*4
        coeff6 = [float(self.num_subarray_global_IO)]*4

        # pick usage based on membus_type
        if self.membus_type == Memorybus_type.Data_path:
            self.power_bus = (self.center_stripe.power + self.bank_bus.power)* coeff2
            self.power_local_data = self.local_data_drv.power* coeff2
            if self.semi_repeated_global_line>0:
                self.power_global_data = self.global_data_drv.power* coeff2
            else:
                self.power_global_data = self.global_data_drv.power + self.global_data.power

            # Additional scaling => from code
            # self.power_global_data.readOp.dynamic += 1.8/1e3* deviceType->Vdd *10.0/1e9/64 * data_bits
            self.power_global_data.readOp.dynamic += (1.8/1e3 * self.deviceType.Vdd
                                                      * 10.0/1e9/64.0 * self.data_bits)

            self.power = self.power_bus + self.power_local_data
            if not self.g_ip.fine_gran_bank_lvl:
                self.power = self.power + self.power_global_data

            # out_seg
            self.power_burst = self.out_seg.power* coeff4
            # self.power = self.power + self.power_burst => code is commented out

            if self.g_ip.print_detail_debug:
                print("memorybus.cc: data path center stripe energy =", self.center_stripe.power.readOp.dynamic*1e9,"nJ")
                print("memorybus.cc: data path bank bus energy =", self.bank_bus.power.readOp.dynamic*1e9,"nJ")
                print("memorybus.cc: data path data driver energy =", self.local_data_drv.power.readOp.dynamic*1e9,"nJ")

        elif self.membus_type == Memorybus_type.Row_add_path:
            self.power_bus = (self.center_stripe.power + self.bank_bus.power)* coeff1
            self.power_add_predecoder = self.add_predec.power
            if self.semi_repeated_global_line:
                self.power_add_decoders = self.add_dec.power* coeff5
                if self.g_ip.page_sz_bits>8192:
                    self.power_add_decoders.readOp.dynamic /= (float(self.g_ip.page_sz_bits)/8192.0)
            else:
                self.power_add_decoders = self.add_dec.power

            self.power_lwl_drv = self.lwl_drv.power* coeff3
            # final bus power
            self.power = self.power_bus + self.power_add_predecoder + self.power_add_decoders + self.power_lwl_drv

        elif self.membus_type == Memorybus_type.Col_add_path:
            self.power_bus = (self.center_stripe.power + self.bank_bus.power)* coeff1
            self.power_add_predecoder= self.add_predec.power
            if self.semi_repeated_global_line:
                self.power_add_decoders = self.add_dec.power* coeff6
                self.power_add_decoders.readOp.dynamic *= (float(self.g_ip.page_sz_bits)/ float(self.data_bits))
                self.power_col_sel.readOp.dynamic = 0.0
            else:
                self.power_add_decoders = self.add_dec.power
                self.power_col_sel.readOp.dynamic = (self.column_sel.power.readOp.dynamic
                                                     * float(self.g_ip.page_sz_bits)/ float(self.data_bits))

            self.power = (self.power_bus
                          + self.power_add_predecoder
                          + self.power_add_decoders)
            if not self.g_ip.fine_gran_bank_lvl:
                self.power = self.power + self.power_col_sel

        else:
            raise ValueError("Memorybus: unknown bus type in compute_power_energy()")

    def set_in_rise_time(self, rt: float):
        self.in_rise_time = rt
