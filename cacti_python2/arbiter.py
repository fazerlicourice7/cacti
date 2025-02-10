"""
arbiter.py

Python translation of the arbiter.{h, cc} C++ code. This class models an
Arbiter, which in CACTI is effectively a small logic block for route arbitration
with power/delay/leakage modeling.

References:
  - The code inherits from "Component".
  - We assume that you have:
     g_ip: global InputParameter
     g_tp: global TechnologyParameter
     or these can be passed around as needed.
  - We reuse the standard CACTI style functions gate_C, drain_C_, cmos_Isub_leakage,
    cmos_Ig_leakage, etc. from basic_circuit.py
  - For wire modeling, we use wire.py's "Wire" class for Cw3 with triple spacing, etc.

Notes:
  - The C++ code had "Arbiter(double Req, double flit_sz, double output_len, DeviceType *dt)"
    as the constructor. We'll replicate that in Python.
  - The code used "this->power" for storing final dynamic/leakage. We'll do the same.
"""

import math
from .component import Component
from .basic_circuit import (
    gate_C,
    drain_C_,
    cmos_Isub_leakage,
    cmos_Ig_leakage,
    pmos_to_nmos_sz_ratio,
)
from .const import nand, nor, inv
from .wire import Wire
# from .cacti_interface import powerDef, powerComponents  # If needed
# If your code base provides these from a different location, adjust accordingly.

