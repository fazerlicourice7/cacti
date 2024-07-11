from .decoder import *
from .parameter import *
from .const import *
from .component import *
from .wire import *
from .subarray import *
from .powergating import *

import sympy as sp


# Note: This code relies on several other classes and functions (e.g., Subarray, Decoder, Driver, PredecBlk, PredecBlkDrv, Predec, Wire, Sleep_tx, gate_C, drain_C_, tr_R_on, horowitz, g_tp, g_ip) 
# that are not included here. Ensure these dependencies are defined elsewhere in your codebase.
class Mat(Component):
    def __init__(self, dyn_p):
        super().__init__()
        self.dp = dyn_p

        # Initialize attributes
        self.power_subarray_out_drv = PowerDef()
        self.power_row_decoders = PowerDef()
        self.power_bit_mux_decoders = PowerDef()
        self.power_sa_mux_lev_1_decoders = PowerDef()
        self.power_sa_mux_lev_2_decoders = PowerDef()
        self.power_fa_cam = PowerDef()  # TODO: leakage power is not computed yet
        self.power_bl_precharge_eq_drv = PowerDef()
        self.power_cam_all_active = PowerDef()
        self.power_searchline_precharge = PowerDef()
        self.power_matchline_precharge = PowerDef()
        self.power_ml_to_ram_wl_drv = PowerDef()

        self.delay_fa_tag = 0
        self.delay_cam = 0
        self.delay_before_decoder = 0
        self.delay_bitline = 0
        self.delay_wl_reset = 0
        self.delay_bl_restore = 0
        self.delay_searchline = 0
        self.delay_matchchline = 0
        self.delay_cam_sl_restore = 0
        self.delay_cam_ml_reset = 0
        self.delay_fa_ram_wl = 0
        self.delay_hit_miss_reset = 0
        self.delay_hit_miss = 0
        self.subarray = Subarray(self.dp, self.dp.fully_assoc)
        self.power_bitline = PowerDef()
        self.power_searchline = PowerDef()
        self.power_matchline = PowerDef()
        self.power_bitline_gated = PowerDef()
        self.per_bitline_read_energy = 0
        self.deg_bl_muxing = self.dp.deg_bl_muxing
        self.num_act_mats_hor_dir = dyn_p.num_act_mats_hor_dir
        self.delay_writeback = 0
        self.cell = self.subarray.cell
        self.cam_cell = self.subarray.cam_cell
        self.is_dram = dyn_p.is_dram
        self.pure_cam = dyn_p.pure_cam
        self.num_mats = self.dp.num_mats
        self.power_sa = PowerDef()
        self.delay_sa = 0
        self.leak_power_sense_amps_closed_page_state = 0
        self.leak_power_sense_amps_open_page_state = 0
        self.delay_subarray_out_drv = 0
        self.delay_comparator = 0
        self.power_comparator = PowerDef()
        self.num_do_b_mat = dyn_p.num_do_b_mat
        self.num_so_b_mat = dyn_p.num_so_b_mat
        #print(self.dp.num_subarrays, self.dp.num_mats)
        self.num_subarrays_per_mat = self.dp.num_subarrays / self.dp.num_mats
        self.num_subarrays_per_row = self.dp.Ndwl / self.dp.num_mats_h_dir
        self.array_leakage = 0
        self.wl_leakage = 0
        self.cl_leakage = 0
        self.sram_sleep_tx = None
        self.wl_sleep_tx = None
        self.cl_sleep_tx = None
        self.array_wakeup_e = PowerDef()
        self.array_wakeup_t = 0
        self.array_sleep_tx_area = 0
        self.blfloating_wakeup_e = PowerDef()
        self.blfloating_wakeup_t = 0
        self.blfloating_sleep_tx_area = 0
        self.wl_wakeup_e = PowerDef()
        self.wl_wakeup_t = 0
        self.wl_sleep_tx_area = 0
        self.cl_wakeup_e = PowerDef()
        self.cl_wakeup_t = 0
        self.cl_sleep_tx_area = 0

        print("CHECKPOINT 0")

        assert self.num_subarrays_per_mat <= 4
        assert self.num_subarrays_per_row <= 2
        self.is_fa = self.dp.fully_assoc
        self.camFlag = self.is_fa or self.pure_cam

        if self.is_fa or self.pure_cam:
            self.num_subarrays_per_row = self.num_subarrays_per_mat // 2 if self.num_subarrays_per_mat > 2 else self.num_subarrays_per_mat

        if self.dp.use_inp_params == 1:
            self.RWP = self.dp.num_rw_ports
            self.ERP = self.dp.num_rd_ports
            self.EWP = self.dp.num_wr_ports
            self.SCHP = self.dp.num_search_ports
        else:
            self.RWP = g_ip.num_rw_ports
            self.ERP = g_ip.num_rd_ports
            self.EWP = g_ip.num_wr_ports
            self.SCHP = g_ip.num_search_ports

        if not self.is_fa and not self.pure_cam:
            number_sa_subarray = self.subarray.num_cols / self.deg_bl_muxing
        elif self.is_fa and not self.pure_cam:
            number_sa_subarray = (self.subarray.num_cols_fa_cam + self.subarray.num_cols_fa_ram) / self.deg_bl_muxing
        else:
            number_sa_subarray = self.subarray.num_cols_fa_cam / self.deg_bl_muxing

        num_dec_signals = self.subarray.num_rows
        C_ld_bit_mux_dec_out = 0
        C_ld_sa_mux_lev_1_dec_out = 0
        C_ld_sa_mux_lev_2_dec_out = 0

        if not self.is_fa and not self.pure_cam:
            R_wire_wl_drv_out = self.subarray.num_cols * self.cell.w * g_tp.wire_local.R_per_um
        elif self.is_fa and not self.pure_cam:
            R_wire_wl_drv_out = (self.subarray.num_cols_fa_cam * self.cam_cell.w + self.subarray.num_cols_fa_ram * self.cell.w) * g_tp.wire_local.R_per_um
        else:
            R_wire_wl_drv_out = self.subarray.num_cols_fa_cam * self.cam_cell.w * g_tp.wire_local.R_per_um

        R_wire_bit_mux_dec_out = self.num_subarrays_per_row * self.subarray.num_cols * g_tp.wire_inside_mat.R_per_um * self.cell.w
        R_wire_sa_mux_dec_out = self.num_subarrays_per_row * self.subarray.num_cols * g_tp.wire_inside_mat.R_per_um * self.cell.w

        if self.deg_bl_muxing > 1:
            C_ld_bit_mux_dec_out = (2 * self.num_subarrays_per_mat * self.subarray.num_cols / self.deg_bl_muxing) * gate_C(g_tp.w_nmos_b_mux, 0, self.is_dram) + \
                                   self.num_subarrays_per_row * self.subarray.num_cols * g_tp.wire_inside_mat.C_per_um * self.cell.get_w()

        if self.dp.Ndsam_lev_1 > 1:
            C_ld_sa_mux_lev_1_dec_out = (self.num_subarrays_per_mat * number_sa_subarray / self.dp.Ndsam_lev_1) * gate_C(g_tp.w_nmos_sa_mux, 0, self.is_dram) + \
                                        self.num_subarrays_per_row * self.subarray.num_cols * g_tp.wire_inside_mat.C_per_um * self.cell.get_w()

        if self.dp.Ndsam_lev_2 > 1:
            C_ld_sa_mux_lev_2_dec_out = (self.num_subarrays_per_mat * number_sa_subarray / (self.dp.Ndsam_lev_1 * self.dp.Ndsam_lev_2)) * gate_C(g_tp.w_nmos_sa_mux, 0, self.is_dram) + \
                                        self.num_subarrays_per_row * self.subarray.num_cols * g_tp.wire_inside_mat.C_per_um * self.cell.get_w()

        if self.num_subarrays_per_row >= 2:
            R_wire_bit_mux_dec_out /= 2.0
            R_wire_sa_mux_dec_out /= 2.0

        print("CHECKPOINT 1")

        self.row_dec = Decoder(num_dec_signals, False, self.subarray.C_wl, R_wire_wl_drv_out, False, self.is_dram, True, self.cam_cell if self.camFlag else self.cell)
        self.row_dec.nodes_DSTN = self.subarray.num_rows

        print("CHECKPOINT 2")

        self.bit_mux_dec = Decoder(self.deg_bl_muxing, False, C_ld_bit_mux_dec_out, R_wire_bit_mux_dec_out, False, self.is_dram, False, self.cam_cell if self.camFlag else self.cell)
        self.sa_mux_lev_1_dec = Decoder(self.dp.deg_senseamp_muxing_non_associativity, self.dp.number_way_select_signals_mat, C_ld_sa_mux_lev_1_dec_out, R_wire_sa_mux_dec_out, False, self.is_dram, False, self.cam_cell if self.camFlag else self.cell)
        self.sa_mux_lev_2_dec = Decoder(self.dp.Ndsam_lev_2, False, C_ld_sa_mux_lev_2_dec_out, R_wire_sa_mux_dec_out, False, self.is_dram, False, self.cam_cell if self.camFlag else self.cell)

        if not self.is_fa and not self.pure_cam:
            C_wire_predec_blk_out = self.num_subarrays_per_row * self.subarray.num_rows * g_tp.wire_inside_mat.C_per_um * self.cell.h
            R_wire_predec_blk_out = self.num_subarrays_per_row * self.subarray.num_rows * g_tp.wire_inside_mat.R_per_um * self.cell.h
        else:
            C_wire_predec_blk_out = self.subarray.num_rows * g_tp.wire_inside_mat.C_per_um * self.cam_cell.h
            R_wire_predec_blk_out = self.subarray.num_rows * g_tp.wire_inside_mat.R_per_um * self.cam_cell.h

        if self.is_fa or self.pure_cam:
            num_dec_signals += int(math.log2(self.num_subarrays_per_mat))

        print("CHECKPOINT 3")
        print(f'num_dec_signals {num_dec_signals}')
        print(f'deg_bl_muxing {self.deg_bl_muxing}')
        self.r_predec_blk1 = PredecBlk(num_dec_signals, self.row_dec, C_wire_predec_blk_out, R_wire_predec_blk_out, self.num_subarrays_per_mat, self.is_dram, True)
        print("CHECKPOINT 3.1")
        self.r_predec_blk2 = PredecBlk(num_dec_signals, self.row_dec, C_wire_predec_blk_out, R_wire_predec_blk_out, self.num_subarrays_per_mat, self.is_dram, False)
        self.b_mux_predec_blk1 = PredecBlk(self.deg_bl_muxing, self.bit_mux_dec, 0, 0, 1, self.is_dram, True)
        self.b_mux_predec_blk2 = PredecBlk(self.deg_bl_muxing, self.bit_mux_dec, 0, 0, 1, self.is_dram, False)
        print("CHECKPOINT 3.2")
        self.sa_mux_lev_1_predec_blk1 = PredecBlk(dyn_p.deg_senseamp_muxing_non_associativity, self.sa_mux_lev_1_dec, 0, 0, 1, self.is_dram, True)
        self.sa_mux_lev_1_predec_blk2 = PredecBlk(dyn_p.deg_senseamp_muxing_non_associativity, self.sa_mux_lev_1_dec, 0, 0, 1, self.is_dram, False)
        print("CHECKPOINT 3.3")
        self.sa_mux_lev_2_predec_blk1 = PredecBlk(self.dp.Ndsam_lev_2, self.sa_mux_lev_2_dec, 0, 0, 1, self.is_dram, True)
        self.sa_mux_lev_2_predec_blk2 = PredecBlk(self.dp.Ndsam_lev_2, self.sa_mux_lev_2_dec, 0, 0, 1, self.is_dram, False)
        self.dummy_way_sel_predec_blk1 = PredecBlk(1, self.sa_mux_lev_1_dec, 0, 0, 0, self.is_dram, True)
        self.dummy_way_sel_predec_blk2 = PredecBlk(1, self.sa_mux_lev_1_dec, 0, 0, 0, self.is_dram, False)

        print("CHECKPOINT 4")
        self.r_predec_blk_drv1 = PredecBlkDrv(0, self.r_predec_blk1, self.is_dram)
        self.r_predec_blk_drv2 = PredecBlkDrv(0, self.r_predec_blk2, self.is_dram)
        self.b_mux_predec_blk_drv1 = PredecBlkDrv(0, self.b_mux_predec_blk1, self.is_dram)
        self.b_mux_predec_blk_drv2 = PredecBlkDrv(0, self.b_mux_predec_blk2, self.is_dram)
        self.sa_mux_lev_1_predec_blk_drv1 = PredecBlkDrv(0, self.sa_mux_lev_1_predec_blk1, self.is_dram)
        self.sa_mux_lev_1_predec_blk_drv2 = PredecBlkDrv(0, self.sa_mux_lev_1_predec_blk2, self.is_dram)
        self.sa_mux_lev_2_predec_blk_drv1 = PredecBlkDrv(0, self.sa_mux_lev_2_predec_blk1, self.is_dram)
        self.sa_mux_lev_2_predec_blk_drv2 = PredecBlkDrv(0, self.sa_mux_lev_2_predec_blk2, self.is_dram)
        self.way_sel_drv1 = PredecBlkDrv(dyn_p.number_way_select_signals_mat, self.dummy_way_sel_predec_blk1, self.is_dram)
        self.dummy_way_sel_predec_blk_drv2 = PredecBlkDrv(1, self.dummy_way_sel_predec_blk2, self.is_dram)

        print("CHECKPOINT 5")
        self.r_predec = Predec(self.r_predec_blk_drv1, self.r_predec_blk_drv2)
        self.b_mux_predec = Predec(self.b_mux_predec_blk_drv1, self.b_mux_predec_blk_drv2)
        self.sa_mux_lev_1_predec = Predec(self.sa_mux_lev_1_predec_blk_drv1, self.sa_mux_lev_1_predec_blk_drv2)
        self.sa_mux_lev_2_predec = Predec(self.sa_mux_lev_2_predec_blk_drv1, self.sa_mux_lev_2_predec_blk_drv2)

        print("CHECKPOINT 6")
        self.subarray_out_wire = Wire(self.dp.wtype, self.subarray.area.w if g_ip.cl_vertical else self.subarray.area.h)

        # def __init__(self, wire_model, length, nsense=1, width_scaling=1, spacing_scaling=1, wire_placement=outside_mat, resistivity=CU_RESISTIVITY, dt=g_tp.peri_global):

        print("CHECKPOINT 7")
        if self.is_fa or self.pure_cam:
            driver_c_gate_load = self.subarray.num_cols_fa_cam * gate_C(2 * g_tp.w_pmos_bl_precharge + g_tp.w_pmos_bl_eq, 0, self.is_dram, False, False)
            driver_c_wire_load = self.subarray.num_cols_fa_cam * self.cam_cell.w * g_tp.wire_outside_mat.C_per_um
            driver_r_wire_load = self.subarray.num_cols_fa_cam * self.cam_cell.w * g_tp.wire_outside_mat.R_per_um
            self.cam_bl_precharge_eq_drv = Driver(driver_c_gate_load, driver_c_wire_load, driver_r_wire_load, self.is_dram)

            if not self.pure_cam:
                driver_c_gate_load = self.subarray.num_cols_fa_ram * gate_C(2 * g_tp.w_pmos_bl_precharge + g_tp.w_pmos_bl_eq, 0, self.is_dram, False, False)
                driver_c_wire_load = self.subarray.num_cols_fa_ram * self.cell.w * g_tp.wire_outside_mat.C_per_um
                driver_r_wire_load = self.subarray.num_cols_fa_ram * self.cell.w * g_tp.wire_outside_mat.R_per_um
                self.bl_precharge_eq_drv = Driver(driver_c_gate_load, driver_c_wire_load, driver_r_wire_load, self.is_dram)
        else:
            driver_c_gate_load = self.subarray.num_cols * gate_C(2 * g_tp.w_pmos_bl_precharge + g_tp.w_pmos_bl_eq, 0, self.is_dram, False, False)
            driver_c_wire_load = self.subarray.num_cols * self.cell.w * g_tp.wire_outside_mat.C_per_um
            driver_r_wire_load = self.subarray.num_cols * self.cell.w * g_tp.wire_outside_mat.R_per_um
            self.bl_precharge_eq_drv = Driver(driver_c_gate_load, driver_c_wire_load, driver_r_wire_load, self.is_dram)

        area_row_decoder = self.row_dec.area.get_area() * self.subarray.num_rows * (self.RWP + self.ERP + self.EWP)
        w_row_decoder = area_row_decoder / self.subarray.area.get_h()

        h_bit_mux_sense_amp_precharge_sa_mux_write_driver_write_mux = self.compute_bit_mux_sa_precharge_sa_mux_wr_drv_wr_mux_h()
        h_subarray_out_drv = self.subarray_out_wire.area.get_area() * (self.subarray.num_cols / (self.deg_bl_muxing * self.dp.Ndsam_lev_1 * self.dp.Ndsam_lev_2)) / self.subarray.area.get_w()
        h_subarray_out_drv *= (self.RWP + self.ERP + self.SCHP)

        h_comparators = 0.0
        w_row_predecode_output_wires = 0.0
        h_bit_mux_dec_out_wires = 0.0
        h_senseamp_mux_dec_out_wires = 0.0

        if not self.is_fa and self.dp.is_tag:
            h_comparators = self.compute_comparators_height(self.dp.tagbits, dyn_p.num_do_b_mat, self.subarray.area.get_w())
            h_comparators *= (self.RWP + self.ERP)

        is_footer = False
        Isat_subarray = 2 * simplified_nmos_Isat(g_tp.sram.cell_nmos_w, self.is_dram, True) #only one wordline active in a subarray 2 means two inverters in an SRAM cell
        detalV_array = 0 #, deltaV_wl, deltaV_floatingBL
        c_wakeup_array = 0

        if not (self.is_fa or self.pure_cam) and g_ip.power_gating:
            c_wakeup_array = drain_C_(g_tp.sram.cell_pmos_w, PCH, 1, 1, self.cell.h, self.is_dram, True)
            c_wakeup_array += 2 * drain_C_(g_tp.sram.cell_pmos_w, PCH, 1, 1, self.cell.h, self.is_dram, True) + \
                              drain_C_(g_tp.sram.cell_nmos_w, NCH, 1, 1, self.cell.h, self.is_dram, True)
            c_wakeup_array *= self.subarray.num_rows
            detalV_array = g_tp.sram_cell.Vdd - g_tp.sram_cell.Vcc_min

            self.sram_sleep_tx = SleepTx(g_ip.perfloss, Isat_subarray, is_footer, c_wakeup_array, detalV_array, 1, self.cell)
            self.subarray.area.set_h(self.subarray.area.h + self.sram_sleep_tx.area.h)

        branch_effort_predec_blk1_out = sp.Pow(2, self.r_predec_blk2.number_input_addr_bits)
        branch_effort_predec_blk2_out = sp.Pow(2, self.r_predec_blk1.number_input_addr_bits)
        w_row_predecode_output_wires = (branch_effort_predec_blk1_out + branch_effort_predec_blk2_out) * g_tp.wire_inside_mat.pitch * (self.RWP + self.ERP + self.EWP)

        h_non_cell_area = (self.num_subarrays_per_mat / self.num_subarrays_per_row) * (h_bit_mux_sense_amp_precharge_sa_mux_write_driver_write_mux + h_subarray_out_drv + h_comparators)
        w_non_cell_area = symbolic_convex_max(w_row_predecode_output_wires, self.num_subarrays_per_row * w_row_decoder)

        if self.deg_bl_muxing > 1:
            h_bit_mux_dec_out_wires = self.deg_bl_muxing * g_tp.wire_inside_mat.pitch * (self.RWP + self.ERP)

        if self.dp.Ndsam_lev_1 > 1:
            h_senseamp_mux_dec_out_wires = self.dp.Ndsam_lev_1 * g_tp.wire_inside_mat.pitch * (self.RWP + self.ERP)

        if self.dp.Ndsam_lev_2 > 1:
            h_senseamp_mux_dec_out_wires += self.dp.Ndsam_lev_2 * g_tp.wire_inside_mat.pitch * (self.RWP + self.ERP)

        if not g_ip.ver_htree_wires_over_array:
            h_addr_datain_wires = (self.dp.number_addr_bits_mat + self.dp.number_way_select_signals_mat + (self.dp.num_di_b_mat + self.dp.num_do_b_mat) / self.num_subarrays_per_row) * g_tp.wire_inside_mat.pitch * (self.RWP + self.ERP + self.EWP)

            if self.is_fa or self.pure_cam:
                h_addr_datain_wires = (self.dp.number_addr_bits_mat + self.dp.number_way_select_signals_mat + (self.dp.num_di_b_mat + self.dp.num_do_b_mat) / self.num_subarrays_per_row) * g_tp.wire_inside_mat.pitch * (self.RWP + self.ERP + self.EWP) + \
                                      (self.dp.num_si_b_mat + self.dp.num_so_b_mat) / self.num_subarrays_per_row * g_tp.wire_inside_mat.pitch * self.SCHP

            h_non_cell_area = (h_bit_mux_sense_amp_precharge_sa_mux_write_driver_write_mux + h_comparators + h_subarray_out_drv) * (self.num_subarrays_per_mat / self.num_subarrays_per_row) + \
                              h_addr_datain_wires + h_bit_mux_dec_out_wires + h_senseamp_mux_dec_out_wires

        area_mat_center_circuitry = (self.r_predec_blk_drv1.area.get_area() + self.b_mux_predec_blk_drv1.area.get_area() + self.sa_mux_lev_1_predec_blk_drv1.area.get_area() + self.sa_mux_lev_2_predec_blk_drv1.area.get_area() + \
                                     self.way_sel_drv1.area.get_area() + self.r_predec_blk_drv2.area.get_area() + self.b_mux_predec_blk_drv2.area.get_area() + self.sa_mux_lev_1_predec_blk_drv2.area.get_area() + self.sa_mux_lev_2_predec_blk_drv2.area.get_area() + \
                                     self.r_predec_blk1.area.get_area() + self.b_mux_predec_blk1.area.get_area() + self.sa_mux_lev_1_predec_blk1.area.get_area() + self.sa_mux_lev_2_predec_blk1.area.get_area() + \
                                     self.r_predec_blk2.area.get_area() + self.b_mux_predec_blk2.area.get_area() + self.sa_mux_lev_1_predec_blk2.area.get_area() + self.sa_mux_lev_2_predec_blk2.area.get_area() + \
                                     self.bit_mux_dec.area.get_area() + self.sa_mux_lev_1_dec.area.get_area() + self.sa_mux_lev_2_dec.area.get_area()) * (self.RWP + self.ERP + self.EWP)

        assert self.num_subarrays_per_mat / self.num_subarrays_per_row > 0
        self.area.h = (self.num_subarrays_per_mat / self.num_subarrays_per_row) * self.subarray.area.h + h_non_cell_area
        self.area.w = self.num_subarrays_per_row * self.subarray.area.get_w() + w_non_cell_area
        self.area.w = (self.area.h * self.area.w + area_mat_center_circuitry) / self.area.h

        if g_ip.is_3d_mem:
            h_non_cell_area = h_bit_mux_sense_amp_precharge_sa_mux_write_driver_write_mux + h_subarray_out_drv
            self.area.h = self.subarray.area.h + h_non_cell_area
            self.area.w = self.subarray.area.w

        # assert self.area.h > 0
        # assert self.area.w > 0

    def compute_delays(self, inrisetime):
        print("CHECKPOINT 0")
        if self.is_fa or self.pure_cam:
            outrisetime_search = self.compute_cam_delay(inrisetime)

            if self.is_fa:
                self.bl_precharge_eq_drv.compute_delay(0)
                k = self.ml_to_ram_wl_drv.number_gates - 1
                rd = tr_R_on(self.ml_to_ram_wl_drv.width_n[k], NCH, 1, self.is_dram, False, True)
                C_intrinsic = drain_C_(self.ml_to_ram_wl_drv.width_n[k], PCH, 1, 1, 4 * self.cell.h, self.is_dram, False, True) + \
                              drain_C_(self.ml_to_ram_wl_drv.width_n[k], NCH, 1, 1, 4 * self.cell.h, self.is_dram, False, True)
                C_ld = self.ml_to_ram_wl_drv.c_gate_load + self.ml_to_ram_wl_drv.c_wire_load
                tf = rd * (C_intrinsic + C_ld) + self.ml_to_ram_wl_drv.r_wire_load * C_ld / 2
                self.delay_wl_reset = horowitz(0, tf, 0.5, 0.5, RISE)

                R_bl_precharge = tr_R_on(g_tp.w_pmos_bl_precharge, PCH, 1, self.is_dram, False, False)
                r_b_metal = self.cam_cell.h * g_tp.wire_local.R_per_um
                R_bl = self.subarray.num_rows * r_b_metal
                C_bl = self.subarray.C_bl
                self.delay_bl_restore = self.bl_precharge_eq_drv.delay + \
                                        sp.log((g_tp.sram.Vbitpre - 0.1 * self.dp.V_b_sense) / (g_tp.sram.Vbitpre - self.dp.V_b_sense)) * \
                                        (R_bl_precharge * C_bl + R_bl * C_bl / 2)

                outrisetime_search = self.compute_bitline_delay(outrisetime_search)
                outrisetime_search = self.compute_sa_delay(outrisetime_search)

            print("CHECKPOINT 1")
            outrisetime_search = self.compute_subarray_out_drv(outrisetime_search)
            self.subarray_out_wire.set_in_rise_time(outrisetime_search)
            outrisetime_search = self.subarray_out_wire.signal_rise_time()
            self.delay_subarray_out_drv_htree = self.delay_subarray_out_drv + self.subarray_out_wire.delay

            print("CHECKPOINT 2")
            outrisetime = self.r_predec.compute_delays(inrisetime)
            row_dec_outrisetime = self.row_dec.compute_delays(outrisetime)

            print("CHECKPOINT 3")
            outrisetime = self.b_mux_predec.compute_delays(inrisetime)
            self.bit_mux_dec.compute_delays(outrisetime)

            print("CHECKPOINT 4")
            outrisetime = self.sa_mux_lev_1_predec.compute_delays(inrisetime)
            self.sa_mux_lev_1_dec.compute_delays(outrisetime)

            print("CHECKPOINT 5")
            outrisetime = self.sa_mux_lev_2_predec.compute_delays(inrisetime)
            self.sa_mux_lev_2_dec.compute_delays(outrisetime)

            print("Computed all predec delays")

            if self.pure_cam:
                outrisetime = self.compute_bitline_delay(row_dec_outrisetime)
                outrisetime = self.compute_sa_delay(outrisetime)

            return outrisetime_search
        else:
            print("compute delays CHECKPOINT 6 ?")
            self.bl_precharge_eq_drv.compute_delay(0)
            print("compute delays CHECKPOINT 6.5 ?")
            if self.row_dec.exist:
                k = self.row_dec.num_gates - 1
                rd = tr_R_on(self.row_dec.w_dec_n[k], NCH, 1, self.is_dram, False, True)
                C_intrinsic = drain_C_(self.row_dec.w_dec_p[k], PCH, 1, 1, 4 * self.cell.h, self.is_dram, False, True) + \
                              drain_C_(self.row_dec.w_dec_n[k], NCH, 1, 1, 4 * self.cell.h, self.is_dram, False, True)
                C_ld = self.row_dec.C_ld_dec_out
                tf = rd * (C_intrinsic + C_ld) + self.row_dec.R_wire_dec_out * C_ld / 2
                self.delay_wl_reset = horowitz(0, tf, 0.5, 0.5, RISE)

            R_bl_precharge = tr_R_on(g_tp.w_pmos_bl_precharge, PCH, 1, self.is_dram, False, False)
            r_b_metal = self.cell.h * g_tp.wire_local.R_per_um
            R_bl = self.subarray.num_rows * r_b_metal
            C_bl = self.subarray.C_bl

            if self.is_dram:
                self.delay_bl_restore = self.bl_precharge_eq_drv.delay + 2.3 * (R_bl_precharge * C_bl + R_bl * C_bl / 2)
            else:
                self.delay_bl_restore = self.bl_precharge_eq_drv.delay + \
                                        sp.log((g_tp.sram.Vbitpre - 0.1 * self.dp.V_b_sense) / (g_tp.sram.Vbitpre - self.dp.V_b_sense)) * \
                                        (R_bl_precharge * C_bl + R_bl * C_bl / 2)

        print("CHECKPOINT 7")
        outrisetime = self.r_predec.compute_delays(inrisetime)
        row_dec_outrisetime = self.row_dec.compute_delays(outrisetime)

        print(outrisetime)
        print(row_dec_outrisetime)

        print("CHECKPOINT 8")
        outrisetime = self.b_mux_predec.compute_delays(inrisetime)
        self.bit_mux_dec.compute_delays(outrisetime)

        print(outrisetime)
        print(self.b_mux_predec.delay)
        print(self.bit_mux_dec.delay)

        print("CHECKPOINT 9")
        outrisetime = self.sa_mux_lev_1_predec.compute_delays(inrisetime)
        self.sa_mux_lev_1_dec.compute_delays(outrisetime)

        print("CHECKPOINT 10")
        outrisetime = self.sa_mux_lev_2_predec.compute_delays(inrisetime)
        self.sa_mux_lev_2_dec.compute_delays(outrisetime)

        if g_ip.is_3d_mem:
            row_dec_outrisetime = inrisetime

        print("CHECKPOINT 11")
        outrisetime = self.compute_bitline_delay(row_dec_outrisetime)
        outrisetime = self.compute_sa_delay(outrisetime)
        outrisetime = self.compute_subarray_out_drv(outrisetime)
        self.subarray_out_wire.set_in_rise_time(outrisetime)
        outrisetime = self.subarray_out_wire.signal_rise_time()

        print("CHECKPOINT 12")
        self.delay_subarray_out_drv_htree = self.delay_subarray_out_drv + self.subarray_out_wire.delay

        if self.dp.is_tag and not self.dp.fully_assoc:
            self.compute_comparator_delay(0)

        print("CHECKPOINT 13")

        if not self.row_dec.exist:
            self.delay_wl_reset = symbolic_convex_max(self.r_predec.blk1.delay, self.r_predec.blk2.delay)

        print("CHECKPOINT 14")

        return outrisetime
    
    def compute_bit_mux_sa_precharge_sa_mux_wr_drv_wr_mux_h(self):
        height = compute_tr_width_after_folding(g_tp.w_pmos_bl_precharge, self.cam_cell.w if self.camFlag else self.cell.w / (2 * (self.RWP + self.ERP + self.SCHP))) + \
                 compute_tr_width_after_folding(g_tp.w_pmos_bl_eq, self.cam_cell.w if self.camFlag else self.cell.w / (self.RWP + self.ERP + self.SCHP))

        if self.deg_bl_muxing > 1:
            height += compute_tr_width_after_folding(g_tp.w_nmos_b_mux, self.cell.w / (2 * (self.RWP + self.ERP)))

        height += height_sense_amplifier(self.cell.w * self.deg_bl_muxing / (self.RWP + self.ERP))

        if self.dp.Ndsam_lev_1 > 1:
            height += compute_tr_width_after_folding(g_tp.w_nmos_sa_mux, self.cell.w * self.dp.Ndsam_lev_1 / (self.RWP + self.ERP))

        if self.dp.Ndsam_lev_2 > 1:
            height += compute_tr_width_after_folding(g_tp.w_nmos_sa_mux, self.cell.w * self.deg_bl_muxing * self.dp.Ndsam_lev_1 / (self.RWP + self.ERP))
            height += 2 * compute_tr_width_after_folding(pmos_to_nmos_sz_ratio(self.is_dram) * g_tp.min_w_nmos_, self.cell.w * self.dp.Ndsam_lev_2 / (self.RWP + self.ERP))
            height += 2 * compute_tr_width_after_folding(g_tp.min_w_nmos_, self.cell.w * self.dp.Ndsam_lev_2 / (self.RWP + self.ERP))

        if g_ip.is_3d_mem:
            width_write_driver_write_mux = self.width_write_driver_or_write_mux()
            height_write_driver_write_mux = compute_tr_width_after_folding(2 * width_write_driver_write_mux, self.cell.w)
            height += height_write_driver_write_mux

        return height

    def compute_cam_delay(self, inrisetime):
        out_time_ramp, this_delay = 0, 0
        Rwire, tf, c_intrinsic, rd, Cwire, c_gate_load = 0, 0, 0, 0, 0, 0

        Wfaprechp, Wdummyn, Wdummyinvn, Wdummyinvp, Waddrnandn, Waddrnandp = 0, 0, 0, 0, 0, 0
        Wfanorn, Wfanorp, W_hit_miss_n, W_hit_miss_p = 0, 0, 0, 0

        c_matchline_metal, r_matchline_metal, c_searchline_metal, r_searchline_metal, dynSearchEng = 0, 0, 0, 0, 0
        Htagbits = 0

        driver_c_gate_load = 0
        driver_c_wire_load = 0
        driver_r_wire_load = 0

        leak_power_cc_inverters_sram_cell = 0
        leak_power_acc_tr_RW_or_WR_port_sram_cell = 0
        leak_power_RD_port_sram_cell = 0
        leak_power_SCHP_port_sram_cell = 0
        leak_comparator_cam_cell = 0

        gate_leak_comparator_cam_cell = 0
        gate_leak_power_cc_inverters_sram_cell = 0
        gate_leak_power_RD_port_sram_cell = 0
        gate_leak_power_SCHP_port_sram_cell = 0

        c_matchline_metal = self.cam_cell.get_w() * g_tp.wire_local.C_per_um
        c_searchline_metal = self.cam_cell.get_h() * g_tp.wire_local.C_per_um
        r_matchline_metal = self.cam_cell.get_w() * g_tp.wire_local.R_per_um
        r_searchline_metal = self.cam_cell.get_h() * g_tp.wire_local.R_per_um

        dynSearchEng = 0.0
        self.delay_matchchline = 0.0
        p_to_n_sizing_r = pmos_to_nmos_sz_ratio(self.is_dram)
        linear_scaling = False

        if linear_scaling:
            Wfaprechp = 12.5 * g_ip.F_sz_um
            Wdummyn = 12.5 * g_ip.F_sz_um
            Wdummyinvn = 75 * g_ip.F_sz_um
            Wdummyinvp = 100 * g_ip.F_sz_um
            Waddrnandn = 62.5 * g_ip.F_sz_um
            Waddrnandp = 62.5 * g_ip.F_sz_um
            Wfanorn = 6.25 * g_ip.F_sz_um
            Wfanorp = 12.5 * g_ip.F_sz_um
            W_hit_miss_n = Wdummyn
            W_hit_miss_p = g_tp.min_w_nmos_ * p_to_n_sizing_r
        else:
            Wfaprechp = g_tp.w_pmos_bl_precharge
            Wdummyn = g_tp.cam.cell_nmos_w
            Wdummyinvn = 75 * g_ip.F_sz_um
            Wdummyinvp = 100 * g_ip.F_sz_um
            Waddrnandn = 62.5 * g_ip.F_sz_um
            Waddrnandp = 62.5 * g_ip.F_sz_um
            Wfanorn = 6.25 * g_ip.F_sz_um
            Wfanorp = 12.5 * g_ip.F_sz_um
            W_hit_miss_n = Wdummyn
            W_hit_miss_p = g_tp.min_w_nmos_ * p_to_n_sizing_r

        #TODO deleted int
        Htagbits = sp.ceiling(self.subarray.num_cols_fa_cam / 2.0)

        driver_c_gate_load = self.subarray.num_cols_fa_cam * gate_C(2 * g_tp.w_pmos_bl_precharge + g_tp.w_pmos_bl_eq, 0, self.is_dram, False, False)
        driver_c_wire_load = self.subarray.num_cols_fa_cam * self.cam_cell.w * g_tp.wire_outside_mat.C_per_um
        driver_r_wire_load = self.subarray.num_cols_fa_cam * self.cam_cell.w * g_tp.wire_outside_mat.R_per_um

        self.sl_precharge_eq_drv = Driver(driver_c_gate_load, driver_c_wire_load, driver_r_wire_load, self.is_dram)

        driver_c_gate_load = (self.subarray.num_rows + 1) * gate_C(Wdummyn, 0, self.is_dram, False, False)
        driver_c_wire_load = (self.subarray.num_rows + 1) * c_searchline_metal
        driver_r_wire_load = (self.subarray.num_rows + 1) * r_searchline_metal
        self.sl_data_drv = Driver(driver_c_gate_load, driver_c_wire_load, driver_r_wire_load, self.is_dram)

        self.sl_precharge_eq_drv.compute_delay(0)
        R_bl_precharge = tr_R_on(g_tp.w_pmos_bl_precharge, PCH, 1, self.is_dram, False, False)
        r_b_metal = self.cam_cell.h * g_tp.wire_local.R_per_um
        R_bl = (self.subarray.num_rows + 1) * r_b_metal
        C_bl = self.subarray.C_bl_cam
        self.delay_cam_sl_restore = self.sl_precharge_eq_drv.delay + sp.log(g_tp.cam.Vbitpre) * (R_bl_precharge * C_bl + R_bl * C_bl / 2)

        out_time_ramp = self.sl_data_drv.compute_delay(inrisetime)
        self.delay_matchchline += self.sl_data_drv.delay

        driver_c_gate_load = (self.subarray.num_rows + 1) * gate_C(Wfaprechp, 0, self.is_dram)
        driver_c_wire_load = (self.subarray.num_rows + 1) * c_searchline_metal
        driver_r_wire_load = (self.subarray.num_rows + 1) * r_searchline_metal

        self.ml_precharge_drv = Driver(driver_c_gate_load, driver_c_wire_load, driver_r_wire_load, self.is_dram)
        self.ml_precharge_drv.compute_delay(0)

        rd = tr_R_on(Wdummyn, NCH, 2, self.is_dram)
        c_intrinsic = Htagbits * (2 * drain_C_(Wdummyn, NCH, 2, 1, g_tp.cell_h_def, self.is_dram) + drain_C_(Wfaprechp, PCH, 1, 1, g_tp.cell_h_def, self.is_dram) / Htagbits)
        Cwire = c_matchline_metal * Htagbits
        Rwire = r_matchline_metal * Htagbits
        c_gate_load = gate_C(Waddrnandn + Waddrnandp, 0, self.is_dram)

        R_ml_precharge = tr_R_on(Wfaprechp, PCH, 1, self.is_dram)
        R_ml = Rwire
        C_ml = Cwire + c_intrinsic
        self.delay_cam_ml_reset = self.ml_precharge_drv.delay + sp.log(g_tp.cam.Vbitpre) * (R_ml_precharge * C_ml + R_ml * C_ml / 2)

        tf = rd * (c_intrinsic + Cwire / 2 + c_gate_load) + Rwire * (Cwire / 2 + c_gate_load)
        this_delay = horowitz(out_time_ramp, tf, VTHFA2, VTHFA3, FALL)
        self.delay_matchchline += this_delay
        out_time_ramp = this_delay / VTHFA3

        dynSearchEng += (c_intrinsic + Cwire + c_gate_load) * (self.subarray.num_rows + 1) * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd * 2

        rd = tr_R_on(Waddrnandn, NCH, 2, self.is_dram)
        c_intrinsic = drain_C_(Waddrnandn, NCH, 2, 1, g_tp.cell_h_def, self.is_dram) + drain_C_(Waddrnandp, PCH, 1, 1, g_tp.cell_h_def, self.is_dram) * 2
        c_gate_load = gate_C(Wdummyinvn + Wdummyinvp, 0, self.is_dram)
        tf = rd * (c_intrinsic + c_gate_load)
        this_delay = horowitz(out_time_ramp, tf, VTHFA3, VTHFA4, RISE)
        out_time_ramp = this_delay / (1 - VTHFA4)
        self.delay_matchchline += this_delay

        dynSearchEng += (c_intrinsic * (self.subarray.num_rows + 1) + c_gate_load * 2) * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd

        rd = tr_R_on(Wdummyinvn, NCH, 1, self.is_dram)
        c_intrinsic = drain_C_(Wdummyinvn, NCH, 1, 1, g_tp.cell_h_def, self.is_dram) + drain_C_(Wdummyinvp, NCH, 1, 1, g_tp.cell_h_def, self.is_dram)
        Cwire = c_matchline_metal * Htagbits + c_searchline_metal * (self.subarray.num_rows + 1) / 2
        Rwire = r_matchline_metal * Htagbits + r_searchline_metal * (self.subarray.num_rows + 1) / 2
        c_gate_load = gate_C(Wfanorn + Wfanorp, 0, self.is_dram)
        tf = rd * (c_intrinsic + Cwire + c_gate_load) + Rwire * (Cwire / 2 + c_gate_load)
        this_delay = horowitz(out_time_ramp, tf, VTHFA4, VTHFA5, FALL)
        out_time_ramp = this_delay / VTHFA5
        self.delay_matchchline += this_delay

        dynSearchEng += (c_intrinsic + Cwire + self.subarray.num_rows * c_gate_load) * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd

        driver_c_gate_load = gate_C(W_hit_miss_n, 0, self.is_dram, False, False)
        driver_c_wire_load = self.subarray.C_wl_ram
        driver_r_wire_load = self.subarray.R_wl_ram

        self.ml_to_ram_wl_drv = Driver(driver_c_gate_load, driver_c_wire_load, driver_r_wire_load, self.is_dram)

        rd = tr_R_on(Wfanorn, NCH, 1, self.is_dram)
        c_intrinsic = 2 * drain_C_(Wfanorn, NCH, 1, 1, g_tp.cell_h_def, self.is_dram) + drain_C_(Wfanorp, NCH, 1, 1, g_tp.cell_h_def, self.is_dram)
        c_gate_load = gate_C(self.ml_to_ram_wl_drv.width_n[0] + self.ml_to_ram_wl_drv.width_p[0], 0, self.is_dram)
        tf = rd * (c_intrinsic + c_gate_load)
        this_delay = horowitz(out_time_ramp, tf, 0.5, 0.5, RISE)
        out_time_ramp = this_delay / (1 - 0.5)
        self.delay_matchchline += this_delay

        out_time_ramp = self.ml_to_ram_wl_drv.compute_delay(out_time_ramp)
        dynSearchEng += c_intrinsic * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd

        c_intrinsic = 2 * drain_C_(W_hit_miss_p, NCH, 2, 1, g_tp.cell_h_def, self.is_dram)
        Cwire = c_searchline_metal * self.subarray.num_rows
        Rwire = r_searchline_metal * self.subarray.num_rows
        c_gate_load = drain_C_(W_hit_miss_n, NCH, 1, 1, g_tp.cell_h_def, self.is_dram) * self.subarray.num_rows

        rd = tr_R_on(W_hit_miss_p, PCH, 1, self.is_dram, False, False)
        R_hit_miss = Rwire
        C_hit_miss = Cwire + c_intrinsic
        self.delay_hit_miss_reset = sp.log(g_tp.cam.Vbitpre) * (rd * C_hit_miss + R_hit_miss * C_hit_miss / 2)
        dynSearchEng += (c_intrinsic + Cwire + c_gate_load) * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd

        c_intrinsic = 2 * drain_C_(W_hit_miss_n, NCH, 2, 1, g_tp.cell_h_def, self.is_dram)
        Cwire = c_searchline_metal * self.subarray.num_rows
        Rwire = r_searchline_metal * self.subarray.num_rows
        c_gate_load = drain_C_(W_hit_miss_n, NCH, 1, 1, g_tp.cell_h_def, self.is_dram) * self.subarray.num_rows

        rd = tr_R_on(W_hit_miss_n, PCH, 1, self.is_dram, False, False)
        tf = rd * (c_intrinsic + Cwire / 2 + c_gate_load) + Rwire * (Cwire / 2 + c_gate_load)

        self.delay_hit_miss = horowitz(0, tf, 0.5, 0.5, FALL)

        if self.is_fa:
            self.delay_matchchline += symbolic_convex_max(self.ml_to_ram_wl_drv.delay, self.delay_hit_miss)

        dynSearchEng += (c_intrinsic + Cwire + c_gate_load) * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd

        self.power_matchline.searchOp.dynamic = dynSearchEng

        Iport = cmos_Isub_leakage(g_tp.cam.cell_a_w, 0, 1, nmos, False, True)
        Iport_erp = cmos_Isub_leakage(g_tp.cam.cell_a_w, 0, 2, nmos, False, True)
        Icell = cmos_Isub_leakage(g_tp.cam.cell_nmos_w, g_tp.cam.cell_pmos_w, 1, inv, False, True) * 2
        Icell_comparator = cmos_Isub_leakage(Wdummyn, Wdummyn, 1, inv, False, True) * 2

        self.leak_power_cc_inverters_sram_cell = Icell * g_tp.cam_cell.Vdd
        self.leak_comparator_cam_cell = Icell_comparator * g_tp.cam_cell.Vdd
        self.leak_power_acc_tr_RW_or_WR_port_sram_cell = Iport * g_tp.cam_cell.Vdd
        self.leak_power_RD_port_sram_cell = Iport_erp * g_tp.cam_cell.Vdd
        self.leak_power_SCHP_port_sram_cell = 0

        self.power_matchline.searchOp.leakage += self.leak_power_cc_inverters_sram_cell + self.leak_comparator_cam_cell + self.leak_power_acc_tr_RW_or_WR_port_sram_cell + \
                                                  self.leak_power_acc_tr_RW_or_WR_port_sram_cell * (self.RWP + self.EWP - 1) + self.leak_power_RD_port_sram_cell * self.ERP + \
                                                  self.leak_power_SCHP_port_sram_cell * self.SCHP
        self.power_matchline.searchOp.leakage *= (self.subarray.num_rows + 1) * self.subarray.num_cols_fa_cam
        self.power_matchline.searchOp.leakage += (self.subarray.num_rows + 1) * cmos_Isub_leakage(0, Wfaprechp, 1, pmos) * g_tp.cam_cell.Vdd
        self.power_matchline.searchOp.leakage += (self.subarray.num_rows + 1) * cmos_Isub_leakage(Waddrnandn, Waddrnandp, 2, nand) * g_tp.cam_cell.Vdd
        self.power_matchline.searchOp.leakage += (self.subarray.num_rows + 1) * cmos_Isub_leakage(Wfanorn, Wfanorp, 2, nor) * g_tp.cam_cell.Vdd
        self.power_matchline.searchOp.leakage += 0

        Ig_port_erp = cmos_Ig_leakage(g_tp.cam.cell_a_w, 0, 1, nmos, False, True)
        Ig_cell = cmos_Ig_leakage(g_tp.cam.cell_nmos_w, g_tp.cam.cell_pmos_w, 1, inv, False, True) * 2
        Ig_cell_comparator = cmos_Ig_leakage(Wdummyn, Wdummyn, 1, inv, False, True) * 2

        self.gate_leak_comparator_cam_cell = Ig_cell_comparator * g_tp.cam_cell.Vdd
        self.gate_leak_power_cc_inverters_sram_cell = Ig_cell * g_tp.cam_cell.Vdd
        self.gate_leak_power_RD_port_sram_cell = Ig_port_erp * g_tp.sram_cell.Vdd
        self.gate_leak_power_SCHP_port_sram_cell = 0

        self.power_matchline.searchOp.gate_leakage += self.gate_leak_power_cc_inverters_sram_cell
        self.power_matchline.searchOp.gate_leakage += self.gate_leak_comparator_cam_cell
        self.power_matchline.searchOp.gate_leakage += self.gate_leak_power_SCHP_port_sram_cell * self.SCHP + self.gate_leak_power_RD_port_sram_cell * self.ERP
        self.power_matchline.searchOp.gate_leakage *= (self.subarray.num_rows + 1) * self.subarray.num_cols_fa_cam
        self.power_matchline.searchOp.gate_leakage += (self.subarray.num_rows + 1) * cmos_Ig_leakage(0, Wfaprechp, 1, pmos) * g_tp.cam_cell.Vdd
        self.power_matchline.searchOp.gate_leakage += (self.subarray.num_rows + 1) * cmos_Ig_leakage(Waddrnandn, Waddrnandp, 2, nand) * g_tp.cam_cell.Vdd
        self.power_matchline.searchOp.gate_leakage += (self.subarray.num_rows + 1) * cmos_Ig_leakage(Wfanorn, Wfanorp, 2, nor) * g_tp.cam_cell.Vdd
        self.power_matchline.searchOp.gate_leakage += self.subarray.num_rows * cmos_Ig_leakage(W_hit_miss_n, 0, 1, nmos) * g_tp.cam_cell.Vdd + cmos_Ig_leakage(0, W_hit_miss_p, 1, pmos) * g_tp.cam_cell.Vdd

        return out_time_ramp

    def width_write_driver_or_write_mux(self):
        R_sram_cell_pull_up_tr = tr_R_on(g_tp.sram.cell_pmos_w, NCH, 1, self.is_dram, True)
        R_access_tr = tr_R_on(g_tp.sram.cell_a_w, NCH, 1, self.is_dram, True)
        target_R_write_driver_and_mux = (2 * R_sram_cell_pull_up_tr - R_access_tr) / 2
        width_write_driver_nmos = R_to_w(target_R_write_driver_and_mux, NCH, self.is_dram)

        return width_write_driver_nmos
    
    def compute_comparators_height(self, tagbits, number_ways_in_mat, subarray_mem_cell_area_width):
        nand2_area = compute_gate_area(NAND, 2, 0, g_tp.w_comp_n, g_tp.cell_h_def)
        cumulative_area = nand2_area * number_ways_in_mat * tagbits / 4
        return cumulative_area / subarray_mem_cell_area_width

    def compute_bitline_delay(self, inrisetime):
        V_b_pre, v_th_mem_cell, V_wl = 0, 0, 0
        tstep = 0
        dynRdEnergy = 0.0
        dynWriteEnergy = 0.0
        blfloating_c = 0.0
        R_cell_pull_down = 0.0
        R_cell_acc = 0.0
        r_dev = 0.0
        deg_senseamp_muxing = self.dp.Ndsam_lev_1 * self.dp.Ndsam_lev_2

        R_b_metal = self.cam_cell.h if self.camFlag else self.cell.h * g_tp.wire_local.R_per_um
        R_bl = self.subarray.num_rows * R_b_metal
        C_bl = self.subarray.C_bl

        leak_power_cc_inverters_sram_cell = 0
        gate_leak_power_cc_inverters_sram_cell = 0
        leak_power_acc_tr_RW_or_WR_port_sram_cell = 0
        leak_power_RD_port_sram_cell = 0
        gate_leak_power_RD_port_sram_cell = 0

        if self.is_dram:
            V_b_pre = g_tp.dram.Vbitpre
            v_th_mem_cell = g_tp.dram_acc.Vth
            V_wl = g_tp.vpp
            R_cell_acc = tr_R_on(g_tp.dram.cell_a_w, NCH, 1, True, True)
            r_dev = g_tp.dram_cell_Vdd / g_tp.dram_cell_I_on + R_bl / 2
        else:
            V_b_pre = g_tp.sram.Vbitpre
            v_th_mem_cell = g_tp.sram_cell.Vth
            V_wl = g_tp.sram_cell.Vdd
            R_cell_pull_down = tr_R_on(g_tp.sram.cell_nmos_w, NCH, 1, False, True)
            R_cell_acc = tr_R_on(g_tp.sram.cell_a_w, NCH, 1, False, True)

            Iport = cmos_Isub_leakage(g_tp.sram.cell_a_w, 0, 1, nmos, False, True)
            Iport_erp = cmos_Isub_leakage(g_tp.sram.cell_a_w, 0, 2, nmos, False, True)
            Icell = cmos_Isub_leakage(g_tp.sram.cell_nmos_w, g_tp.sram.cell_pmos_w, 1, inv, False, True) * 2

            leak_power_cc_inverters_sram_cell = Icell * (g_ip.array_power_gated and g_tp.sram_cell.Vcc_min or g_tp.sram_cell.Vdd)
            leak_power_acc_tr_RW_or_WR_port_sram_cell = Iport * (g_ip.bitline_floating and g_tp.sram.Vbitfloating or g_tp.sram_cell.Vdd)
            leak_power_RD_port_sram_cell = Iport_erp * (g_ip.bitline_floating and g_tp.sram.Vbitfloating or g_tp.sram_cell.Vdd)

            Ig_port_erp = cmos_Ig_leakage(g_tp.sram.cell_a_w, 0, 1, nmos, False, True)
            Ig_cell = cmos_Ig_leakage(g_tp.sram.cell_nmos_w, g_tp.sram.cell_pmos_w, 1, inv, False, True)

            gate_leak_power_cc_inverters_sram_cell = Ig_cell * g_tp.sram_cell.Vdd
            gate_leak_power_RD_port_sram_cell = Ig_port_erp * g_tp.sram_cell.Vdd

        C_drain_bit_mux = drain_C_(g_tp.w_nmos_b_mux, NCH, 1, 0, self.cam_cell.w if self.camFlag else self.cell.w / (2 * (self.RWP + self.ERP + self.SCHP)), self.is_dram)
        R_bit_mux = tr_R_on(g_tp.w_nmos_b_mux, NCH, 1, self.is_dram)
        C_drain_sense_amp_iso = drain_C_(g_tp.w_iso, PCH, 1, 0, self.cam_cell.w if self.camFlag else self.cell.w * self.deg_bl_muxing / (self.RWP + self.ERP + self.SCHP), self.is_dram)
        R_sense_amp_iso = tr_R_on(g_tp.w_iso, PCH, 1, self.is_dram)
        C_sense_amp_latch = gate_C(g_tp.w_sense_p + g_tp.w_sense_n, 0, self.is_dram) + \
            drain_C_(g_tp.w_sense_n, NCH, 1, 0, self.cam_cell.w if self.camFlag else self.cell.w * self.deg_bl_muxing / (self.RWP + self.ERP + self.SCHP), self.is_dram) + \
            drain_C_(g_tp.w_sense_p, PCH, 1, 0, self.cam_cell.w if self.camFlag else self.cell.w * self.deg_bl_muxing / (self.RWP + self.ERP + self.SCHP), self.is_dram)
        C_drain_sense_amp_mux = drain_C_(g_tp.w_nmos_sa_mux, NCH, 1, 0, self.cam_cell.w if self.camFlag else self.cell.w * self.deg_bl_muxing / (self.RWP + self.ERP + self.SCHP), self.is_dram)

        if self.is_dram:
            fraction = self.dp.V_b_sense / ((g_tp.dram_cell_Vdd / 2) * g_tp.dram_cell_C / (g_tp.dram_cell_C + C_bl))
            tstep = fraction * r_dev * (g_ip.is_3d_mem and 1 or 2.3) * \
                (g_tp.dram_cell_C * (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux)) / \
                (g_tp.dram_cell_C + (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux))
            self.delay_writeback = tstep
            dynRdEnergy += (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) * (g_tp.dram_cell_Vdd / 2) * g_tp.dram_cell_Vdd
            dynWriteEnergy += (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch) * (g_tp.dram_cell_Vdd / 2) * g_tp.dram_cell_Vdd * self.num_act_mats_hor_dir * 100
            self.per_bitline_read_energy = (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) * (g_tp.dram_cell_Vdd / 2) * g_tp.dram_cell_Vdd
        else:
            if self.deg_bl_muxing > 1:
                tau = (R_cell_pull_down + R_cell_acc) * \
                    (C_bl + 2 * C_drain_bit_mux + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) + \
                    R_bl * (C_bl / 2 + 2 * C_drain_bit_mux + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) + \
                    R_bit_mux * (C_drain_bit_mux + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) + \
                    R_sense_amp_iso * (C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux)
                dynRdEnergy += (C_bl + 2 * C_drain_bit_mux) * 2 * self.dp.V_b_sense * g_tp.sram_cell.Vdd
                blfloating_c += (C_bl + 2 * C_drain_bit_mux) * 2
                dynRdEnergy += (2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) * 2 * self.dp.V_b_sense * g_tp.sram_cell.Vdd * (1.0 / self.deg_bl_muxing)
                blfloating_c += (2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) * 2
                dynWriteEnergy += (1.0 / self.deg_bl_muxing / deg_senseamp_muxing) * self.num_act_mats_hor_dir * (C_bl + 2 * C_drain_bit_mux) * g_tp.sram_cell.Vdd * g_tp.sram_cell.Vdd * 2
            else:
                tau = (R_cell_pull_down + R_cell_acc) * \
                    (C_bl + C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) + R_bl * C_bl / 2 + \
                    R_sense_amp_iso * (C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux)
                dynRdEnergy += (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) * 2 * self.dp.V_b_sense * g_tp.sram_cell.Vdd
                blfloating_c += (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) * 2
                dynWriteEnergy += (1.0 / self.deg_bl_muxing / deg_senseamp_muxing) * self.num_act_mats_hor_dir * C_bl * g_tp.sram_cell.Vdd * g_tp.sram_cell.Vdd * 2

            tstep = tau * sp.log(V_b_pre / (V_b_pre - self.dp.V_b_sense))

            self.power_bitline.readOp.leakage = leak_power_cc_inverters_sram_cell + \
                leak_power_acc_tr_RW_or_WR_port_sram_cell + \
                leak_power_acc_tr_RW_or_WR_port_sram_cell * (self.RWP + self.EWP - 1) + \
                leak_power_RD_port_sram_cell * self.ERP
            self.power_bitline.readOp.gate_leakage = gate_leak_power_cc_inverters_sram_cell + \
                gate_leak_power_RD_port_sram_cell * self.ERP

        m = V_wl / inrisetime

        print(f'tstep: {tstep}')
        # TODO Relational
        # if tstep <= (0.5 * (V_wl - v_th_mem_cell) / m):
        self.delay_bitline = sp.sqrt(2 * tstep * (V_wl - v_th_mem_cell) / m)
        # else:
        #     self.delay_bitline = tstep + (V_wl - v_th_mem_cell) / (2 * m)
        # condition = tstep <= (0.5 * (V_wl - v_th_mem_cell) / m)
        # delay_bitline_if_true = sp.sqrt(2 * tstep * (V_wl - v_th_mem_cell) / m)
        # delay_bitline_if_false = tstep + (V_wl - v_th_mem_cell) / (2 * m)

        # # Use Piecewise to define the delay_bitline symbolically
        # self.delay_bitline = sp.Piecewise((delay_bitline_if_true, condition),
        #                             (delay_bitline_if_false, not condition))

        # TODO VISIT

        is_fa = bool(self.dp.fully_assoc)

        if not self.dp.is_tag or not is_fa:
            self.power_bitline.readOp.dynamic = dynRdEnergy
            self.power_bitline.writeOp.dynamic = dynWriteEnergy

        self.blfloating_wakeup_t = blfloating_c * (g_tp.sram_cell.Vdd - g_tp.sram.Vbitfloating) / \
            (simplified_pmos_Isat(g_tp.w_pmos_bl_precharge) / Ilinear_to_Isat_ratio)
        self.blfloating_wakeup_e.readOp.dynamic = dynRdEnergy / self.dp.V_b_sense * (g_tp.sram_cell.Vdd - g_tp.sram.Vbitfloating) * \
            self.subarray.num_rows * self.num_subarrays_per_mat * self.dp.num_act_mats_hor_dir

        outrisetime = 0

        return outrisetime
    
    def compute_sa_delay(self, inrisetime):
        # Bitline circuitry leakage.
        Iiso = simplified_pmos_leakage(g_tp.w_iso, self.is_dram)
        IsenseEn = simplified_nmos_leakage(g_tp.w_sense_en, self.is_dram)
        IsenseN = simplified_nmos_leakage(g_tp.w_sense_n, self.is_dram)
        IsenseP = simplified_pmos_leakage(g_tp.w_sense_p, self.is_dram)

        lkgIdlePh = IsenseEn
        lkgReadPh = Iiso + IsenseN + IsenseP
        lkgIdle = lkgIdlePh
        self.leak_power_sense_amps_closed_page_state = lkgIdlePh * g_tp.peri_global.Vdd
        self.leak_power_sense_amps_open_page_state = lkgReadPh * g_tp.peri_global.Vdd

        # Load seen by sense amp.
        C_ld = gate_C(g_tp.w_sense_p + g_tp.w_sense_n, 0, self.is_dram) + \
               drain_C_(g_tp.w_sense_n, NCH, 1, 0, self.cam_cell.w if self.camFlag else self.cell.w * self.deg_bl_muxing / (self.RWP + self.ERP + self.SCHP), self.is_dram) + \
               drain_C_(g_tp.w_sense_p, PCH, 1, 0, self.cam_cell.w if self.camFlag else self.cell.w * self.deg_bl_muxing / (self.RWP + self.ERP + self.SCHP), self.is_dram) + \
               drain_C_(g_tp.w_iso, PCH, 1, 0, self.cam_cell.w if self.camFlag else self.cell.w * self.deg_bl_muxing / (self.RWP + self.ERP + self.SCHP), self.is_dram) + \
               drain_C_(g_tp.w_nmos_sa_mux, NCH, 1, 0, self.cam_cell.w if self.camFlag else self.cell.w * self.deg_bl_muxing / (self.RWP + self.ERP + self.SCHP), self.is_dram)

        tau = C_ld / g_tp.gm_sense_amp_latch
        self.delay_sa = tau * sp.log(g_tp.peri_global.Vdd / self.dp.V_b_sense)
        self.power_sa.readOp.dynamic = C_ld * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd
        self.power_sa.readOp.leakage = lkgIdle * g_tp.peri_global.Vdd

        outrisetime = 0
        return outrisetime

    def compute_subarray_out_drv(self, inrisetime):
        p_to_n_sz_r = pmos_to_nmos_sz_ratio(self.is_dram)

        # Delay of signal through pass-transistor of first level of sense-amp mux to input of inverter-buffer.
        rd = tr_R_on(g_tp.w_nmos_sa_mux, NCH, 1, self.is_dram)
        C_ld = self.dp.Ndsam_lev_1 * drain_C_(g_tp.w_nmos_sa_mux, NCH, 1, 0, self.cam_cell.w if self.camFlag else self.cell.w * self.deg_bl_muxing / (self.RWP + self.ERP + self.SCHP), self.is_dram) + \
               gate_C(g_tp.min_w_nmos_ + p_to_n_sz_r * g_tp.min_w_nmos_, 0.0, self.is_dram)
        tf = rd * C_ld
        this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
        self.delay_subarray_out_drv += this_delay
        inrisetime = this_delay / (1.0 - 0.5)
        self.power_subarray_out_drv.readOp.dynamic += C_ld * 0.5 * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd
        self.power_subarray_out_drv.readOp.gate_leakage += cmos_Ig_leakage(g_tp.w_nmos_sa_mux, 0, 1, nmos) * g_tp.peri_global.Vdd

        # Delay of signal through inverter-buffer to second level of sense-amp mux.
        rd = tr_R_on(g_tp.min_w_nmos_, NCH, 1, self.is_dram)
        C_ld = drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def, self.is_dram) + \
               drain_C_(p_to_n_sz_r * g_tp.min_w_nmos_, PCH, 1, 1, g_tp.cell_h_def, self.is_dram) + \
               gate_C(g_tp.min_w_nmos_ + p_to_n_sz_r * g_tp.min_w_nmos_, 0.0, self.is_dram)
        tf = rd * C_ld
        this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
        self.delay_subarray_out_drv += this_delay
        inrisetime = this_delay / (1.0 - 0.5)
        self.power_subarray_out_drv.readOp.dynamic += C_ld * 0.5 * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd
        self.power_subarray_out_drv.readOp.leakage += cmos_Isub_leakage(g_tp.min_w_nmos_, p_to_n_sz_r * g_tp.min_w_nmos_, 1, inv, self.is_dram) * g_tp.peri_global.Vdd
        self.power_subarray_out_drv.readOp.gate_leakage += cmos_Ig_leakage(g_tp.min_w_nmos_, p_to_n_sz_r * g_tp.min_w_nmos_, 1, inv) * g_tp.peri_global.Vdd

        # Inverter driving drain of pass transistor of second level of sense-amp mux.
        rd = tr_R_on(g_tp.min_w_nmos_, NCH, 1, self.is_dram)
        C_ld = drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def, self.is_dram) + \
               drain_C_(p_to_n_sz_r * g_tp.min_w_nmos_, PCH, 1, 1, g_tp.cell_h_def, self.is_dram) + \
               drain_C_(g_tp.w_nmos_sa_mux, NCH, 1, 0, self.cam_cell.w if self.camFlag else self.cell.w * self.deg_bl_muxing * self.dp.Ndsam_lev_1 / (self.RWP + self.ERP + self.SCHP), self.is_dram)
        tf = rd * C_ld
        this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
        self.delay_subarray_out_drv += this_delay
        inrisetime = this_delay / (1.0 - 0.5)
        self.power_subarray_out_drv.readOp.dynamic += C_ld * 0.5 * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd
        self.power_subarray_out_drv.readOp.leakage += cmos_Isub_leakage(g_tp.min_w_nmos_, p_to_n_sz_r * g_tp.min_w_nmos_, 1, inv) * g_tp.peri_global.Vdd
        self.power_subarray_out_drv.readOp.gate_leakage += cmos_Ig_leakage(g_tp.min_w_nmos_, p_to_n_sz_r * g_tp.min_w_nmos_, 1, inv) * g_tp.peri_global.Vdd

        # Delay of signal through pass-transistor to input of subarray output driver.
        rd = tr_R_on(g_tp.w_nmos_sa_mux, NCH, 1, self.is_dram)
        C_ld = self.dp.Ndsam_lev_2 * drain_C_(g_tp.w_nmos_sa_mux, NCH, 1, 0, self.cam_cell.w if self.camFlag else self.cell.w * self.deg_bl_muxing * self.dp.Ndsam_lev_1 / (self.RWP + self.ERP + self.SCHP), self.is_dram) + \
               gate_C(self.subarray_out_wire.repeater_size * (self.subarray_out_wire.wire_length / self.subarray_out_wire.repeater_spacing) * g_tp.min_w_nmos_ * (1 + p_to_n_sz_r), 0.0, self.is_dram)
        tf = rd * C_ld
        this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
        self.delay_subarray_out_drv += this_delay
        inrisetime = this_delay / (1.0 - 0.5)
        self.power_subarray_out_drv.readOp.dynamic += C_ld * 0.5 * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd
        self.power_subarray_out_drv.readOp.gate_leakage += cmos_Ig_leakage(g_tp.w_nmos_sa_mux, 0, 1, nmos) * g_tp.peri_global.Vdd

        return inrisetime

    def compute_comparator_delay(self, inrisetime):
        A = g_ip.tag_assoc
        tagbits_ = self.dp.tagbits // 4  # Assuming there are 4 quarter comparators. input tagbits is already a multiple of 4.

        # First Inverter
        Ceq = gate_C(g_tp.w_comp_inv_n2 + g_tp.w_comp_inv_p2, 0, self.is_dram) + \
              drain_C_(g_tp.w_comp_inv_p1, PCH, 1, 1, g_tp.cell_h_def, self.is_dram) + \
              drain_C_(g_tp.w_comp_inv_n1, NCH, 1, 1, g_tp.cell_h_def, self.is_dram)
        Req = tr_R_on(g_tp.w_comp_inv_p1, PCH, 1, self.is_dram)
        tf = Req * Ceq
        st1del = horowitz(inrisetime, tf, VTHCOMPINV, VTHCOMPINV, FALL)
        nextinputtime = st1del / VTHCOMPINV
        self.power_comparator.readOp.dynamic += 0.5 * Ceq * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd * 4 * A

        lkgCurrent = cmos_Isub_leakage(g_tp.w_comp_inv_n1, g_tp.w_comp_inv_p1, 1, inv, self.is_dram) * 4 * A
        gatelkgCurrent = cmos_Ig_leakage(g_tp.w_comp_inv_n1, g_tp.w_comp_inv_p1, 1, inv, self.is_dram) * 4 * A

        # Second Inverter
        Ceq = gate_C(g_tp.w_comp_inv_n3 + g_tp.w_comp_inv_p3, 0, self.is_dram) + \
              drain_C_(g_tp.w_comp_inv_p2, PCH, 1, 1, g_tp.cell_h_def, self.is_dram) + \
              drain_C_(g_tp.w_comp_inv_n2, NCH, 1, 1, g_tp.cell_h_def, self.is_dram)
        Req = tr_R_on(g_tp.w_comp_inv_n2, NCH, 1, self.is_dram)
        tf = Req * Ceq
        st2del = horowitz(nextinputtime, tf, VTHCOMPINV, VTHCOMPINV, RISE)
        nextinputtime = st2del / (1.0 - VTHCOMPINV)
        self.power_comparator.readOp.dynamic += 0.5 * Ceq * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd * 4 * A
        lkgCurrent += cmos_Isub_leakage(g_tp.w_comp_inv_n2, g_tp.w_comp_inv_p2, 1, inv, self.is_dram) * 4 * A
        gatelkgCurrent += cmos_Ig_leakage(g_tp.w_comp_inv_n2, g_tp.w_comp_inv_p2, 1, inv, self.is_dram) * 4 * A

        # Third Inverter
        Ceq = gate_C(g_tp.w_eval_inv_n + g_tp.w_eval_inv_p, 0, self.is_dram) + \
              drain_C_(g_tp.w_comp_inv_p3, PCH, 1, 1, g_tp.cell_h_def, self.is_dram) + \
              drain_C_(g_tp.w_comp_inv_n3, NCH, 1, 1, g_tp.cell_h_def, self.is_dram)
        Req = tr_R_on(g_tp.w_comp_inv_p3, PCH, 1, self.is_dram)
        tf = Req * Ceq
        st3del = horowitz(nextinputtime, tf, VTHCOMPINV, VTHEVALINV, FALL)
        nextinputtime = st3del / VTHEVALINV
        self.power_comparator.readOp.dynamic += 0.5 * Ceq * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd * 4 * A
        lkgCurrent += cmos_Isub_leakage(g_tp.w_comp_inv_n3, g_tp.w_comp_inv_p3, 1, inv, self.is_dram) * 4 * A
        gatelkgCurrent += cmos_Ig_leakage(g_tp.w_comp_inv_n3, g_tp.w_comp_inv_p3, 1, inv, self.is_dram) * 4 * A

        # Final Inverter (virtual ground driver) discharging compare part
        r1 = tr_R_on(g_tp.w_comp_n, NCH, 2, self.is_dram)
        r2 = tr_R_on(g_tp.w_eval_inv_n, NCH, 1, self.is_dram)
        c2 = (tagbits_) * (drain_C_(g_tp.w_comp_n, NCH, 1, 1, g_tp.cell_h_def, self.is_dram) + \
                           drain_C_(g_tp.w_comp_n, NCH, 2, 1, g_tp.cell_h_def, self.is_dram)) + \
             drain_C_(g_tp.w_eval_inv_p, PCH, 1, 1, g_tp.cell_h_def, self.is_dram) + \
             drain_C_(g_tp.w_eval_inv_n, NCH, 1, 1, g_tp.cell_h_def, self.is_dram)
        c1 = (tagbits_) * (drain_C_(g_tp.w_comp_n, NCH, 1, 1, g_tp.cell_h_def, self.is_dram) + \
                           drain_C_(g_tp.w_comp_n, NCH, 2, 1, g_tp.cell_h_def, self.is_dram)) + \
             drain_C_(g_tp.w_comp_p, PCH, 1, 1, g_tp.cell_h_def, self.is_dram) + \
             gate_C(WmuxdrvNANDn + WmuxdrvNANDp, 0, self.is_dram)
        self.power_comparator.readOp.dynamic += 0.5 * c2 * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd * 4 * A
        self.power_comparator.readOp.dynamic += c1 * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd * (A - 1)
        lkgCurrent += cmos_Isub_leakage(g_tp.w_eval_inv_n, g_tp.w_eval_inv_p, 1, inv, self.is_dram) * 4 * A
        lkgCurrent += cmos_Isub_leakage(g_tp.w_comp_n, g_tp.w_comp_n, 1, inv, self.is_dram) * 4 * A

        gatelkgCurrent += cmos_Ig_leakage(g_tp.w_eval_inv_n, g_tp.w_eval_inv_p, 1, inv, self.is_dram) * 4 * A
        gatelkgCurrent += cmos_Ig_leakage(g_tp.w_comp_n, g_tp.w_comp_n, 1, inv, self.is_dram) * 4 * A

        tstep = (r2 * c2 + (r1 + r2) * c1) * sp.log(1.0 / VTHMUXNAND)
        m = g_tp.peri_global.Vdd / nextinputtime

        # TODO RELATIONAL
        # if tstep <= (0.5 * (g_tp.peri_global.Vdd - g_tp.peri_global.Vth) / m):
        #     a = m
        #     b = 2 * ((g_tp.peri_global.Vdd * VTHEVALINV) - g_tp.peri_global.Vth)
        #     c = -2 * tstep * (g_tp.peri_global.Vdd - g_tp.peri_global.Vth) + 1 / m * ((g_tp.peri_global.Vdd * VTHEVALINV) - g_tp.peri_global.Vth) * ((g_tp.peri_global.Vdd * VTHEVALINV) - g_tp.peri_global.Vth)
        #     Tcomparatorni = (-b + sp.sqrt(b * b - 4 * a * c)) / (2 * a)
        # else:
        Tcomparatorni = tstep + (g_tp.peri_global.Vdd + g_tp.peri_global.Vth) / (2 * m) - (g_tp.peri_global.Vdd * VTHEVALINV) / m

        self.delay_comparator = Tcomparatorni + st1del + st2del + st3del
        self.power_comparator.readOp.leakage = lkgCurrent * g_tp.peri_global.Vdd
        self.power_comparator.readOp.gate_leakage = gatelkgCurrent * g_tp.peri_global.Vdd

        return Tcomparatorni / (1.0 - VTHMUXNAND)
    
    def compute_power_energy(self):
        # For cam and FA, power.readOp is the plain read power, power.searchOp is the associative search related power
        # When search all subarrays and all mats are fully active
        # When plain read/write only one subarray in a single mat is active.

        # Add energy consumed in predecoder drivers. This unit is shared by all subarrays in a mat.
        if g_ip.is_3d_mem:
            if g_ip.print_detail_debug:
                print(f"mat.cc: subarray.num_cols = {self.subarray.num_cols}")

            self.power_bl_precharge_eq_drv.readOp.dynamic = self.bl_precharge_eq_drv.power.readOp.dynamic
            self.power_sa.readOp.dynamic *= self.subarray.num_cols
            self.power_bitline.readOp.dynamic *= self.subarray.num_cols
            self.power_subarray_out_drv.readOp.dynamic = (
                self.power_subarray_out_drv.readOp.dynamic * g_ip.io_width * g_ip.burst_depth
            )

            if g_ip.print_detail_debug:
                print(f"mat.cc: power_bl_precharge_eq_drv.readOp.dynamic = {self.power_bl_precharge_eq_drv.readOp.dynamic * 1e9} nJ")
                print(f"mat.cc: power_sa.readOp.dynamic = {self.power_sa.readOp.dynamic * 1e9} nJ")
                print(f"mat.cc: power_bitline.readOp.dynamic = {self.power_bitline.readOp.dynamic * 1e9} nJ")
                print(f"mat.cc: power_subarray_out_drv.readOp.dynamic = {self.power_subarray_out_drv.readOp.dynamic * 1e9} nJ")

            self.power.readOp.dynamic += (
                self.power_bl_precharge_eq_drv.readOp.dynamic +
                self.power_sa.readOp.dynamic +
                self.power_bitline.readOp.dynamic +
                self.power_subarray_out_drv.readOp.dynamic
            )

        else:  # is_3d_mem
            self.power.readOp.dynamic += (
                self.r_predec.power.readOp.dynamic +
                self.b_mux_predec.power.readOp.dynamic +
                self.sa_mux_lev_1_predec.power.readOp.dynamic +
                self.sa_mux_lev_2_predec.power.readOp.dynamic
            )

            # Add energy consumed in decoders
            self.power_row_decoders.readOp.dynamic = self.row_dec.power.readOp.dynamic
            if not (self.is_fa or self.pure_cam):
                self.power_row_decoders.readOp.dynamic *= self.num_subarrays_per_mat

            # Add energy consumed in bitline prechargers, SAs, and bitlines
            if not (self.is_fa or self.pure_cam):
                # Add energy consumed in bitline prechargers
                self.power_bl_precharge_eq_drv.readOp.dynamic = self.bl_precharge_eq_drv.power.readOp.dynamic
                self.power_bl_precharge_eq_drv.readOp.dynamic *= self.num_subarrays_per_mat

                # Add sense amps energy
                self.num_sa_subarray = self.subarray.num_cols / self.deg_bl_muxing
                self.power_sa.readOp.dynamic *= self.num_sa_subarray * self.num_subarrays_per_mat

                # Add energy consumed in bitlines
                self.power_bitline.readOp.dynamic *= self.num_subarrays_per_mat * self.subarray.num_cols
                self.power_bitline.writeOp.dynamic *= self.num_subarrays_per_mat * self.subarray.num_cols

                # Add subarray output energy
                self.power_subarray_out_drv.readOp.dynamic = (
                    (self.power_subarray_out_drv.readOp.dynamic + self.subarray_out_wire.power.readOp.dynamic) * self.num_do_b_mat
                )

                self.power.readOp.dynamic += (
                    self.power_bl_precharge_eq_drv.readOp.dynamic +
                    self.power_sa.readOp.dynamic +
                    self.power_bitline.readOp.dynamic +
                    self.power_subarray_out_drv.readOp.dynamic
                )

                self.power.readOp.dynamic += (
                    self.power_row_decoders.readOp.dynamic +
                    self.bit_mux_dec.power.readOp.dynamic +
                    self.sa_mux_lev_1_dec.power.readOp.dynamic +
                    self.sa_mux_lev_2_dec.power.readOp.dynamic +
                    self.power_comparator.readOp.dynamic
                )

            elif self.is_fa:
                # For plain read/write only one subarray in a mat is active
                # Add energy consumed in bitline prechargers
                self.power_bl_precharge_eq_drv.readOp.dynamic = (
                    self.bl_precharge_eq_drv.power.readOp.dynamic + self.cam_bl_precharge_eq_drv.power.readOp.dynamic
                )
                self.power_bl_precharge_eq_drv.searchOp.dynamic = self.bl_precharge_eq_drv.power.readOp.dynamic

                # Add sense amps energy
                self.num_sa_subarray = (self.subarray.num_cols_fa_cam + self.subarray.num_cols_fa_ram) / self.deg_bl_muxing
                self.num_sa_subarray_search = self.subarray.num_cols_fa_ram / self.deg_bl_muxing
                self.power_sa.searchOp.dynamic = self.power_sa.readOp.dynamic * self.num_sa_subarray_search
                self.power_sa.readOp.dynamic *= self.num_sa_subarray

                # Add energy consumed in bitlines
                self.power_bitline.searchOp.dynamic = self.power_bitline.readOp.dynamic
                self.power_bitline.readOp.dynamic *= (self.subarray.num_cols_fa_cam + self.subarray.num_cols_fa_ram)
                self.power_bitline.writeOp.dynamic *= (self.subarray.num_cols_fa_cam + self.subarray.num_cols_fa_ram)
                self.power_bitline.searchOp.dynamic *= self.subarray.num_cols_fa_ram

                # Add subarray output energy
                self.power_subarray_out_drv.searchOp.dynamic = (
                    (self.power_subarray_out_drv.readOp.dynamic + self.subarray_out_wire.power.readOp.dynamic) * self.num_so_b_mat
                )
                self.power_subarray_out_drv.readOp.dynamic = (
                    (self.power_subarray_out_drv.readOp.dynamic + self.subarray_out_wire.power.readOp.dynamic) * self.num_do_b_mat
                )

                self.power.readOp.dynamic += (
                    self.power_bl_precharge_eq_drv.readOp.dynamic +
                    self.power_sa.readOp.dynamic +
                    self.power_bitline.readOp.dynamic +
                    self.power_subarray_out_drv.readOp.dynamic
                )

                self.power.readOp.dynamic += (
                    self.power_row_decoders.readOp.dynamic +
                    self.bit_mux_dec.power.readOp.dynamic +
                    self.sa_mux_lev_1_dec.power.readOp.dynamic +
                    self.sa_mux_lev_2_dec.power.readOp.dynamic +
                    self.power_comparator.readOp.dynamic
                )

                # Add energy consumed inside cam
                self.power_matchline.searchOp.dynamic *= self.num_subarrays_per_mat
                self.power_searchline_precharge = self.sl_precharge_eq_drv.power
                self.power_searchline_precharge.searchOp.dynamic = self.power_searchline_precharge.readOp.dynamic * self.num_subarrays_per_mat
                self.power_searchline = self.sl_data_drv.power
                self.power_searchline.searchOp.dynamic = self.power_searchline.readOp.dynamic * self.subarray.num_cols_fa_cam * self.num_subarrays_per_mat
                self.power_matchline_precharge = self.ml_precharge_drv.power
                self.power_matchline_precharge.searchOp.dynamic = self.power_matchline_precharge.readOp.dynamic * self.num_subarrays_per_mat
                self.power_ml_to_ram_wl_drv = self.ml_to_ram_wl_drv.power
                self.power_ml_to_ram_wl_drv.searchOp.dynamic = self.ml_to_ram_wl_drv.power.readOp.dynamic

                self.power_cam_all_active.searchOp.dynamic = self.power_matchline.searchOp.dynamic
                self.power_cam_all_active.searchOp.dynamic += self.power_searchline_precharge.searchOp.dynamic
                self.power_cam_all_active.searchOp.dynamic += self.power_searchline.searchOp.dynamic
                self.power_cam_all_active.searchOp.dynamic += self.power_matchline_precharge.searchOp.dynamic

                self.power.searchOp.dynamic += self.power_cam_all_active.searchOp.dynamic

            else:
                # Add energy consumed in bitline prechargers
                self.power_bl_precharge_eq_drv.readOp.dynamic = self.cam_bl_precharge_eq_drv.power.readOp.dynamic

                # Add sense amps energy
                self.num_sa_subarray = self.subarray.num_cols_fa_cam / self.deg_bl_muxing
                self.power_sa.readOp.dynamic *= self.num_sa_subarray

                self.power_bitline.readOp.dynamic *= self.subarray.num_cols_fa_cam
                self.power_bitline.writeOp.dynamic *= self.subarray.num_cols_fa_cam

                self.power_subarray_out_drv.searchOp.dynamic = (
                    (self.power_subarray_out_drv.readOp.dynamic + self.subarray_out_wire.power.readOp.dynamic) * self.num_so_b_mat
                )
                self.power_subarray_out_drv.readOp.dynamic = (
                    (self.power_subarray_out_drv.readOp.dynamic + self.subarray_out_wire.power.readOp.dynamic) * self.num_do_b_mat
                )

                self.power.readOp.dynamic += (
                    self.power_bl_precharge_eq_drv.readOp.dynamic +
                    self.power_sa.readOp.dynamic +
                    self.power_bitline.readOp.dynamic +
                    self.power_subarray_out_drv.readOp.dynamic
                )

                self.power.readOp.dynamic += (
                    self.power_row_decoders.readOp.dynamic +
                    self.bit_mux_dec.power.readOp.dynamic +
                    self.sa_mux_lev_1_dec.power.readOp.dynamic +
                    self.sa_mux_lev_2_dec.power.readOp.dynamic +
                    self.power_comparator.readOp.dynamic
                )

                # Add energy consumed inside cam
                self.power_matchline.searchOp.dynamic *= self.num_subarrays_per_mat
                self.power_searchline_precharge = self.sl_precharge_eq_drv.power
                self.power_searchline_precharge.searchOp.dynamic = self.power_searchline_precharge.readOp.dynamic * self.num_subarrays_per_mat
                self.power_searchline = self.sl_data_drv.power
                self.power_searchline.searchOp.dynamic = self.power_searchline.readOp.dynamic * self.subarray.num_cols_fa_cam * self.num_subarrays_per_mat
                self.power_matchline_precharge = self.ml_precharge_drv.power
                self.power_matchline_precharge.searchOp.dynamic = self.power_matchline_precharge.readOp.dynamic * self.num_subarrays_per_mat
                self.power_ml_to_ram_wl_drv = self.ml_to_ram_wl_drv.power
                self.power_ml_to_ram_wl_drv.searchOp.dynamic = self.ml_to_ram_wl_drv.power.readOp.dynamic

                self.power_cam_all_active.searchOp.dynamic = self.power_matchline.searchOp.dynamic
                self.power_cam_all_active.searchOp.dynamic += self.power_searchline_precharge.searchOp.dynamic
                self.power_cam_all_active.searchOp.dynamic += self.power_searchline.searchOp.dynamic
                self.power_cam_all_active.searchOp.dynamic += self.power_matchline_precharge.searchOp.dynamic

                self.power.searchOp.dynamic += self.power_cam_all_active.searchOp.dynamic

        # Calculate leakage power
        if not (self.is_fa or self.pure_cam):
            self.number_output_drivers_subarray = self.num_sa_subarray / (self.dp.Ndsam_lev_1 * self.dp.Ndsam_lev_2)

            self.power_bitline.readOp.leakage *= self.subarray.num_rows * self.subarray.num_cols * self.num_subarrays_per_mat
            self.power_bl_precharge_eq_drv.readOp.leakage = self.bl_precharge_eq_drv.power.readOp.leakage * self.num_subarrays_per_mat
            self.power_sa.readOp.leakage *= self.num_sa_subarray * self.num_subarrays_per_mat * (self.RWP + self.ERP)

            self.power_subarray_out_drv.readOp.leakage = (
                (self.power_subarray_out_drv.readOp.leakage + self.subarray_out_wire.power.readOp.leakage) *
                self.number_output_drivers_subarray * self.num_subarrays_per_mat * (self.RWP + self.ERP)
            )

            self.power.readOp.leakage += (
                self.power_bitline.readOp.leakage +
                self.power_bl_precharge_eq_drv.readOp.leakage +
                self.power_sa.readOp.leakage +
                self.power_subarray_out_drv.readOp.leakage
            )

            self.power_comparator.readOp.leakage *= self.num_do_b_mat * (self.RWP + self.ERP)
            self.power.readOp.leakage += self.power_comparator.readOp.leakage

            self.array_leakage = self.power_bitline.readOp.leakage

            self.cl_leakage = (
                self.power_bl_precharge_eq_drv.readOp.leakage +
                self.power_sa.readOp.leakage +
                self.power_subarray_out_drv.readOp.leakage +
                self.power_comparator.readOp.leakage
            )

            # Decoder blocks
            self.power_row_decoders.readOp.leakage = self.row_dec.power.readOp.leakage * self.subarray.num_rows * self.num_subarrays_per_mat
            self.power_bit_mux_decoders.readOp.leakage = self.bit_mux_dec.power.readOp.leakage * self.deg_bl_muxing
            self.power_sa_mux_lev_1_decoders.readOp.leakage = self.sa_mux_lev_1_dec.power.readOp.leakage * self.dp.Ndsam_lev_1
            self.power_sa_mux_lev_2_decoders.readOp.leakage = self.sa_mux_lev_2_dec.power.readOp.leakage * self.dp.Ndsam_lev_2

            if not g_ip.wl_power_gated:
                self.power.readOp.leakage += (
                    self.r_predec.power.readOp.leakage +
                    self.b_mux_predec.power.readOp.leakage +
                    self.sa_mux_lev_1_predec.power.readOp.leakage +
                    self.sa_mux_lev_2_predec.power.readOp.leakage +
                    self.power_row_decoders.readOp.leakage +
                    self.power_bit_mux_decoders.readOp.leakage +
                    self.power_sa_mux_lev_1_decoders.readOp.leakage +
                    self.power_sa_mux_lev_2_decoders.readOp.leakage
                )
            else:
                self.power.readOp.leakage += (
                    (self.r_predec.power.readOp.leakage +
                     self.b_mux_predec.power.readOp.leakage +
                     self.sa_mux_lev_1_predec.power.readOp.leakage +
                     self.sa_mux_lev_2_predec.power.readOp.leakage +
                     self.power_row_decoders.readOp.leakage +
                     self.power_bit_mux_decoders.readOp.leakage +
                     self.power_sa_mux_lev_1_decoders.readOp.leakage +
                     self.power_sa_mux_lev_2_decoders.readOp.leakage) / g_tp.peri_global.Vdd * g_tp.peri_global.Vcc_min
                )

            self.wl_leakage = (
                self.r_predec.power.readOp.leakage +
                self.b_mux_predec.power.readOp.leakage +
                self.sa_mux_lev_1_predec.power.readOp.leakage +
                self.sa_mux_lev_2_predec.power.readOp.leakage +
                self.power_row_decoders.readOp.leakage +
                self.power_bit_mux_decoders.readOp.leakage +
                self.power_sa_mux_lev_1_decoders.readOp.leakage +
                self.power_sa_mux_lev_2_decoders.readOp.leakage
            )

            # Gate leakage
            self.power_bitline.readOp.gate_leakage *= self.subarray.num_rows * self.subarray.num_cols * self.num_subarrays_per_mat
            self.power_bl_precharge_eq_drv.readOp.gate_leakage = self.bl_precharge_eq_drv.power.readOp.gate_leakage * self.num_subarrays_per_mat
            self.power_sa.readOp.gate_leakage *= self.num_sa_subarray * self.num_subarrays_per_mat * (self.RWP + self.ERP)

            self.power_subarray_out_drv.readOp.gate_leakage = (
                (self.power_subarray_out_drv.readOp.gate_leakage + self.subarray_out_wire.power.readOp.gate_leakage) *
                self.number_output_drivers_subarray * self.num_subarrays_per_mat * (self.RWP + self.ERP)
            )

            self.power.readOp.gate_leakage += (
                self.power_bitline.readOp.gate_leakage +
                self.power_bl_precharge_eq_drv.readOp.gate_leakage +
                self.power_sa.readOp.gate_leakage +
                self.power_subarray_out_drv.readOp.gate_leakage
            )

            self.power_comparator.readOp.gate_leakage *= self.num_do_b_mat * (self.RWP + self.ERP)
            self.power.readOp.gate_leakage += self.power_comparator.readOp.gate_leakage

            if g_ip.power_gating:
                self.array_sleep_tx_area = self.sram_sleep_tx.area.get_area() * self.subarray.num_cols * self.num_subarrays_per_mat * self.dp.num_mats
                self.array_wakeup_e.readOp.dynamic = self.sram_sleep_tx.wakeup_power.readOp.dynamic * self.num_subarrays_per_mat * self.subarray.num_cols * self.dp.num_act_mats_hor_dir
                self.array_wakeup_t = self.sram_sleep_tx.wakeup_delay

                self.wl_sleep_tx_area = self.row_dec.sleeptx.area.get_area() * self.subarray.num_rows * self.num_subarrays_per_mat * self.dp.num_mats
                self.wl_wakeup_e.readOp.dynamic = self.row_dec.sleeptx.wakeup_power.readOp.dynamic * self.num_subarrays_per_mat * self.subarray.num_rows * self.dp.num_act_mats_hor_dir
                self.wl_wakeup_t = self.row_dec.sleeptx.wakeup_delay

            self.power_row_decoders.readOp.gate_leakage = self.row_dec.power.readOp.gate_leakage * self.subarray.num_rows * self.num_subarrays_per_mat
            self.power_bit_mux_decoders.readOp.gate_leakage = self.bit_mux_dec.power.readOp.gate_leakage * self.deg_bl_muxing
            self.power_sa_mux_lev_1_decoders.readOp.gate_leakage = self.sa_mux_lev_1_dec.power.readOp.gate_leakage * self.dp.Ndsam_lev_1
            self.power_sa_mux_lev_2_decoders.readOp.gate_leakage = self.sa_mux_lev_2_dec.power.readOp.gate_leakage * self.dp.Ndsam_lev_2

            self.power.readOp.gate_leakage += (
                self.r_predec.power.readOp.gate_leakage +
                self.b_mux_predec.power.readOp.gate_leakage +
                self.sa_mux_lev_1_predec.power.readOp.gate_leakage +
                self.sa_mux_lev_2_predec.power.readOp.gate_leakage +
                self.power_row_decoders.readOp.gate_leakage +
                self.power_bit_mux_decoders.readOp.gate_leakage +
                self.power_sa_mux_lev_1_decoders.readOp.gate_leakage +
                self.power_sa_mux_lev_2_decoders.readOp.gate_leakage
            )

        elif self.is_fa:
            self.number_output_drivers_subarray = self.num_sa_subarray

            self.power_bitline.readOp.leakage *= self.subarray.num_rows * self.subarray.num_cols * self.num_subarrays_per_mat
            self.power_bl_precharge_eq_drv.readOp.leakage = self.bl_precharge_eq_drv.power.readOp.leakage * self.num_subarrays_per_mat
            self.power_bl_precharge_eq_drv.searchOp.leakage = self.cam_bl_precharge_eq_drv.power.readOp.leakage * self.num_subarrays_per_mat
            self.power_sa.readOp.leakage *= self.num_sa_subarray * self.num_subarrays_per_mat * (self.RWP + self.ERP + self.SCHP)

            self.power_subarray_out_drv.readOp.leakage = (
                (self.power_subarray_out_drv.readOp.leakage + self.subarray_out_wire.power.readOp.leakage) *
                self.number_output_drivers_subarray * self.num_subarrays_per_mat * (self.RWP + self.ERP + self.SCHP)
            )

            self.power.readOp.leakage += (
                self.power_bitline.readOp.leakage +
                self.power_bl_precharge_eq_drv.readOp.leakage +
                self.power_bl_precharge_eq_drv.searchOp.leakage +
                self.power_sa.readOp.leakage +
                self.power_subarray_out_drv.readOp.leakage
            )

            self.power_row_decoders.readOp.leakage = self.row_dec.power.readOp.leakage * self.subarray.num_rows * self.num_subarrays_per_mat
            self.power.readOp.leakage += (
                self.r_predec.power.readOp.leakage +
                self.power_row_decoders.readOp.leakage
            )

            self.power_cam_all_active.searchOp.leakage = self.power_matchline.searchOp.leakage
            self.power_cam_all_active.searchOp.leakage += self.sl_precharge_eq_drv.power.readOp.leakage
            self.power_cam_all_active.searchOp.leakage += self.sl_data_drv.power.readOp.leakage * self.subarray.num_cols_fa_cam
            self.power_cam_all_active.searchOp.leakage += self.ml_precharge_drv.power.readOp.dynamic
            self.power_cam_all_active.searchOp.leakage *= self.num_subarrays_per_mat

            self.power.readOp.leakage += self.power_cam_all_active.searchOp.leakage

            self.power_bitline.readOp.gate_leakage *= self.subarray.num_rows * self.subarray.num_cols * self.num_subarrays_per_mat
            self.power_bl_precharge_eq_drv.readOp.gate_leakage = self.bl_precharge_eq_drv.power.readOp.gate_leakage * self.num_subarrays_per_mat
            self.power_bl_precharge_eq_drv.searchOp.gate_leakage = self.cam_bl_precharge_eq_drv.power.readOp.gate_leakage * self.num_subarrays_per_mat
            self.power_sa.readOp.gate_leakage *= self.num_sa_subarray * self.num_subarrays_per_mat * (self.RWP + self.ERP + self.SCHP)

            self.power_subarray_out_drv.readOp.gate_leakage = (
                (self.power_subarray_out_drv.readOp.gate_leakage + self.subarray_out_wire.power.readOp.gate_leakage) *
                self.number_output_drivers_subarray * self.num_subarrays_per_mat * (self.RWP + self.ERP + self.SCHP)
            )

            self.power.readOp.gate_leakage += (
                self.power_bitline.readOp.gate_leakage +
                self.power_bl_precharge_eq_drv.readOp.gate_leakage +
                self.power_bl_precharge_eq_drv.searchOp.gate_leakage +
                self.power_sa.readOp.gate_leakage +
                self.power_subarray_out_drv.readOp.gate_leakage
            )

            self.power_row_decoders.readOp.gate_leakage = self.row_dec.power.readOp.gate_leakage * self.subarray.num_rows * self.num_subarrays_per_mat
            self.power.readOp.gate_leakage += (
                self.r_predec.power.readOp.gate_leakage +
                self.power_row_decoders.readOp.gate_leakage
            )

            self.power_cam_all_active.searchOp.gate_leakage = self.power_matchline.searchOp.gate_leakage
            self.power_cam_all_active.searchOp.gate_leakage += self.sl_precharge_eq_drv.power.readOp.gate_leakage
            self.power_cam_all_active.searchOp.gate_leakage += self.sl_data_drv.power.readOp.gate_leakage * self.subarray.num_cols_fa_cam
            self.power_cam_all_active.searchOp.gate_leakage += self.ml_precharge_drv.power.readOp.dynamic
            self.power_cam_all_active.searchOp.gate_leakage *= self.num_subarrays_per_mat

            self.power.readOp.gate_leakage += self.power_cam_all_active.searchOp.gate_leakage

        else:
            self.number_output_drivers_subarray = self.num_sa_subarray

            self.power_bl_precharge_eq_drv.searchOp.leakage = self.cam_bl_precharge_eq_drv.power.readOp.leakage * self.num_subarrays_per_mat
            self.power_sa.readOp.leakage *= self.num_sa_subarray * self.num_subarrays_per_mat * (self.RWP + self.ERP + self.SCHP)

            self.power_subarray_out_drv.readOp.leakage = (
                (self.power_subarray_out_drv.readOp.leakage + self.subarray_out_wire.power.readOp.leakage) *
                self.number_output_drivers_subarray * self.num_subarrays_per_mat * (self.RWP + self.ERP + self.SCHP)
            )

            self.power.readOp.leakage += (
                self.power_bl_precharge_eq_drv.searchOp.leakage +
                self.power_sa.readOp.leakage +
                self.power_subarray_out_drv.readOp.leakage
            )

            self.power_row_decoders.readOp.leakage = self.row_dec.power.readOp.leakage * self.subarray.num_rows * self.num_subarrays_per_mat * (self.RWP + self.ERP + self.EWP)
            self.power.readOp.leakage += (
                self.r_predec.power.readOp.leakage +
                self.power_row_decoders.readOp.leakage
            )

            self.power_cam_all_active.searchOp.leakage = self.power_matchline.searchOp.leakage
            self.power_cam_all_active.searchOp.leakage += self.sl_precharge_eq_drv.power.readOp.leakage
            self.power_cam_all_active.searchOp.leakage += self.sl_data_drv.power.readOp.leakage * self.subarray.num_cols_fa_cam
            self.power_cam_all_active.searchOp.leakage += self.ml_precharge_drv.power.readOp.dynamic
            self.power_cam_all_active.searchOp.leakage *= self.num_subarrays_per_mat

            self.power.readOp.leakage += self.power_cam_all_active.searchOp.leakage

            self.power_bl_precharge_eq_drv.searchOp.gate_leakage = self.cam_bl_precharge_eq_drv.power.readOp.gate_leakage * self.num_subarrays_per_mat
            self.power_sa.readOp.gate_leakage *= self.num_sa_subarray * self.num_subarrays_per_mat * (self.RWP + self.ERP + self.SCHP)

            self.power_subarray_out_drv.readOp.gate_leakage = (
                (self.power_subarray_out_drv.readOp.gate_leakage + self.subarray_out_wire.power.readOp.gate_leakage) *
                self.number_output_drivers_subarray * self.num_subarrays_per_mat * (self.RWP + self.ERP + self.SCHP)
            )

            self.power.readOp.gate_leakage += (
                self.power_bl_precharge_eq_drv.searchOp.gate_leakage +
                self.power_sa.readOp.gate_leakage +
                self.power_subarray_out_drv.readOp.gate_leakage
            )

            self.power_row_decoders.readOp.gate_leakage = self.row_dec.power.readOp.gate_leakage * self.subarray.num_rows * self.num_subarrays_per_mat * (self.RWP + self.ERP + self.EWP)
            self.power.readOp.gate_leakage += (
                self.r_predec.power.readOp.gate_leakage +
                self.power_row_decoders.readOp.gate_leakage
            )

            self.power_cam_all_active.searchOp.gate_leakage = self.power_matchline.searchOp.gate_leakage
            self.power_cam_all_active.searchOp.gate_leakage += self.sl_precharge_eq_drv.power.readOp.gate_leakage
            self.power_cam_all_active.searchOp.gate_leakage += self.sl_data_drv.power.readOp.gate_leakage * self.subarray.num_cols_fa_cam
            self.power_cam_all_active.searchOp.gate_leakage += self.ml_precharge_drv.power.readOp.dynamic
            self.power_cam_all_active.searchOp.gate_leakage *= self.num_subarrays_per_mat

            self.power.readOp.gate_leakage += self.power_cam_all_active.searchOp.gate_leakage
    
    


