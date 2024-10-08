import math
import time

from .area import Area
from . import parameter
from .parameter import _log2
from .cacti_interface import *
from .powergating import *
from .component import Component
from .powergating import SleepTx
from .parameter import g_tp

class Decoder(Component):
    def __init__(self, g_ip, _num_dec_signals, flag_way_select, _C_ld_dec_out, _R_wire_dec_out, fully_assoc_, is_dram_, is_wl_tr_, cell_):
        super().__init__()
        self.g_ip = g_ip
        self.exist = False
        self.C_ld_dec_out = _C_ld_dec_out
        self.R_wire_dec_out = _R_wire_dec_out
        self.num_gates = 0
        self.num_gates_min = 2
        self.delay = 0
        self.fully_assoc = fully_assoc_
        self.is_dram = is_dram_
        self.is_wl_tr = is_wl_tr_
        self.total_driver_nwidth = 0
        self.total_driver_pwidth = 0
        self.cell = cell_
        self.nodes_DSTN = 1

        self.w_dec_n = [0] * MAX_NUMBER_GATES_STAGE
        self.w_dec_p = [0] * MAX_NUMBER_GATES_STAGE

        num_addr_bits_dec = _log2(_num_dec_signals)

        # Relational
        # if num_addr_bits_dec < 4:
        #     if flag_way_select:
        #         self.exist = True
        #         self.num_in_signals = 2
        #     else:
        #         self.num_in_signals = 0
        # else:
        #     self.exist = True
        #     if flag_way_select:
        #         self.num_in_signals = 3
        #     else:
        #         self.num_in_signals = 2

        if self.g_ip.use_piecewise:
            self.num_in_signals = sp.Piecewise(
                (2, sp.And(num_addr_bits_dec < 4, flag_way_select != 0)),  # self.num_in_signals = 2 if num_addr_bits_dec < 4 and flag_way_select
                (0, sp.And(num_addr_bits_dec < 4, flag_way_select == 0)),  # self.num_in_signals = 0 if num_addr_bits_dec < 4 and not flag_way_select
                (3, sp.And(num_addr_bits_dec >= 4, flag_way_select != 0)),  # self.num_in_signals = 3 if num_addr_bits_dec >= 4 and flag_way_select
                (2, True)  # self.num_in_signals = 2 if num_addr_bits_dec >= 4 and not flag_way_select
            )
        else:
            self.num_in_signals = 2

        # assert self.cell.h > 0
        # assert self.cell.w > 0
        self.area.h = g_tp.h_dec * self.cell.h

        self.compute_widths()
        self.compute_area()

    def compute_widths(self):
        p_to_n_sz_ratio = parameter.pmos_to_nmos_sz_ratio(self.is_dram, self.is_wl_tr)
        gnand2 = (2 + p_to_n_sz_ratio) / (1 + p_to_n_sz_ratio)
        gnand3 = (3 + p_to_n_sz_ratio) / (1 + p_to_n_sz_ratio)

        if self.exist:
            if self.num_in_signals == 2 or self.fully_assoc:
                self.w_dec_n[0] = 2 * g_tp.min_w_nmos_
                self.w_dec_p[0] = p_to_n_sz_ratio * g_tp.min_w_nmos_
                F = gnand2
            else:
                self.w_dec_n[0] = 3 * g_tp.min_w_nmos_
                self.w_dec_p[0] = p_to_n_sz_ratio * g_tp.min_w_nmos_
                F = gnand3

            F *= self.C_ld_dec_out / (gate_C(self.w_dec_n[0], 0, self.is_dram, False, self.is_wl_tr) +
                                      gate_C(self.w_dec_p[0], 0, self.is_dram, False, self.is_wl_tr))
            
            # print("Made it to Decoder Logical Effort")
            self.num_gates = logical_effort(
                self.num_gates_min,
                gnand2 if self.num_in_signals == 2 else gnand3,
                F,
                self.w_dec_n,
                self.w_dec_p,
                self.C_ld_dec_out,
                p_to_n_sz_ratio,
                self.is_dram,
                self.is_wl_tr,
                g_tp.max_w_nmos_dec
            )
            # print("Made it past Decoder Logical Effort")

    def compute_area(self):
        cumulative_area = 0
        cumulative_curr = 0
        cumulative_curr_Ig = 0

        if self.exist:
            if self.num_in_signals == 2:
                cumulative_area = compute_gate_area(self.g_ip, NAND, 2, self.w_dec_p[0], self.w_dec_n[0], self.area.h)
                cumulative_curr = cmos_Isub_leakage(self.w_dec_n[0], self.w_dec_p[0], 2, nand, self.is_dram)
                cumulative_curr_Ig = cmos_Ig_leakage(self.w_dec_n[0], self.w_dec_p[0], 2, nand, self.is_dram)
            elif self.num_in_signals == 3:
                cumulative_area = compute_gate_area(self.g_ip, NAND, 3, self.w_dec_p[0], self.w_dec_n[0], self.area.h)
                cumulative_curr = cmos_Isub_leakage(self.w_dec_n[0], self.w_dec_p[0], 3, nand, self.is_dram)
                cumulative_curr_Ig = cmos_Ig_leakage(self.w_dec_n[0], self.w_dec_p[0], 3, nand, self.is_dram)

            for i in range(1, self.num_gates):
                cumulative_area += compute_gate_area(self.g_ip, INV, 1, self.w_dec_p[i], self.w_dec_n[i], self.area.h)
                cumulative_curr += cmos_Isub_leakage(self.w_dec_n[i], self.w_dec_p[i], 1, inv, self.is_dram)
                cumulative_curr_Ig += cmos_Ig_leakage(self.w_dec_n[i], self.w_dec_p[i], 1, inv, self.is_dram)

            self.power.readOp.leakage = cumulative_curr * g_tp.peri_global.Vdd
            self.power.readOp.gate_leakage = cumulative_curr_Ig * g_tp.peri_global.Vdd

            self.area.w = cumulative_area / self.area.h

    def compute_power_gating(self):
        for i in range(1, self.num_gates):
            self.total_driver_nwidth += self.w_dec_n[i]
            self.total_driver_pwidth += self.w_dec_p[i]

        is_footer = False
        Isat_subarray = simplified_nmos_Isat(self.total_driver_nwidth)
        detalV = g_tp.peri_global.Vdd - g_tp.peri_global.Vcc_min
        c_wakeup = drain_C_(self.total_driver_pwidth, PCH, 1, 1, self.cell.h)

        if self.g_ip.power_gating:
            self.sleeptx = SleepTx(
                self.g_ip.perfloss,
                Isat_subarray,
                is_footer,
                c_wakeup,
                detalV,
                self.nodes_DSTN,
                self.area
            )

    def compute_delays(self, inrisetime):
        if not self.exist:
            return 0.0

        ret_val = 0
        rd = tr_R_on(self.w_dec_n[0], NCH, self.num_in_signals, self.is_dram, False, self.is_wl_tr)
        c_load = gate_C(self.w_dec_n[1] + self.w_dec_p[1], 0.0, self.is_dram, False, self.is_wl_tr)
        c_intrinsic = drain_C_(self.w_dec_p[0], PCH, 1, 1, self.area.h, self.is_dram, False, self.is_wl_tr) * self.num_in_signals + \
                      drain_C_(self.w_dec_n[0], NCH, self.num_in_signals, 1, self.area.h, self.is_dram, False, self.is_wl_tr)
        tf = rd * (c_intrinsic + c_load)
        this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
        self.delay += this_delay
        inrisetime = this_delay / (1.0 - 0.5)
        self.power.readOp.dynamic += (c_load + c_intrinsic) * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd

        for i in range(1, self.num_gates - 1):
            rd = tr_R_on(self.w_dec_n[i], NCH, 1, self.is_dram, False, self.is_wl_tr)
            c_load = gate_C(self.w_dec_p[i + 1] + self.w_dec_n[i + 1], 0.0, self.is_dram, False, self.is_wl_tr)
            c_intrinsic = drain_C_(self.w_dec_p[i], PCH, 1, 1, self.area.h, self.is_dram, False, self.is_wl_tr) + \
                          drain_C_(self.w_dec_n[i], NCH, 1, 1, self.area.h, self.is_dram, False, self.is_wl_tr)
            tf = rd * (c_intrinsic + c_load)
            this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
            self.delay += this_delay
            inrisetime = this_delay / (1.0 - 0.5)
            self.power.readOp.dynamic += (c_load + c_intrinsic) * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd

        i = self.num_gates - 1
        c_load = self.C_ld_dec_out
        rd = tr_R_on(self.w_dec_n[i], NCH, 1, self.is_dram, False, self.is_wl_tr)
        c_intrinsic = drain_C_(self.w_dec_p[i], PCH, 1, 1, self.area.h, self.is_dram, False, self.is_wl_tr) + \
                      drain_C_(self.w_dec_n[i], NCH, 1, 1, self.area.h, self.is_dram, False, self.is_wl_tr)
        tf = rd * (c_intrinsic + c_load) + self.R_wire_dec_out * c_load / 2
        this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
        self.delay += this_delay
        ret_val = this_delay / (1.0 - 0.5)
        self.power.readOp.dynamic += c_load * g_tp.vpp * g_tp.vpp + c_intrinsic * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd

        self.compute_power_gating()
        return ret_val

    def leakage_feedback(self, temperature):
        cumulative_curr = 0
        cumulative_curr_Ig = 0

        if self.exist:
            if self.num_in_signals == 2:
                cumulative_curr = cmos_Isub_leakage(self.w_dec_n[0], self.w_dec_p[0], 2, nand, self.is_dram)
                cumulative_curr_Ig = cmos_Ig_leakage(self.w_dec_n[0], self.w_dec_p[0], 2, nand, self.is_dram)
            elif self.num_in_signals == 3:
                cumulative_curr = cmos_Isub_leakage(self.w_dec_n[0], self.w_dec_p[0], 3, nand, self.is_dram)
                cumulative_curr_Ig = cmos_Ig_leakage(self.w_dec_n[0], self.w_dec_p[0], 3, nand, self.is_dram)

            for i in range(1, self.num_gates):
                cumulative_curr += cmos_Isub_leakage(self.w_dec_n[i], self.w_dec_p[i], 1, inv, self.is_dram)
                cumulative_curr_Ig += cmos_Ig_leakage(self.w_dec_n[i], self.w_dec_p[i], 1, inv, self.is_dram)

            self.power.readOp.leakage = cumulative_curr * g_tp.peri_global.Vdd
            self.power.readOp.gate_leakage = cumulative_curr_Ig * g_tp.peri_global.Vdd