class Arbiter(Component):
    def __init__(self, g_ip, g_tp,
                 n_req: float,
                 flit_size_: float,
                 output_len: float,
                 deviceType=None):
        """
        Python version of:
          Arbiter::Arbiter(double n_req, double flit_size_, double output_len, DeviceType* dt)
        in arbiter.cc.

        :param g_ip: global input parameters object
        :param g_tp: global technology parameters object
        :param n_req: R (number of requests)
        :param flit_size_: flit size in bits
        :param output_len: crossbar control line length (?)
        :param deviceType: references to g_tp.peri_global by default if not specified
        """

        super().__init__()  # Initialize base class "Component"

        self.g_ip = g_ip
        self.g_tp = g_tp

        if deviceType is None:
            deviceType = self.g_tp.peri_global

        self.deviceType = deviceType

        self.R = n_req
        self.flit_size = flit_size_
        self.o_len = output_len
        self.min_w_pmos = (self.deviceType.n_to_p_eff_curr_drv_ratio
                           * self.g_tp.min_w_nmos_)
        self.Vdd = self.deviceType.Vdd

        # We read "technology = g_ip->F_sz_um" in the code
        technology = self.g_ip.F_sz_um

        # The code sets:
        # NTn1, PTn1, NTn2, PTn2, NTi, PTi, NTtr, PTtr
        # Each is: e.g. 13.5 * technology / 2
        self.NTn1 = 13.5 * technology / 2.0
        self.PTn1 = 76.0  * technology / 2.0
        self.NTn2 = 13.5 * technology / 2.0
        self.PTn2 = 76.0  * technology / 2.0
        self.NTi  = 12.5 * technology / 2.0
        self.PTi  = 25.0  * technology / 2.0
        self.NTtr = 10.0  * technology / 2.0
        self.PTtr = 20.0  * technology / 2.0

    def __del__(self):
        """
        Python doesn't need a destructor the way C++ does, but we mimic if needed.
        """
        pass

    def arb_req(self) -> float:
        """
        C++: double Arbiter::arb_req()
        This is the switching cap for the 'request' portion of the arbiter logic.
        """
        # replicate:
        # ((R-1)*(2*gate_C(NTn1,0)+gate_C(PTn1,0)) + 2*gate_C(NTn2,0)
        #  + gate_C(PTn2,0) + gate_C(NTi,0) + gate_C(PTi,0)
        #  + drain_C_(NTi,0,1,1,cell_h_def)+drain_C_(PTi,1,1,1,cell_h_def))
        ctotal = 0.0
        ctotal += ((self.R - 1.0)
                   * (2.0*gate_C(self.g_ip, self.g_tp, self.NTn1, 0.0)
                      + gate_C(self.g_ip, self.g_tp, self.PTn1, 0.0)))
        ctotal += (2.0*gate_C(self.g_ip, self.g_tp, self.NTn2, 0.0)
                   + gate_C(self.g_ip, self.g_tp, self.PTn2, 0.0)
                   + gate_C(self.g_ip, self.g_tp, self.NTi,  0.0)
                   + gate_C(self.g_ip, self.g_tp, self.PTi,  0.0))

        ctotal += drain_C_(self.g_ip, self.g_tp, self.NTi, 0, 1, 1,
                           self.g_tp.cell_h_def)
        ctotal += drain_C_(self.g_ip, self.g_tp, self.PTi, 1, 1, 1,
                           self.g_tp.cell_h_def)
        return ctotal

    def arb_pri(self) -> float:
        """
        C++: double Arbiter::arb_pri()
        Priority logic portion
        """
        # 2*(2*gate_C(NTn1,0) + gate_C(PTn1,0))
        ctotal = 2.0 * (2.0 * gate_C(self.g_ip, self.g_tp, self.NTn1, 0.0)
                        + gate_C(self.g_ip, self.g_tp, self.PTn1, 0.0))
        return ctotal

    def arb_grant(self) -> float:
        """
        C++: double Arbiter::arb_grant()
        The 'grant' portion of the logic
        """
        # drain_C_(NTn1,0,1,1,..)*2 + drain_C_(PTn1,1,1,1,..) + crossbar_ctrline()
        ctotal = 0.0
        ctotal += (drain_C_(self.g_ip, self.g_tp, self.NTn1, 0, 1, 1,
                            self.g_tp.cell_h_def)*2.0)
        ctotal += drain_C_(self.g_ip, self.g_tp, self.PTn1, 1, 1, 1,
                           self.g_tp.cell_h_def)
        ctotal += self.crossbar_ctrline()
        return ctotal

    def arb_int(self) -> float:
        """
        C++: double Arbiter::arb_int()
        The internal nodes portion
        """
        # ( drain_C_(NTn1)*2 + drain_C_(PTn1)
        #   + 2*gate_C(NTn2,0) + gate_C(PTn2,0) )
        ctotal = ((drain_C_(self.g_ip, self.g_tp, self.NTn1, 0, 1, 1,
                            self.g_tp.cell_h_def)*2.0)
                  + drain_C_(self.g_ip, self.g_tp, self.PTn1, 1, 1, 1,
                             self.g_tp.cell_h_def)
                  + 2.0*gate_C(self.g_ip, self.g_tp, self.NTn2, 0.0)
                  + gate_C(self.g_ip, self.g_tp, self.PTn2, 0.0))
        return ctotal

    def compute_power(self):
        """
        C++: void Arbiter::compute_power()
        Summarize dynamic & leakage.
        """
        # replicate expression:
        # power.readOp.dynamic =  (R*arb_req()*Vdd^2/2 + R*arb_pri()*Vdd^2/2 +
        #                          arb_grant()*Vdd^2 + arb_int()*0.5*Vdd^2 )
        self.power.readOp.dynamic = (
            self.R * self.arb_req()   * self.Vdd*self.Vdd / 2.0
            + self.R * self.arb_pri() * self.Vdd*self.Vdd / 2.0
            + self.arb_grant()        * self.Vdd*self.Vdd
            + self.arb_int()          * 0.5 * self.Vdd*self.Vdd
        )

        # now leakage
        # nor1_leak = cmos_Isub_leakage(g_tp.min_w_nmos_*NTn1*2, min_w_pmos * PTn1*2, 2, nor)
        # note that cmos_Isub_leakage expects (nWidth, pWidth, fanin, gate_type, ...)
        # so nWidth = (g_tp.min_w_nmos_ * NTn1 * 2).
        # pWidth = (min_w_pmos * PTn1 *2).
        # fanin=2, gate_type="nor".
        nor1_leak = cmos_Isub_leakage(
            self.g_tp,
            self.g_tp.min_w_nmos_ * self.NTn1 * 2.0,
            self.min_w_pmos      * self.PTn1 * 2.0,
            2, "nor"
        )
        nor2_leak = cmos_Isub_leakage(
            self.g_tp,
            self.g_tp.min_w_nmos_ * self.NTn2 * self.R,
            self.min_w_pmos      * self.PTn2 * self.R,
            2, "nor"
        )
        not_leak = cmos_Isub_leakage(
            self.g_tp,
            self.g_tp.min_w_nmos_*self.NTi,
            self.min_w_pmos     *self.PTi,
            1, "inv"
        )

        # gate leakage
        nor1_leak_gate = cmos_Ig_leakage(
            self.g_tp,
            self.g_tp.min_w_nmos_*self.NTn1*2.0,
            self.min_w_pmos     *self.PTn1*2.0,
            2, "nor"
        )
        nor2_leak_gate = cmos_Ig_leakage(
            self.g_tp,
            self.g_tp.min_w_nmos_*self.NTn2*self.R,
            self.min_w_pmos     *self.PTn2*self.R,
            2, "nor"
        )
        not_leak_gate = cmos_Ig_leakage(
            self.g_tp,
            self.g_tp.min_w_nmos_*self.NTi,
            self.min_w_pmos*self.PTi,
            1, "inv"
        )

        # sum
        # subthreshold leakage => multiply by Vdd
        self.power.readOp.leakage = (
            (nor1_leak + nor2_leak + not_leak)
            * self.Vdd
        )
        # gate leakage => also * Vdd
        self.power.readOp.gate_leakage = (
            (nor1_leak_gate + nor2_leak_gate + not_leak_gate)
            * self.Vdd
        )

    def Cw3(self, length: float) -> float:
        """
        C++: double Arbiter::Cw3(double length)
        'wire cap with triple spacing' => Wire w(g_ip->wt, length, 1, 3, 3)
        Then w.wire_cap(length, true).
        We pass length in (um). The code calls length*1e-6 => in meters for the Wire constructor.
        """
        # In the code: Wire wc(g_ip->wt, length, 1, 3, 3).
        # We'll replicate. We pass wire_model = g_ip->wt, wire_length= length,
        #  nsense=1, width_scaling=3, spacing_scaling=3,
        # wire_placement default outside_mat => let's guess. 
        # Then call wc.wire_cap(length, true).
        w = Wire(self.g_ip, self.g_tp,
                 wire_model=self.g_ip.wt,  # e.g. "Global"
                 wire_length=length,       # in microns
                 nsense=1,
                 width_scaling=3.0,
                 spacing_scaling=3.0)
        # call wire_cap with length in meters or the 2-arg approach. In the code: wire_cap(len, call_from_outside=True).
        # Because the constructor will convert length(um) => meters internally,
        # we do wire_cap with call_from_outside=True to replicate c++ logic.
        cap = w.wire_cap(length, call_from_outside=True)
        return cap

    def crossbar_ctrline(self) -> float:
        """
        C++: double Arbiter::crossbar_ctrline()
        => ( Cw3(o_len*1e-6) + drain_C_(NTi, 0,1,1,...)+drain_C_(PTi,1,1,1,...)
             + gate_C(NTi,0) + gate_C(PTi,0) ).
        """
        wirecap = self.Cw3(self.o_len)  # pass microns
        ctotal = (wirecap
                  + drain_C_(self.g_ip, self.g_tp, self.NTi, 0, 1, 1,
                             self.g_tp.cell_h_def)
                  + drain_C_(self.g_ip, self.g_tp, self.PTi, 1, 1, 1,
                             self.g_tp.cell_h_def)
                  + gate_C(self.g_ip, self.g_tp, self.NTi, 0.0)
                  + gate_C(self.g_ip, self.g_tp, self.PTi, 0.0))
        return ctotal

    def transmission_buf_ctrcap(self) -> float:
        """
        C++: double Arbiter::transmission_buf_ctrcap()
        => gate_C(NTtr,0) + gate_C(PTtr,0)
        """
        return (gate_C(self.g_ip, self.g_tp, self.NTtr, 0.0)
                + gate_C(self.g_ip, self.g_tp, self.PTtr, 0.0))

    def print_arbiter(self):
        """
        C++: void Arbiter::print_arbiter()
        Just prints the final stats
        """
        print(f"\nArbiter Stats ({self.R} input arbiter)")
        print(f"Flit size      : {self.flit_size} bits")
        print(f"Dynamic Power  : {self.power.readOp.dynamic*1e9} (nJ)")
        print(f"Leakage Power  : {self.power.readOp.leakage*1e3} (mW)")
        print()
