# decoder.py

import math
import sympy as sp

from .area import Area
from .cacti_interface import PowerDef
from .component import (
    Component, logical_effort, compute_gate_area
)

from .const import *
from . import parameter
from .powergating import SleepTx

from .basic_circuit import (
    is_pow2, _log2, is_equal,
    wire_resistance, wire_capacitance, tsv_resistance, tsv_capacitance, tsv_area,
    pmos_to_nmos_sz_ratio, gate_C, gate_C_pass, tr_R_on, drain_C_, cmos_Ig_leakage,
    horowitz, cmos_Isub_leakage, simplified_nmos_Isat
)

# For piecewise or max approximations:
def symbolic_convex_max(a, b):
    """
    An approximation to the max function that plays well with numeric
    or symbolic solvers.
    """
    return 0.5 * (a + b + abs(a - b))

def is_symbolic(x):
    """Return True if x is a sympy symbolic expression."""
    return isinstance(x, sp.Basic)

###############################################################################
# Decoder class
###############################################################################

class Decoder(Component):
    """
    Python version of the 'Decoder' class from decoder.cc/decoder.h
    """

    def __init__(self,
                 g_ip,
                 g_tp,
                 num_dec_signals,       # _num_dec_signals
                 flag_way_select,
                 C_ld_dec_out,
                 R_wire_dec_out,
                 fully_assoc_,
                 is_dram_,
                 is_wl_tr_,
                 cell_):

        super().__init__()
        self.g_ip = g_ip
        self.g_tp = g_tp

        self.exist = False
        self.num_in_signals = 0
        self.C_ld_dec_out   = C_ld_dec_out
        self.R_wire_dec_out = R_wire_dec_out
        self.num_gates      = 0
        self.num_gates_min  = 2
        self.delay          = 0.0

        self.fully_assoc = fully_assoc_
        self.is_dram     = is_dram_
        self.is_wl_tr    = is_wl_tr_

        self.total_driver_nwidth = 0.0
        self.total_driver_pwidth = 0.0
        self.sleeptx = None

        self.cell      = cell_
        self.nodes_DSTN = 1   # from the original code

        self.w_dec_n = [0.0]*MAX_NUMBER_GATES_STAGE
        self.w_dec_p = [0.0]*MAX_NUMBER_GATES_STAGE

        num_addr_bits_dec = _log2(num_dec_signals)

        # Decide if we have a decoder
        if not is_symbolic(num_addr_bits_dec):
            if num_addr_bits_dec < 4:
                if flag_way_select:
                    self.exist = True
                    self.num_in_signals = 2
                else:
                    self.num_in_signals = 0
            else:
                self.exist = True
                if flag_way_select:
                    self.num_in_signals = 3
                else:
                    self.num_in_signals = 2
        else:
            # #PATH_APPROX for symbolic case
            # Assume typical path with num_addr_bits_dec >= 4
            self.exist = True
            if flag_way_select:
                self.num_in_signals = 3
            else:
                self.num_in_signals = 2

        # area: the original code sets area.h = g_tp.h_dec * cell.h
        self.area.h = g_tp.h_dec * self.cell.h
        # width will be computed after we sum up gate areas

        # only if exist is true do we do the sizing
        if self.cell.h <= 0 or self.cell.w <= 0:
            # in C++ it uses assert(cell.h>0 && cell.w>0)
            assert self.cell.h > 0
            assert self.cell.w > 0

        self.compute_widths()
        self.compute_area()

    def compute_widths(self):
        """
        Equivalent to the C++ Decoder::compute_widths().
        """
        p_to_n_sz_ratio = pmos_to_nmos_sz_ratio(self.g_tp, self.is_dram, self.is_wl_tr)
        gnand2 = (2.0 + p_to_n_sz_ratio)/(1.0 + p_to_n_sz_ratio)
        gnand3 = (3.0 + p_to_n_sz_ratio)/(1.0 + p_to_n_sz_ratio)

        if self.exist:
            if self.num_in_signals == 2 or self.fully_assoc:
                self.w_dec_n[0] = 2.0 * self.g_tp.min_w_nmos_
                self.w_dec_p[0] = p_to_n_sz_ratio * self.g_tp.min_w_nmos_
                base_g = gnand2
            else:
                self.w_dec_n[0] = 3.0 * self.g_tp.min_w_nmos_
                self.w_dec_p[0] = p_to_n_sz_ratio * self.g_tp.min_w_nmos_
                base_g = gnand3

            c_first = gate_C(self.g_tp, self.w_dec_n[0], 0, self.is_dram, False, self.is_wl_tr) + \
                      gate_C(self.g_tp, self.w_dec_p[0], 0, self.is_dram, False, self.is_wl_tr)
            F = base_g * self.C_ld_dec_out / c_first

            # call logical_effort to find number of gates
            self.num_gates = logical_effort(
                self.g_tp,
                self.num_gates_min,
                base_g,
                F,
                self.w_dec_n,
                self.w_dec_p,
                self.C_ld_dec_out,
                p_to_n_sz_ratio,
                self.is_dram,
                self.is_wl_tr,
                self.g_tp.max_w_nmos_dec
            )

    def compute_area(self):
        """
        Summation of gate areas across all gates in the decoder.
        Also sets leakage/gate_leakage from cmos_Isub_leakage/cmos_Ig_leakage.
        """
        cumulative_area = 0.0
        cumulative_curr = 0.0
        cumulative_curr_Ig = 0.0

        if self.exist:
            # first gate
            if self.num_in_signals == 2:
                # NAND2
                cumulative_area = compute_gate_area(self.g_tp, NAND, 2,
                                                              self.w_dec_p[0], self.w_dec_n[0],
                                                              self.area.h)
                cumulative_curr = cmos_Isub_leakage(self.g_tp,
                                                self.w_dec_n[0], self.w_dec_p[0],
                                                2, NAND, self.is_dram)
                cumulative_curr_Ig = cmos_Ig_leakage(self.g_tp,
                                                self.w_dec_n[0], self.w_dec_p[0],
                                                2, NAND, self.is_dram)
            elif self.num_in_signals == 3:
                # NAND3
                cumulative_area = compute_gate_area(self.g_tp, NAND, 3,
                                                              self.w_dec_p[0], self.w_dec_n[0],
                                                              self.area.h)
                cumulative_curr = cmos_Isub_leakage(self.g_tp,
                                                self.w_dec_n[0], self.w_dec_p[0],
                                                3, NAND, self.is_dram)
                cumulative_curr_Ig = cmos_Ig_leakage(self.g_tp,
                                                self.w_dec_n[0], self.w_dec_p[0],
                                                3, NAND, self.is_dram)

            # subsequent gates are inverters
            # CHECK Affected by NUM GATE COMPONENT
            for i in range(1, self.num_gates):
                cumulative_area += compute_gate_area(self.g_tp, INV, 1,
                                                               self.w_dec_p[i], self.w_dec_n[i],
                                                               self.area.h)
                cumulative_curr += cmos_Isub_leakage(self.g_tp,
                                                    self.w_dec_n[i], self.w_dec_p[i],
                                                    1, INV, self.is_dram)
                # CHECK - C says = not +=
                cumulative_curr_Ig = cmos_Ig_leakage(self.g_tp,
                                                    self.w_dec_n[i], self.w_dec_p[i],
                                                    1, INV, self.is_dram)

            self.power.readOp.leakage      = cumulative_curr * self.g_tp.peri_global.Vdd
            self.power.readOp.gate_leakage = cumulative_curr_Ig * self.g_tp.peri_global.Vdd

            # CHECK WHY SELF.H CHECK?   
            # final area dimension
            # if self.area.h > 0:
            #     self.area.w = cumulative_area / self.area.h
            # else:
            #     self.area.w = 0
            self.area.w = cumulative_area / self.area.h

    def compute_power_gating(self):
        """
        Create a SleepTx object for power gating, if needed.
        The original code sets up the total transistor widths and calls Sleep_tx.
        """
        # the code does for (int i=1; i<=num_gates; i++), in Python we do:
        for i in range(1, self.num_gates+1):
            # PATH_APPROX we assume i in range(1, self.num_gates) is enough
            # CHECK why have this bounds check?
            # if i < len(self.w_dec_n):
            self.total_driver_nwidth += self.w_dec_n[i]
            self.total_driver_pwidth += self.w_dec_p[i]

        # compute the single sleep tx
        is_footer     = False
        Isat_subarray = simplified_nmos_Isat(self.g_tp, self.total_driver_nwidth)
        detalV        = self.g_tp.peri_global.Vdd - self.g_tp.peri_global.Vcc_min
        c_wakeup      = drain_C_(self.g_ip, self.g_tp,
                                           self.total_driver_pwidth,
                                           PCH,
                                           1,1,
                                           self.cell.h)

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

    # CHECK Could be source of ERROR
    def compute_delays(self, inrisetime):
        """
        Implementation of Decoder::compute_delays(double inrisetime).
        Returns outrisetime.
        """
        if not self.exist:
            return 0.0

        ret_val = 0.0
        # local references
        Vdd = self.g_tp.peri_global.Vdd

        # Decide if Vpp is needed
        if self.is_wl_tr and self.is_dram:
            Vpp = self.g_tp.vpp
        elif self.is_wl_tr:
            Vpp = self.g_tp.sram_cell.Vdd
        else:
            Vpp = Vdd

        # first gate
        rd = tr_R_on(self.g_tp, self.w_dec_n[0], NCH, self.num_in_signals,
                               self.is_dram, False, self.is_wl_tr)
        c_load = gate_C(self.g_tp,
                                  (self.w_dec_n[1] + self.w_dec_p[1]) if self.num_gates > 1 else 0.0,
                                  0.0, self.is_dram, False, self.is_wl_tr)
        c_intrinsic = drain_C_(self.g_ip, self.g_tp, self.w_dec_p[0], PCH,
                                         1,1, self.area.h,
                                         self.is_dram, False, self.is_wl_tr) * self.num_in_signals \
                      + drain_C_(self.g_ip, self.g_tp, self.w_dec_n[0], NCH,
                                           self.num_in_signals,1, self.area.h,
                                           self.is_dram, False, self.is_wl_tr)

        tf = rd*(c_intrinsic + c_load)
        this_delay = horowitz(self.g_ip, inrisetime, tf, 0.5, 0.5, RISE)
        self.delay += this_delay
        inrisetime  = this_delay/(1.0 - 0.5)
        self.power.readOp.dynamic += (c_load + c_intrinsic)*(Vdd*Vdd)

        # middle stages
        for i in range(1, self.num_gates - 1):
            rd = tr_R_on(self.g_tp, self.w_dec_n[i], NCH,
                                   1, self.is_dram, False, self.is_wl_tr)
            c_load = gate_C(self.g_tp,
                                      self.w_dec_n[i+1] + self.w_dec_p[i+1]
                                      if (i+1)<self.num_gates else 0.0,
                                      0.0, self.is_dram, False, self.is_wl_tr)
            c_intrinsic = drain_C_(self.g_ip, self.g_tp,
                                             self.w_dec_p[i], PCH,1,1,self.area.h,
                                             self.is_dram,False,self.is_wl_tr) \
                          + drain_C_(self.g_ip, self.g_tp,
                                               self.w_dec_n[i], NCH,1,1,
                                               self.area.h,self.is_dram,False,self.is_wl_tr)
            tf = rd*(c_intrinsic + c_load)
            this_delay = horowitz(self.g_ip, inrisetime, tf, 0.5, 0.5, RISE)
            self.delay += this_delay
            inrisetime = this_delay/(1.0 - 0.5)
            self.power.readOp.dynamic += (c_intrinsic + c_load)*(Vdd*Vdd)

        # final stage
        # Check added boundary condition here:, reliant on COMPONENT logical effort
        if self.num_gates > 0:
            i       = self.num_gates - 1
            c_load  = self.C_ld_dec_out
            rd = tr_R_on(self.g_tp, self.w_dec_n[i], NCH,
                                   1, self.is_dram, False, self.is_wl_tr)
            c_intrinsic = drain_C_(self.g_ip, self.g_tp,
                                             self.w_dec_p[i], PCH,1,1,self.area.h,
                                             self.is_dram,False,self.is_wl_tr) \
                          + drain_C_(self.g_ip, self.g_tp,
                                               self.w_dec_n[i], NCH,1,1,self.area.h,
                                               self.is_dram,False,self.is_wl_tr)
            tf = rd*(c_intrinsic + c_load) + self.R_wire_dec_out*c_load*0.5
            this_delay = horowitz(self.g_ip, inrisetime, tf, 0.5, 0.5, RISE)
            self.delay += this_delay
            ret_val = this_delay/(1.0 - 0.5)

            # dynamic
            self.power.readOp.dynamic += c_load*(Vpp*Vpp) + c_intrinsic*(Vdd*Vdd)

        self.compute_power_gating()
        return ret_val

    def leakage_feedback(self, temperature):
        """
        Recompute leakage if temperature changes. Summation of subthreshold/gate currents
        in all gate stages.
        """
        if not self.exist:
            return
        cumulative_curr = 0.0
        cumulative_curr_Ig = 0.0

        if self.num_in_signals == 2:
            cumulative_curr += cmos_Isub_leakage(self.g_tp,
                                                      self.w_dec_n[0], self.w_dec_p[0],
                                                      2, NAND, self.is_dram)
            cumulative_curr_Ig  += cmos_Ig_leakage(self.g_tp,
                                                    self.w_dec_n[0], self.w_dec_p[0],
                                                    2, NAND, self.is_dram)
        elif self.num_in_signals == 3:
            cumulative_curr += cmos_Isub_leakage(self.g_tp,
                                                      self.w_dec_n[0], self.w_dec_p[0],
                                                      3, NAND, self.is_dram)
            cumulative_curr_Ig  += cmos_Ig_leakage(self.g_tp,
                                                    self.w_dec_n[0], self.w_dec_p[0],
                                                    3, NAND, self.is_dram)

        for i in range(1, self.num_gates):
            cumulative_curr += cmos_Isub_leakage(self.g_tp,
                                                      self.w_dec_n[i], self.w_dec_p[i],
                                                      1, INV, self.is_dram)
            # CHECK C has = and not +=
            cumulative_curr_Ig = cmos_Ig_leakage(self.g_tp,
                                                    self.w_dec_n[i], self.w_dec_p[i],
                                                    1, INV, self.is_dram)

        self.power.readOp.leakage      = cumulative_curr*self.g_tp.peri_global.Vdd
        self.power.readOp.gate_leakage = cumulative_curr_Ig *self.g_tp.peri_global.Vdd


