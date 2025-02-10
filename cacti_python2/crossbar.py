# crossbar.py

import math
import sys
import sympy as sp

# Import your own modules/classes for:
#   - basic_circuit (drain_C_, gate_C, cmos_Isub_leakage, cmos_Ig_leakage, tr_R_on, horowitz, compute_gate_area)
#   - const (INV, NAND, NOR, etc.)
#   - component (Component, which has self.area, self.power, self.delay, etc.)
#   - wire (Wire)

from .component import Component
from .basic_circuit import (
    drain_C_,
    gate_C,
    cmos_Isub_leakage,
    cmos_Ig_leakage,
    tr_R_on,
    horowitz,
    compute_gate_area,
)
from .const import *
from .wire import Wire

def symbolic_convex_max(a, b):
    """
    An approximation to the max function that plays well with numeric
    or symbolic solvers.
    """
    return 0.5 * (a + b + abs(a - b))

def is_symbolic(x):
    """Return True if x is a sympy symbolic expression."""
    return isinstance(x, sp.Basic)


class Crossbar(Component):
    """
    Python translation of crossbar.h/crossbar.cc, passing g_ip/g_tp as parameters.
    
    Fields:
      - n_inp: number of inputs (double)
      - n_out: number of outputs (double)
      - flit_size: flit size in bits (double)
      - deviceType: pointer to a "DeviceType" object 
      - g_ip: InputParameter reference
      - g_tp: TechnologyParameter reference

      - tri_inp_cap, tri_out_cap, tri_ctr_cap, tri_int_cap: node caps
      - TriS1, TriS2: sizing factors for tri-state buffers
      - CB_ADJ: factor for adjusting crossbar layout if aspect ratio is too small
      - min_w_pmos, Vdd for transistor sizing
    """

    def __init__(
        self,
        g_ip,               # The InputParameter object
        g_tp,               # The TechnologyParameter object
        n_inp_,             # number of input ports
        n_out_,             # number of output ports
        flit_size_,         # flit width in bits
        dt=None             # optional DeviceType, defaults to g_tp.peri_global
    ):
        """
        Corresponds to Crossbar::Crossbar(...) in C++.
        """
        super().__init__()

        self.g_ip = g_ip
        self.g_tp = g_tp
        self.n_inp = n_inp_
        self.n_out = n_out_
        self.flit_size = flit_size_

        if dt is None:
            dt = self.g_tp.peri_global
        self.deviceType = dt

        # From crossbar.cc
        self.min_w_pmos = (
            self.deviceType.n_to_p_eff_curr_drv_ratio * self.g_tp.min_w_nmos_
        )
        self.Vdd = self.deviceType.Vdd
        self.CB_ADJ = 1.0

        # Tri-state caps and sizing
        self.tri_inp_cap = 0.0
        self.tri_out_cap = 0.0
        self.tri_ctr_cap = 0.0
        self.tri_int_cap = 0.0
        self.TriS1 = 0.0
        self.TriS2 = 0.0

    def __del__(self):
        """
        Equivalent to Crossbar::~Crossbar(). Typically unnecessary in Python.
        """
        pass

    def output_buffer(self) -> float:
        """
        Equivalent to Crossbar::output_buffer().
        Creates a Wire of length = n_inp*flit_size*g_tp.wire_outside_mat.pitch,
        calculates tri-state buffer sizes (TriS1, TriS2), updates tri_inp_cap,
        tri_out_cap, tri_ctr_cap, tri_int_cap, and returns the sum of
        (input_cap + output_cap + ctr_cap).
        """
        # The "effective" length from crossbar.cc
        l_eff = self.n_inp * self.flit_size * self.g_tp.wire_outside_mat.pitch

        # Make a wire with length = l_eff (microns).
        # We'll pass in self.g_ip.wt for the wire type if needed.
        w1 = Wire(
            self.g_ip,
            self.g_tp,
            wire_model=self.g_ip.wt,
            wire_length=l_eff
        )

        # The code does:
        # double s1 = w1.repeater_size * ( l_eff < w1.repeater_spacing ? (l_eff*ADJ/w1.repeater_spacing) : ADJ);
        ADJ = 1
        if l_eff < w1.repeater_spacing:
            s1 = w1.repeater_size * (l_eff * ADJ / w1.repeater_spacing)
        else:
            s1 = w1.repeater_size * ADJ

        pton_size = self.deviceType.n_to_p_eff_curr_drv_ratio
        # TriS1, TriS2 from crossbar.cc
        # TriS1 = s1*(1+pton_size)/(2+pton_size+1+2*pton_size)
        # TriS2 = s1
        self.TriS1 = s1 * (1.0 + pton_size) / (2.0 + pton_size + 1.0 + 2.0 * pton_size)
        self.TriS2 = s1

        # clamp TriS1 >= 1
        if self.TriS1 < 1.0:
            self.TriS1 = 1.0

        # input_cap => gate_C(...) for TriS1*(2*min_w_pmos + g_tp.min_w_nmos_), plus ...
        input_cap = (
            gate_C(
                self.g_ip,
                self.g_tp,
                self.TriS1 * (2.0 * self.min_w_pmos + self.g_tp.min_w_nmos_),
                0.0
            )
            + gate_C(
                self.g_ip,
                self.g_tp,
                self.TriS1 * (self.min_w_pmos + 2.0 * self.g_tp.min_w_nmos_),
                0.0
            )
        )

        # internal node cap from crossbar.cc
        self.tri_int_cap = (
            drain_C_(
                self.g_ip,
                self.g_tp,
                self.TriS1 * self.g_tp.min_w_nmos_,
                NCH, 1, 1, self.g_tp.cell_h_def
            )
            + drain_C_(
                self.g_ip,
                self.g_tp,
                self.TriS1 * self.min_w_pmos,
                PCH, 1, 1, self.g_tp.cell_h_def
            )
            * 2.0
            + gate_C(
                self.g_ip,
                self.g_tp,
                self.TriS2 * self.g_tp.min_w_nmos_,
                0.0
            )
            + drain_C_(
                self.g_ip,
                self.g_tp,
                self.TriS1 * self.min_w_pmos,
                NCH, 1, 1, self.g_tp.cell_h_def
            )
            * 2.0
            + drain_C_(
                self.g_ip,
                self.g_tp,
                self.TriS1 * self.min_w_pmos,
                PCH, 1, 1, self.g_tp.cell_h_def
            )
            + gate_C(
                self.g_ip,
                self.g_tp,
                self.TriS2 * self.min_w_pmos,
                0.0
            )
        )

        # output cap
        output_cap = (
            drain_C_(
                self.g_ip,
                self.g_tp,
                self.TriS2 * self.g_tp.min_w_nmos_,
                NCH, 1, 1, self.g_tp.cell_h_def
            )
            + drain_C_(
                self.g_ip,
                self.g_tp,
                self.TriS2 * self.min_w_pmos,
                PCH, 1, 1, self.g_tp.cell_h_def
            )
        )

        # control cap
        ctr_cap = gate_C(
            self.g_ip,
            self.g_tp,
            self.TriS2 * (self.min_w_pmos + self.g_tp.min_w_nmos_),
            0.0
        )

        self.tri_inp_cap = input_cap
        self.tri_out_cap = output_cap
        self.tri_ctr_cap = ctr_cap

        return (input_cap + output_cap + ctr_cap)

    def compute_power(self):
        """
        Python translation of Crossbar::compute_power().
        1) Calls output_buffer() to get tri-state buffer caps and sizing
        2) Computes area of tri-state logic
        3) Builds 2 Wires (w1 for width, w2 for height)
        4) Possibly adjusts CB_ADJ if aspect ratio < ASPECT_THRESHOLD
        5) Accumulates dynamic/leakage power for crossbar
        6) Calculates crossbar delay via horowitz
        """

        # 1) Tri-state buffer
        tri_cap = self.output_buffer()

        if not is_symbolic(tri_cap):
            assert tri_cap > 0.0, "Crossbar output buffer computed zero or negative tri_cap?"

        # 2) area of tri-state logic
        # from crossbar.cc => compute_gate_area calls for INV, NAND(2), NOR(2)
        g_area = 0.0

        # 2.1) invert output transistors => 2 * ...
        inv_area = compute_gate_area(
            self.g_ip,
            self.g_tp,
            INV,
            1,
            self.TriS2 * self.g_tp.min_w_nmos_,
            self.TriS2 * self.min_w_pmos,
            self.g_tp.cell_h_def
        )
        g_area += 2.0 * inv_area

        # 2.2) NAND(2)
        nand_area = compute_gate_area(
            self.g_ip,
            self.g_tp,
            NAND,
            2,
            self.TriS1 * 2.0 * self.g_tp.min_w_nmos_,
            self.TriS1 * self.min_w_pmos,
            self.g_tp.cell_h_def
        )
        g_area += nand_area

        # 2.3) NOR(2)
        nor_area = compute_gate_area(
            self.g_ip,
            self.g_tp,
            NOR,
            2,
            self.TriS1 * self.g_tp.min_w_nmos_,
            self.TriS1 * 2.0 * self.min_w_pmos,
            self.g_tp.cell_h_def
        )
        g_area += nor_area

        width_per_tri = g_area / (self.CB_ADJ * self.g_tp.cell_h_def)

        # 3) Build wires: 
        #    int ntri = ceil(g_tp.cell_h_def / g_tp.wire_outside_mat.pitch)
        #    wire_len => max(width_per_tri * ntri * n_out, flit_size*g_tp.wire_outside_mat.pitch*n_out)
        ntri = int(math.ceil(
            self.g_tp.cell_h_def / self.g_tp.wire_outside_mat.pitch
        ))
        wire_len = symbolic_convex_max(
            width_per_tri * ntri * self.n_out,
            self.flit_size * self.g_tp.wire_outside_mat.pitch * self.n_out
        )

        # w1 => horizontal dimension
        w1 = Wire(
            self.g_ip,
            self.g_tp,
            wire_model=self.g_ip.wt,
            wire_length=wire_len
        )

        # set Crossbar area
        self.area.w = wire_len
        self.area.h = (
            self.g_tp.wire_outside_mat.pitch
            * self.n_inp
            * self.flit_size
            * self.CB_ADJ
        )

        # w2 => vertical dimension
        w2 = Wire(
            self.g_ip,
            self.g_tp,
            wire_model=self.g_ip.wt,
            wire_length=self.area.h
        )

        # 4) check aspect ratio
        aspect_ratio_cb = (
            (self.area.h / self.area.w) * (self.n_out / self.n_inp)
        )
        if aspect_ratio_cb > 1.0:
            aspect_ratio_cb = 1.0 / aspect_ratio_cb

        if aspect_ratio_cb < ASPECT_THRESHOLD:
            if self.n_out > 2 and self.n_inp > 2:
                self.CB_ADJ += 0.2
                if self.CB_ADJ < 4.0:
                    # recursion
                    self.compute_power()
                    return

        # 5) compute dynamic power
        # power.readOp.dynamic => (w1 + w2 + tri caps) * flit_size
        # from crossbar.cc
        self.power.readOp.dynamic = (
            w1.power.readOp.dynamic
            + w2.power.readOp.dynamic
            + (
                self.tri_inp_cap * self.n_out
                + self.tri_out_cap * self.n_inp
                + self.tri_ctr_cap
                + self.tri_int_cap
            )
            * self.Vdd
            * self.Vdd
        ) * self.flit_size

        # 5.1) leakage
        from .basic_circuit import cmos_Isub_leakage, cmos_Ig_leakage

        self.power.readOp.leakage = (
            self.n_inp
            * self.n_out
            * self.flit_size
            * (
                cmos_Isub_leakage(
                    self.g_ip,    # pass g_ip
                    self.g_tp,
                    self.g_tp.min_w_nmos_ * self.TriS2 * 2.0,
                    self.min_w_pmos * self.TriS2 * 2.0,
                    fanin=1,
                    gate_type=INV
                )
                * self.Vdd
                + cmos_Isub_leakage(
                    self.g_ip,
                    self.g_tp,
                    self.g_tp.min_w_nmos_ * self.TriS1 * 3.0,
                    self.min_w_pmos * self.TriS1 * 3.0,
                    fanin=2,
                    gate_type=NAND
                )
                * self.Vdd
                + cmos_Isub_leakage(
                    self.g_ip,
                    self.g_tp,
                    self.g_tp.min_w_nmos_ * self.TriS1 * 3.0,
                    self.min_w_pmos * self.TriS1 * 3.0,
                    fanin=2,
                    gate_type=NOR
                )
                * self.Vdd
                + w1.power.readOp.leakage
                + w2.power.readOp.leakage
            )
        )

        # 5.2) gate leakage
        self.power.readOp.gate_leakage = (
            self.n_inp
            * self.n_out
            * self.flit_size
            * (
                cmos_Ig_leakage(
                    self.g_ip,
                    self.g_tp,
                    self.g_tp.min_w_nmos_ * self.TriS2 * 2.0,
                    self.min_w_pmos * self.TriS2 * 2.0,
                    fanin=1,
                    gate_type=INV
                )
                * self.Vdd
                + cmos_Ig_leakage(
                    self.g_ip,
                    self.g_tp,
                    self.g_tp.min_w_nmos_ * self.TriS1 * 3.0,
                    self.min_w_pmos * self.TriS1 * 3.0,
                    fanin=2,
                    gate_type=NAND
                )
                * self.Vdd
                + cmos_Ig_leakage(
                    self.g_ip,
                    self.g_tp,
                    self.g_tp.min_w_nmos_ * self.TriS1 * 3.0,
                    self.min_w_pmos * self.TriS1 * 3.0,
                    fanin=2,
                    gate_type=NOR
                )
                * self.Vdd
                + w1.power.readOp.gate_leakage
                + w2.power.readOp.gate_leakage
            )
        )

        # 6) delay
        # from crossbar.cc
        # double l_eff = n_inp*flit_size*g_tp.wire_outside_mat.pitch
        l_eff = self.n_inp * self.flit_size * self.g_tp.wire_outside_mat.pitch

        # create wire to represent driver?
        wdriver = Wire(
            self.g_ip,
            self.g_tp,
            wire_model=self.g_ip.wt,
            wire_length=l_eff
        )

        # res => g_tp.wire_outside_mat.R_per_um*(area.w+area.h) + tr_R_on(...)
        # cap => g_tp.wire_outside_mat.C_per_um*(area.w+area.h) + n_out*tri_inp_cap + n_inp*tri_out_cap
        wire_R_per_um = self.g_tp.wire_outside_mat.R_per_um
        wire_C_per_um = self.g_tp.wire_outside_mat.C_per_um

        res = (
            wire_R_per_um * (self.area.w + self.area.h)
            + tr_R_on(
                self.g_tp,
                (self.g_tp.min_w_nmos_ * wdriver.repeater_size),
                NCH, 1
            )
        )
        cap = (
            wire_C_per_um * (self.area.w + self.area.h)
            + self.n_out * self.tri_inp_cap
            + self.n_inp * self.tri_out_cap
        )

        # final crossbar delay => horowitz
        self.delay = horowitz(
            w1.signal_rise_time(),
            res * cap,
            self.deviceType.Vth / self.deviceType.Vdd,
            self.deviceType.Vth / self.deviceType.Vdd,
            RISE
        )

        # No usage for "Wire wreset();" in the original code => do nothing

    def print_crossbar(self):
        """
        Python translation of Crossbar::print_crossbar().
        Outputs crossbar stats to stdout (like the C++ code does with cout).
        """
        print(f"\nCrossbar Stats ({self.n_inp}x{self.n_out})\n")
        print(f"Flit size        : {self.flit_size} bits")
        print(f"Width            : {self.area.w} u")
        print(f"Height           : {self.area.h} u")

        # The original code multiplies dynamic power by MIN(n_inp, n_out).
        dyn_energy = self.power.readOp.dynamic * 1e9 * MIN(self.n_inp, self.n_out)
        print(f"Dynamic Power    : {dyn_energy} (nJ)")

        print(f"Leakage Power    : {self.power.readOp.leakage * 1e3} (mW)")
        print(f"Gate Leakage Power : {self.power.readOp.gate_leakage * 1e3} (mW)")
        print(f"Crossbar Delay   : {self.delay * 1e12} ps\n")