class PredecBlk(Component):
    def __init__(self, g_ip, num_dec_signals, dec_, C_wire_predec_blk_out, R_wire_predec_blk_out_, num_dec_per_predec, is_dram, is_blk1):
        super().__init__()
        self.g_ip = g_ip
        self.dec = dec_
        self.exist = False
        self.number_input_addr_bits = 0
        self.C_ld_predec_blk_out = 0
        self.R_wire_predec_blk_out = 0
        self.branch_effort_nand2_gate_output = 1
        self.branch_effort_nand3_gate_output = 1
        self.flag_two_unique_paths = False
        self.flag_L2_gate = 0
        self.number_inputs_L1_gate = 0
        self.number_gates_L1_nand2_path = 0
        self.number_gates_L1_nand3_path = 0
        self.number_gates_L2 = 0
        self.min_number_gates_L1 = 2
        self.min_number_gates_L2 = 2
        self.num_L1_active_nand2_path = 0
        self.num_L1_active_nand3_path = 0
        self.delay_nand2_path = 0
        self.delay_nand3_path = 0
        self.power_nand2_path = PowerDef()
        self.power_nand3_path = PowerDef()
        self.power_L2 = PowerDef()
        self.is_dram_ = is_dram

        # check converted from int to math.ceil and added check
        num_dec_signals = math.ceil(num_dec_signals)

        if(num_dec_signals < 1):
            num_dec_signals = 4

        num_addr_bits_dec = sp.log(num_dec_signals, 2)
        blk1_num_input_addr_bits = (num_addr_bits_dec + 1) // 2
        blk2_num_input_addr_bits = num_addr_bits_dec - blk1_num_input_addr_bits

        # debug
        self.debug_num_addr_bits_dec = num_addr_bits_dec
        self.debug_blk1_num_input_addr_bits = blk1_num_input_addr_bits
        self.debug_blk2_num_input_addr_bits = blk2_num_input_addr_bits
        #

        self.w_L1_nand2_n = [0] * MAX_NUMBER_GATES_STAGE
        self.w_L1_nand2_p = [0] * MAX_NUMBER_GATES_STAGE
        self.w_L1_nand3_n = [0] * MAX_NUMBER_GATES_STAGE
        self.w_L1_nand3_p = [0] * MAX_NUMBER_GATES_STAGE
        self.w_L2_n = [0] * MAX_NUMBER_GATES_STAGE
        self.w_L2_p = [0] * MAX_NUMBER_GATES_STAGE

        # CHANGE: RELATIONAL: set to default values, otherwise, expression will be too long
        # if is_blk1:
        #     if num_addr_bits_dec <= 0:
        #         return
        #     elif num_addr_bits_dec < 4:
        #         self.exist = True
        #         self.number_input_addr_bits = num_addr_bits_dec
        #         self.R_wire_predec_blk_out = self.dec.R_wire_dec_out
        #         self.C_ld_predec_blk_out = self.dec.C_ld_dec_out
        #     else:
        #         self.exist = True
        #         self.number_input_addr_bits = blk1_num_input_addr_bits
        #         branch_effort_predec_out = (1 << blk2_num_input_addr_bits)
        #         C_ld_dec_gate = num_dec_per_predec * gate_C(self.dec.w_dec_n[0] + self.dec.w_dec_p[0], 0, self.is_dram_, False, False)
        #         self.R_wire_predec_blk_out = R_wire_predec_blk_out_
        #         self.C_ld_predec_blk_out = branch_effort_predec_out * C_ld_dec_gate + C_wire_predec_blk_out
        # else:
        #     if num_addr_bits_dec >= 4:

        self.exist = True
        self.number_input_addr_bits = blk2_num_input_addr_bits
        branch_effort_predec_out = sp.Pow(2, blk1_num_input_addr_bits) #(1 << blk1_num_input_addr_bits)
        C_ld_dec_gate = num_dec_per_predec * parameter.gate_C(self.dec.w_dec_n[0] + self.dec.w_dec_p[0], 0, self.is_dram_, False, False)
        self.R_wire_predec_blk_out = R_wire_predec_blk_out_
        self.C_ld_predec_blk_out = branch_effort_predec_out * C_ld_dec_gate + C_wire_predec_blk_out

        # self.exist = sp.Piecewise(
        #     (self.exist, sp.And(is_blk1, num_addr_bits_dec <= 0)),
        #     (True, True)
        # )

        # self.number_input_addr_bits = sp.Piecewise(
        #     (num_addr_bits_dec, sp.And(is_blk1, num_addr_bits_dec < 4)),  # self.number_input_addr_bits = num_addr_bits_dec if is_blk1 and 0 < num_addr_bits_dec < 4
        #     (blk1_num_input_addr_bits, sp.And(is_blk1, num_addr_bits_dec >= 4)),  # self.number_input_addr_bits = blk1_num_input_addr_bits if is_blk1 and num_addr_bits_dec >= 4
        #     (blk2_num_input_addr_bits, True)  # self.number_input_addr_bits = blk2_num_input_addr_bits if not is_blk1
        # )

        # branch_effort_predec_out = sp.Piecewise(
        #     (sp.Pow(2, blk2_num_input_addr_bits), sp.And(is_blk1, num_addr_bits_dec >= 4)),  # branch_effort_predec_out = 2^blk2_num_input_addr_bits if is_blk1 and num_addr_bits_dec >= 4
        #     (sp.Pow(2, blk1_num_input_addr_bits), True)
        # )

        # C_ld_dec_gate = sp.Piecewise(
        #     (num_dec_per_predec * gate_C(self.dec.w_dec_n[0] + self.dec.w_dec_p[0], 0, self.is_dram_, False, False),
        #     num_addr_bits_dec >= 4), # C_ld_dec_gate calculation based on conditions
        #     (1, True)  # C_ld_dec_gate = 13/10 if num_addr_bits_dec <= 0
        # )

        # self.R_wire_predec_blk_out = sp.Piecewise(
        #     (self.dec.R_wire_dec_out, num_addr_bits_dec < 4),  # self.R_wire_predec_blk_out based on conditions
        #     (R_wire_predec_blk_out_, True),  # self.R_wire_predec_blk_out = 3/2 if num_addr_bits_dec <= 0
        # )

        # self.C_ld_predec_blk_out = sp.Piecewise(
        #     (self.dec.C_ld_dec_out, num_addr_bits_dec < 4),  # self.C_ld_predec_blk_out based on conditions
        #     (branch_effort_predec_out * C_ld_dec_gate + C_wire_predec_blk_out, True)  # self.C_ld_predec_blk_out = 13/10 if num_addr_bits_dec <= 0
        # )

        self.compute_widths()
        self.compute_area()

    def compute_widths(self):
        if not self.exist:
            return

        p_to_n_sz_ratio = parameter.pmos_to_nmos_sz_ratio(self.is_dram_)
        gnand2 = (2 + p_to_n_sz_ratio) / (1 + p_to_n_sz_ratio)
        gnand3 = (3 + p_to_n_sz_ratio) / (1 + p_to_n_sz_ratio)

        flag_L2_gate = 0
        number_inputs_L1_gate = 0

        if self.number_input_addr_bits == 1:
            flag_two_unique_paths = False
            number_inputs_L1_gate = 2
            flag_L2_gate = 0
        elif self.number_input_addr_bits == 2:
            flag_two_unique_paths = False
            number_inputs_L1_gate = 2
            flag_L2_gate = 0
        elif self.number_input_addr_bits == 3:
            flag_two_unique_paths = False
            number_inputs_L1_gate = 3
            flag_L2_gate = 0
        elif self.number_input_addr_bits == 4:
            flag_two_unique_paths = False
            number_inputs_L1_gate = 2
            flag_L2_gate = 2
            branch_effort_nand2_gate_output = 4
        elif self.number_input_addr_bits == 5:
            flag_two_unique_paths = True
            flag_L2_gate = 2
            branch_effort_nand2_gate_output = 8
            branch_effort_nand3_gate_output = 4
        elif self.number_input_addr_bits == 6:
            flag_two_unique_paths = False
            number_inputs_L1_gate = 3
            flag_L2_gate = 2
            branch_effort_nand3_gate_output = 8
        elif self.number_input_addr_bits == 7:
            flag_two_unique_paths = True
            flag_L2_gate = 3
            branch_effort_nand2_gate_output = 32
            branch_effort_nand3_gate_output = 16
        elif self.number_input_addr_bits == 8:
            flag_two_unique_paths = True
            flag_L2_gate = 3
            branch_effort_nand2_gate_output = 64
            branch_effort_nand3_gate_output = 32
        elif self.number_input_addr_bits == 9:
            flag_two_unique_paths = False
            number_inputs_L1_gate = 3
            flag_L2_gate = 3
            branch_effort_nand3_gate_output = 64
        else:
            flag_two_unique_paths = False
            number_inputs_L1_gate = 2
            flag_L2_gate = 2
            branch_effort_nand2_gate_output = 4

        self.flag_two_unique_paths = flag_two_unique_paths
        self.number_inputs_L1_gate = number_inputs_L1_gate
        self.flag_L2_gate = flag_L2_gate

        if flag_L2_gate:
            if flag_L2_gate == 2:
                self.w_L2_n[0] = 2 * g_tp.min_w_nmos_
                F = gnand2
            else:
                self.w_L2_n[0] = 3 * g_tp.min_w_nmos_
                F = gnand3
            self.w_L2_p[0] = p_to_n_sz_ratio * g_tp.min_w_nmos_
            F *= self.C_ld_predec_blk_out / (
                parameter.gate_C(self.w_L2_n[0], 0, self.is_dram_)
                + parameter.gate_C(self.w_L2_p[0], 0, self.is_dram_)
            )
            self.number_gates_L2 = logical_effort(
                self.min_number_gates_L2,
                gnand2 if flag_L2_gate == 2 else gnand3,
                F,
                self.w_L2_n,
                self.w_L2_p,
                self.C_ld_predec_blk_out,
                p_to_n_sz_ratio,
                self.is_dram_, False,
                g_tp.max_w_nmos_
            )

            if self.flag_two_unique_paths or self.number_inputs_L1_gate == 2:
                c_load_nand2_path = branch_effort_nand2_gate_output * (
                    parameter.gate_C(self.w_L2_n[0], 0, self.is_dram_)
                    + parameter.gate_C(self.w_L2_p[0], 0, self.is_dram_)
                )
                self.w_L1_nand2_n[0] = 2 * g_tp.min_w_nmos_
                self.w_L1_nand2_p[0] = p_to_n_sz_ratio * g_tp.min_w_nmos_
                F = (
                    gnand2
                    * c_load_nand2_path
                    / (
                        parameter.gate_C(self.w_L1_nand2_n[0], 0, self.is_dram_)
                        + parameter.gate_C(self.w_L1_nand2_p[0], 0, self.is_dram_)
                    )
                )
                self.number_gates_L1_nand2_path = logical_effort(
                    self.min_number_gates_L1,
                    gnand2,
                    F,
                    self.w_L1_nand2_n,
                    self.w_L1_nand2_p,
                    c_load_nand2_path,
                    p_to_n_sz_ratio,
                    self.is_dram_, False,
                    g_tp.max_w_nmos_
                )

            if self.flag_two_unique_paths or self.number_inputs_L1_gate == 3:
                c_load_nand3_path = branch_effort_nand3_gate_output * \
                                    (gate_C(self.w_L2_n[0], 0, self.is_dram_) + gate_C(self.w_L2_p[0], 0, self.is_dram_))
                self.w_L1_nand3_n[0] = 3 * g_tp.min_w_nmos_
                self.w_L1_nand3_p[0] = p_to_n_sz_ratio * g_tp.min_w_nmos_
                F = (
                    gnand3
                    * c_load_nand3_path
                    / (
                        parameter.gate_C(self.w_L1_nand3_n[0], 0, self.is_dram_)
                        + parameter.gate_C(self.w_L1_nand3_p[0], 0, self.is_dram_)
                    )
                )
                self.number_gates_L1_nand3_path = logical_effort(
                    self.min_number_gates_L1,
                    gnand3,
                    F,
                    self.w_L1_nand3_n,
                    self.w_L1_nand3_p,
                    c_load_nand3_path,
                    p_to_n_sz_ratio,
                    self.is_dram_, False,
                    g_tp.max_w_nmos_
                )
        else:
            if self.number_inputs_L1_gate == 2:
                self.w_L1_nand2_n[0] = 2 * g_tp.min_w_nmos_
                self.w_L1_nand2_p[0] = p_to_n_sz_ratio * g_tp.min_w_nmos_
                F = gnand2 * self.C_ld_predec_blk_out / (gate_C(self.w_L1_nand2_n[0], 0, self.is_dram_) + gate_C(self.w_L1_nand2_p[0], 0, self.is_dram_))
                self.number_gates_L1_nand2_path = logical_effort(
                    self.min_number_gates_L1,
                    gnand2,
                    F,
                    self.w_L1_nand2_n,
                    self.w_L1_nand2_p,
                    self.C_ld_predec_blk_out,
                    p_to_n_sz_ratio,
                    self.is_dram_, False,
                    g_tp.max_w_nmos_
                )
            elif self.number_inputs_L1_gate == 3:
                self.w_L1_nand3_n[0] = 3 * g_tp.min_w_nmos_
                self.w_L1_nand3_p[0] = p_to_n_sz_ratio * g_tp.min_w_nmos_
                F = gnand3 * self.C_ld_predec_blk_out / (gate_C(self.w_L1_nand3_n[0], 0, self.is_dram_) + gate_C(self.w_L1_nand3_p[0], 0, self.is_dram_))
                self.number_gates_L1_nand3_path = logical_effort(
                    self.min_number_gates_L1,
                    gnand3,
                    F,
                    self.w_L1_nand3_n,
                    self.w_L1_nand3_p,
                    self.C_ld_predec_blk_out,
                    p_to_n_sz_ratio,
                    self.is_dram_, False,
                    g_tp.max_w_nmos_
                )

    def compute_area(self):
        if self.exist:
            num_L1_nand2 = 0
            num_L1_nand3 = 0
            num_L2 = 0
            tot_area_L1_nand3 = 0
            leak_L1_nand3 = 0
            gate_leak_L1_nand3 = 0

            tot_area_L1_nand2 = compute_gate_area(self.g_ip, NAND, 2, self.w_L1_nand2_p[0], self.w_L1_nand2_n[0], g_tp.cell_h_def)
            leak_L1_nand2 = parameter.cmos_Isub_leakage(self.w_L1_nand2_n[0], self.w_L1_nand2_p[0], 2, nand, self.is_dram_)
            gate_leak_L1_nand2 = parameter.cmos_Ig_leakage(
                self.w_L1_nand2_n[0], self.w_L1_nand2_p[0], 2, nand, self.is_dram_
            )

            if self.number_inputs_L1_gate != 3:
                tot_area_L1_nand3 = 0
                leak_L1_nand3 = 0
                gate_leak_L1_nand3 = 0
            else:
                tot_area_L1_nand3 = compute_gate_area(self.g_ip, NAND, 3, self.w_L1_nand3_p[0], self.w_L1_nand3_n[0], g_tp.cell_h_def)
                leak_L1_nand3 = cmos_Isub_leakage(self.w_L1_nand3_n[0], self.w_L1_nand3_p[0], 3, nand)
                gate_leak_L1_nand3 = cmos_Ig_leakage(self.w_L1_nand3_n[0], self.w_L1_nand3_p[0], 3, nand)

            if self.number_input_addr_bits == 1:
                num_L1_nand2 = 2
                num_L2 = 0
                self.num_L1_active_nand2_path = 1
                self.num_L1_active_nand3_path = 0
            elif self.number_input_addr_bits == 2:
                num_L1_nand2 = 4
                num_L2 = 0
                self.num_L1_active_nand2_path = 1
                self.num_L1_active_nand3_path = 0
            elif self.number_input_addr_bits == 3:
                num_L1_nand3 = 8
                num_L2 = 0
                self.num_L1_active_nand2_path = 0
                self.num_L1_active_nand3_path = 1
            elif self.number_input_addr_bits == 4:
                num_L1_nand2 = 8
                num_L2 = 16
                self.num_L1_active_nand2_path = 2
                self.num_L1_active_nand3_path = 0
            elif self.number_input_addr_bits == 5:
                num_L1_nand2 = 4
                num_L1_nand3 = 8
                num_L2 = 32
                self.num_L1_active_nand2_path = 1
                self.num_L1_active_nand3_path = 1
            elif self.number_input_addr_bits == 6:
                num_L1_nand3 = 16
                num_L2 = 64
                self.num_L1_active_nand2_path = 0
                self.num_L1_active_nand3_path = 2
            elif self.number_input_addr_bits == 7:
                num_L1_nand2 = 8
                num_L1_nand3 = 8
                num_L2 = 128
                self.num_L1_active_nand2_path = 2
                self.num_L1_active_nand3_path = 1
            elif self.number_input_addr_bits == 8:
                num_L1_nand2 = 4
                num_L1_nand3 = 16
                num_L2 = 256
                self.num_L1_active_nand2_path = 2
                self.num_L1_active_nand3_path = 2
            elif self.number_input_addr_bits == 9:
                num_L1_nand3 = 24
                num_L2 = 512
                self.num_L1_active_nand2_path = 0
                self.num_L1_active_nand3_path = 3

            for i in range(1, self.number_gates_L1_nand2_path):
                tot_area_L1_nand2 += compute_gate_area(self.g_ip, INV, 1, self.w_L1_nand2_p[i], self.w_L1_nand2_n[i], g_tp.cell_h_def)
                leak_L1_nand2 += parameter.cmos_Isub_leakage(self.w_L1_nand2_n[i], self.w_L1_nand2_p[i], 2, nand, self.is_dram_)
                gate_leak_L1_nand2 += parameter.cmos_Ig_leakage(
                    self.w_L1_nand2_n[i], self.w_L1_nand2_p[i], 2, nand, self.is_dram_
                )

            tot_area_L1_nand2 *= num_L1_nand2
            leak_L1_nand2 *= num_L1_nand2
            gate_leak_L1_nand2 *= num_L1_nand2

            for i in range(1, self.number_gates_L1_nand3_path):
                tot_area_L1_nand3 += compute_gate_area(self.g_ip, INV, 1, self.w_L1_nand3_p[i], self.w_L1_nand3_n[i], g_tp.cell_h_def)
                leak_L1_nand3 += cmos_Isub_leakage(self.w_L1_nand3_n[i], self.w_L1_nand3_p[i], 3, nand, self.is_dram_)
                gate_leak_L1_nand3 += cmos_Ig_leakage(self.w_L1_nand3_n[i], self.w_L1_nand3_p[i], 3, nand, self.is_dram_)

            tot_area_L1_nand3 *= num_L1_nand3
            leak_L1_nand3 *= num_L1_nand3
            gate_leak_L1_nand3 *= num_L1_nand3

            cumulative_area_L1 = tot_area_L1_nand2 + tot_area_L1_nand3
            cumulative_area_L2 = 0.0
            leakage_L2 = 0.0
            gate_leakage_L2 = 0.0

            if self.flag_L2_gate == 2:
                cumulative_area_L2 = compute_gate_area(self.g_ip, NAND, 2, self.w_L2_p[0], self.w_L2_n[0], g_tp.cell_h_def)
                leakage_L2 = parameter.cmos_Isub_leakage(self.w_L2_n[0], self.w_L2_p[0], 2, nand, self.is_dram_)
                gate_leakage_L2 = parameter.cmos_Ig_leakage(
                    self.w_L2_n[0], self.w_L2_p[0], 2, nand, self.is_dram_
                )
            elif self.flag_L2_gate == 3:
                cumulative_area_L2 = compute_gate_area(self.g_ip, NAND, 3, self.w_L2_p[0], self.w_L2_n[0], g_tp.cell_h_def)
                leakage_L2 = parameter.cmos_Isub_leakage(self.w_L2_n[0], self.w_L2_p[0], 3, nand, self.is_dram_)
                gate_leakage_L2 = parameter.cmos_Ig_leakage(
                    self.w_L2_n[0], self.w_L2_p[0], 3, nand, self.is_dram_
                )

            for i in range(1, self.number_gates_L2):
                cumulative_area_L2 += compute_gate_area(self.g_ip, INV, 1, self.w_L2_p[i], self.w_L2_n[i], g_tp.cell_h_def)
                leakage_L2 += parameter.cmos_Isub_leakage(
                    self.w_L2_n[i], self.w_L2_p[i], 2, inv, self.is_dram_
                )
                gate_leakage_L2 += parameter.cmos_Ig_leakage(
                    self.w_L2_n[i], self.w_L2_p[i], 2, inv, self.is_dram_
                )

            cumulative_area_L2 *= num_L2
            leakage_L2 *= num_L2
            gate_leakage_L2 *= num_L2

            self.power_nand2_path.readOp.leakage = leak_L1_nand2 * g_tp.peri_global.Vdd
            self.power_nand3_path.readOp.leakage = leak_L1_nand3 * g_tp.peri_global.Vdd
            self.power_L2.readOp.leakage = leakage_L2 * g_tp.peri_global.Vdd
            self.area.set_area(cumulative_area_L1 + cumulative_area_L2)
            self.power_nand2_path.readOp.gate_leakage = gate_leak_L1_nand2 * g_tp.peri_global.Vdd
            self.power_nand3_path.readOp.gate_leakage = gate_leak_L1_nand3 * g_tp.peri_global.Vdd
            self.power_L2.readOp.gate_leakage = gate_leakage_L2 * g_tp.peri_global.Vdd

    def compute_delays(self, inrisetime):
        ret_val = (0, 0)

        if self.exist:
            Vdd = g_tp.peri_global.Vdd
            inrisetime_nand2_path = inrisetime[0]
            inrisetime_nand3_path = inrisetime[1]

            if self.flag_two_unique_paths or self.number_inputs_L1_gate == 2:
                rd = parameter.tr_R_on(self.w_L1_nand2_n[0], NCH, 2, self.is_dram_)
                c_load = parameter.gate_C(self.w_L1_nand2_n[1] + self.w_L1_nand2_p[1], 0.0, self.is_dram_)
                c_intrinsic = 2 * parameter.drain_C_(
                    self.w_L1_nand2_p[0], PCH, 1, 1, g_tp.cell_h_def, self.is_dram_
                ) + parameter.drain_C_(
                    self.w_L1_nand2_n[0], NCH, 2, 1, g_tp.cell_h_def, self.is_dram_
                )
                tf = rd * (c_intrinsic + c_load)
                this_delay = parameter.horowitz(
                    inrisetime_nand2_path, tf, 0.5, 0.5, RISE
                )
                self.delay_nand2_path += this_delay
                inrisetime_nand2_path = this_delay / (1.0 - 0.5)
                self.power_nand2_path.readOp.dynamic += (c_load + c_intrinsic) * Vdd * Vdd

                for i in range(1, self.number_gates_L1_nand2_path - 1):
                    rd = parameter.tr_R_on(self.w_L1_nand2_n[i], NCH, 1, self.is_dram_)
                    c_load = parameter.gate_C(self.w_L1_nand2_n[i + 1] + self.w_L1_nand2_p[i + 1], 0.0, self.is_dram_)
                    c_intrinsic = parameter.drain_C_(
                        self.w_L1_nand2_p[i], PCH, 1, 1, g_tp.cell_h_def, self.is_dram_
                    ) + parameter.drain_C_(
                        self.w_L1_nand2_n[i], NCH, 1, 1, g_tp.cell_h_def, self.is_dram_
                    )
                    tf = rd * (c_intrinsic + c_load)
                    this_delay = parameter.horowitz(
                        inrisetime_nand2_path, tf, 0.5, 0.5, RISE
                    )
                    self.delay_nand2_path += this_delay
                    inrisetime_nand2_path = this_delay / (1.0 - 0.5)
                    self.power_nand2_path.readOp.dynamic += (c_intrinsic + c_load) * Vdd * Vdd

                i = self.number_gates_L1_nand2_path - 1
                rd = parameter.tr_R_on(self.w_L1_nand2_n[i], NCH, 1, self.is_dram_)
                c_intrinsic = parameter.drain_C_(
                    self.w_L1_nand2_p[i], PCH, 1, 1, g_tp.cell_h_def, self.is_dram_
                ) + parameter.drain_C_(
                    self.w_L1_nand2_n[i], NCH, 1, 1, g_tp.cell_h_def, self.is_dram_
                )
                c_load = self.C_ld_predec_blk_out
                tf = rd * (c_intrinsic + c_load) + self.R_wire_predec_blk_out * c_load / 2
                this_delay = parameter.horowitz(
                    inrisetime_nand2_path, tf, 0.5, 0.5, RISE
                )
                self.delay_nand2_path += this_delay
                ret_val = (this_delay / (1.0 - 0.5), ret_val[1])
                self.power_nand2_path.readOp.dynamic += (c_intrinsic + c_load) * Vdd * Vdd

            if self.flag_two_unique_paths or self.number_inputs_L1_gate == 3:
                rd = parameter.tr_R_on(self.w_L1_nand3_n[0], NCH, 3, self.is_dram_)
                c_load = parameter.gate_C(self.w_L1_nand3_n[1] + self.w_L1_nand3_p[1], 0.0, self.is_dram_)
                c_intrinsic = 3 * parameter.drain_C_(
                    self.w_L1_nand3_p[0], PCH, 1, 1, g_tp.cell_h_def, self.is_dram_
                ) + parameter.drain_C_(
                    self.w_L1_nand3_n[0], NCH, 3, 1, g_tp.cell_h_def, self.is_dram_
                )
                tf = rd * (c_intrinsic + c_load)
                this_delay = parameter.horowitz(
                    inrisetime_nand3_path, tf, 0.5, 0.5, RISE
                )
                self.delay_nand3_path += this_delay
                inrisetime_nand3_path = this_delay / (1.0 - 0.5)
                self.power_nand3_path.readOp.dynamic += (c_intrinsic + c_load) * Vdd * Vdd

                for i in range(1, self.number_gates_L1_nand3_path - 1):
                    rd = parameter.tr_R_on(self.w_L1_nand3_n[i], NCH, 1, self.is_dram_)
                    c_load = parameter.gate_C(self.w_L1_nand3_n[i + 1] + self.w_L1_nand3_p[i + 1], 0.0, self.is_dram_)
                    c_intrinsic = parameter.drain_C_(self.w_L1_nand3_p[i], PCH, 1, 1, g_tp.cell_h_def, self.is_dram_) + \
                                  drain_C_(self.w_L1_nand3_n[i], NCH, 1, 1, g_tp.cell_h_def, self.is_dram_)
                    tf = rd * (c_intrinsic + c_load)
                    this_delay = parameter.horowitz(
                        inrisetime_nand3_path, tf, 0.5, 0.5, RISE
                    )
                    self.delay_nand3_path += this_delay
                    inrisetime_nand3_path = this_delay / (1.0 - 0.5)
                    self.power_nand3_path.readOp.dynamic += (c_intrinsic + c_load) * Vdd * Vdd

                i = self.number_gates_L1_nand3_path - 1
                rd = parameter.tr_R_on(self.w_L1_nand3_n[i], NCH, 1, self.is_dram_)
                c_intrinsic = parameter.drain_C_(
                    self.w_L1_nand3_p[i], PCH, 1, 1, g_tp.cell_h_def, self.is_dram_
                ) + drain_C_(
                    self.w_L1_nand3_n[i], NCH, 1, 1, g_tp.cell_h_def, self.is_dram_
                )
                c_load = self.C_ld_predec_blk_out
                tf = rd * (c_intrinsic + c_load) + self.R_wire_predec_blk_out * c_load / 2
                this_delay = parameter.horowitz(
                    inrisetime_nand3_path, tf, 0.5, 0.5, RISE
                )
                self.delay_nand3_path += this_delay
                ret_val = (ret_val[0], this_delay / (1.0 - 0.5))
                self.power_nand3_path.readOp.dynamic += (c_intrinsic + c_load) * Vdd * Vdd
        return ret_val

    def leakage_feedback(self, temperature):
        if self.exist:
            num_L1_nand2 = 0
            num_L1_nand3 = 0
            num_L2 = 0
            leak_L1_nand3 = 0
            gate_leak_L1_nand3 = 0

            leak_L1_nand2 = parameter.cmos_Isub_leakage(self.w_L1_nand2_n[0], self.w_L1_nand2_p[0], 2, nand, self.is_dram_)
            gate_leak_L1_nand2 = parameter.cmos_Ig_leakage(
                self.w_L1_nand2_n[0], self.w_L1_nand2_p[0], 2, nand, self.is_dram_
            )

            if self.number_inputs_L1_gate != 3:
                leak_L1_nand3 = 0
                gate_leak_L1_nand3 = 0
            else:
                leak_L1_nand3 = parameter.cmos_Isub_leakage(self.w_L1_nand3_n[0], self.w_L1_nand3_p[0], 3, nand)
                gate_leak_L1_nand3 = parameter.cmos_Ig_leakage(
                    self.w_L1_nand3_n[0], self.w_L1_nand3_p[0], 3, nand
                )

            if self.number_input_addr_bits == 1:
                num_L1_nand2 = 2
                num_L2 = 0
                self.num_L1_active_nand2_path = 1
                self.num_L1_active_nand3_path = 0
            elif self.number_input_addr_bits == 2:
                num_L1_nand2 = 4
                num_L2 = 0
                self.num_L1_active_nand2_path = 1
                self.num_L1_active_nand3_path = 0
            elif self.number_input_addr_bits == 3:
                num_L1_nand3 = 8
                num_L2 = 0
                self.num_L1_active_nand2_path = 0
                self.num_L1_active_nand3_path = 1
            elif self.number_input_addr_bits == 4:
                num_L1_nand2 = 8
                num_L2 = 16
                self.num_L1_active_nand2_path = 2
                self.num_L1_active_nand3_path = 0
            elif self.number_input_addr_bits == 5:
                num_L1_nand2 = 4
                num_L1_nand3 = 8
                num_L2 = 32
                self.num_L1_active_nand2_path = 1
                self.num_L1_active_nand3_path = 1
            elif self.number_input_addr_bits == 6:
                num_L1_nand3 = 16
                num_L2 = 64
                self.num_L1_active_nand2_path = 0
                self.num_L1_active_nand3_path = 2
            elif self.number_input_addr_bits == 7:
                num_L1_nand2 = 8
                num_L1_nand3 = 8
                num_L2 = 128
                self.num_L1_active_nand2_path = 2
                self.num_L1_active_nand3_path = 1
            elif self.number_input_addr_bits == 8:
                num_L1_nand2 = 4
                num_L1_nand3 = 16
                num_L2 = 256
                self.num_L1_active_nand2_path = 2
                self.num_L1_active_nand3_path = 2
            elif self.number_input_addr_bits == 9:
                num_L1_nand3 = 24
                num_L2 = 512
                self.num_L1_active_nand2_path = 0
                self.num_L1_active_nand3_path = 3

            for i in range(1, self.number_gates_L1_nand2_path):
                leak_L1_nand2 += parameter.cmos_Isub_leakage(self.w_L1_nand2_n[i], self.w_L1_nand2_p[i], 2, nand, self.is_dram_)
                gate_leak_L1_nand2 += parameter.cmos_Ig_leakage(
                    self.w_L1_nand2_n[i], self.w_L1_nand2_p[i], 2, nand, self.is_dram_
                )

            leak_L1_nand2 *= num_L1_nand2
            gate_leak_L1_nand2 *= num_L1_nand2

            for i in range(1, self.number_gates_L1_nand3_path):
                leak_L1_nand3 += parameter.cmos_Isub_leakage(self.w_L1_nand3_n[i], self.w_L1_nand3_p[i], 3, nand, self.is_dram_)
                gate_leak_L1_nand3 += parameter.cmos_Ig_leakage(
                    self.w_L1_nand3_n[i], self.w_L1_nand3_p[i], 3, nand, self.is_dram_
                )

            leak_L1_nand3 *= num_L1_nand3
            gate_leak_L1_nand3 *= num_L1_nand3

            leakage_L2 = 0.0
            gate_leakage_L2 = 0.0

            if self.flag_L2_gate == 2:
                leakage_L2 = parameter.cmos_Isub_leakage(self.w_L2_n[0], self.w_L2_p[0], 2, nand, self.is_dram_)
                gate_leakage_L2 = parameter.cmos_Ig_leakage(
                    self.w_L2_n[0], self.w_L2_p[0], 2, nand, self.is_dram_
                )
            elif self.flag_L2_gate == 3:
                leakage_L2 = parameter.cmos_Isub_leakage(self.w_L2_n[0], self.w_L2_p[0], 3, nand, self.is_dram_)
                gate_leakage_L2 = parameter.cmos_Ig_leakage(
                    self.w_L2_n[0], self.w_L2_p[0], 3, nand, self.is_dram_
                )

            for i in range(1, self.number_gates_L2):
                leakage_L2 += parameter.cmos_Isub_leakage(self.w_L2_n[i], self.w_L2_p[i], 2, inv, self.is_dram_)
                gate_leakage_L2 += parameter.cmos_Ig_leakage(
                    self.w_L2_n[i], self.w_L2_p[i], 2, inv, self.is_dram_
                )

            leakage_L2 *= num_L2
            gate_leakage_L2 *= num_L2

            self.power_nand2_path.readOp.leakage = leak_L1_nand2 * g_tp.peri_global.Vdd
            self.power_nand3_path.readOp.leakage = leak_L1_nand3 * g_tp.peri_global.Vdd
            self.power_L2.readOp.leakage = leakage_L2 * g_tp.peri_global.Vdd

            self.power_nand2_path.readOp.gate_leakage = gate_leak_L1_nand2 * g_tp.peri_global.Vdd
            self.power_nand3_path.readOp.gate_leakage = gate_leak_L1_nand3 * g_tp.peri_global.Vdd
            self.power_L2.readOp.gate_leakage = gate_leakage_L2 * g_tp.peri_global.Vdd