###############################################################################
# PredecBlk class
###############################################################################

class PredecBlk(Component):
    """
    Python version of 'PredecBlk' from decoder.cc/decoder.h

    This version fills in the previously #PATH_APPROX sections to replicate
    the logic from the original C++ code for widths, area, delay, and leakage.
    """

    def __init__(self,
                 g_ip,
                 g_tp,
                 num_dec_signals,
                 dec,                  # pointer to a Decoder
                 C_wire_predec_blk_out,
                 R_wire_predec_blk_out,
                 num_dec_per_predec,
                 is_dram_,
                 is_blk1):
        super().__init__()

        self.g_ip  = g_ip
        self.g_tp  = g_tp
        self.dec   = dec
        self.exist = False

        # internal data members, matching the C++ class
        self.number_input_addr_bits      = 0
        self.C_ld_predec_blk_out         = 0.0
        self.R_wire_predec_blk_out       = 0.0
        self.branch_effort_nand2_gate_output = 1
        self.branch_effort_nand3_gate_output = 1
        self.flag_two_unique_paths       = False
        self.flag_L2_gate               = 0
        self.number_inputs_L1_gate      = 0
        self.number_gates_L1_nand2_path = 0
        self.number_gates_L1_nand3_path = 0
        self.number_gates_L2            = 0
        self.min_number_gates_L1        = 2
        self.min_number_gates_L2        = 2
        self.num_L1_active_nand2_path   = 0
        self.num_L1_active_nand3_path   = 0

        self.is_dram_ = is_dram_

        # widths arrays
        self.w_L1_nand2_n = [0.0]*MAX_NUMBER_GATES_STAGE
        self.w_L1_nand2_p = [0.0]*MAX_NUMBER_GATES_STAGE
        self.w_L1_nand3_n = [0.0]*MAX_NUMBER_GATES_STAGE
        self.w_L1_nand3_p = [0.0]*MAX_NUMBER_GATES_STAGE

        # CHECK - why instantiate here
        self.w_L2_n       = [0.0]*MAX_NUMBER_GATES_STAGE
        self.w_L2_p       = [0.0]*MAX_NUMBER_GATES_STAGE

        # delay accumulators
        self.delay_nand2_path = 0.0
        self.delay_nand3_path = 0.0

        # power data for each path
        self.power_nand2_path = PowerDef()
        self.power_nand3_path = PowerDef()
        self.power_L2         = PowerDef()

        # area is inherited from Component
        self.area = Area()

        # replicate the constructor logic
        num_addr_bits_dec         = _log2(num_dec_signals)
        blk1_num_input_addr_bits  = (num_addr_bits_dec + 1)//2
        blk2_num_input_addr_bits  = num_addr_bits_dec - blk1_num_input_addr_bits

        # Initialize the first stage widths to 0 (as in the C++ code)
        self.w_L1_nand2_n[0] = 0.0
        self.w_L1_nand2_p[0] = 0.0
        self.w_L1_nand3_n[0] = 0.0
        self.w_L1_nand3_p[0] = 0.0

        # Decide existence logic
        if is_blk1:
            if not is_symbolic(num_addr_bits_dec):
                if num_addr_bits_dec <= 0:
                    return
                elif num_addr_bits_dec < 4:
                    # single predecoder block
                    self.exist = True
                    self.number_input_addr_bits = num_addr_bits_dec
                    self.R_wire_predec_blk_out  = dec.R_wire_dec_out
                    self.C_ld_predec_blk_out    = dec.C_ld_dec_out
                else:
                    self.exist = True
                    self.number_input_addr_bits = blk1_num_input_addr_bits
                    branch_effort_predec_out    = (1 << blk2_num_input_addr_bits)
                    c_ld_dec_gate = (num_dec_per_predec *
                                     gate_C(self.g_tp,
                                                      dec.w_dec_n[0] + dec.w_dec_p[0],
                                                      0,
                                                      self.is_dram_,
                                                      False,
                                                      False))
                    self.R_wire_predec_blk_out = R_wire_predec_blk_out
                    self.C_ld_predec_blk_out   = branch_effort_predec_out * c_ld_dec_gate + C_wire_predec_blk_out
            else:
                # ERROR PATH_APPROX for symbolic
                # self.exist = True
                # self.number_input_addr_bits = 3
                # self.R_wire_predec_blk_out = R_wire_predec_blk_out
                # self.C_ld_predec_blk_out   = 0.0
                # single predecoder block
                self.exist = True
                self.number_input_addr_bits = num_addr_bits_dec
                self.R_wire_predec_blk_out  = dec.R_wire_dec_out
                self.C_ld_predec_blk_out    = dec.C_ld_dec_out
        else:
            # second block
            if not is_symbolic(num_addr_bits_dec):
                if num_addr_bits_dec >= 4:
                    self.exist = True
                    self.number_input_addr_bits = blk2_num_input_addr_bits
                    branch_effort_predec_out = (1 << blk1_num_input_addr_bits)
                    c_ld_dec_gate = (num_dec_per_predec *
                                     gate_C(self.g_tp,
                                                      dec.w_dec_n[0] + dec.w_dec_p[0],
                                                      0,
                                                      self.is_dram_,
                                                      False,
                                                      False))
                    self.R_wire_predec_blk_out = R_wire_predec_blk_out
                    self.C_ld_predec_blk_out   = branch_effort_predec_out*c_ld_dec_gate + C_wire_predec_blk_out
                else:
                    # no block
                    pass
            # ERROR PATH_APPROX for symbolic, possibl do 50/50
            # more likely that (num_addr_bits_dec >= 4) will happen?
            else:
                # #PATH_APPROX for symbolic
                # self.exist = True
                # self.number_input_addr_bits = 4
                # self.R_wire_predec_blk_out  = R_wire_predec_blk_out
                # self.C_ld_predec_blk_out    = 0.0
                self.exist = True
                self.number_input_addr_bits = blk2_num_input_addr_bits
                branch_effort_predec_out = (1 << blk1_num_input_addr_bits)
                c_ld_dec_gate = (num_dec_per_predec *
                                    gate_C(self.g_tp,
                                                    dec.w_dec_n[0] + dec.w_dec_p[0],
                                                    0,
                                                    self.is_dram_,
                                                    False,
                                                    False))
                self.R_wire_predec_blk_out = R_wire_predec_blk_out
                self.C_ld_predec_blk_out   = branch_effort_predec_out*c_ld_dec_gate + C_wire_predec_blk_out

        # now do the sizing & area
        self.compute_widths()
        self.compute_area()

    def compute_widths(self):
        """
        Translate from PredecBlk::compute_widths() (C++ code),
        filling in the big switch logic and the logical_effort calls.
        """

        if not self.exist:
            return

        p_to_n_sz_ratio = pmos_to_nmos_sz_ratio(self.g_tp, self.is_dram_)
        gnand2 = (2 + p_to_n_sz_ratio) / (1 + p_to_n_sz_ratio)
        gnand3 = (3 + p_to_n_sz_ratio) / (1 + p_to_n_sz_ratio)

        # Switch on number_input_addr_bits
        if self.number_input_addr_bits == 1:
            self.flag_two_unique_paths     = False
            self.number_inputs_L1_gate     = 2
            self.flag_L2_gate              = 0
        elif self.number_input_addr_bits == 2:
            self.flag_two_unique_paths     = False
            self.number_inputs_L1_gate     = 2
            self.flag_L2_gate              = 0
        elif self.number_input_addr_bits == 3:
            self.flag_two_unique_paths     = False
            self.number_inputs_L1_gate     = 3
            self.flag_L2_gate              = 0
        elif self.number_input_addr_bits == 4:
            self.flag_two_unique_paths     = False
            self.number_inputs_L1_gate     = 2
            self.flag_L2_gate              = 2
            self.branch_effort_nand2_gate_output = 4
        elif self.number_input_addr_bits == 5:
            self.flag_two_unique_paths     = True
            self.flag_L2_gate              = 2
            self.branch_effort_nand2_gate_output = 8
            self.branch_effort_nand3_gate_output = 4
        elif self.number_input_addr_bits == 6:
            self.flag_two_unique_paths     = False
            self.number_inputs_L1_gate     = 3
            self.flag_L2_gate              = 2
            self.branch_effort_nand3_gate_output = 8
        elif self.number_input_addr_bits == 7:
            self.flag_two_unique_paths     = True
            self.flag_L2_gate              = 3
            self.branch_effort_nand2_gate_output = 32
            self.branch_effort_nand3_gate_output = 16
        elif self.number_input_addr_bits == 8:
            self.flag_two_unique_paths     = True
            self.flag_L2_gate              = 3
            self.branch_effort_nand2_gate_output = 64
            self.branch_effort_nand3_gate_output = 32
        elif self.number_input_addr_bits == 9:
            self.flag_two_unique_paths     = False
            self.number_inputs_L1_gate     = 3
            self.flag_L2_gate              = 3
            self.branch_effort_nand3_gate_output = 64
        else:
            # CHECK
            assert(False)

        # If there's a second level
        if self.flag_L2_gate:
            if self.flag_L2_gate == 2:
                self.w_L2_n[0] = 2.0 * self.g_tp.min_w_nmos_
                base_g = gnand2
            else:  # == 3
                self.w_L2_n[0] = 3.0 * self.g_tp.min_w_nmos_
                base_g = gnand3

            self.w_L2_p[0] = p_to_n_sz_ratio * self.g_tp.min_w_nmos_

            c_input_stage = (
                gate_C(self.g_tp, self.w_L2_n[0], 0, self.is_dram_)
                + gate_C(self.g_tp, self.w_L2_p[0], 0, self.is_dram_)
            )
            F_L2 = (self.C_ld_predec_blk_out / c_input_stage) * base_g

            self.number_gates_L2 = logical_effort(
                self.g_tp,
                self.min_number_gates_L2,
                base_g,
                F_L2,
                self.w_L2_n,
                self.w_L2_p,
                self.C_ld_predec_blk_out,
                p_to_n_sz_ratio,
                self.is_dram_,
                False,
                self.g_tp.max_w_nmos_
            )

            # L1: NAND2 path (if needed)
            if self.flag_two_unique_paths or (self.number_inputs_L1_gate == 2):
                c_load_nand2_path = self.branch_effort_nand2_gate_output * (
                    gate_C(self.g_tp, self.w_L2_n[0], 0, self.is_dram_)
                    + gate_C(self.g_tp, self.w_L2_p[0], 0, self.is_dram_)
                )
                self.w_L1_nand2_n[0] = 2.0 * self.g_tp.min_w_nmos_
                self.w_L1_nand2_p[0] = p_to_n_sz_ratio * self.g_tp.min_w_nmos_

                c_first = (
                    gate_C(self.g_tp, self.w_L1_nand2_n[0], 0, self.is_dram_)
                    + gate_C(self.g_tp, self.w_L1_nand2_p[0], 0, self.is_dram_)
                )
                F_n2 = gnand2 * c_load_nand2_path / c_first

                self.number_gates_L1_nand2_path = logical_effort(
                    self.g_tp,
                    self.min_number_gates_L1,
                    gnand2,
                    F_n2,
                    self.w_L1_nand2_n,
                    self.w_L1_nand2_p,
                    c_load_nand2_path,
                    p_to_n_sz_ratio,
                    self.is_dram_,
                    False,
                    self.g_tp.max_w_nmos_
                )

            # L1: NAND3 path (if needed)
            if self.flag_two_unique_paths or (self.number_inputs_L1_gate == 3):
                c_load_nand3_path = self.branch_effort_nand3_gate_output * (
                    gate_C(self.g_tp, self.w_L2_n[0], 0, self.is_dram_)
                    + gate_C(self.g_tp, self.w_L2_p[0], 0, self.is_dram_)
                )
                self.w_L1_nand3_n[0] = 3.0 * self.g_tp.min_w_nmos_
                self.w_L1_nand3_p[0] = p_to_n_sz_ratio * self.g_tp.min_w_nmos_

                c_first3 = (
                    gate_C(self.g_tp, self.w_L1_nand3_n[0], 0, self.is_dram_)
                    + gate_C(self.g_tp, self.w_L1_nand3_p[0], 0, self.is_dram_)
                )
                # CHECK
                F_n3 = gnand3 * c_load_nand3_path / c_first3

                self.number_gates_L1_nand3_path = logical_effort(
                    self.g_tp,
                    self.min_number_gates_L1,
                    gnand3,
                    F_n3,
                    self.w_L1_nand3_n,
                    self.w_L1_nand3_p,
                    c_load_nand3_path,
                    p_to_n_sz_ratio,
                    self.is_dram_,
                    False,
                    self.g_tp.max_w_nmos_
                )

        else:
            # no second level
            if self.number_inputs_L1_gate == 2:
                self.w_L1_nand2_n[0] = 2.0 * self.g_tp.min_w_nmos_
                self.w_L1_nand2_p[0] = p_to_n_sz_ratio * self.g_tp.min_w_nmos_

                c_first = (
                    gate_C(self.g_tp, self.w_L1_nand2_n[0], 0, self.is_dram_)
                    + gate_C(self.g_tp, self.w_L1_nand2_p[0], 0, self.is_dram_)
                )
                # CHECK
                F_single = gnand2 * (self.C_ld_predec_blk_out / c_first)

                self.number_gates_L1_nand2_path = logical_effort(
                    self.g_tp,
                    self.min_number_gates_L1,
                    gnand2,
                    F_single,
                    self.w_L1_nand2_n,
                    self.w_L1_nand2_p,
                    self.C_ld_predec_blk_out,
                    p_to_n_sz_ratio,
                    self.is_dram_,
                    False,
                    self.g_tp.max_w_nmos_
                )
            elif self.number_inputs_L1_gate == 3:
                self.w_L1_nand3_n[0] = 3.0 * self.g_tp.min_w_nmos_
                self.w_L1_nand3_p[0] = p_to_n_sz_ratio * self.g_tp.min_w_nmos_

                c_first = (
                    gate_C(self.g_tp, self.w_L1_nand3_n[0], 0, self.is_dram_)
                    + gate_C(self.g_tp, self.w_L1_nand3_p[0], 0, self.is_dram_)
                )
                F_single = gnand3 * (self.C_ld_predec_blk_out / c_first)

                self.number_gates_L1_nand3_path = logical_effort(
                    self.g_tp,
                    self.min_number_gates_L1,
                    gnand3,
                    F_single,
                    self.w_L1_nand3_n,
                    self.w_L1_nand3_p,
                    self.C_ld_predec_blk_out,
                    p_to_n_sz_ratio,
                    self.is_dram_,
                    False,
                    self.g_tp.max_w_nmos_
                )

    def compute_area(self):
        """
        Summation of gate areas in the 2-level or 1-level predec,
        also sets the leakages.
        """
        if not self.exist:
            return

        # replicate the switch logic to determine how many NAND2 or NAND3 blocks
        # needed in the L1 stage, plus how many in the L2
        num_L1_nand2 = 0
        num_L1_nand3 = 0
        num_L2       = 0

        # base area/leak of the first gate in each path (NAND2, NAND3)
        tot_area_L1_nand2 = compute_gate_area(
            self.g_tp, NAND, 2,
            self.w_L1_nand2_p[0],
            self.w_L1_nand2_n[0],
            self.g_tp.cell_h_def
        )
        leak_L1_nand2 = cmos_Isub_leakage(
            self.g_tp,
            self.w_L1_nand2_n[0],
            self.w_L1_nand2_p[0],
            2,
            NAND,
            self.is_dram_
        )
        gate_leak_L1_nand2 = cmos_Ig_leakage(
            self.g_tp,
            self.w_L1_nand2_n[0],
            self.w_L1_nand2_p[0],
            2,
            NAND,
            self.is_dram_
        )

        tot_area_L1_nand3 = 0.0
        leak_L1_nand3     = 0.0
        gate_leak_L1_nand3= 0.0

        # if the L1 gate is indeed NAND3, we compute those
        if self.number_inputs_L1_gate == 3:
            tot_area_L1_nand3 = compute_gate_area(
                self.g_tp, NAND, 3,
                self.w_L1_nand3_p[0],
                self.w_L1_nand3_n[0],
                self.g_tp.cell_h_def
            )
            leak_L1_nand3 = cmos_Isub_leakage(
                self.g_tp,
                self.w_L1_nand3_n[0],
                self.w_L1_nand3_p[0],
                3,
                NAND,
                self.is_dram_
            )
            gate_leak_L1_nand3 = cmos_Ig_leakage(
                self.g_tp,
                self.w_L1_nand3_n[0],
                self.w_L1_nand3_p[0],
                3,
                NAND,
                self.is_dram_
            )

        # based on number_input_addr_bits
        if self.number_input_addr_bits == 1:
            num_L1_nand2 = 2
            num_L2       = 0
            self.num_L1_active_nand2_path = 1
            self.num_L1_active_nand3_path = 0
        elif self.number_input_addr_bits == 2:
            num_L1_nand2 = 4
            num_L2       = 0
            self.num_L1_active_nand2_path = 1
            self.num_L1_active_nand3_path = 0
        elif self.number_input_addr_bits == 3:
            num_L1_nand3 = 8
            num_L2       = 0
            self.num_L1_active_nand2_path = 0
            self.num_L1_active_nand3_path = 1
        elif self.number_input_addr_bits == 4:
            num_L1_nand2 = 8
            num_L2       = 16
            self.num_L1_active_nand2_path = 2
            self.num_L1_active_nand3_path = 0
        elif self.number_input_addr_bits == 5:
            num_L1_nand2 = 4
            num_L1_nand3 = 8
            num_L2       = 32
            self.num_L1_active_nand2_path = 1
            self.num_L1_active_nand3_path = 1
        elif self.number_input_addr_bits == 6:
            num_L1_nand3 = 16
            num_L2       = 64
            self.num_L1_active_nand2_path = 0
            self.num_L1_active_nand3_path = 2
        elif self.number_input_addr_bits == 7:
            num_L1_nand2 = 8
            num_L1_nand3 = 8
            num_L2       = 128
            self.num_L1_active_nand2_path = 2
            self.num_L1_active_nand3_path = 1
        elif self.number_input_addr_bits == 8:
            num_L1_nand2 = 4
            num_L1_nand3 = 16
            num_L2       = 256
            self.num_L1_active_nand2_path = 2
            self.num_L1_active_nand3_path = 2
        elif self.number_input_addr_bits == 9:
            num_L1_nand3 = 24
            num_L2       = 512
            self.num_L1_active_nand2_path = 0
            self.num_L1_active_nand3_path = 3

        # for each additional gate in the L1_nand2 path
        for i in range(1, self.number_gates_L1_nand2_path):
            tot_area_L1_nand2 += compute_gate_area(
                self.g_tp, INV, 1,
                self.w_L1_nand2_p[i],
                self.w_L1_nand2_n[i],
                self.g_tp.cell_h_def
            )
            leak_L1_nand2 += cmos_Isub_leakage(
                self.g_tp,
                self.w_L1_nand2_n[i],
                self.w_L1_nand2_p[i],
                2,  # the original code might pass “1, inv” here, but we follow the same pattern
                NAND,
                self.is_dram_
            )
            gate_leak_L1_nand2 += cmos_Ig_leakage(
                self.g_tp,
                self.w_L1_nand2_n[i],
                self.w_L1_nand2_p[i],
                2,
                NAND,
                self.is_dram_
            )

        tot_area_L1_nand2  *= num_L1_nand2
        leak_L1_nand2      *= num_L1_nand2
        gate_leak_L1_nand2 *= num_L1_nand2

        # for each additional gate in the L1_nand3 path
        for i in range(1, self.number_gates_L1_nand3_path):
            tot_area_L1_nand3 += compute_gate_area(
                self.g_tp, INV, 1,
                self.w_L1_nand3_p[i],
                self.w_L1_nand3_n[i],
                self.g_tp.cell_h_def
            )
            leak_L1_nand3 += cmos_Isub_leakage(
                self.g_tp,
                self.w_L1_nand3_n[i],
                self.w_L1_nand3_p[i],
                3,
                NAND,
                self.is_dram_
            )
            gate_leak_L1_nand3 += cmos_Ig_leakage(
                self.g_tp,
                self.w_L1_nand3_n[i],
                self.w_L1_nand3_p[i],
                3,
                NAND,
                self.is_dram_
            )

        tot_area_L1_nand3  *= num_L1_nand3
        leak_L1_nand3      *= num_L1_nand3
        gate_leak_L1_nand3 *= num_L1_nand3

        cumulative_area_L1 = tot_area_L1_nand2 + tot_area_L1_nand3

        # second level
        cumulative_area_L2 = 0.0
        leakage_L2         = 0.0
        gate_leakage_L2    = 0.0

        if self.flag_L2_gate == 2:
            # NAND2
            base_area_L2 = compute_gate_area(
                self.g_tp, NAND, 2,
                self.w_L2_p[0], self.w_L2_n[0],
                self.g_tp.cell_h_def
            )
            base_leak_L2 = cmos_Isub_leakage(
                self.g_tp,
                self.w_L2_n[0], self.w_L2_p[0],
                2,
                NAND,
                self.is_dram_
            )
            base_gate_L2 = cmos_Ig_leakage(
                self.g_tp,
                self.w_L2_n[0], self.w_L2_p[0],
                2,
                NAND,
                self.is_dram_
            )
        elif self.flag_L2_gate == 3:
            # NAND3
            base_area_L2 = compute_gate_area(
                self.g_tp, NAND, 3,
                self.w_L2_p[0], self.w_L2_n[0],
                self.g_tp.cell_h_def
            )
            base_leak_L2 = cmos_Isub_leakage(
                self.g_tp,
                self.w_L2_n[0], self.w_L2_p[0],
                3,
                NAND,
                self.is_dram_
            )
            base_gate_L2 = cmos_Ig_leakage(
                self.g_tp,
                self.w_L2_n[0], self.w_L2_p[0],
                3,
                NAND,
                self.is_dram_
            )
        else:
            # no L2 gate
            base_area_L2 = 0.0
            base_leak_L2 = 0.0
            base_gate_L2 = 0.0

        # Additional inverters in L2
        area_sum_L2 = base_area_L2
        leak_sum_L2 = base_leak_L2
        gate_sum_L2 = base_gate_L2

        for i in range(1, self.number_gates_L2):
            area_sum_L2 += compute_gate_area(
                self.g_tp, INV, 1,
                self.w_L2_p[i], self.w_L2_n[i],
                self.g_tp.cell_h_def
            )
            leak_sum_L2 += cmos_Isub_leakage(
                self.g_tp,
                self.w_L2_n[i], self.w_L2_p[i],
                1,  # 1 for inverter
                INV,
                self.is_dram_
            )
            gate_sum_L2 += cmos_Ig_leakage(
                self.g_tp,
                self.w_L2_n[i], self.w_L2_p[i],
                1,
                INV,
                self.is_dram_
            )

        area_sum_L2 *= num_L2
        leak_sum_L2 *= num_L2
        gate_sum_L2 *= num_L2

        cumulative_area_L2 = area_sum_L2
        leakage_L2         = leak_sum_L2
        gate_leakage_L2    = gate_sum_L2

        # final
        self.power_nand2_path.readOp.leakage      = leak_L1_nand2 * self.g_tp.peri_global.Vdd
        self.power_nand2_path.readOp.gate_leakage = gate_leak_L1_nand2 * self.g_tp.peri_global.Vdd

        self.power_nand3_path.readOp.leakage      = leak_L1_nand3 * self.g_tp.peri_global.Vdd
        self.power_nand3_path.readOp.gate_leakage = gate_leak_L1_nand3 * self.g_tp.peri_global.Vdd

        self.power_L2.readOp.leakage      = leakage_L2 * self.g_tp.peri_global.Vdd
        self.power_L2.readOp.gate_leakage = gate_leakage_L2 * self.g_tp.peri_global.Vdd

        self.area.set_area(cumulative_area_L1 + cumulative_area_L2)

    # CHECK - note that PredecBlk different function signature
    def compute_delays(self, inrisetime_nand2, inrisetime_nand3):
        """
        Python translation of:
        pair<double, double> PredecBlk::compute_delays(pair<double,double> inrisetime)

        The input is two separate rising times: inrisetime_nand2_path, inrisetime_nand3_path.
        We return a Python tuple (outrisetime_nand2_path, outrisetime_nand3_path).

        This function updates:
        - self.delay_nand2_path, self.delay_nand3_path accumulators
        - self.power_nand2_path.readOp.dynamic, self.power_nand3_path.readOp.dynamic
        - self.power_L2.readOp.dynamic
        - final return value is (out_nand2, out_nand3)
        """

        # The result we will return:
        outrise_nand2 = 0.0
        outrise_nand3 = 0.0

        # Local references
        Vdd = self.g_tp.peri_global.Vdd

        # If the block does not exist, simply return (0,0)
        if not self.exist:
            return (0.0, 0.0)

        # Shorthand references for code clarity
        # "inrisetime_nand2_path" vs. "inrisetime_nand3_path"
        nand2_in = inrisetime_nand2
        nand3_in = inrisetime_nand3

        # -- 1) Delay in the 1st-level NAND2 path (if either two-unique-paths or is a 2-input gate)
        if self.flag_two_unique_paths or (self.number_inputs_L1_gate == 2):
            # First gate is a NAND2
            rd = tr_R_on(self.w_L1_nand2_n[0],
                        channel_type=NCH,   # integer constant for n-channel
                        num_stacked=2,
                        is_dram_=self.is_dram_)
            c_load = gate_C(self.w_L1_nand2_n[1] + self.w_L1_nand2_p[1],
                            0.0,
                            self.is_dram_)
            c_intrinsic = (2.0 * drain_C_(self.w_L1_nand2_p[0],
                                        PCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_)
                        + drain_C_(self.w_L1_nand2_n[0],
                                    NCH, 2, 1,
                                    self.g_tp.cell_h_def,
                                    self.is_dram_))
            tf = rd * (c_intrinsic + c_load)
            this_delay = horowitz(nand2_in, tf, 0.5, 0.5, RISE)
            self.delay_nand2_path += this_delay
            nand2_in = this_delay / (1.0 - 0.5)

            self.power_nand2_path.readOp.dynamic += (c_load + c_intrinsic) * (Vdd * Vdd)

            # Add delays of all but the last inverter in L1 chain
            for i in range(1, self.number_gates_L1_nand2_path - 1):
                rd = tr_R_on(self.w_L1_nand2_n[i],
                            channel_type=NCH, num_stacked=1,
                            is_dram_=self.is_dram_)
                c_load = gate_C((self.w_L1_nand2_n[i+1] + self.w_L1_nand2_p[i+1]),
                                0.0,
                                self.is_dram_)
                c_intrinsic = (drain_C_(self.w_L1_nand2_p[i],
                                        PCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_)
                            + drain_C_(self.w_L1_nand2_n[i],
                                        NCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_))
                tf = rd * (c_intrinsic + c_load)
                this_delay = horowitz(nand2_in, tf, 0.5, 0.5, RISE)
                self.delay_nand2_path += this_delay
                nand2_in = this_delay / (1.0 - 0.5)

                self.power_nand2_path.readOp.dynamic += (c_intrinsic + c_load) * (Vdd * Vdd)

            # The last inverter in the chain
            i = self.number_gates_L1_nand2_path - 1
            rd = tr_R_on(self.w_L1_nand2_n[i],
                        channel_type=NCH, num_stacked=1,
                        is_dram_=self.is_dram_)

            if self.flag_L2_gate:
                # if there is a second level, the "load" is that second-level gate
                c_load = (self.branch_effort_nand2_gate_output *
                        (gate_C(self.w_L2_n[0], 0.0, self.is_dram_)
                        + gate_C(self.w_L2_p[0], 0.0, self.is_dram_)))
                c_intrinsic = (drain_C_(self.w_L1_nand2_p[i],
                                        PCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_)
                            + drain_C_(self.w_L1_nand2_n[i],
                                        NCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_))
                tf = rd * (c_intrinsic + c_load)
                this_delay = horowitz(nand2_in, tf, 0.5, 0.5, RISE)
                self.delay_nand2_path += this_delay
                nand2_in = this_delay / (1.0 - 0.5)

                self.power_nand2_path.readOp.dynamic += (c_intrinsic + c_load) * (Vdd * Vdd)
            else:
                # first-level path drives the final load C_ld_predec_blk_out
                c_load = self.C_ld_predec_blk_out
                c_intrinsic = (drain_C_(self.w_L1_nand2_p[i],
                                        PCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_)
                            + drain_C_(self.w_L1_nand2_n[i],
                                        NCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_))
                # note: the original c++ adds: + R_wire_predec_blk_out * c_load/2
                tf = rd * (c_intrinsic + c_load) + self.R_wire_predec_blk_out * c_load * 0.5
                this_delay = horowitz(nand2_in, tf, 0.5, 0.5, RISE)
                self.delay_nand2_path += this_delay
                outrise_nand2 = this_delay / (1.0 - 0.5)  # ret_val.first
                self.power_nand2_path.readOp.dynamic += (c_intrinsic + c_load) * (Vdd * Vdd)

        # -- 2) Delay in the 1st-level NAND3 path (if either two_unique_paths or 3-input gate)
        if self.flag_two_unique_paths or (self.number_inputs_L1_gate == 3):
            # First gate is NAND3
            rd = tr_R_on(self.w_L1_nand3_n[0],
                        channel_type=NCH, num_stacked=3,
                        is_dram_=self.is_dram_)
            c_load = gate_C(self.w_L1_nand3_n[1] + self.w_L1_nand3_p[1],
                            0.0,
                            self.is_dram_)
            c_intrinsic = (3.0 * drain_C_(self.w_L1_nand3_p[0],
                                        PCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_)
                        + drain_C_(self.w_L1_nand3_n[0],
                                    NCH, 3, 1,
                                    self.g_tp.cell_h_def,
                                    self.is_dram_))
            tf = rd * (c_intrinsic + c_load)
            this_delay = horowitz(nand3_in, tf, 0.5, 0.5, RISE)
            self.delay_nand3_path += this_delay
            nand3_in = this_delay / (1.0 - 0.5)
            self.power_nand3_path.readOp.dynamic += (c_intrinsic + c_load) * (Vdd * Vdd)

            # middle inverters
            for i in range(1, self.number_gates_L1_nand3_path - 1):
                rd = tr_R_on(self.w_L1_nand3_n[i], NCH, 1, self.is_dram_)
                c_load = gate_C(self.w_L1_nand3_n[i+1] + self.w_L1_nand3_p[i+1],
                                0.0,
                                self.is_dram_)
                c_intrinsic = (drain_C_(self.w_L1_nand3_p[i],
                                        PCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_)
                            + drain_C_(self.w_L1_nand3_n[i],
                                        NCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_))
                tf = rd*(c_intrinsic + c_load)
                this_delay = horowitz(nand3_in, tf, 0.5, 0.5, RISE)
                self.delay_nand3_path += this_delay
                nand3_in = this_delay/(1.0 - 0.5)
                self.power_nand3_path.readOp.dynamic += (c_intrinsic + c_load) * (Vdd * Vdd)

            # last stage in L1
            i = self.number_gates_L1_nand3_path - 1
            rd = tr_R_on(self.w_L1_nand3_n[i], NCH, 1, self.is_dram_)
            if self.flag_L2_gate:
                c_load = (self.branch_effort_nand3_gate_output
                        * (gate_C(self.w_L2_n[0], 0, self.is_dram_)
                            + gate_C(self.w_L2_p[0], 0, self.is_dram_)))
                c_intrinsic = (drain_C_(self.w_L1_nand3_p[i],
                                        PCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_)
                            + drain_C_(self.w_L1_nand3_n[i],
                                        NCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_))
                tf = rd * (c_intrinsic + c_load)
                this_delay = horowitz(nand3_in, tf, 0.5, 0.5, RISE)
                self.delay_nand3_path += this_delay
                nand3_in = this_delay/(1.0 - 0.5)
                self.power_nand3_path.readOp.dynamic += (c_intrinsic + c_load) * (Vdd * Vdd)
            else:
                # direct to dec output
                c_load = self.C_ld_predec_blk_out
                c_intrinsic = (drain_C_(self.w_L1_nand3_p[i],
                                        PCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_)
                            + drain_C_(self.w_L1_nand3_n[i],
                                        NCH, 1, 1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_))
                tf = rd*(c_intrinsic + c_load) + self.R_wire_predec_blk_out*c_load*0.5
                this_delay = horowitz(nand3_in, tf, 0.5, 0.5, RISE)
                self.delay_nand3_path += this_delay
                outrise_nand3 = this_delay / (1.0 - 0.5)
                self.power_nand3_path.readOp.dynamic += (c_intrinsic + c_load) * (Vdd * Vdd)

        # 3) Delay in the second level (if flag_L2_gate)
        if self.flag_L2_gate:
            # First gate in L2:
            if self.flag_L2_gate == 2:
                # NAND2 in L2
                rd = tr_R_on(self.w_L2_n[0], NCH, 2, self.is_dram_)
                c_load = gate_C(self.w_L2_n[1] + self.w_L2_p[1], 0.0, self.is_dram_)
                c_intrinsic = (2.0 * drain_C_(self.w_L2_p[0], PCH, 1,1,
                                            self.g_tp.cell_h_def,
                                            self.is_dram_)
                            + drain_C_(self.w_L2_n[0], NCH, 2,1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_))
                tf = rd*(c_intrinsic + c_load)
                this_delay = horowitz(nand2_in, tf, 0.5, 0.5, RISE)
                self.delay_nand2_path += this_delay
                nand2_in = this_delay/(1.0 - 0.5)
                self.power_L2.readOp.dynamic += (c_intrinsic + c_load) * (Vdd * Vdd)

            else:
                # NAND3 in L2
                rd = tr_R_on(self.w_L2_n[0], NCH, 3, self.is_dram_)
                c_load = gate_C(self.w_L2_n[1] + self.w_L2_p[1], 0.0, self.is_dram_)
                c_intrinsic = (3.0 * drain_C_(self.w_L2_p[0],
                                            PCH,1,1,
                                            self.g_tp.cell_h_def,
                                            self.is_dram_)
                            + drain_C_(self.w_L2_n[0],
                                        NCH, 3,1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_))
                tf = rd*(c_intrinsic + c_load)
                this_delay = horowitz(nand3_in, tf, 0.5, 0.5, RISE)
                self.delay_nand3_path += this_delay
                nand3_in = this_delay/(1.0 - 0.5)
                self.power_L2.readOp.dynamic += (c_intrinsic + c_load) * (Vdd * Vdd)

            # The middle gates of L2
            for i in range(1, self.number_gates_L2 - 1):
                rd = tr_R_on(self.w_L2_n[i], NCH, 1, self.is_dram_)
                c_load = gate_C(self.w_L2_n[i+1] + self.w_L2_p[i+1], 0.0, self.is_dram_)
                c_intrinsic = (drain_C_(self.w_L2_p[i],
                                        PCH, 1,1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_)
                            + drain_C_(self.w_L2_n[i],
                                        NCH, 1,1,
                                        self.g_tp.cell_h_def,
                                        self.is_dram_))
                tf = rd*(c_intrinsic + c_load)
                # apply to NAND2 path
                this_delay = horowitz(nand2_in, tf, 0.5, 0.5, RISE)
                self.delay_nand2_path += this_delay
                nand2_in = this_delay/(1.0 - 0.5)
                # apply to NAND3 path
                this_delay = horowitz(nand3_in, tf, 0.5, 0.5, RISE)
                self.delay_nand3_path += this_delay
                nand3_in = this_delay/(1.0 - 0.5)

                self.power_L2.readOp.dynamic += (c_intrinsic + c_load) * (Vdd * Vdd)

            # final L2 gate
            i = self.number_gates_L2 - 1
            c_load = self.C_ld_predec_blk_out
            rd = tr_R_on(self.w_L2_n[i], NCH, 1, self.is_dram_)
            c_intrinsic = (drain_C_(self.w_L2_p[i],
                                    PCH,1,1,
                                    self.g_tp.cell_h_def,
                                    self.is_dram_)
                        + drain_C_(self.w_L2_n[i],
                                    NCH,1,1,
                                    self.g_tp.cell_h_def,
                                    self.is_dram_))
            tf = rd*(c_intrinsic + c_load) + self.R_wire_predec_blk_out * c_load * 0.5

            # We do both nand2_in, nand3_in
            this_delay = horowitz(nand2_in, tf, 0.5, 0.5, RISE)
            self.delay_nand2_path += this_delay
            outrise_nand2 = this_delay/(1.0 - 0.5)

            this_delay = horowitz(nand3_in, tf, 0.5, 0.5, RISE)
            self.delay_nand3_path += this_delay
            outrise_nand3 = this_delay/(1.0 - 0.5)

            self.power_L2.readOp.dynamic += (c_intrinsic + c_load)*(Vdd*Vdd)

        # The final "delay" is the max( nand2, nand3 )
        self.delay = symbolic_convex_max(outrise_nand2, outrise_nand3)
        return (outrise_nand2, outrise_nand3)


    def leakage_feedback(self, temperature):
        """
        Python translation of:
        void PredecBlk::leakage_feedback(double temperature)

        The 'temperature' parameter is not used in the C++ code. We keep it for signature consistency.
        """

        if not self.exist:
            # If no predecoder block is needed, do nothing.
            return

        # local variables
        num_L1_nand2 = 0
        num_L1_nand3 = 0
        num_L2       = 0

        # Starting subthreshold/gate leakage currents for NAND2 and NAND3 in the L1 stage
        leak_L1_nand2 = cmos_Isub_leakage(self.w_L1_nand2_n[0],
                                        self.w_L1_nand2_p[0],
                                        2, 
                                        nand, 
                                        self.is_dram_)
        gate_leak_L1_nand2 = cmos_Ig_leakage(self.w_L1_nand2_n[0],
                                            self.w_L1_nand2_p[0],
                                            2, 
                                            nand, 
                                            self.is_dram_)

        # NAND3 path in L1 depends on whether the first gate is actually 3 inputs
        if self.number_inputs_L1_gate != 3:
            leak_L1_nand3      = 0.0
            gate_leak_L1_nand3 = 0.0
        else:
            # If the first gate is NAND3
            leak_L1_nand3 = cmos_Isub_leakage(self.w_L1_nand3_n[0],
                                            self.w_L1_nand3_p[0],
                                            3,
                                            nand)  # not passing is_dram_ in original c++ for the first call
            gate_leak_L1_nand3 = cmos_Ig_leakage(self.w_L1_nand3_n[0],
                                                self.w_L1_nand3_p[0],
                                                3,
                                                nand)

        #
        # Switch on self.number_input_addr_bits to figure out how many L1 NAND2, L1 NAND3, L2 gates, etc.
        #
        if   self.number_input_addr_bits == 1:
            num_L1_nand2 = 2
            num_L2       = 0
            self.num_L1_active_nand2_path = 1
            self.num_L1_active_nand3_path = 0
        elif self.number_input_addr_bits == 2:
            num_L1_nand2 = 4
            num_L2       = 0
            self.num_L1_active_nand2_path = 1
            self.num_L1_active_nand3_path = 0
        elif self.number_input_addr_bits == 3:
            num_L1_nand3 = 8
            num_L2       = 0
            self.num_L1_active_nand2_path = 0
            self.num_L1_active_nand3_path = 1
        elif self.number_input_addr_bits == 4:
            num_L1_nand2 = 8
            num_L2       = 16
            self.num_L1_active_nand2_path = 2
            self.num_L1_active_nand3_path = 0
        elif self.number_input_addr_bits == 5:
            num_L1_nand2 = 4
            num_L1_nand3 = 8
            num_L2       = 32
            self.num_L1_active_nand2_path = 1
            self.num_L1_active_nand3_path = 1
        elif self.number_input_addr_bits == 6:
            num_L1_nand3 = 16
            num_L2       = 64
            self.num_L1_active_nand2_path = 0
            self.num_L1_active_nand3_path = 2
        elif self.number_input_addr_bits == 7:
            num_L1_nand2 = 8
            num_L1_nand3 = 8
            num_L2       = 128
            self.num_L1_active_nand2_path = 2
            self.num_L1_active_nand3_path = 1
        elif self.number_input_addr_bits == 8:
            num_L1_nand2 = 4
            num_L1_nand3 = 16
            num_L2       = 256
            self.num_L1_active_nand2_path = 2
            self.num_L1_active_nand3_path = 2
        elif self.number_input_addr_bits == 9:
            num_L1_nand3 = 24
            num_L2       = 512
            self.num_L1_active_nand2_path = 0
            self.num_L1_active_nand3_path = 3
        else:
            # The original code has `default: break;` which effectively does nothing
            pass

        #
        # Add in the subthreshold/gate leakage from the rest of the L1 NAND2 path gates
        #
        for i in range(1, self.number_gates_L1_nand2_path):
            leak_L1_nand2 += cmos_Isub_leakage(self.w_L1_nand2_n[i],
                                            self.w_L1_nand2_p[i],
                                            2, 
                                            nand, 
                                            self.is_dram_)
            gate_leak_L1_nand2 += cmos_Ig_leakage(self.w_L1_nand2_n[i],
                                                self.w_L1_nand2_p[i],
                                                2, 
                                                nand, 
                                                self.is_dram_)

        leak_L1_nand2      *= num_L1_nand2
        gate_leak_L1_nand2 *= num_L1_nand2

        #
        # Similarly for NAND3 path gates in L1
        #
        for i in range(1, self.number_gates_L1_nand3_path):
            leak_L1_nand3 += cmos_Isub_leakage(self.w_L1_nand3_n[i],
                                            self.w_L1_nand3_p[i],
                                            3, 
                                            nand, 
                                            self.is_dram_)
            gate_leak_L1_nand3 += cmos_Ig_leakage(self.w_L1_nand3_n[i],
                                                self.w_L1_nand3_p[i],
                                                3, 
                                                nand, 
                                                self.is_dram_)

        leak_L1_nand3      *= num_L1_nand3
        gate_leak_L1_nand3 *= num_L1_nand3

        #
        # L2 portion
        #
        leakage_L2      = 0.0
        gate_leakage_L2 = 0.0

        if self.flag_L2_gate == 2:
            leakage_L2      = cmos_Isub_leakage(self.w_L2_n[0],
                                                self.w_L2_p[0],
                                                2, 
                                                nand, 
                                                self.is_dram_)
            gate_leakage_L2 = cmos_Ig_leakage(self.w_L2_n[0],
                                            self.w_L2_p[0],
                                            2, 
                                            nand, 
                                            self.is_dram_)
        elif self.flag_L2_gate == 3:
            leakage_L2      = cmos_Isub_leakage(self.w_L2_n[0],
                                                self.w_L2_p[0],
                                                3, 
                                                nand, 
                                                self.is_dram_)
            gate_leakage_L2 = cmos_Ig_leakage(self.w_L2_n[0],
                                            self.w_L2_p[0],
                                            3, 
                                            nand, 
                                            self.is_dram_)

        for i in range(1, self.number_gates_L2):
            leakage_L2      += cmos_Isub_leakage(self.w_L2_n[i],
                                                self.w_L2_p[i],
                                                2, 
                                                inv, 
                                                self.is_dram_)
            gate_leakage_L2 += cmos_Ig_leakage(self.w_L2_n[i],
                                            self.w_L2_p[i],
                                            2, 
                                            inv, 
                                            self.is_dram_)

        leakage_L2      *= num_L2
        gate_leakage_L2 *= num_L2

        #
        # Finally assign these scaled leakage currents into the class-level power structures
        # multiplied by supply voltage
        #
        supply = self.g_tp.peri_global.Vdd

        self.power_nand2_path.readOp.leakage      = leak_L1_nand2 * supply
        self.power_nand3_path.readOp.leakage      = leak_L1_nand3 * supply
        self.power_L2.readOp.leakage              = leakage_L2    * supply

        self.power_nand2_path.readOp.gate_leakage = gate_leak_L1_nand2 * supply
        self.power_nand3_path.readOp.gate_leakage = gate_leak_L1_nand3 * supply
        self.power_L2.readOp.gate_leakage         = gate_leakage_L2    * supply



