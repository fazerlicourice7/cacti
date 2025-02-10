# tsv.py
"""
Python translation of TSV.h and TSV.cc from CACTI.

Requires:
  - Access to the global technology parameters (g_tp) and possibly global input parameters (g_ip).
  - The basic_circuit and decoder utilities for things like:
      cmos_Isub_leakage, cmos_Ig_leakage, gate_C, drain_C_, horowitz, tr_R_on, compute_gate_area,
      logical_effort, etc.
  - The 'Component' base class for area/power/delay fields.
"""

import math
from .component import Component
from .basic_circuit import (
    cmos_Isub_leakage, cmos_Ig_leakage, drain_C_, gate_C, horowitz, tr_R_on,
    logical_effort, compute_gate_area
)
from .cacti_interface import powerDef, TSV_type
from .const import *

# If you have TSV_type enumerations in your code, e.g. Fine=0, Coarse=1, import them from const:
# from .const import TSV_type

class TSV(Component):
    """
    Python version of the C++ TSV class.
    Inherits from Component to have self.area, self.power, and self.delay fields.
    """
    def __init__(self,
                 g_ip,
                 g_tp,
                 tsv_type,    # e.g. TSV_type.Fine, TSV_type.Coarse
                 deviceType=None):
        """
        Constructor arguments replicate the C++ signature:

        tsv_type: an enum or int specifying 'Fine' or 'Coarse'.
        deviceType: DeviceType pointer (default = g_tp.peri_global in C++).
        g_ip, g_tp: references to global input and tech parameters (passed in from your code).
        """
        super().__init__()  # calls Component.__init__(), sets self.power, self.delay=0, etc.

        self.g_ip = g_ip
        self.g_tp = g_tp

        if deviceType is None:
            # default to g_tp.peri_global if not provided
            deviceType = g_tp.peri_global
        self.deviceType = deviceType

        # fields from TSV.h
        self.tsv_type = tsv_type  # Fine=0, Coarse=1
        self.res = 0.0
        self.cap = 0.0
        self.C_load_TSV = 0.0
        self.min_area   = 0.0

        self.num_gates      = 1
        self.num_gates_min  = 1
        self.w_TSV_n = [0.0]*MAX_NUMBER_GATES_STAGE
        self.w_TSV_p = [0.0]*MAX_NUMBER_GATES_STAGE

        self.is_dram = 0.0
        self.is_wl_tr = 0.0

        self.min_w_pmos = self.deviceType.n_to_p_eff_curr_drv_ratio * self.g_tp.min_w_nmos_

        # sub-areas
        self.TSV_metal_area = Component()
        self.Buffer_area    = Component()

        # Switch on tsv_type
        if self.tsv_type == TSV_type.Fine:  # e.g. Fine
            self.cap      = g_tp.tsv_parasitic_capacitance_fine
            self.res      = g_tp.tsv_parasitic_resistance_fine
            self.min_area = g_tp.tsv_minimum_area_fine
        elif self.tsv_type == TSV_type.Coarse:  # e.g. Coarse
            self.cap      = g_tp.tsv_parasitic_capacitance_coarse
            self.res      = g_tp.tsv_parasitic_resistance_coarse
            self.min_area = g_tp.tsv_minimum_area_coarse
        else:
            # or raise an exception
            pass

        # set the first stage buffer widths
        first_buf_stg_coef = 5.0
        self.w_TSV_n[0] = self.g_tp.min_w_nmos_ * first_buf_stg_coef
        self.w_TSV_p[0] = self.min_w_pmos * first_buf_stg_coef

        # The constructor calls:
        self.compute_buffer_stage()
        self.compute_area()
        self.compute_delay()

    def compute_buffer_stage(self):
        """
        Mirrors the C++ code: TSV::compute_buffer_stage().
        Decides how many buffer chain stages are needed,
        calls 'logical_effort()' with the final load = C_load_TSV, etc.
        """
        # building final load
        # previously code had some commented 'cap_beol'
        self.C_load_TSV = self.cap + gate_C(self.g_tp,
                                            self.g_tp.min_w_nmos_ + self.min_w_pmos,
                                            0.0)  # e.g. + 57.5e-15 if needed

        if self.g_ip.print_detail_debug:
            # print the input cap of 1st buffer
            c_in_1st = gate_C(self.g_tp, (self.w_TSV_n[0] + self.w_TSV_p[0]), 0.0)
            print("The input cap of 1st buffer: {:.3f} fF".format(c_in_1st*1e15))

        # compute F => ratio of final load to that input
        c_input_stage = gate_C(self.g_tp,
                               (self.w_TSV_n[0] + self.w_TSV_p[0]),
                               0.0)
        F = self.C_load_TSV / (c_input_stage+1e-30)
        if self.g_ip.print_detail_debug:
            print("F is", F)

        # call logical_effort to get self.num_gates and fill w_TSV_n[], w_TSV_p[]
        p_to_n_sz_ratio = self.deviceType.n_to_p_eff_curr_drv_ratio
        # arguments to logical_effort in c++:
        # (min_num_gates, <g>, F, w_TSV_n, w_TSV_p, C_load_TSV, p_to_n_sz_ratio, is_dram, is_wl_tr, max_w_nmos)
        self.num_gates = logical_effort(
            self.num_gates_min,
            base_logical_effort=1.0,    # "g" factor for an inverter
            F=F,
            w_n=self.w_TSV_n,
            w_p=self.w_TSV_p,
            c_load=self.C_load_TSV,
            p_to_n_sz_ratio=p_to_n_sz_ratio,
            is_dram=(self.is_dram>0),
            is_wl_tr=(self.is_wl_tr>0),
            max_w_nmos=self.g_tp.max_w_nmos_
        )

    def compute_area(self):
        """
        Python version of TSV::compute_area().
        Sums up the buffer chain area, sets the leakage. Also sets final area if buffer < min_area.
        """
        Vdd = self.deviceType.Vdd
        cumulative_area = 0.0
        cumulative_curr = 0.0  # subthreshold
        cumulative_curr_Ig = 0.0  # gate leakage

        # We treat the default buffer height as g_tp.cell_h_def
        self.Buffer_area.h = self.g_tp.cell_h_def

        # Sum up the area for each stage
        for i in range(self.num_gates):
            # compute gate area for an INV with 1 input => w_p[i], w_n[i]
            a_gate = compute_gate_area(self.g_tp, INV, 1,
                                       self.w_TSV_p[i], self.w_TSV_n[i],
                                       self.Buffer_area.h)
            cumulative_area += a_gate

            if self.g_ip.print_detail_debug:
                print("\tArea up to stage {} is: {} um^2".format(i+1, cumulative_area))

            # subthreshold
            # cmos_Isub_leakage(w_n, w_p, fanin=1, gate_type=inv, is_dram?)
            # note that we pass is_dram=bool(self.is_dram) if needed
            s_leak = cmos_Isub_leakage(
                self.g_tp,
                self.w_TSV_n[i],
                self.w_TSV_p[i],
                fanin=1,
                gate_type="inv",  # or inv
                is_dram=(self.is_dram>0)
            )
            cumulative_curr += s_leak

            # gate leakage
            g_leak = cmos_Ig_leakage(
                self.g_tp,
                self.w_TSV_n[i],
                self.w_TSV_p[i],
                fanin=1,
                gate_type="inv",
                is_dram=(self.is_dram>0)
            )
            cumulative_curr_Ig += g_leak

        # scale by supply
        self.power.readOp.leakage = cumulative_curr*Vdd
        self.power.readOp.gate_leakage = cumulative_curr_Ig*Vdd

        # finalize buffer area
        self.Buffer_area.set_area(cumulative_area)
        if self.Buffer_area.h>0:
            self.Buffer_area.w = cumulative_area/self.Buffer_area.h
        else:
            self.Buffer_area.w = 0.0

        # area for the TSV metal itself
        # code: TSV_metal_area.set_area(min_area*3.1416/16)
        # This suggests the TSV is a circle of min_area => pi*r^2 => or a fraction?
        self.TSV_metal_area.set_area(self.min_area*3.1416/16.0)

        # final area: if Buffer_area < min_area minus TSV metal => clamp to min_area
        if (self.Buffer_area.get_area() < (self.min_area - self.TSV_metal_area.get_area())):
            self.area.set_area(self.min_area)
        else:
            self.area.set_area(self.Buffer_area.get_area() + self.TSV_metal_area.get_area())

    def compute_delay(self):
        """
        Python version of TSV::compute_delay().
        Goes stage-by-stage for the buffer chain, then adds final stage driving the TSV.
        Accumulates dynamic power.
        """
        inrisetime = 0.0
        Vdd = self.deviceType.Vdd

        # local references
        # first stage
        i = 0
        rd = tr_R_on(self.g_tp, self.w_TSV_n[0], NCH, stack=1,
                     is_dram=(self.is_dram>0), is_cell=False, is_wl_tr=(self.is_wl_tr>0))
        c_load = gate_C(self.g_tp, self.w_TSV_n[1] + self.w_TSV_p[1] if self.num_gates>1 else 0.0,
                        0.0, (self.is_dram>0), False, (self.is_wl_tr>0))
        c_intrinsic = (drain_C_(self.g_ip, self.g_tp, self.w_TSV_p[0], PCH, 1,1, self.area.h,
                                (self.is_dram>0), False, (self.is_wl_tr>0))
                       + drain_C_(self.g_ip, self.g_tp, self.w_TSV_n[0], NCH, 1,1, self.area.h,
                                  (self.is_dram>0), False, (self.is_wl_tr>0)))
        tf = rd*(c_intrinsic + c_load)
        this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
        self.delay += this_delay

        # new inrisetime
        inrisetime = this_delay/(1.0 - 0.5)

        # dynamic
        self.power.readOp.dynamic += (c_intrinsic + c_load)* Vdd * Vdd

        # middle stages
        for i in range(1, self.num_gates - 1):
            rd = tr_R_on(self.g_tp, self.w_TSV_n[i], NCH,1,
                         (self.is_dram>0),False,(self.is_wl_tr>0))
            c_load = gate_C(self.g_tp, (self.w_TSV_n[i+1]+ self.w_TSV_p[i+1]) if (i+1)<self.num_gates else 0.0,
                            0.0, (self.is_dram>0), False, (self.is_wl_tr>0))
            c_intrinsic = (drain_C_(self.g_ip, self.g_tp,
                                    self.w_TSV_p[i], PCH,1,1, self.area.h,
                                    (self.is_dram>0),False,(self.is_wl_tr>0))
                           + drain_C_(self.g_ip, self.g_tp,
                                      self.w_TSV_n[i], NCH,1,1, self.area.h,
                                      (self.is_dram>0),False,(self.is_wl_tr>0)))
            tf = rd*(c_intrinsic + c_load)
            stage_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
            self.delay += stage_delay
            inrisetime = stage_delay/(1.0 - 0.5)
            self.power.readOp.dynamic += (c_intrinsic + c_load)* Vdd * Vdd

        # final stage that drives the TSV
        i = self.num_gates - 1
        rd = tr_R_on(self.g_tp, self.w_TSV_n[i], NCH,1,
                     (self.is_dram>0),False,(self.is_wl_tr>0))
        c_intrinsic = (drain_C_(self.g_ip, self.g_tp,
                                self.w_TSV_p[i], PCH,1,1, self.area.h,
                                (self.is_dram>0),False,(self.is_wl_tr>0))
                       + drain_C_(self.g_ip, self.g_tp,
                                  self.w_TSV_n[i], NCH,1,1, self.area.h,
                                  (self.is_dram>0),False,(self.is_wl_tr>0)))
        c_load = self.C_load_TSV
        # plus some portion for the TSV line: res/2 * c_load
        tf = rd*(c_intrinsic + c_load) + self.res*c_load * 0.5
        this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
        self.delay += this_delay

        # dynamic
        self.power.readOp.dynamic += (c_intrinsic + c_load)* Vdd*Vdd

        # done. self.delay is total chain + TSV

    def print_TSV(self):
        """
        Print out final TSV parameters in a debug style, replicating the c++ version.
        """
        print("\nTSV Properties:\n")
        print("  Delay Optimal -")
        print(f"   TSV Cap: {self.cap*1e15:.3f} fF")
        print(f"   TSV Res: {self.res*1e3:.3f} mOhm")
        print(f"   Number of Buffer Chain stages: {self.num_gates}")
        print(f"   Delay: {self.delay*1e9:.3f} ns")
        print(f"   PowerD: {self.power.readOp.dynamic*1e9:.3f} nJ")
        print(f"   PowerL: {self.power.readOp.leakage*1e3:.3f} mW")
        print(f"   PowerLgate: {self.power.readOp.gate_leakage*1e3:.3f} mW")
        print(f"   Buffer  Area: {self.Buffer_area.get_area():.3f} um^2")
        print(f"   Buffer Height: {self.Buffer_area.h:.3f} um")
        print(f"   Buffer Width: {self.Buffer_area.w:.3f} um")
        print(f"   TSV metal area: {self.TSV_metal_area.get_area():.3f} um^2")
        print(f"   TSV minimum occupied area: {self.min_area:.3f} um^2")
        print(f"   Total area: {self.area.get_area():.3f} um^2")
        print()