class PredecBlkDrv(Component):
    def __init__(self, g_ip, way_select, blk, is_dram):
        super().__init__()
        self.g_ip = g_ip
        self.flag_driver_exists = 0
        self.number_input_addr_bits = 0
        self.number_gates_nand2_path = 0
        self.number_gates_nand3_path = 0
        self.min_number_gates = 2
        self.num_buffers_driving_1_nand2_load = 0
        self.num_buffers_driving_2_nand2_load = 0
        self.num_buffers_driving_4_nand2_load = 0
        self.num_buffers_driving_2_nand3_load = 0
        self.num_buffers_driving_8_nand3_load = 0
        self.num_buffers_nand3_path = 0
        self.c_load_nand2_path_out = 0
        self.c_load_nand3_path_out = 0
        self.r_load_nand2_path_out = 0
        self.r_load_nand3_path_out = 0
        self.delay_nand2_path = 0
        self.delay_nand3_path = 0
        self.power_nand2_path = PowerDef()
        self.power_nand3_path = PowerDef()
        self.blk = blk
        self.dec = blk.dec
        self.is_dram = is_dram
        self.way_select = way_select
        self.width_nand2_path_n = [0] * MAX_NUMBER_GATES_STAGE
        self.width_nand2_path_p = [0] * MAX_NUMBER_GATES_STAGE
        self.width_nand3_path_n = [0] * MAX_NUMBER_GATES_STAGE
        self.width_nand3_path_p = [0] * MAX_NUMBER_GATES_STAGE

        self.number_input_addr_bits = blk.number_input_addr_bits

        if way_select > 1:
            self.flag_driver_exists = 1
            self.number_input_addr_bits = way_select
            if self.dec.num_in_signals == 2:
                self.c_load_nand2_path_out = gate_C(self.dec.w_dec_n[0] + self.dec.w_dec_p[0], 0, is_dram)
                self.num_buffers_driving_2_nand2_load = self.number_input_addr_bits
            elif self.dec.num_in_signals == 3:
                self.c_load_nand3_path_out = gate_C(self.dec.w_dec_n[0] + self.dec.w_dec_p[0], 0, is_dram)
                self.num_buffers_driving_2_nand3_load = self.number_input_addr_bits
        elif way_select == 0:
            if blk.exist:
                self.flag_driver_exists = 1

        self.compute_widths()
        self.compute_area()

    def compute_widths(self):
        p_to_n_sz_ratio = parameter.pmos_to_nmos_sz_ratio(self.is_dram)

        if self.flag_driver_exists:
            C_nand2_gate_blk = parameter.gate_C(self.blk.w_L1_nand2_n[0] + self.blk.w_L1_nand2_p[0], 0, self.is_dram)
            C_nand3_gate_blk = parameter.gate_C(
                self.blk.w_L1_nand3_n[0] + self.blk.w_L1_nand3_p[0], 0, self.is_dram
            )

            if self.way_select == 0:
                if self.blk.number_input_addr_bits == 1:
                    self.num_buffers_driving_2_nand2_load = 1
                    self.c_load_nand2_path_out = 2 * C_nand2_gate_blk
                elif self.blk.number_input_addr_bits == 2:
                    self.num_buffers_driving_4_nand2_load = 2
                    self.c_load_nand2_path_out = 4 * C_nand2_gate_blk
                elif self.blk.number_input_addr_bits == 3:
                    self.num_buffers_driving_8_nand3_load = 3
                    self.c_load_nand3_path_out = 8 * C_nand3_gate_blk
                elif self.blk.number_input_addr_bits == 4:
                    self.num_buffers_driving_4_nand2_load = 4
                    self.c_load_nand2_path_out = 4 * C_nand2_gate_blk
                elif self.blk.number_input_addr_bits == 5:
                    self.num_buffers_driving_4_nand2_load = 2
                    self.num_buffers_driving_8_nand3_load = 3
                    self.c_load_nand2_path_out = 4 * C_nand2_gate_blk
                    self.c_load_nand3_path_out = 8 * C_nand3_gate_blk
                elif self.blk.number_input_addr_bits == 6:
                    self.num_buffers_driving_8_nand3_load = 6
                    self.c_load_nand3_path_out = 8 * C_nand3_gate_blk
                elif self.blk.number_input_addr_bits == 7:
                    self.num_buffers_driving_4_nand2_load = 4
                    self.num_buffers_driving_8_nand3_load = 3
                    self.c_load_nand2_path_out = 4 * C_nand2_gate_blk
                    self.c_load_nand3_path_out = 8 * C_nand3_gate_blk
                elif self.blk.number_input_addr_bits == 8:
                    self.num_buffers_driving_4_nand2_load = 2
                    self.num_buffers_driving_8_nand3_load = 6
                    self.c_load_nand2_path_out = 4 * C_nand2_gate_blk
                    self.c_load_nand3_path_out = 8 * C_nand3_gate_blk
                elif self.blk.number_input_addr_bits == 9:
                    self.num_buffers_driving_8_nand3_load = 9
                    self.c_load_nand3_path_out = 8 * C_nand3_gate_blk

            if (self.blk.flag_two_unique_paths or
                self.blk.number_inputs_L1_gate == 2 or
                self.number_input_addr_bits == 0 or
                (self.way_select and self.dec.num_in_signals == 2)):
                self.width_nand2_path_n[0] = g_tp.min_w_nmos_
                self.width_nand2_path_p[0] = p_to_n_sz_ratio * self.width_nand2_path_n[0]
                F = self.c_load_nand2_path_out / parameter.gate_C(
                    self.width_nand2_path_n[0] + self.width_nand2_path_p[0],
                    0,
                    self.is_dram,
                )
                self.number_gates_nand2_path = logical_effort(
                    self.min_number_gates, 1, F,
                    self.width_nand2_path_n, self.width_nand2_path_p,
                    self.c_load_nand2_path_out, p_to_n_sz_ratio,
                    self.is_dram, False, g_tp.max_w_nmos_)

            if (self.blk.flag_two_unique_paths or
                self.blk.number_inputs_L1_gate == 3 or
                (self.way_select and self.dec.num_in_signals == 3)):
                self.width_nand3_path_n[0] = g_tp.min_w_nmos_
                self.width_nand3_path_p[0] = p_to_n_sz_ratio * self.width_nand3_path_n[0]
                F = self.c_load_nand3_path_out / parameter.gate_C(
                    self.width_nand3_path_n[0] + self.width_nand3_path_p[0],
                    0,
                    self.is_dram,
                )
                self.number_gates_nand3_path = logical_effort(
                    self.min_number_gates, 1, F,
                    self.width_nand3_path_n, self.width_nand3_path_p,
                    self.c_load_nand3_path_out, p_to_n_sz_ratio,
                    self.is_dram, False, g_tp.max_w_nmos_)

    def compute_area(self):
        area_nand2_path = 0
        area_nand3_path = 0
        leak_nand2_path = 0
        leak_nand3_path = 0
        gate_leak_nand2_path = 0
        gate_leak_nand3_path = 0

        if self.flag_driver_exists:
            for i in range(self.number_gates_nand2_path):
                area_nand2_path += compute_gate_area(self.g_ip, INV, 1, self.width_nand2_path_p[i], self.width_nand2_path_n[i], g_tp.cell_h_def)
                leak_nand2_path += parameter.cmos_Isub_leakage(self.width_nand2_path_n[i], self.width_nand2_path_p[i], 1, inv, self.is_dram)
                gate_leak_nand2_path += parameter.cmos_Ig_leakage(
                    self.width_nand2_path_n[i],
                    self.width_nand2_path_p[i],
                    1,
                    inv,
                    self.is_dram,
                )

            area_nand2_path *= (self.num_buffers_driving_1_nand2_load +
                                self.num_buffers_driving_2_nand2_load +
                                self.num_buffers_driving_4_nand2_load)
            leak_nand2_path *= (self.num_buffers_driving_1_nand2_load +
                                self.num_buffers_driving_2_nand2_load +
                                self.num_buffers_driving_4_nand2_load)
            gate_leak_nand2_path *= (self.num_buffers_driving_1_nand2_load +
                                     self.num_buffers_driving_2_nand2_load +
                                     self.num_buffers_driving_4_nand2_load)

            for i in range(self.number_gates_nand3_path):
                area_nand3_path += compute_gate_area(self.g_ip, INV, 1, self.width_nand3_path_p[i], self.width_nand3_path_n[i], g_tp.cell_h_def)
                leak_nand3_path += parameter.cmos_Isub_leakage(self.width_nand3_path_n[i], self.width_nand3_path_p[i], 1, inv, self.is_dram)
                gate_leak_nand3_path += parameter.cmos_Ig_leakage(
                    self.width_nand3_path_n[i],
                    self.width_nand3_path_p[i],
                    1,
                    inv,
                    self.is_dram,
                )

            area_nand3_path *= (self.num_buffers_driving_2_nand3_load + self.num_buffers_driving_8_nand3_load)
            leak_nand3_path *= (self.num_buffers_driving_2_nand3_load + self.num_buffers_driving_8_nand3_load)
            gate_leak_nand3_path *= (self.num_buffers_driving_2_nand3_load + self.num_buffers_driving_8_nand3_load)

            self.power_nand2_path.readOp.leakage = leak_nand2_path * g_tp.peri_global.Vdd
            self.power_nand3_path.readOp.leakage = leak_nand3_path * g_tp.peri_global.Vdd
            self.power_nand2_path.readOp.gate_leakage = gate_leak_nand2_path * g_tp.peri_global.Vdd
            self.power_nand3_path.readOp.gate_leakage = gate_leak_nand3_path * g_tp.peri_global.Vdd
            self.area.set_area(area_nand2_path + area_nand3_path)

    def compute_delays(self, inrisetime_nand2_path, inrisetime_nand3_path):
        ret_val = (0, 0)
        Vdd = g_tp.peri_global.Vdd

        if self.flag_driver_exists:
            for i in range(self.number_gates_nand2_path - 1):
                rd = parameter.tr_R_on(self.width_nand2_path_n[i], NCH, 1, self.is_dram)
                c_gate_load = parameter.gate_C(self.width_nand2_path_p[i + 1] + self.width_nand2_path_n[i + 1], 0.0, self.is_dram)
                c_intrinsic = parameter.drain_C_(
                    self.width_nand2_path_p[i], PCH, 1, 1, g_tp.cell_h_def, self.is_dram
                ) + parameter.drain_C_(
                    self.width_nand2_path_n[i], NCH, 1, 1, g_tp.cell_h_def, self.is_dram
                )

                tf = rd * (c_intrinsic + c_gate_load)
                this_delay = parameter.horowitz(
                    inrisetime_nand2_path, tf, 0.5, 0.5, RISE
                )
                self.delay_nand2_path += this_delay
                inrisetime_nand2_path = this_delay / (1.0 - 0.5)
                self.power_nand2_path.readOp.dynamic += (c_gate_load + c_intrinsic) * 0.5 * Vdd * Vdd

            if self.number_gates_nand2_path != 0:
                i = self.number_gates_nand2_path - 1
                rd = parameter.tr_R_on(self.width_nand2_path_n[i], NCH, 1, self.is_dram)
                c_intrinsic = parameter.drain_C_(
                    self.width_nand2_path_p[i], PCH, 1, 1, g_tp.cell_h_def, self.is_dram
                ) + parameter.drain_C_(
                    self.width_nand2_path_n[i], NCH, 1, 1, g_tp.cell_h_def, self.is_dram
                )
                c_load = self.c_load_nand2_path_out
                tf = rd * (c_intrinsic + c_load) + self.r_load_nand2_path_out * c_load / 2
                this_delay = parameter.horowitz(
                    inrisetime_nand2_path, tf, 0.5, 0.5, RISE
                )
                self.delay_nand2_path += this_delay
                ret_val = (this_delay / (1.0 - 0.5), ret_val[1])
                self.power_nand2_path.readOp.dynamic += (c_intrinsic + c_load) * 0.5 * Vdd * Vdd

            for i in range(self.number_gates_nand3_path - 1):
                rd = parameter.tr_R_on(self.width_nand3_path_n[i], NCH, 1, self.is_dram)
                c_gate_load = parameter.gate_C(self.width_nand3_path_p[i + 1] + self.width_nand3_path_n[i + 1], 0.0, self.is_dram)
                c_intrinsic = parameter.drain_C_(
                    self.width_nand3_path_p[i], PCH, 1, 1, g_tp.cell_h_def, self.is_dram
                ) + drain_C_(
                    self.width_nand3_path_n[i], NCH, 1, 1, g_tp.cell_h_def, self.is_dram
                )
                tf = rd * (c_intrinsic + c_gate_load)
                this_delay = parameter.horowitz(
                    inrisetime_nand3_path, tf, 0.5, 0.5, RISE
                )
                self.delay_nand3_path += this_delay
                inrisetime_nand3_path = this_delay / (1.0 - 0.5)
                self.power_nand3_path.readOp.dynamic += (c_gate_load + c_intrinsic) * 0.5 * Vdd * Vdd

            if self.number_gates_nand3_path != 0:
                i = self.number_gates_nand3_path - 1
                rd = tr_R_on(self.width_nand3_path_n[i], NCH, 1, self.is_dram)
                c_intrinsic = drain_C_(self.width_nand3_path_p[i], PCH, 1, 1, g_tp.cell_h_def, self.is_dram) + \
                              drain_C_(self.width_nand3_path_n[i], NCH, 1, 1, g_tp.cell_h_def, self.is_dram)
                c_load = self.c_load_nand3_path_out
                tf = rd * (c_intrinsic + c_load) + self.r_load_nand3_path_out * c_load / 2
                this_delay = horowitz(inrisetime_nand3_path, tf, 0.5, 0.5, RISE)
                self.delay_nand3_path += this_delay
                ret_val = (ret_val[0], this_delay / (1.0 - 0.5))
                self.power_nand3_path.readOp.dynamic += (c_intrinsic + c_load) * 0.5 * Vdd * Vdd
        return ret_val

    def get_rdOp_dynamic_E(self, num_act_mats_hor_dir):
        return (self.num_addr_bits_nand2_path() * self.power_nand2_path.readOp.dynamic +
                self.num_addr_bits_nand3_path() * self.power_nand3_path.readOp.dynamic) * num_act_mats_hor_dir

    def num_addr_bits_nand2_path(self):
        return self.num_buffers_driving_1_nand2_load + \
               self.num_buffers_driving_2_nand2_load + \
               self.num_buffers_driving_4_nand2_load

    def num_addr_bits_nand3_path(self):
        return self.num_buffers_driving_2_nand3_load + \
               self.num_buffers_driving_8_nand3_load

    # Check this cmos_Ig_leakage
    def leakage_feedback(self, temperature):
        leak_nand2_path = 0
        leak_nand3_path = 0
        gate_leak_nand2_path = 0
        gate_leak_nand3_path = 0

        if self.flag_driver_exists:  # first check whether a predecoder block driver is needed
            for i in range(self.number_gates_nand2_path):
                leak_nand2_path += cmos_Isub_leakage(self.width_nand2_path_n[i], self.width_nand2_path_p[i], 1, INV, self.is_dram)
                gate_leak_nand2_path += cmos_Ig_leakage(self.width_nand2_path_n[i], self.width_nand2_path_p[i], 1, INV, self.is_dram)

            leak_nand2_path *= (self.num_buffers_driving_1_nand2_load +
                                self.num_buffers_driving_2_nand2_load +
                                self.num_buffers_driving_4_nand2_load)
            gate_leak_nand2_path *= (self.num_buffers_driving_1_nand2_load +
                                    self.num_buffers_driving_2_nand2_load +
                                    self.num_buffers_driving_4_nand2_load)

            for i in range(self.number_gates_nand3_path):
                leak_nand3_path += parameter.cmos_Isub_leakage(self.width_nand3_path_n[i], self.width_nand3_path_p[i], 1, INV, self.is_dram)
                gate_leak_nand3_path += parameter.cmos_Ig_leakage(
                    self.width_nand3_path_n[i],
                    self.width_nand3_path_p[i],
                    1,
                    INV,
                    self.is_dram,
                )

            leak_nand3_path *= (self.num_buffers_driving_2_nand3_load + self.num_buffers_driving_8_nand3_load)
            gate_leak_nand3_path *= (self.num_buffers_driving_2_nand3_load + self.num_buffers_driving_8_nand3_load)

            self.power_nand2_path.readOp.leakage = leak_nand2_path * g_tp.peri_global.Vdd
            self.power_nand3_path.readOp.leakage = leak_nand3_path * g_tp.peri_global.Vdd
            self.power_nand2_path.readOp.gate_leakage = gate_leak_nand2_path * g_tp.peri_global.Vdd
            self.power_nand3_path.readOp.gate_leakage = gate_leak_nand3_path * g_tp.peri_global.Vdd