###############################################################################
# PredecBlkDrv class
###############################################################################

class PredecBlkDrv(Component):
    """
    Python version of 'PredecBlkDrv' from decoder.cc/decoder.h.
    Fills in the #PATH_APPROX parts for widths, area, delay, and leakage.
    """

    def __init__(self,
                 g_ip,
                 g_tp,
                 way_select,
                 blk,
                 is_dram):
        super().__init__()
        self.g_ip = g_ip
        self.g_tp = g_tp
        self.way_select = way_select
        self.blk = blk
        self.dec = blk.dec
        self.is_dram_ = is_dram

        self.flag_driver_exists = 0
        self.number_input_addr_bits = blk.number_input_addr_bits
        self.number_gates_nand2_path = 0
        self.number_gates_nand3_path = 0
        self.min_number_gates = 2

        self.num_buffers_driving_1_nand2_load = 0
        self.num_buffers_driving_2_nand2_load = 0
        self.num_buffers_driving_4_nand2_load = 0
        self.num_buffers_driving_2_nand3_load = 0
        self.num_buffers_driving_8_nand3_load = 0
        self.num_buffers_nand3_path = 0

        self.c_load_nand2_path_out = 0.0
        self.c_load_nand3_path_out = 0.0
        self.r_load_nand2_path_out = 0.0
        self.r_load_nand3_path_out = 0.0

        self.width_nand2_path_n = [0.0]*MAX_NUMBER_GATES_STAGE
        self.width_nand2_path_p = [0.0]*MAX_NUMBER_GATES_STAGE
        self.width_nand3_path_n = [0.0]*MAX_NUMBER_GATES_STAGE
        self.width_nand3_path_p = [0.0]*MAX_NUMBER_GATES_STAGE

        self.delay_nand2_path = 0.0
        self.delay_nand3_path = 0.0
        self.power_nand2_path = PowerDef()
        self.power_nand3_path = PowerDef()

        self.area = Area()

        # replicate logic from the C++ constructor
        if self.way_select > 1:
            # driver is needed
            self.flag_driver_exists = 1
            self.number_input_addr_bits = self.way_select
            # Check signals in dec
            if self.dec.num_in_signals == 2:
                # NAND2
                self.c_load_nand2_path_out = gate_C(
                    self.g_tp,
                    (self.dec.w_dec_n[0] + self.dec.w_dec_p[0]),
                    0.0,
                    self.is_dram_
                )
                self.num_buffers_driving_2_nand2_load = self.number_input_addr_bits
            elif self.dec.num_in_signals == 3:
                # NAND3
                self.c_load_nand3_path_out = gate_C(
                    self.g_tp,
                    (self.dec.w_dec_n[0] + self.dec.w_dec_p[0]),
                    0.0,
                    self.is_dram_
                )
                self.num_buffers_driving_2_nand3_load = self.number_input_addr_bits
        elif self.way_select == 0:
            # only if the block itself exists
            if self.blk.exist:
                self.flag_driver_exists = 1

        # now compute widths & area
        self.compute_widths()
        self.compute_area()

    def compute_widths(self):
        """
        Replicate PredecBlkDrv::compute_widths logic from the C++ code,
        filling in #PATH_APPROX.
        """
        if not self.flag_driver_exists:
            return

        p_to_n_sz_ratio = pmos_to_nmos_sz_ratio(self.g_tp, self.is_dram_)

        # from the C++: double C_nand2_gate_blk = ...
        C_nand2_gate_blk = gate_C(
            self.g_tp,
            (self.blk.w_L1_nand2_n[0] + self.blk.w_L1_nand2_p[0]),
            0.0,
            self.is_dram_
        )
        C_nand3_gate_blk = gate_C(
            self.g_tp,
            (self.blk.w_L1_nand3_n[0] + self.blk.w_L1_nand3_p[0]),
            0.0,
            self.is_dram_
        )

        # The C++ code does the switch based on way_select == 0
        # to figure out how many loads we have to drive, c_load_nand2_path_out, etc.
        # For convenience, replicate that logic:

        if self.way_select == 0:
            # we are not driving "way_select > 1" but we do exist
            # so the predecoder block driver is used to generate
            # the signals from the H-tree
            if self.blk.number_input_addr_bits == 1:
                # 2 NAND2 gates
                self.num_buffers_driving_2_nand2_load = 1
                self.c_load_nand2_path_out = 2.0 * C_nand2_gate_blk
            elif self.blk.number_input_addr_bits == 2:
                # 4 NAND2 gates
                self.num_buffers_driving_4_nand2_load = 2
                self.c_load_nand2_path_out = 4.0 * C_nand2_gate_blk
            elif self.blk.number_input_addr_bits == 3:
                # 8 NAND3 gates
                self.num_buffers_driving_8_nand3_load = 3
                self.c_load_nand3_path_out = 8.0 * C_nand3_gate_blk
            elif self.blk.number_input_addr_bits == 4:
                # 4 + 4 NAND2 gates
                self.num_buffers_driving_4_nand2_load = 4
                self.c_load_nand2_path_out = 4.0 * C_nand2_gate_blk
            elif self.blk.number_input_addr_bits == 5:
                # 4 NAND2 gates, 8 NAND3 gates
                self.num_buffers_driving_4_nand2_load = 2
                self.num_buffers_driving_8_nand3_load = 3
                self.c_load_nand2_path_out = 4.0 * C_nand2_gate_blk
                self.c_load_nand3_path_out = 8.0 * C_nand3_gate_blk
            elif self.blk.number_input_addr_bits == 6:
                # 8 + 8 NAND3 gates
                self.num_buffers_driving_8_nand3_load = 6
                self.c_load_nand3_path_out = 8.0 * C_nand3_gate_blk
            elif self.blk.number_input_addr_bits == 7:
                # 4 + 4 NAND2 gates, 8 NAND3 gates
                self.num_buffers_driving_4_nand2_load = 4
                self.num_buffers_driving_8_nand3_load = 3
                self.c_load_nand2_path_out = 4.0 * C_nand2_gate_blk
                self.c_load_nand3_path_out = 8.0 * C_nand3_gate_blk
            elif self.blk.number_input_addr_bits == 8:
                # 4 NAND2 gates, 8 + 8 NAND3 gates
                self.num_buffers_driving_4_nand2_load = 2
                self.num_buffers_driving_8_nand3_load = 6
                self.c_load_nand2_path_out = 4.0 * C_nand2_gate_blk
                self.c_load_nand3_path_out = 8.0 * C_nand3_gate_blk
            elif self.blk.number_input_addr_bits == 9:
                # 8 + 8 + 8 NAND3 gates
                self.num_buffers_driving_8_nand3_load = 9
                self.c_load_nand3_path_out = 8.0 * C_nand3_gate_blk

        # Next, if we are driving NAND2 (way_select or not):
        c_load_nand2_total = self.c_load_nand2_path_out
        if (self.blk.flag_two_unique_paths or
            (self.blk.number_inputs_L1_gate == 2) or
            (self.number_input_addr_bits == 0) or
            ((self.way_select != 0) and (self.dec.num_in_signals == 2))):
            # set up the first stage widths
            self.width_nand2_path_n[0] = self.g_tp.min_w_nmos_
            self.width_nand2_path_p[0] = p_to_n_sz_ratio * self.width_nand2_path_n[0]

            # compute the total fan-out
            c_first = gate_C(
                self.g_tp,
                (self.width_nand2_path_n[0] + self.width_nand2_path_p[0]),
                0.0,
                self.is_dram_
            )
            F_n2 = (c_load_nand2_total / c_first)

            self.number_gates_nand2_path = logical_effort(
                self.g_tp,
                self.min_number_gates,
                1,  # "g" factor is 1 if we treat this as an inverter chain
                F_n2,
                self.width_nand2_path_n,
                self.width_nand2_path_p,
                c_load_nand2_total,
                p_to_n_sz_ratio,
                self.is_dram_,
                False,
                self.g_tp.max_w_nmos_
            )

        # If we are driving NAND3:
        c_load_nand3_total = self.c_load_nand3_path_out
        if (self.blk.flag_two_unique_paths or
            (self.blk.number_inputs_L1_gate == 3) or
            ((self.way_select != 0) and (self.dec.num_in_signals == 3))):
            self.width_nand3_path_n[0] = self.g_tp.min_w_nmos_
            self.width_nand3_path_p[0] = p_to_n_sz_ratio * self.width_nand3_path_n[0]

            c_first = gate_C(
                self.g_tp,
                (self.width_nand3_path_n[0] + self.width_nand3_path_p[0]),
                0.0,
                self.is_dram_
            )
            F_n3 = (c_load_nand3_total / c_first)

            self.number_gates_nand3_path = logical_effort(
                self.g_tp,
                self.min_number_gates,
                1,
                F_n3,
                self.width_nand3_path_n,
                self.width_nand3_path_p,
                c_load_nand3_total,
                p_to_n_sz_ratio,
                self.is_dram_,
                False,
                self.g_tp.max_w_nmos_
            )

    def compute_area(self):
        """
        Summation of gate areas replicating PredecBlkDrv::compute_area logic.
        """
        area_nand2_path = 0.0
        area_nand3_path = 0.0
        leak_nand2_path = 0.0
        leak_nand3_path = 0.0
        gate_leak_nand2_path = 0.0
        gate_leak_nand3_path = 0.0

        if not self.flag_driver_exists:
            return

        # for all gates in the nand2 path
        for i in range(self.number_gates_nand2_path):
            # area
            area_nand2_path += compute_gate_area(
                self.g_tp,
                INV,  # treat each stage as an inverter
                1,
                self.width_nand2_path_p[i],
                self.width_nand2_path_n[i],
                self.g_tp.cell_h_def
            )
            # subthreshold
            leak_nand2_path += cmos_Isub_leakage(
                self.g_tp,
                self.width_nand2_path_n[i],
                self.width_nand2_path_p[i],
                1,  # 1 input for INV
                INV,
                self.is_dram_
            )
            # gate leakage
            gate_leak_nand2_path += cmos_Ig_leakage(
                self.g_tp,
                self.width_nand2_path_n[i],
                self.width_nand2_path_p[i],
                1,
                INV,
                self.is_dram_
            )

        # multiply by the replication factor
        # from the C++: area_nand2_path *= (num_buffers_driving_1_nand2_load + ...)
        nsum = (self.num_buffers_driving_1_nand2_load +
                self.num_buffers_driving_2_nand2_load +
                self.num_buffers_driving_4_nand2_load)
        area_nand2_path *= nsum
        leak_nand2_path *= nsum
        gate_leak_nand2_path *= nsum

        # for all gates in the nand3 path
        for i in range(self.number_gates_nand3_path):
            area_nand3_path += compute_gate_area(
                self.g_tp,
                INV,
                1,
                self.width_nand3_path_p[i],
                self.width_nand3_path_n[i],
                self.g_tp.cell_h_def
            )
            leak_nand3_path += cmos_Isub_leakage(
                self.g_tp,
                self.width_nand3_path_n[i],
                self.width_nand3_path_p[i],
                1,
                INV,
                self.is_dram_
            )
            gate_leak_nand3_path += cmos_Ig_leakage(
                self.g_tp,
                self.width_nand3_path_n[i],
                self.width_nand3_path_p[i],
                1,
                INV,
                self.is_dram_
            )

        # multiply by the replication factor for nand3 path
        nsum3 = (self.num_buffers_driving_2_nand3_load +
                 self.num_buffers_driving_8_nand3_load)
        area_nand3_path *= nsum3
        leak_nand3_path *= nsum3
        gate_leak_nand3_path *= nsum3

        # store in power & area fields
        self.power_nand2_path.readOp.leakage = leak_nand2_path * self.g_tp.peri_global.Vdd
        self.power_nand3_path.readOp.leakage = leak_nand3_path * self.g_tp.peri_global.Vdd

        self.power_nand2_path.readOp.gate_leakage = gate_leak_nand2_path * self.g_tp.peri_global.Vdd
        self.power_nand3_path.readOp.gate_leakage = gate_leak_nand3_path * self.g_tp.peri_global.Vdd

        self.area.set_area(area_nand2_path + area_nand3_path)

    def compute_delays(self, inrisetime_nand2_path, inrisetime_nand3_path):
        """
        Return (outrisetime_nand2, outrisetime_nand3).
        This replicates PredecBlkDrv::compute_delays from the C++ code.
        """
        outrise_nand2 = 0.0
        outrise_nand3 = 0.0
        Vdd = self.g_tp.peri_global.Vdd

        if not self.flag_driver_exists:
            return (outrise_nand2, outrise_nand3)

        # replicate the for-loops from the c++ code:
        # 1) intermediate stages
        # 2) final stage
        # The user code accumulates in self.delay_nand2_path, self.delay_nand3_path

        # For NAND2 path
        tmp_in_n2 = inrisetime_nand2_path
        for i in range(self.number_gates_nand2_path - 1):
            rd = tr_R_on(self.g_tp, self.width_nand2_path_n[i], NCH, 1, self.is_dram_)
            c_gate_load = gate_C(
                self.g_tp,
                (self.width_nand2_path_n[i+1] + self.width_nand2_path_p[i+1]),
                0.0,
                self.is_dram_
            )
            c_intrinsic = drain_C_(
                self.g_ip, self.g_tp,
                self.width_nand2_path_p[i],
                PCH, 1, 1, self.g_tp.cell_h_def
            ) + drain_C_(
                self.g_ip, self.g_tp,
                self.width_nand2_path_n[i],
                NCH, 1, 1, self.g_tp.cell_h_def
            )
            tf = rd * (c_intrinsic + c_gate_load)
            this_delay = horowitz(
                self.g_ip,
                tmp_in_n2,
                tf,
                0.5,
                0.5,
                RISE
            )
            self.delay_nand2_path += this_delay
            tmp_in_n2 = this_delay / (1.0 - 0.5)
            # dynamic power
            self.power_nand2_path.readOp.dynamic += (c_gate_load + c_intrinsic)*0.5*(Vdd*Vdd)

        # final stage for NAND2
        if self.number_gates_nand2_path > 0:
            i = self.number_gates_nand2_path - 1
            rd = tr_R_on(self.g_tp, self.width_nand2_path_n[i], NCH, 1, self.is_dram_)
            c_intrinsic = drain_C_(
                self.g_ip, self.g_tp,
                self.width_nand2_path_p[i],
                PCH, 1, 1, self.g_tp.cell_h_def
            ) + drain_C_(
                self.g_ip, self.g_tp,
                self.width_nand2_path_n[i],
                NCH, 1, 1, self.g_tp.cell_h_def
            )

            c_load = self.c_load_nand2_path_out
            tf = rd*(c_intrinsic + c_load) + self.r_load_nand2_path_out*(c_load*0.5)

            this_delay = horowitz(
                self.g_ip,
                tmp_in_n2,
                tf,
                0.5,
                0.5,
                RISE
            )
            self.delay_nand2_path += this_delay
            outrise_nand2 = this_delay / (1.0 - 0.5)
            self.power_nand2_path.readOp.dynamic += (c_intrinsic + c_load)*0.5*(Vdd*Vdd)

        # For NAND3 path
        tmp_in_n3 = inrisetime_nand3_path
        for i in range(self.number_gates_nand3_path - 1):
            rd = tr_R_on(self.g_tp, self.width_nand3_path_n[i], NCH, 1, self.is_dram_)
            c_gate_load = gate_C(
                self.g_tp,
                (self.width_nand3_path_n[i+1] + self.width_nand3_path_p[i+1]),
                0.0,
                self.is_dram_
            )
            c_intrinsic = drain_C_(
                self.g_ip, self.g_tp,
                self.width_nand3_path_p[i],
                PCH, 1, 1, self.g_tp.cell_h_def
            ) + drain_C_(
                self.g_ip, self.g_tp,
                self.width_nand3_path_n[i],
                NCH, 1, 1, self.g_tp.cell_h_def
            )
            tf = rd*(c_intrinsic + c_gate_load)
            this_delay = horowitz(
                self.g_ip,
                tmp_in_n3,
                tf,
                0.5,
                0.5,
                RISE
            )
            self.delay_nand3_path += this_delay
            tmp_in_n3 = this_delay / (1.0 - 0.5)
            self.power_nand3_path.readOp.dynamic += (c_gate_load + c_intrinsic)*0.5*(Vdd*Vdd)

        # final stage for NAND3
        if self.number_gates_nand3_path > 0:
            i = self.number_gates_nand3_path - 1
            rd = tr_R_on(self.g_tp, self.width_nand3_path_n[i], NCH, 1, self.is_dram_)
            c_intrinsic = drain_C_(
                self.g_ip, self.g_tp,
                self.width_nand3_path_p[i],
                PCH, 1, 1, self.g_tp.cell_h_def
            ) + drain_C_(
                self.g_ip, self.g_tp,
                self.width_nand3_path_n[i],
                NCH, 1, 1, self.g_tp.cell_h_def
            )
            c_load = self.c_load_nand3_path_out
            tf = rd*(c_intrinsic + c_load) + self.r_load_nand3_path_out*(c_load*0.5)

            this_delay = horowitz(
                self.g_ip,
                tmp_in_n3,
                tf,
                0.5,
                0.5,
                RISE
            )
            self.delay_nand3_path += this_delay
            outrise_nand3 = this_delay / (1.0 - 0.5)
            self.power_nand3_path.readOp.dynamic += (c_intrinsic + c_load)*0.5*(Vdd*Vdd)

        return (outrise_nand2, outrise_nand3)

    def num_addr_bits_nand2_path(self):
        return self.num_buffers_driving_1_nand2_load + \
               self.num_buffers_driving_2_nand2_load + \
               self.num_buffers_driving_4_nand2_load

    def num_addr_bits_nand3_path(self):
        return self.num_buffers_driving_2_nand3_load + \
               self.num_buffers_driving_8_nand3_load


    def get_rdOp_dynamic_E(self, num_act_mats_hor_dir):
        """
        from the code: (num_addr_bits_nand2_path()*power_nand2_path.readOp.dynamic +
                        num_addr_bits_nand3_path()*power_nand3_path.readOp.dynamic)
                        * num_act_mats_hor_dir
        """
        # you might define num_addr_bits_nand2_path() etc., or just do:
        # e.g. (self.number_input_addr_bits) if that's how the code is intended.
        # The c++ does: num_addr_bits_nand2_path()*power_nand2_path + ...
        # #PATH_APPROX: suppose num_addr_bits_nand2_path is:
        # n2_bits = self.number_input_addr_bits if (self.dec.num_in_signals == 2) else 0
        # n3_bits = self.number_input_addr_bits if (self.dec.num_in_signals == 3) else 0
        n2_bits = self.num_addr_bits_nand2_path()
        n3_bits = self.num_addr_bits_nand3_path()

        return (n2_bits * self.power_nand2_path.readOp.dynamic +
                n3_bits * self.power_nand3_path.readOp.dynamic) * num_act_mats_hor_dir

    def leakage_feedback(self, temperature):
        """
        Recompute subthreshold/gate leakage the same way we do in compute_area,
        but ignoring the area part.
        """
        if not self.flag_driver_exists:
            return

        leak_nand2_path = 0.0
        leak_nand3_path = 0.0
        gate_leak_nand2_path = 0.0
        gate_leak_nand3_path = 0.0

        # sum up the subthreshold and gate leakage again for each stage
        for i in range(self.number_gates_nand2_path):
            leak_nand2_path += cmos_Isub_leakage(
                self.g_tp,
                self.width_nand2_path_n[i],
                self.width_nand2_path_p[i],
                1,
                INV,
                self.is_dram_
            )
            gate_leak_nand2_path += cmos_Ig_leakage(
                self.g_tp,
                self.width_nand2_path_n[i],
                self.width_nand2_path_p[i],
                1,
                INV,
                self.is_dram_
            )

        nsum = (self.num_buffers_driving_1_nand2_load +
                self.num_buffers_driving_2_nand2_load +
                self.num_buffers_driving_4_nand2_load)
        leak_nand2_path *= nsum
        gate_leak_nand2_path *= nsum

        for i in range(self.number_gates_nand3_path):
            leak_nand3_path += cmos_Isub_leakage(
                self.g_tp,
                self.width_nand3_path_n[i],
                self.width_nand3_path_p[i],
                1,
                INV,
                self.is_dram_
            )
            gate_leak_nand3_path += cmos_Ig_leakage(
                self.g_tp,
                self.width_nand3_path_n[i],
                self.width_nand3_path_p[i],
                1,
                INV,
                self.is_dram_
            )

        nsum3 = (self.num_buffers_driving_2_nand3_load +
                 self.num_buffers_driving_8_nand3_load)
        leak_nand3_path *= nsum3
        gate_leak_nand3_path *= nsum3

        # update power
        self.power_nand2_path.readOp.leakage = leak_nand2_path * self.g_tp.peri_global.Vdd
        self.power_nand2_path.readOp.gate_leakage = gate_leak_nand2_path * self.g_tp.peri_global.Vdd

        self.power_nand3_path.readOp.leakage = leak_nand3_path * self.g_tp.peri_global.Vdd
        self.power_nand3_path.readOp.gate_leakage = gate_leak_nand3_path * self.g_tp.peri_global.Vdd