class Predec(Component):
    def __init__(self, drv1, drv2):
        super().__init__()
        self.blk1 = drv1.blk
        self.blk2 = drv2.blk
        self.drv1 = drv1
        self.drv2 = drv2
        self.driver_power = PowerDef()
        self.block_power = PowerDef()
        self.power = PowerDef()
        self.delay = 0

        self.driver_power.readOp.leakage = drv1.power_nand2_path.readOp.leakage + \
                                           drv1.power_nand3_path.readOp.leakage + \
                                           drv2.power_nand2_path.readOp.leakage + \
                                           drv2.power_nand3_path.readOp.leakage
        self.block_power.readOp.leakage = self.blk1.power_nand2_path.readOp.leakage + \
                                          self.blk1.power_nand3_path.readOp.leakage + \
                                          self.blk1.power_L2.readOp.leakage + \
                                          self.blk2.power_nand2_path.readOp.leakage + \
                                          self.blk2.power_nand3_path.readOp.leakage + \
                                          self.blk2.power_L2.readOp.leakage
        self.power.readOp.leakage = self.driver_power.readOp.leakage + self.block_power.readOp.leakage

        self.driver_power.readOp.gate_leakage = drv1.power_nand2_path.readOp.gate_leakage + \
                                                drv1.power_nand3_path.readOp.gate_leakage + \
                                                drv2.power_nand2_path.readOp.gate_leakage + \
                                                drv2.power_nand3_path.readOp.gate_leakage
        self.block_power.readOp.gate_leakage = self.blk1.power_nand2_path.readOp.gate_leakage + \
                                               self.blk1.power_nand3_path.readOp.gate_leakage + \
                                               self.blk1.power_L2.readOp.gate_leakage + \
                                               self.blk2.power_nand2_path.readOp.gate_leakage + \
                                               self.blk2.power_nand3_path.readOp.gate_leakage + \
                                               self.blk2.power_L2.readOp.gate_leakage
        self.power.readOp.gate_leakage = self.driver_power.readOp.gate_leakage + self.block_power.readOp.gate_leakage

    def compute_delays(self, inrisetime):
        tmp_pair1 = self.drv1.compute_delays(inrisetime, inrisetime)
        tmp_pair1 = self.blk1.compute_delays(tmp_pair1)
        tmp_pair2 = self.drv2.compute_delays(inrisetime, inrisetime)
        tmp_pair2 = self.blk2.compute_delays(tmp_pair2)

        tmp_pair1 = self.get_max_delay_before_decoder(tmp_pair1, tmp_pair2)

        self.driver_power.readOp.dynamic = self.drv1.num_addr_bits_nand2_path() * self.drv1.power_nand2_path.readOp.dynamic + \
                                           self.drv1.num_addr_bits_nand3_path() * self.drv1.power_nand3_path.readOp.dynamic + \
                                           self.drv2.num_addr_bits_nand2_path() * self.drv2.power_nand2_path.readOp.dynamic + \
                                           self.drv2.num_addr_bits_nand3_path() * self.drv2.power_nand3_path.readOp.dynamic

        self.block_power.readOp.dynamic = self.blk1.power_nand2_path.readOp.dynamic * self.blk1.num_L1_active_nand2_path + \
                                          self.blk1.power_nand3_path.readOp.dynamic * self.blk1.num_L1_active_nand3_path + \
                                          self.blk1.power_L2.readOp.dynamic + \
                                          self.blk2.power_nand2_path.readOp.dynamic * self.blk1.num_L1_active_nand2_path + \
                                          self.blk2.power_nand3_path.readOp.dynamic * self.blk1.num_L1_active_nand3_path + \
                                          self.blk2.power_L2.readOp.dynamic

        self.power.readOp.dynamic = self.driver_power.readOp.dynamic + self.block_power.readOp.dynamic

        self.delay = tmp_pair1[0]
        return tmp_pair1[1]

    def leakage_feedback(self, temperature):
        self.drv1.leakage_feedback(temperature)
        self.drv2.leakage_feedback(temperature)
        self.blk1.leakage_feedback(temperature)
        self.blk2.leakage_feedback(temperature)

        self.driver_power.readOp.leakage = self.drv1.power_nand2_path.readOp.leakage + \
                                           self.drv1.power_nand3_path.readOp.leakage + \
                                           self.drv2.power_nand2_path.readOp.leakage + \
                                           self.drv2.power_nand3_path.readOp.leakage
        self.block_power.readOp.leakage = self.blk1.power_nand2_path.readOp.leakage + \
                                          self.blk1.power_nand3_path.readOp.leakage + \
                                          self.blk1.power_L2.readOp.leakage + \
                                          self.blk2.power_nand2_path.readOp.leakage + \
                                          self.blk2.power_nand3_path.readOp.leakage + \
                                          self.blk2.power_L2.readOp.leakage
        self.power.readOp.leakage = self.driver_power.readOp.leakage + self.block_power.readOp.leakage

        self.driver_power.readOp.gate_leakage = self.drv1.power_nand2_path.readOp.gate_leakage + \
                                                self.drv1.power_nand3_path.readOp.gate_leakage + \
                                                self.drv2.power_nand2_path.readOp.gate_leakage + \
                                                self.drv2.power_nand3_path.readOp.gate_leakage
        self.block_power.readOp.gate_leakage = self.blk1.power_nand2_path.readOp.gate_leakage + \
                                               self.blk1.power_nand3_path.readOp.gate_leakage + \
                                               self.blk1.power_L2.readOp.gate_leakage + \
                                               self.blk2.power_nand2_path.readOp.gate_leakage + \
                                               self.blk2.power_nand3_path.readOp.gate_leakage + \
                                               self.blk2.power_L2.readOp.gate_leakage
        self.power.readOp.gate_leakage = self.driver_power.readOp.gate_leakage + self.block_power.readOp.gate_leakage

    def get_max_delay_before_decoder(self, input_pair1, input_pair2):
        ret_val = [0, 0]

        # CHANGE: MAX: set to one option, otherwise, expression will be too long

        # delay = self.drv1.delay_nand2_path + self.blk1.delay_nand2_path
        # ret_val[0] = delay
        # ret_val[1] = input_pair1[0]
        # delay = self.drv1.delay_nand3_path + self.blk1.delay_nand3_path
        # if ret_val[0] < delay:
        #     ret_val[0] = delay
        #     ret_val[1] = input_pair1[1]
        # delay = self.drv2.delay_nand2_path + self.blk2.delay_nand2_path
        # if ret_val[0] < delay:
        #     ret_val[0] = delay
        #     ret_val[1] = input_pair2[0]
        # delay = self.drv2.delay_nand3_path + self.blk2.delay_nand3_path
        # if ret_val[0] < delay:
        #     ret_val[0] = delay
        #     ret_val[1] = input_pair2[1]

        delay1 = self.drv1.delay_nand2_path + self.blk1.delay_nand2_path
        delay2 = self.drv1.delay_nand3_path + self.blk1.delay_nand3_path

        delay3 = self.drv2.delay_nand2_path + self.blk2.delay_nand2_path
        delay4 = self.drv2.delay_nand3_path + self.blk2.delay_nand3_path

        max_delay = parameter.symbolic_convex_max(
            parameter.symbolic_convex_max(delay1, delay2),
            symbolic_convex_max(delay3, delay4),
        )
        # delay2  # picked an option to reduce expression size

        ret_val[0] = max_delay
        ret_val[1] = input_pair1[0]

        return ret_val