###############################################################################
# Predec class
###############################################################################

class Predec(Component):
    """
    Python version of the aggregator 'Predec', which has two PredecBlkDrv and two PredecBlks.
    """

    def __init__(self, drv1, drv2):
        super().__init__()
        self.blk1 = drv1.blk
        self.blk2 = drv2.blk
        self.drv1 = drv1
        self.drv2 = drv2

        self.block_power  = PowerDef()
        self.driver_power = PowerDef()

        # sum up leakages
        self.driver_power.readOp.leakage = (drv1.power_nand2_path.readOp.leakage +
                                            drv1.power_nand3_path.readOp.leakage +
                                            drv2.power_nand2_path.readOp.leakage +
                                            drv2.power_nand3_path.readOp.leakage)
        self.block_power.readOp.leakage  = (self.blk1.power_nand2_path.readOp.leakage +
                                            self.blk1.power_nand3_path.readOp.leakage +
                                            self.blk1.power_L2.readOp.leakage +
                                            self.blk2.power_nand2_path.readOp.leakage +
                                            self.blk2.power_nand3_path.readOp.leakage +
                                            self.blk2.power_L2.readOp.leakage)
        self.power.readOp.leakage = self.driver_power.readOp.leakage + self.block_power.readOp.leakage

        # gate leakage
        self.driver_power.readOp.gate_leakage = (drv1.power_nand2_path.readOp.gate_leakage +
                                                 drv1.power_nand3_path.readOp.gate_leakage +
                                                 drv2.power_nand2_path.readOp.gate_leakage +
                                                 drv2.power_nand3_path.readOp.gate_leakage)
        self.block_power.readOp.gate_leakage  = (self.blk1.power_nand2_path.readOp.gate_leakage +
                                                 self.blk1.power_nand3_path.readOp.gate_leakage +
                                                 self.blk1.power_L2.readOp.gate_leakage +
                                                 self.blk2.power_nand2_path.readOp.gate_leakage +
                                                 self.blk2.power_nand3_path.readOp.gate_leakage +
                                                 self.blk2.power_L2.readOp.gate_leakage)
        self.power.readOp.gate_leakage = self.driver_power.readOp.gate_leakage + self.block_power.readOp.gate_leakage

    def compute_delays(self, inrisetime):
        """
        Predec::compute_delays
        """
        # the code calls compute_delays on drv1, then on blk1, etc.
        tmp_pair1 = self.drv1.compute_delays(inrisetime, inrisetime)
        tmp_pair1 = self.blk1.compute_delays(tmp_pair1)
        tmp_pair2 = self.drv2.compute_delays(inrisetime, inrisetime)
        tmp_pair2 = self.blk2.compute_delays(tmp_pair2)

        # combine
        tmp_pair1 = self.get_max_delay_before_decoder(tmp_pair1, tmp_pair2)

        # dynamic power
        self.driver_power.readOp.dynamic = (self.drv1.num_addr_bits_nand2_path() *
                                            self.drv1.power_nand2_path.readOp.dynamic +
                                            self.drv1.num_addr_bits_nand3_path() *
                                            self.drv1.power_nand3_path.readOp.dynamic +
                                            self.drv2.num_addr_bits_nand2_path() *
                                            self.drv2.power_nand2_path.readOp.dynamic +
                                            self.drv2.num_addr_bits_nand3_path() *
                                            self.drv2.power_nand3_path.readOp.dynamic)
        self.block_power.readOp.dynamic  = (self.blk1.power_nand2_path.readOp.dynamic *
                                            self.blk1.num_L1_active_nand2_path +
                                            self.blk1.power_nand3_path.readOp.dynamic *
                                            self.blk1.num_L1_active_nand3_path +
                                            self.blk1.power_L2.readOp.dynamic +
                                            self.blk2.power_nand2_path.readOp.dynamic *
                                            self.blk1.num_L1_active_nand2_path +
                                            self.blk2.power_nand3_path.readOp.dynamic *
                                            self.blk1.num_L1_active_nand3_path +
                                            self.blk2.power_L2.readOp.dynamic)
        self.power.readOp.dynamic = self.driver_power.readOp.dynamic + self.block_power.readOp.dynamic

        self.delay = tmp_pair1[0]
        return tmp_pair1[1]

    def leakage_feedback(self, temperature):
        """
        same pattern as c++ predec
        """
        self.drv1.leakage_feedback(temperature)
        self.drv2.leakage_feedback(temperature)
        self.blk1.leakage_feedback(temperature)
        self.blk2.leakage_feedback(temperature)

        self.driver_power.readOp.leakage = (self.drv1.power_nand2_path.readOp.leakage +
                                            self.drv1.power_nand3_path.readOp.leakage +
                                            self.drv2.power_nand2_path.readOp.leakage +
                                            self.drv2.power_nand3_path.readOp.leakage)
        self.block_power.readOp.leakage  = (self.blk1.power_nand2_path.readOp.leakage +
                                            self.blk1.power_nand3_path.readOp.leakage +
                                            self.blk1.power_L2.readOp.leakage +
                                            self.blk2.power_nand2_path.readOp.leakage +
                                            self.blk2.power_nand3_path.readOp.leakage +
                                            self.blk2.power_L2.readOp.leakage)
        self.power.readOp.leakage = self.driver_power.readOp.leakage + self.block_power.readOp.leakage

        self.driver_power.readOp.gate_leakage = (self.drv1.power_nand2_path.readOp.gate_leakage +
                                                 self.drv1.power_nand3_path.readOp.gate_leakage +
                                                 self.drv2.power_nand2_path.readOp.gate_leakage +
                                                 self.drv2.power_nand3_path.readOp.gate_leakage)
        self.block_power.readOp.gate_leakage  = (self.blk1.power_nand2_path.readOp.gate_leakage +
                                                 self.blk1.power_nand3_path.readOp.gate_leakage +
                                                 self.blk1.power_L2.readOp.gate_leakage +
                                                 self.blk2.power_nand2_path.readOp.gate_leakage +
                                                 self.blk2.power_nand3_path.readOp.gate_leakage +
                                                 self.blk2.power_L2.readOp.gate_leakage)
        self.power.readOp.gate_leakage = self.driver_power.readOp.gate_leakage + self.block_power.readOp.gate_leakage

    # ERROR PATH_APPROX DOUBE CHECK
    def get_max_delay_before_decoder(self, input_pair1, input_pair2):
        delay1 = self.drv1.delay_nand2_path + self.blk1.delay_nand2_path
        delay2 = self.drv1.delay_nand3_path + self.blk1.delay_nand3_path
        delay3 = self.drv2.delay_nand2_path + self.blk2.delay_nand2_path
        delay4 = self.drv2.delay_nand3_path + self.blk2.delay_nand3_path

        # Initialize return with "delay1" and the corresponding risetime
        ret_delay     = delay1
        ret_risetime  = input_pair1[0]  # C++ used input_pair1.first for nand2 path

        # 2) Compare with delay2
        # If both ret_delay and delay2 are numeric, do a normal numeric comparison
        if not (is_symbolic(ret_delay) or is_symbolic(delay2)):
            if ret_delay < delay2:
                ret_delay    = delay2
                ret_risetime = input_pair1[1]  # second risetime from input_pair1
        else:
            # Switch to symbolic max for ret_delay
            # (or do partial approximation if desired)
            ret_delay = symbolic_convex_max(ret_delay, delay2)
            pass

        # 3) Compare with delay3
        if not (is_symbolic(ret_delay) or is_symbolic(delay3)):
            if ret_delay < delay3:
                ret_delay    = delay3
                ret_risetime = input_pair2[0]  # from the second driver, nand2 path
        else:
            ret_delay = symbolic_convex_max(ret_delay, delay3)
            # same logic for risetime
            pass

        # 4) Compare with delay4
        if not (is_symbolic(ret_delay) or is_symbolic(delay4)):
            if ret_delay < delay4:
                ret_delay    = delay4
                ret_risetime = input_pair2[1]  # from the second driver, nand3 path
        else:
            ret_delay = symbolic_convex_max(ret_delay, delay4)
            # same logic for risetime
            pass

        return (ret_delay, ret_risetime)

    # def get_max_delay_before_decoder(self, input_pair1, input_pair2):
    #     """
    #     The c++ returns <delay, risetime>
    #     in the code it does a stepwise check. 
    #     We can do a symbolic max with #PATH_APPROX if desired.
    #     """
    #     # #PATH_APPROX to avoid piecewise
    #     # For a symbolic-friendly approach, let's do a convex max approximation.
    #     # But the user wants us to pick just the best path, or do we do the stepwise?
    #     # We'll do a symbolic max for demonstration:
    #     delay1 = self.drv1.delay_nand2_path + self.blk1.delay_nand2_path
    #     delay2 = self.drv1.delay_nand3_path + self.blk1.delay_nand3_path
    #     delay3 = self.drv2.delay_nand2_path + self.blk2.delay_nand2_path
    #     delay4 = self.drv2.delay_nand3_path + self.blk2.delay_nand3_path

    #     # #PATH_APPROX using symbolic convex max
    #     overall_delay = symbolic_convex_max(symbolic_convex_max(delay1, delay2),
    #                                         symbolic_convex_max(delay3, delay4))

    #     # The second item is "risetime" from whichever was max, but #PATH_APPROX
    #     # we'll just pick input_pair1[0].
    #     return (overall_delay, input_pair1[0])


###############################################################################
# Driver class
###############################################################################

class Driver(Component):
    def __init__(self, g_ip, g_tp, c_gate_load_, c_wire_load_, r_wire_load_, is_dram_):
        super().__init__()
        self.g_ip        = g_ip
        self.g_tp        = g_tp
        self.number_gates= 0
        self.min_number_gates = 2

        self.c_gate_load = c_gate_load_
        self.c_wire_load = c_wire_load_
        self.r_wire_load = r_wire_load_
        self.delay = 0.0
        self.is_dram_ = is_dram_

        self.total_driver_nwidth = 0.0
        self.total_driver_pwidth = 0.0
        self.sleeptx = None

        self.width_n = [0.0]*MAX_NUMBER_GATES_STAGE
        self.width_p = [0.0]*MAX_NUMBER_GATES_STAGE

        self.compute_widths()
        self.compute_area()

    def compute_widths(self):
        p_to_n_sz_ratio = pmos_to_nmos_sz_ratio(self.g_tp, self.is_dram_)
        c_load = self.c_gate_load + self.c_wire_load

        self.width_n[0] = self.g_tp.min_w_nmos_
        self.width_p[0] = p_to_n_sz_ratio * self.g_tp.min_w_nmos_

        F = c_load / gate_C(self.g_tp, (self.width_n[0] + self.width_p[0]), 0, self.is_dram_)
        self.number_gates = logical_effort(
            self.g_tp,
            self.min_number_gates,
            1,
            F,
            self.width_n,
            self.width_p,
            c_load,
            p_to_n_sz_ratio,
            self.is_dram_,
            False,
            self.g_tp.max_w_nmos_
        )

    def compute_area(self):
        """
        Summation of the gate areas for each stage
        """
        self.area = Area()
        self.area.h = self.g_tp.cell_h_def
        total_area = 0.0

        for i in range(self.number_gates):
            total_area += compute_gate_area(self.g_tp, INV, 1,
                                                      self.width_p[i], self.width_n[i],
                                                      self.area.h)
        if self.area.h > 0:
            self.area.w = total_area / self.area.h
        else:
            self.area.w = 0

    def compute_power_gating(self):
        """
        Summation of device widths, then create SleepTx.
        """
        for i in range(self.number_gates+1):
            # CHECK PATH_APPROX
            # if i < len(self.width_n):
            self.total_driver_nwidth += self.width_n[i]
            self.total_driver_pwidth += self.width_p[i]

        is_footer     = False
        Isat_subarray = simplified_nmos_Isat(self.g_tp, self.total_driver_nwidth)
        detalV        = self.g_tp.peri_global.Vdd - self.g_tp.peri_global.Vcc_min
        c_wakeup      = drain_C_(self.g_ip, self.g_tp,
                                           self.total_driver_pwidth,
                                           PCH, 1,1, self.area.h)

        if self.g_ip.power_gating:
            self.sleeptx = SleepTx(self.g_ip.perfloss,
                                   Isat_subarray,
                                   is_footer,
                                   c_wakeup,
                                   detalV,
                                   1,
                                   self.area)

    def compute_delay(self, inrisetime):
        """
        from c++: double Driver::compute_delay(double inrisetime).
        """
        local_delay = 0.0
        Vdd = self.g_tp.peri_global.Vdd
        new_risetime = inrisetime

        for i in range(self.number_gates - 1):
            rd = tr_R_on(self.g_tp, self.width_n[i], NCH, 1, self.is_dram_)
            c_load = gate_C(self.g_tp, self.width_n[i+1] + self.width_p[i+1], 0.0, self.is_dram_)
            c_intrinsic = drain_C_(self.g_ip, self.g_tp,
                                             self.width_p[i], PCH,1,1,self.g_tp.cell_h_def,
                                             self.is_dram_) \
                          + drain_C_(self.g_ip, self.g_tp,
                                               self.width_n[i], NCH,1,1,self.g_tp.cell_h_def,
                                               self.is_dram_)
            tf = rd*(c_intrinsic + c_load)
            this_d = horowitz(self.g_ip, new_risetime, tf, 0.5, 0.5, RISE)
            self.delay += this_d
            new_risetime = this_d/(1.0 - 0.5)
            self.power.readOp.dynamic += (c_intrinsic + c_load)*(Vdd*Vdd)
            self.power.readOp.leakage += cmos_Isub_leakage(self.g_tp,
                                                                     self.width_n[i], self.width_p[i],
                                                                     1, INV, self.is_dram_)*Vdd
            self.power.readOp.gate_leakage += cmos_Ig_leakage(self.g_tp,
                                                                        self.width_n[i], self.width_p[i],
                                                                        1, INV, self.is_dram_)*Vdd

        # final stage
        i = self.number_gates - 1
        c_load = self.c_gate_load + self.c_wire_load
        rd = tr_R_on(self.g_tp, self.width_n[i], NCH, 1, self.is_dram_)
        c_intrinsic = drain_C_(self.g_ip, self.g_tp, self.width_p[i],
                                         PCH,1,1,self.g_tp.cell_h_def, self.is_dram_) \
                      + drain_C_(self.g_ip, self.g_tp, self.width_n[i],
                                           NCH,1,1,self.g_tp.cell_h_def, self.is_dram_)
        tf = rd*(c_intrinsic + c_load) + self.r_wire_load*(self.c_wire_load*0.5 + self.c_gate_load)
        this_d = horowitz(self.g_ip, new_risetime, tf, 0.5, 0.5, RISE)
        self.delay += this_d
        self.power.readOp.dynamic += (c_intrinsic + c_load)*(Vdd*Vdd)
        self.power.readOp.leakage += cmos_Isub_leakage(self.g_tp,
                                                                 self.width_n[i], self.width_p[i],
                                                                 1, INV, self.is_dram_)*Vdd
        self.power.readOp.gate_leakage += cmos_Ig_leakage(self.g_tp,
                                                                    self.width_n[i], self.width_p[i],
                                                                    1, INV, self.is_dram_)*Vdd
        return this_d/(1.0 - 0.5)