class Driver(Component):
    def __init__(self, g_ip, c_gate_load_, c_wire_load_, r_wire_load_, is_dram):
        super().__init__()
        self.g_ip = g_ip
        self.number_gates = 0
        self.min_number_gates = 2
        self.c_gate_load = c_gate_load_
        self.c_wire_load = c_wire_load_
        self.r_wire_load = r_wire_load_
        self.delay = 0
        self.is_dram_ = is_dram
        self.total_driver_nwidth = 0
        self.total_driver_pwidth = 0
        self.width_n = [0] * MAX_NUMBER_GATES_STAGE
        self.width_p = [0] * MAX_NUMBER_GATES_STAGE
        self.power = PowerDef()

        self.compute_widths()
        self.compute_area()

    def compute_widths(self):
        p_to_n_sz_ratio = parameter.pmos_to_nmos_sz_ratio(self.is_dram_)
        c_load = self.c_gate_load + self.c_wire_load
        self.width_n[0] = g_tp.min_w_nmos_
        self.width_p[0] = p_to_n_sz_ratio * g_tp.min_w_nmos_

        F = c_load / parameter.gate_C(
            self.width_n[0] + self.width_p[0], 0, self.is_dram_
        )
        self.number_gates = logical_effort(
            self.min_number_gates,
            1,
            F,
            self.width_n,
            self.width_p,
            c_load,
            p_to_n_sz_ratio,
            self.is_dram_, False,
            g_tp.max_w_nmos_)

    def compute_area(self):
        cumulative_area = 0
        self.area = Area()
        self.area.h = g_tp.cell_h_def
        for i in range(self.number_gates):
            cumulative_area += compute_gate_area(
                self.g_ip, INV, 1, self.width_p[i], self.width_n[i], self.area.h
            )
        self.area.w = cumulative_area / self.area.h

    def compute_power_gating(self):
        for i in range(self.number_gates + 1):
            self.total_driver_nwidth += self.width_n[i]
            self.total_driver_pwidth += self.width_p[i]

        is_footer = False
        Isat_subarray = simplified_nmos_Isat(self.total_driver_nwidth)
        detalV = g_tp.peri_global.Vdd - g_tp.peri_global.Vcc_min
        c_wakeup = parameter.drain_C_(self.total_driver_pwidth, PCH, 1, 1, self.area.h)

        if self.g_ip.power_gating:
            self.sleeptx = SleepTx(self.g_ip, self.g_ip.perfloss, Isat_subarray, is_footer, c_wakeup, detalV, 1, self.area)

    def compute_delay(self, inrisetime):
        this_delay = 0

        for i in range(self.number_gates - 1):
            rd = parameter.tr_R_on(self.width_n[i], NCH, 1, self.is_dram_)
            c_load = parameter.gate_C(self.width_n[i + 1] + self.width_p[i + 1], 0.0, self.is_dram_)
            c_intrinsic = parameter.drain_C_(
                self.width_p[i], PCH, 1, 1, g_tp.cell_h_def, self.is_dram_
            ) + parameter.drain_C_(
                self.width_n[i], NCH, 1, 1, g_tp.cell_h_def, self.is_dram_
            )
            tf = rd * (c_intrinsic + c_load)
            this_delay = parameter.horowitz(inrisetime, tf, 0.5, 0.5, RISE)
            self.delay += this_delay
            inrisetime = this_delay / (1.0 - 0.5)
            self.power.readOp.dynamic += (c_intrinsic + c_load) * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd
            self.power.readOp.leakage += parameter.cmos_Isub_leakage(self.width_n[i], self.width_p[i], 1, inv, self.is_dram_) * g_tp.peri_global.Vdd
            self.power.readOp.gate_leakage += (
                parameter.cmos_Ig_leakage(
                    self.width_n[i], self.width_p[i], 1, inv, self.is_dram_
                )
                * g_tp.peri_global.Vdd
            )

        i = self.number_gates - 1
        c_load = self.c_gate_load + self.c_wire_load
        rd = parameter.tr_R_on(self.width_n[i], NCH, 1, self.is_dram_)
        c_intrinsic = parameter.drain_C_(
            self.width_p[i], PCH, 1, 1, g_tp.cell_h_def, self.is_dram_
        ) + parameter.drain_C_(
            self.width_n[i], NCH, 1, 1, g_tp.cell_h_def, self.is_dram_
        )
        tf = rd * (c_intrinsic + c_load) + self.r_wire_load * (self.c_wire_load / 2 + self.c_gate_load)
        this_delay = parameter.horowitz(inrisetime, tf, 0.5, 0.5, RISE)
        self.delay += this_delay
        self.power.readOp.dynamic += (c_intrinsic + c_load) * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd
        self.power.readOp.leakage += parameter.cmos_Isub_leakage(self.width_n[i], self.width_p[i], 1, inv, self.is_dram_) * g_tp.peri_global.Vdd
        self.power.readOp.gate_leakage += (
            parameter.cmos_Ig_leakage(
                self.width_n[i], self.width_p[i], 1, inv, self.is_dram_
            )
            * g_tp.peri_global.Vdd
        )

        return this_delay / (1.0 - 0.5)


# Helper functions and constants (placeholders for actual implementations)
NAND = 'nand'
INV = 'inv'
