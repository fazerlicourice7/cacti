"""
wire.py
Translation of wire.h and wire.cc into Python, as close as possible to the
original C++ logic. Relies on previously provided modules:
  - basic_circuit.py
  - component.py
  - parameter.py
  - cacti_interface.py (for enumerations Wire_type, etc.)
  - const.py
"""

import math
import sys
from math import sqrt
from typing import List

# We assume these modules were previously provided:
from .component import Component, is_symbolic
from .cacti_interface import powerDef, powerComponents, Wire_type
from .basic_circuit import (drain_C_, gate_C, horowitz, tr_R_on, cmos_Isub_leakage,
                            cmos_Ig_leakage, pmos_to_nmos_sz_ratio, R_to_w)
from .const import *

# or wherever your BIGNUM is defined, e.g. from .const import BIGNUM
# If BIGNUM is not defined, define it here:
# BIGNUM = 1e99

def symbolic_convex_min(a, b):
    """
    An approximation to the max function that plays well with numeric
    or symbolic solvers.
    """
    return 0.5 * (a + b - abs(a - b))


def symbolic_convex_max(a, b):
    """
    An approximation to the max function that plays well with numeric
    or symbolic solvers.
    """
    return 0.5 * (a + b + abs(a - b))

class Wire(Component):
    """
    Python translation of the C++ Wire class, which inherits from Component.
    Closely follows the logic of wire.h/wire.cc.
    """

    # Class/static variables corresponding to the C++ "static Component ..." members
    global_ = Component()
    global_5 = Component()
    global_10 = Component()
    global_20 = Component()
    global_30 = Component()
    low_swing = Component()

    initialized: int = 0
    wire_width_init: float = 0.0
    wire_spacing_init: float = 0.0

    def __init__(self,
                 g_ip,
                 g_tp,
                 wire_model=None,
                 wire_length=None,  # length in micrometers if passed in the "full" constructor
                 nsense=1,
                 width_scaling=1.0,
                 spacing_scaling=1.0,
                 wire_placement=Wire_placement.outside_mat,
                 resistivity=CU_RESISTIVITY,
                 deviceType=None):
        """
        Python constructor that can function like both C++ constructors:

        1) If wire_model is not None and wire_length is not None, it matches:
           Wire(enum Wire_type wire_model, double len(in um), int nsense=1, ...)
        2) Otherwise, it matches:
           Wire(double w_s=1, double s_s=1, enum Wire_placement wp=outside_mat, ...)

        For the second usage, wire_model and wire_length can remain None, so we
        detect that path accordingly.
        """

        super().__init__()  # Initialize base class (Component)

        self.g_ip = g_ip
        self.g_tp = g_tp

        # If deviceType not provided, fall back to self.g_tp.peri_global
        if deviceType is None:
            deviceType = self.g_tp.peri_global

        self.deviceType = deviceType

        # Shared fields (some will be used in only one constructor path)
        self.nsense = nsense
        self.w_scale = width_scaling
        self.s_scale = spacing_scaling
        self.wire_placement = wire_placement
        self.resistivity = resistivity
        self.min_w_pmos = self.deviceType.n_to_p_eff_curr_drv_ratio * self.g_tp.min_w_nmos_
        self.in_rise_time = 0.0
        self.out_rise_time = 0.0
        self.wire_length = 0.0    # Will store in meters internally
        self.wire_spacing = 0.0   # Meters
        self.wire_width = 0.0     # Meters
        self.repeater_size = 0.0
        self.repeater_spacing = 0.0
        self.wt = None            # enum Wire_type

        # If wire_model and wire_length are both provided => "full" constructor path
        if wire_model is not None and wire_length is not None:
            # C++ code: Wire(enum Wire_type wire_model, double len, int n, w_s=1, s_s=1, wire_placement=..., resistivity=..., dt=...)
            self.wt = wire_model
            # Convert from microns to meters
            self.wire_length = wire_length * 1e-6
            # remainder already set above
            if Wire.initialized != 1:
                # "Wire not initialized. Initializing it with default values"
                # We emulate the "Wire winit;" call:
                temp_wire = Wire(g_ip=self.g_ip,
                                 g_tp=self.g_tp,
                                 width_scaling=1.0,
                                 spacing_scaling=1.0,
                                 wire_placement=Wire_placement.outside_mat,
                                 resistivity=CU_RESISTIVITY,
                                 deviceType=self.g_tp.peri_global)

            self.calculate_wire_stats()

            # Revert everything back to "seconds, microns, Joules" like the original code
            self.repeater_spacing *= 1e6
            self.wire_length *= 1e6
            self.wire_width *= 1e6
            self.wire_spacing *= 1e6

            # Check the code's original asserts:
            assert self.wire_length > 0
            assert self.power.readOp.dynamic > 0
            assert self.power.readOp.leakage > 0
            assert self.power.readOp.gate_leakage > 0

        else:
            # The alternate constructor: Wire(double w_s, double s_s, enum Wire_placement wp, double res, DeviceType *dt)
            # with default arguments in C++ code
            # This sets the "initialized=1; init_wire();"
            # then sets wire_width_init, wire_spacing_init

            # For local logic: we must choose wire_width from self.g_tp. E.g. (outside_mat => self.g_tp.wire_outside_mat.pitch/2)
            # We'll replicate that logic:
            if self.wire_placement == Wire_placement.outside_mat:
                self.wire_width = self.g_tp.wire_outside_mat.pitch / 2
            elif self.wire_placement == Wire_placement.inside_mat:
                self.wire_width = self.g_tp.wire_inside_mat.pitch / 2
            else:
                # default wire_local
                self.wire_width = self.g_tp.wire_local.pitch / 2

            self.wire_spacing = self.wire_width
            # Convert to meters
            self.wire_width *= (self.w_scale * 1e-6 / 2)
            self.wire_spacing *= (self.s_scale * 1e-6 / 2)

            Wire.initialized = 1
            self.init_wire()

            Wire.wire_width_init = self.wire_width
            Wire.wire_spacing_init = self.wire_spacing

            # Check the code's original asserts:
            assert self.power.readOp.dynamic > 0
            assert self.power.readOp.leakage > 0
            assert self.power.readOp.gate_leakage > 0

    def set_in_rise_time(self, rt: float):
        """Equivalent to the C++ set_in_rise_time function."""
        self.in_rise_time = rt

    def calculate_wire_stats(self):
        """
        This corresponds to Wire::calculate_wire_stats() in the C++ code,
        which sets up widths, calls delay/power models, etc.
        """

        # Step 1: pick wire width based on placement
        if self.wire_placement == Wire_placement.outside_mat:
            self.wire_width = self.g_tp.wire_outside_mat.pitch / 2
        elif self.wire_placement == Wire_placement.inside_mat:
            self.wire_width = self.g_tp.wire_inside_mat.pitch / 2
        else:
            self.wire_width = self.g_tp.wire_local.pitch / 2

        self.wire_spacing = self.wire_width

        # Convert to meters
        self.wire_width *= (self.w_scale * 1e-6 / 2)
        self.wire_spacing *= (self.s_scale * 1e-6 / 2)

        # If not Low-swing => full-swing repeated wire
        if self.wt != Wire_type.Low_swing:
            # The code basically sets "delay, power, area" from one of the stored wire solutions
            # in {global_, global_5, global_10, global_20, global_30}
            if self.wt == Wire_type.Global_:
                self.delay = Wire.global_.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_.area.w
                self.repeater_size = Wire.global_.area.h
                # set area
                # area => (wire_length / repeater_spacing) * areaOfOneRepeater
                # use compute_gate_area for an INV gate
                from .component import compute_gate_area
                gate_area = compute_gate_area(self.g_ip, self.g_tp,
                                              INV,
                                              1,
                                              self.min_w_pmos * self.repeater_size,
                                              self.g_tp.min_w_nmos_ * self.repeater_size,
                                              self.g_tp.cell_h_def)
                # store it
                self.area.set_area((self.wire_length / self.repeater_spacing) * gate_area)

            elif self.wt == Wire_type.Global_5:
                self.delay = Wire.global_5.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_5.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_5.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_5.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_5.area.w
                self.repeater_size = Wire.global_5.area.h
                from .component import compute_gate_area
                gate_area = compute_gate_area(self.g_ip, self.g_tp,
                                              INV, 1,
                                              self.min_w_pmos * self.repeater_size,
                                              self.g_tp.min_w_nmos_ * self.repeater_size,
                                              self.g_tp.cell_h_def)
                self.area.set_area((self.wire_length / self.repeater_spacing) * gate_area)

            elif self.wt == Wire_type.Global_10:
                self.delay = Wire.global_10.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_10.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_10.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_10.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_10.area.w
                self.repeater_size = Wire.global_10.area.h
                from .component import compute_gate_area
                gate_area = compute_gate_area(self.g_ip, self.g_tp,
                                              INV, 1,
                                              self.min_w_pmos * self.repeater_size,
                                              self.g_tp.min_w_nmos_ * self.repeater_size,
                                              self.g_tp.cell_h_def)
                self.area.set_area((self.wire_length / self.repeater_spacing) * gate_area)

            elif self.wt == Wire_type.Global_20:
                self.delay = Wire.global_20.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_20.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_20.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_20.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_20.area.w
                self.repeater_size = Wire.global_20.area.h
                from .component import compute_gate_area
                gate_area = compute_gate_area(self.g_ip, self.g_tp,
                                              INV, 1,
                                              self.min_w_pmos * self.repeater_size,
                                              self.g_tp.min_w_nmos_ * self.repeater_size,
                                              self.g_tp.cell_h_def)
                self.area.set_area((self.wire_length / self.repeater_spacing) * gate_area)

            elif self.wt == Wire_type.Global_30:
                self.delay = Wire.global_30.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_30.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_30.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_30.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_30.area.w
                self.repeater_size = Wire.global_30.area.h
                from .component import compute_gate_area
                gate_area = compute_gate_area(self.g_ip, self.g_tp,
                                              INV, 1,
                                              self.min_w_pmos * self.repeater_size,
                                              self.g_tp.min_w_nmos_ * self.repeater_size,
                                              self.g_tp.cell_h_def)
                self.area.set_area((self.wire_length / self.repeater_spacing) * gate_area)

            else:
                # Should not happen if enumerations are correct
                assert(0)
                pass

            # out_rise_time = delay * repeater_spacing / deviceType->Vth
            # But code is out_rise_time = delay * repeater_spacing/deviceType->Vth
            # We'll replicate:
            self.out_rise_time = (self.delay * self.repeater_spacing) / self.deviceType.Vth

        elif self.wt == Wire_type.Low_swing:
            # Low_swing
            self.low_swing_model()
            self.repeater_spacing = self.wire_length
            self.repeater_size = 1
        else:
            assert(0)

    def signal_fall_time(self) -> float:
        """
        C++: double Wire::signal_fall_time()
        A helper function that returns the fall time of an input signal
        to the first stage (like in CACTI 1).
        """

        # timeconst => the combined transistor + gate load
        # note the usage in the code:
        #   timeconst = (drain_C_(min_w_nmos_, NCH, ...) + drain_C_(min_w_pmos, PCH, ...)
        #       + gate_C(min_w_pmos + min_w_nmos_)) * tr_R_on(min_w_pmos, PCH, ...)
        from .basic_circuit import drain_C_, gate_C, tr_R_on, horowitz

        # 1) rise time of inverter 1's output
        timeconst = (
            drain_C_(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def)
            + drain_C_(self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def)
            + gate_C(self.g_ip, self.g_tp, self.min_w_pmos + self.g_tp.min_w_nmos_, 0.0)
        ) * tr_R_on(self.g_tp, self.min_w_pmos, PCH, 1)
        rt = horowitz(0.0, timeconst,
                      self.deviceType.Vth / self.deviceType.Vdd,
                      self.deviceType.Vth / self.deviceType.Vdd,
                      FALL) / (self.deviceType.Vdd - self.deviceType.Vth)

        # 2) fall time of inverter 2's output
        timeconst = (
            drain_C_(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def)
            + drain_C_(self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def)
            + gate_C(self.g_ip, self.g_tp, self.min_w_pmos + self.g_tp.min_w_nmos_, 0.0)
        ) * tr_R_on(self.g_tp, self.g_tp.min_w_nmos_, NCH, 1)
        ft = horowitz(rt, timeconst,
                      self.deviceType.Vth / self.deviceType.Vdd,
                      self.deviceType.Vth / self.deviceType.Vdd,
                      RISE) / self.deviceType.Vth
        return ft

    def signal_rise_time(self) -> float:
        """
        C++: double Wire::signal_rise_time()
        Like signal_fall_time but for the rising edge.
        """

        from .basic_circuit import drain_C_, gate_C, tr_R_on, horowitz

        # 1) rise time of inverter 1's output, but with "in_rise_time=0 => used for FALL?
        timeconst = (
            drain_C_(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def)
            + drain_C_(self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def)
            + gate_C(self.g_ip, self.g_tp, self.min_w_pmos + self.g_tp.min_w_nmos_, 0.0)
        ) * tr_R_on(self.g_tp, self.g_tp.min_w_nmos_, NCH, 1)
        rt = horowitz(0.0, timeconst,
                      self.deviceType.Vth / self.deviceType.Vdd,
                      self.deviceType.Vth / self.deviceType.Vdd,
                      RISE) / self.deviceType.Vth

        # 2) fall time of inverter 2's output
        timeconst = (
            drain_C_(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def)
            + drain_C_(self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def)
            + gate_C(self.g_ip, self.g_tp, self.min_w_pmos + self.g_tp.min_w_nmos_, 0.0)
        ) * tr_R_on(self.g_tp, self.min_w_pmos, PCH, 1)
        ft = horowitz(rt, timeconst,
                      self.deviceType.Vth / self.deviceType.Vdd,
                      self.deviceType.Vth / self.deviceType.Vdd,
                      FALL) / (self.deviceType.Vdd - self.deviceType.Vth)
        return ft

    def wire_cap(self, length_m: float, call_from_outside: bool = False) -> float:
        """
        C++: double Wire::wire_cap(double len, bool call_from_outside=false)
        Return wire capacitance in Farads for length = length_m (in meters).
        """
        epsilon0 = 8.8542e-12
        if self.wire_placement == Wire_placement.outside_mat:
            aspect_ratio = self.g_tp.wire_outside_mat.aspect_ratio
            horiz_dielectric_constant = self.g_tp.wire_outside_mat.horiz_dielectric_constant
            vert_dielectric_constant = self.g_tp.wire_outside_mat.vert_dielectric_constant
            miller_value = self.g_tp.wire_outside_mat.miller_value
            ild_thickness = self.g_tp.wire_outside_mat.ild_thickness
        elif self.wire_placement == Wire_placement.inside_mat:
            aspect_ratio = self.g_tp.wire_inside_mat.aspect_ratio
            horiz_dielectric_constant = self.g_tp.wire_inside_mat.horiz_dielectric_constant
            vert_dielectric_constant = self.g_tp.wire_inside_mat.vert_dielectric_constant
            miller_value = self.g_tp.wire_inside_mat.miller_value
            ild_thickness = self.g_tp.wire_inside_mat.ild_thickness
        else:
            aspect_ratio = self.g_tp.wire_local.aspect_ratio
            horiz_dielectric_constant = self.g_tp.wire_local.horiz_dielectric_constant
            vert_dielectric_constant = self.g_tp.wire_local.vert_dielectric_constant
            miller_value = self.g_tp.wire_local.miller_value
            ild_thickness = self.g_tp.wire_local.ild_thickness

        # In the code, if call_from_outside is True, the function multiplies wire_width & wire_spacing
        # by 1e-6, then does the calcs, then multiplies them back. We replicate that:
        if call_from_outside:
            saved_width = self.wire_width
            saved_spacing = self.wire_spacing
            self.wire_width *= 1e-6
            self.wire_spacing *= 1e-6

        wire_height = (self.wire_width / self.w_scale) * aspect_ratio

        # sidewall:
        sidewall = (miller_value * horiz_dielectric_constant
                    * (wire_height / self.wire_spacing) * epsilon0)

        # adjacency (vertical):
        adj = (miller_value * vert_dielectric_constant
               * self.wire_width / (ild_thickness * 1e-6)
               * epsilon0)

        # tot_cap => sidewall + adjacency + fringe
        # The code used deviceType->C_fringe, then replaced with (self.g_tp.fringe_cap * 1e6)
        # We'll do:
        tot_cap = sidewall + adj + (self.g_tp.fringe_cap * 1e6)

        if call_from_outside:
            self.wire_width = saved_width
            self.wire_spacing = saved_spacing

        return tot_cap * length_m

    def wire_res(self, length_m: float) -> float:
        """
        C++: double Wire::wire_res(double len)
        Return wire resistance in ohms for length len(in meters).
        """
        alpha_scatter = 1.05
        dishing_thickness = 0.0
        barrier_thickness = 0.0
        # aspect_ratio from the relevant wire type
        if self.wire_placement == Wire_placement.outside_mat:
            aspect_ratio = self.g_tp.wire_outside_mat.aspect_ratio
        elif self.wire_placement == Wire_placement.inside_mat:
            aspect_ratio = self.g_tp.wire_inside_mat.aspect_ratio
        else:
            aspect_ratio = self.g_tp.wire_local.aspect_ratio

        # The code formula:
        # return (alpha_scatter * resistivity * 1e-6 * len /
        #      ((aspect_ratio*wire_width/w_scale-dishing_thickness - barrier_thickness) *
        #       (wire_width - 2*barrier_thickness)));
        denom = ((aspect_ratio * self.wire_width / self.w_scale) - dishing_thickness - barrier_thickness) \
                * (self.wire_width - 2 * barrier_thickness)
        if denom < 1e-30:
            return 1e30  # avoid divide by zero
        r_val = alpha_scatter * self.resistivity * 1e-6 * length_m / denom
        return r_val

    def sense_amp_input_cap(self) -> float:
        """
        C++: double Wire::sense_amp_input_cap()
        Return the input capacitance of the sense amplifier, used in low_swing_model.
        """
        from .basic_circuit import drain_C_, gate_C

        return (
            drain_C_(self.g_ip, self.g_tp, self.g_tp.w_iso, PCH, 1, 1, self.g_tp.cell_h_def)
            + gate_C(self.g_ip, self.g_tp, self.g_tp.w_sense_en + self.g_tp.w_sense_n, 0.0)
            + drain_C_(self.g_ip, self.g_tp, self.g_tp.w_sense_n, NCH, 1, 1, self.g_tp.cell_h_def)
            + drain_C_(self.g_ip, self.g_tp, self.g_tp.w_sense_p, PCH, 1, 1, self.g_tp.cell_h_def)
        )

    def low_swing_model(self):
        """
        C++: void Wire::low_swing_model()
        Models a differential low-swing wire: transmitter + wire + sense amp.
        """
        from .basic_circuit import (
            gate_C, drain_C_, tr_R_on, horowitz, cmos_Isub_leakage, cmos_Ig_leakage
        )

        # len is wire_length in meters
        length_m = self.wire_length
        beta = pmos_to_nmos_sz_ratio(self.g_tp)

        # if in_rise_time=0 => use signal_rise_time()
        if self.in_rise_time == 0:
            inputrise = self.signal_rise_time()
        else:
            inputrise = self.in_rise_time

        # wire cap + res
        cwire = self.wire_cap(length_m)
        rwire = self.wire_res(length_m)

        # driver_res => a target resistance to keep wire delay < ~ 8 FO4
        # The code used: driver_res = (-8*self.g_tp.FO4/(log(0.5) * cwire))/RES_ADJ
        # We'll replicate as is. Then convert that to width via R_to_w.
        RES_ADJ = 8.6  # from code
        driver_res = (-8.0 * self.g_tp.FO4 / (math.log(0.5) * cwire)) / RES_ADJ
        nsize = R_to_w(self.g_tp, driver_res, NCH)

        # clamp
        nsize = symbolic_convex_min(nsize, self.g_tp.max_w_nmos_)
        nsize = symbolic_convex_max(nsize, self.g_tp.min_w_nmos_)

        # if rwire*cwire > 8*self.g_tp.FO4 => pick max driver size
        if (rwire * cwire) > 8.0 * self.g_tp.FO4:
            nsize = self.g_tp.max_w_nmos_

        # Next, we figure out how big to size an inverter to drive that final nmos
        # st_eff = sqrt(...) => the stage effort
        # ...
        # We'll replicate exactly:
        from .basic_circuit import gate_C
        st_eff = math.sqrt(
            ((2.0 + beta / (1.0 + beta))
             * gate_C(self.g_ip, self.g_tp, nsize, 0.0))
            /
            (gate_C(self.g_ip, self.g_tp, 2.0 * self.g_tp.min_w_nmos_, 0.0)
             + gate_C(self.g_ip, self.g_tp, 2.0 * self.min_w_pmos, 0.0))
        )
        # required input cin
        req_cin = ((2.0 + beta / (1.0 + beta))
                   * gate_C(self.g_ip, self.g_tp, nsize, 0.0)) / st_eff
        inv_size = req_cin / (gate_C(self.g_ip, self.g_tp, self.min_w_pmos, 0.0)
                              + gate_C(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, 0.0))
        inv_size = symbolic_convex_max(inv_size, 1.0)

        # Nand gate delay
        # see code
        res_eq = 2.0 * tr_R_on(self.g_tp, self.g_tp.min_w_nmos_, NCH, 1)
        cap_eq = (2.0 * drain_C_(self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def)
                  + drain_C_(self.g_ip, self.g_tp, 2.0 * self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def)
                  + gate_C(self.g_ip, self.g_tp, inv_size * self.g_tp.min_w_nmos_, 0.0)
                  + gate_C(self.g_ip, self.g_tp, inv_size * self.min_w_pmos, 0.0))

        timeconst = res_eq * cap_eq
        delay_val = horowitz(inputrise, timeconst,
                             self.deviceType.Vth / self.deviceType.Vdd,
                             self.deviceType.Vth / self.deviceType.Vdd,
                             RISE)
        temp_power = cap_eq * self.deviceType.Vdd * self.deviceType.Vdd
        inputrise = delay_val / (self.deviceType.Vdd - self.deviceType.Vth)

        # Inverter delay
        res_eq = tr_R_on(self.g_tp, inv_size * self.min_w_pmos, PCH, 1)
        cap_eq = (drain_C_(self.g_ip, self.g_tp, inv_size * self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def)
                  + drain_C_(self.g_ip, self.g_tp, inv_size * self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def)
                  + gate_C(self.g_ip, self.g_tp, nsize, 0.0))
        timeconst = res_eq * cap_eq
        delay_val += horowitz(inputrise, timeconst,
                              self.deviceType.Vth / self.deviceType.Vdd,
                              self.deviceType.Vth / self.deviceType.Vdd,
                              FALL)
        temp_power += cap_eq * self.deviceType.Vdd * self.deviceType.Vdd

        self.delay = delay_val
        self.transmitter = Component()
        self.transmitter.delay = delay_val
        self.transmitter.power.readOp.dynamic = temp_power * 2.0  # differential => x2
        # leakage
        from .basic_circuit import cmos_Isub_leakage, cmos_Ig_leakage
        self.transmitter.power.readOp.leakage = (self.deviceType.Vdd *
            (4.0 * cmos_Isub_leakage(self.g_tp, self.g_tp.min_w_nmos_, self.min_w_pmos, 2, "nand")
             + 4.0 * cmos_Isub_leakage(self.g_tp, self.g_tp.min_w_nmos_, self.min_w_pmos, 1, "inv")))
        self.transmitter.power.readOp.gate_leakage = (self.deviceType.Vdd *
            (4.0 * cmos_Ig_leakage(self.g_tp, self.g_tp.min_w_nmos_, self.min_w_pmos, 2, "nand")
             + 4.0 * cmos_Ig_leakage(self.g_tp, self.g_tp.min_w_nmos_, self.min_w_pmos, 1, "inv")))

        inputrise = delay_val / self.deviceType.Vth

        # Nmos + wire
        wire_load_cap = (cwire
                         + 2.0 * drain_C_(self.g_ip, self.g_tp, nsize, NCH, 1, 1, self.g_tp.cell_h_def)
                         + self.nsense * self.sense_amp_input_cap())
        timeconst = (
            (tr_R_on(self.g_tp, nsize, NCH, 1) * 8.6) *  # RES_ADJ
            (cwire + 2.0 * drain_C_(self.g_ip, self.g_tp, nsize, NCH, 1, 1, self.g_tp.cell_h_def))
            + rwire * cwire / 2.0
            + (tr_R_on(self.g_tp, nsize, NCH, 1) * 8.6 + rwire)
              * self.nsense * self.sense_amp_input_cap()
        )

        # we approximate the net timeconst with pre-equalization, etc.
        delay_val += horowitz(inputrise, timeconst,
                              self.deviceType.Vth / self.deviceType.Vdd, 0.25, 0)
        VOL_SWING = 0.1
        temp_power += wire_load_cap * VOL_SWING * 0.400  # *2 => done next line
        temp_power *= 2.0  # differential

        self.l_wire = Component()
        self.l_wire.delay = delay_val - self.transmitter.delay
        self.l_wire.power.readOp.dynamic = temp_power - self.transmitter.power.readOp.dynamic
        self.l_wire.power.readOp.leakage = (self.deviceType.Vdd *
            (4.0 * cmos_Isub_leakage(self.g_tp, nsize, 0.0, 1, "nmos")))
        self.l_wire.power.readOp.gate_leakage = (self.deviceType.Vdd *
            (4.0 * cmos_Ig_leakage(self.g_tp, nsize, 0.0, 1, "nmos")))

        # sense amp
        delay_val += self.g_tp.sense_delay
        self.sense_amp = Component()
        self.sense_amp.delay = self.g_tp.sense_delay
        self.out_rise_time = self.g_tp.sense_delay / self.deviceType.Vth
        self.sense_amp.power.readOp.dynamic = self.g_tp.sense_dy_power
        self.sense_amp.power.readOp.leakage = 0.0  # FIXME
        self.sense_amp.power.readOp.gate_leakage = 0.0

        self.power.readOp.dynamic = temp_power + self.sense_amp.power.readOp.dynamic
        self.power.readOp.leakage = (self.transmitter.power.readOp.leakage
                                     + self.l_wire.power.readOp.leakage
                                     + self.sense_amp.power.readOp.leakage)
        self.power.readOp.gate_leakage = (self.transmitter.power.readOp.gate_leakage
                                          + self.l_wire.power.readOp.gate_leakage
                                          + self.sense_amp.power.readOp.gate_leakage)

        # Final self.delay
        # CHECK THIS:
        self.delay = delay_val

    def delay_optimal_wire(self):
        """
        C++: void Wire::delay_optimal_wire()
        A subroutine that calculates the repeater spacing/size for minimal wire delay,
        sets 'delay', 'power', 'area'.
        This is used in the 'init_wire()' function to generate the baseline "global" wire.
        """

        length_m = self.wire_length
        beta = pmos_to_nmos_sz_ratio(self.g_tp)

        # input cap of min size driver
        input_cap = gate_C(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_ + self.min_w_pmos, 0.0)

        # output cap:
        out_cap = (drain_C_(self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def)
                   + drain_C_(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def))
        out_res = (tr_R_on(self.g_tp, self.g_tp.min_w_nmos_, NCH, 1)
                   + tr_R_on(self.g_tp, self.min_w_pmos, PCH, 1)) / 2.0

        wr = self.wire_res(length_m)
        wc = self.wire_cap(length_m)

        # The formula in the code:
        #   double repeater_scaling = sqrt(out_res*wc / (wr*input_cap));
        #   double repeater_spacing = sqrt(2 * out_res*(out_cap + input_cap)/((wr/len)*(wc/len)));
        # etc
        repeater_scaling = math.sqrt(out_res * wc / (wr * input_cap))
        self.repeater_size = repeater_scaling
        self.repeater_spacing = math.sqrt(
            2.0 * out_res * (out_cap + input_cap) / ((wr / length_m) * (wc / length_m))
        )

        switching = ((self.repeater_size * (input_cap + out_cap))
                     + self.repeater_spacing * (wc / length_m)) \
                    * self.deviceType.Vdd * self.deviceType.Vdd

        # time constant:
        # tc = out_res*(in+out) + out_res*(wc/len)*(spacing/size)
        #       + wr/len*(spacing)*inCap*(size)
        #       + 0.5*(wr/len)*(wc/len)*spacing^2
        # etc
        tc = (out_res * (input_cap + out_cap)
              + out_res * (wc / length_m) * (self.repeater_spacing / self.repeater_size)
              + wr / length_m * self.repeater_spacing * input_cap * self.repeater_size
              + 0.5 * (wr / length_m) * (wc / length_m)
                * self.repeater_spacing * self.repeater_spacing)

        self.delay = 0.693 * tc * (length_m / self.repeater_spacing)

        # short-circuit
        Ishort_ckt = 65e-6
        short_ckt = self.deviceType.Vdd * self.g_tp.min_w_nmos_ * Ishort_ckt * 1.0986 \
                    * self.repeater_size * tc

        from .basic_circuit import cmos_Isub_leakage, cmos_Ig_leakage
        self.area.set_area((length_m / self.repeater_spacing) *
                           # compute_gate_area for an INV gate
                           # We'll do it like c++ does:
                           #   compute_gate_area(INV, 1, min_w_pmos*repeater_size, min_w_nmos_*repeater_size, cell_h_def)
                           # but we replicate the logic:
                           # We'll do it carefully once we've imported the function
                           0.0)

        # We'll actually compute the area now:
        from .component import compute_gate_area
        gate_area = compute_gate_area(self.g_ip, self.g_tp,
                                      INV, 1,
                                      self.min_w_pmos * self.repeater_size,
                                      self.g_tp.min_w_nmos_ * self.repeater_size,
                                      self.g_tp.cell_h_def)
        self.area.set_area((length_m / self.repeater_spacing) * gate_area)

        self.power.readOp.dynamic = ((length_m / self.repeater_spacing) * (switching + short_ckt))
        self.power.readOp.leakage = ((length_m / self.repeater_spacing)
                                     * self.deviceType.Vdd
                                     * cmos_Isub_leakage(
                                         self.g_tp, self.g_tp.min_w_nmos_ * self.repeater_size,
                                         beta * self.g_tp.min_w_nmos_ * self.repeater_size,
                                         1, "inv"))
        self.power.readOp.gate_leakage = ((length_m / self.repeater_spacing)
                                          * self.deviceType.Vdd
                                          * cmos_Ig_leakage(
                                              self.g_tp, self.g_tp.min_w_nmos_ * self.repeater_size,
                                              beta * self.g_tp.min_w_nmos_ * self.repeater_size,
                                              1, "inv"))

    def init_wire(self):
        """
        C++: void Wire::init_wire()
        Called by the second constructor to generate a range of wire solutions, store them,
        then fill out Wire.global_, global_5, etc. in update_fullswing().
        Also sets Wire.low_swing from a temporary Low_swing wire.
        """

        # set wire_length=1 for modeling => the code's approach
        self.wire_length = 1.0
        self.delay_optimal_wire()

        # Print out "Repeater Spacing, Repeater Size" for debug
        sp = self.repeater_spacing
        si = self.repeater_size
        # The code prints "BOOGA Repeater Spacing: {sp} ... "
        # We'll replicate as print statements:
        print(f"BOOGA Repeater Spacing: {sp*1e6} (microns)")  # c++ uses sp*1e6 => mm, but let's keep as comment
        print(f"BOOGA Repeater Size: {si}")

        # The code sets self.g_ip->repeater_spacing = sp*1e6, self.g_ip->repeater_size = si
        self.g_ip.repeater_spacing = sp*1e6  # in microns
        self.g_ip.repeater_size = si

        # Build repeated_wire list of possible solutions
        # We do a nested loop j in [sp..4*sp], i in [si..1], stepping j by 100
        # Then calls wire_model and collects them
        # Then we remove the last push at the end
        self.repeated_wire: List[Component] = []
        c = Component()
        self.repeated_wire.append(c)

        j = sp
        while j < 4.0 * sp:
            jstep = 100.0  # microns from code
            i = si
            while i > 1.0:
                ptemp, del_val = self.wire_model(j * 1e-6, i)
                self.repeated_wire[-1].delay = del_val
                self.repeated_wire[-1].power.readOp = ptemp.readOp
                self.repeated_wire[-1].area.w = j * 1e-6
                self.repeated_wire[-1].area.h = i
                # push back a new blank component
                self.repeated_wire.append(Component())
                i -= 1.0
            j += jstep

        # remove the last blank
        if len(self.repeated_wire) > 0:
            self.repeated_wire.pop()

        # update the "Wire.global_, global_5, global_10, etc." from repeated_wire
        self.update_fullswing()

        # Low-swing
        # The code: "Wire *l_wire = new Wire(Low_swing, 0.001 /*1mm*/ ,1)"
        # We'll do the same in python
        l_wire = Wire(wire_model=Wire_type.Low_swing,
                      wire_length=1000.0,  # 0.001 mm => 1 mm => 1000 microns
                      nsense=1)
        Wire.low_swing.delay = l_wire.delay
        Wire.low_swing.power = l_wire.power
        del l_wire  # same as "delete l_wire"

    def update_fullswing(self):
        """
        C++: void Wire::update_fullswing()
        Post-process repeated_wire to filter out solutions that exceed certain delay thresholds,
        then pick the best (lowest power) among them for each threshold => store in global_30,
        global_20, global_10, global_5
        """
        # The code sets
        #   del[3] = global_.delay + global_.delay * .3  => 30% overhead
        #   del[2] = global_.delay + global_.delay * .2
        #   del[1] = global_.delay + global_.delay * .1
        #   del[0] = global_.delay + global_.delay * .05
        # Then filters out any repeated_wire whose delay>del[i], picking best cost
        # We do it as in the code:

        del_list = [0.0]*4
        del_list[3] = Wire.global_.delay + Wire.global_.delay * 0.3
        del_list[2] = Wire.global_.delay + Wire.global_.delay * 0.2
        del_list[1] = Wire.global_.delay + Wire.global_.delay * 0.1
        del_list[0] = Wire.global_.delay + Wire.global_.delay * 0.05

        # We'll do i from 4 down to 1
        i = 4
        while i > 0:
            threshold = del_list[i - 1]
            best_cost = BIGNUM
            # Walk repeated_wire
            # If delay > threshold => remove it
            to_remove = []
            for idx, comp in enumerate(self.repeated_wire):
                if comp.delay > threshold:
                    to_remove.append(idx)
            # remove in reverse order so indices remain valid
            for idx in reversed(to_remove):
                self.repeated_wire.pop(idx)

            # among those that remain, pick the best cost
            # cost = comp.power.readOp.dynamic/global_.power.readOp.dynamic + comp.power.readOp.leakage/global_.power.readOp.leakage
            # if cost < best_cost => store in global_30 or global_20 or ...
            for comp in self.repeated_wire:
                ncost = (comp.power.readOp.dynamic / Wire.global_.power.readOp.dynamic
                         + comp.power.readOp.leakage / Wire.global_.power.readOp.leakage)
                if ncost < best_cost:
                    best_cost = ncost
                    if i == 4:
                        Wire.global_30.delay = comp.delay
                        Wire.global_30.power = comp.power
                        Wire.global_30.area = comp.area
                    elif i == 3:
                        Wire.global_20.delay = comp.delay
                        Wire.global_20.power = comp.power
                        Wire.global_20.area = comp.area
                    elif i == 2:
                        Wire.global_10.delay = comp.delay
                        Wire.global_10.power = comp.power
                        Wire.global_10.area = comp.area
                    elif i == 1:
                        Wire.global_5.delay = comp.delay
                        Wire.global_5.power = comp.power
                        Wire.global_5.area = comp.area

            i -= 1

    def wire_model(self, space: float, size: float):
        """
        C++: powerDef Wire::wire_model(double space, double size, double *delay)
        Return (powerDef, delay).
        Suboptimal wire sizing model for a 1 meter wire_length => does single pass calc.
        """
        length_m = 1.0
        beta = pmos_to_nmos_sz_ratio(self.g_tp)
        # input caps
        input_cap = gate_C(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_ + self.min_w_pmos, 0.0)
        out_cap = (drain_C_(self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def)
                   + drain_C_(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def))
        out_res = (tr_R_on(self.g_tp, self.g_tp.min_w_nmos_, NCH, 1)
                   + tr_R_on(self.g_tp, self.min_w_pmos, PCH, 1)) / 2.0
        wr = self.wire_res(length_m)
        wc = self.wire_cap(length_m)

        self.repeater_spacing = space
        self.repeater_size = size

        switching = (self.repeater_size * (input_cap + out_cap)
                     + self.repeater_spacing * (wc / length_m)) * self.deviceType.Vdd * self.deviceType.Vdd

        tc = (out_res * (input_cap + out_cap)
              + out_res * (wc / length_m) * (self.repeater_spacing / self.repeater_size)
              + wr / length_m * self.repeater_spacing * out_cap * self.repeater_size
              + 0.5 * (wr / length_m) * (wc / length_m)
                * self.repeater_spacing * self.repeater_spacing)

        delay_val = 0.693 * tc * (length_m / self.repeater_spacing)

        Ishort_ckt = 65e-6
        short_ckt = (self.deviceType.Vdd * self.g_tp.min_w_nmos_ * Ishort_ckt
                     * 1.0986 * self.repeater_size * tc)

        ptemp = powerDef()
        ptemp.readOp.dynamic = ((length_m / self.repeater_spacing) * (switching + short_ckt))

        from .basic_circuit import cmos_Isub_leakage, cmos_Ig_leakage
        ptemp.readOp.leakage = ((length_m / self.repeater_spacing)
                                * self.deviceType.Vdd
                                * cmos_Isub_leakage(
                                    self.g_tp, self.g_tp.min_w_nmos_ * self.repeater_size,
                                    beta * self.g_tp.min_w_nmos_ * self.repeater_size,
                                    1, "inv"))
        ptemp.readOp.gate_leakage = ((length_m / self.repeater_spacing)
                                     * self.deviceType.Vdd
                                     * cmos_Ig_leakage(
                                         self.g_tp, self.g_tp.min_w_nmos_ * self.repeater_size,
                                         beta * self.g_tp.min_w_nmos_ * self.repeater_size,
                                         1, "inv"))

        return ptemp, delay_val

    def print_wire(self):
        """
        C++: void Wire::print_wire()
        Print out final wire solutions for debugging.
        """

        print("\nWire Properties:\n")
        # Delay Optimal => Wire.global_
        g = Wire.global_
        print("  Delay Optimal")
        print(f"\tRepeater size       : {g.area.h}")
        print(f"\tRepeater spacing    : {g.area.w * 1e3} (mm)")
        print(f"\tDelay               : {g.delay * 1e6} (ns/mm)")
        print(f"\tPowerD              : {g.power.readOp.dynamic * 1e6} (nJ/mm)")
        print(f"\tPowerL              : {g.power.readOp.leakage} (mW/mm)")
        print(f"\tPowerLgate          : {g.power.readOp.gate_leakage} (mW/mm)")
        print(f"\tWire width          : {Wire.wire_width_init * 1e6} microns")
        print(f"\tWire spacing        : {Wire.wire_spacing_init * 1e6} microns\n")

        # 5% Overhead => Wire.global_5
        g = Wire.global_5
        print("  5% Overhead")
        print(f"\tRepeater size       : {g.area.h}")
        print(f"\tRepeater spacing    : {g.area.w * 1e3} (mm)")
        print(f"\tDelay               : {g.delay * 1e6} (ns/mm)")
        print(f"\tPowerD              : {g.power.readOp.dynamic * 1e6} (nJ/mm)")
        print(f"\tPowerL              : {g.power.readOp.leakage} (mW/mm)")
        print(f"\tPowerLgate          : {g.power.readOp.gate_leakage} (mW/mm)")
        print(f"\tWire width          : {Wire.wire_width_init * 1e6} microns")
        print(f"\tWire spacing        : {Wire.wire_spacing_init * 1e6} microns\n")

        # 10%
        g = Wire.global_10
        print("  10% Overhead")
        print(f"\tRepeater size       : {g.area.h}")
        print(f"\tRepeater spacing    : {g.area.w * 1e3} (mm)")
        print(f"\tDelay               : {g.delay * 1e6} (ns/mm)")
        print(f"\tPowerD              : {g.power.readOp.dynamic * 1e6} (nJ/mm)")
        print(f"\tPowerL              : {g.power.readOp.leakage} (mW/mm)")
        print(f"\tPowerLgate          : {g.power.readOp.gate_leakage} (mW/mm)")
        print(f"\tWire width          : {Wire.wire_width_init * 1e6} microns")
        print(f"\tWire spacing        : {Wire.wire_spacing_init * 1e6} microns\n")

        # 20%
        g = Wire.global_20
        print("  20% Overhead")
        print(f"\tRepeater size       : {g.area.h}")
        print(f"\tRepeater spacing    : {g.area.w * 1e3} (mm)")
        print(f"\tDelay               : {g.delay * 1e6} (ns/mm)")
        print(f"\tPowerD              : {g.power.readOp.dynamic * 1e6} (nJ/mm)")
        print(f"\tPowerL              : {g.power.readOp.leakage} (mW/mm)")
        print(f"\tPowerLgate          : {g.power.readOp.gate_leakage} (mW/mm)")
        print(f"\tWire width          : {Wire.wire_width_init * 1e6} microns")
        print(f"\tWire spacing        : {Wire.wire_spacing_init * 1e6} microns\n")

        # 30%
        g = Wire.global_30
        print("  30% Overhead")
        print(f"\tRepeater size       : {g.area.h}")
        print(f"\tRepeater spacing    : {g.area.w * 1e3} (mm)")
        print(f"\tDelay               : {g.delay * 1e6} (ns/mm)")
        print(f"\tPowerD              : {g.power.readOp.dynamic * 1e6} (nJ/mm)")
        print(f"\tPowerL              : {g.power.readOp.leakage} (mW/mm)")
        print(f"\tPowerLgate          : {g.power.readOp.gate_leakage} (mW/mm)")
        print(f"\tWire width          : {Wire.wire_width_init * 1e6} microns")
        print(f"\tWire spacing        : {Wire.wire_spacing_init * 1e6} microns\n")

        # Low-swing (1mm)
        g = Wire.low_swing
        print("  Low-swing wire (1 mm) - Note: Unlike repeated wires,")
        print("   delay and power values of low-swing wires do not have a linear relationship with length.")
        print(f"\tdelay    : {g.delay * 1e9} (ns)")
        print(f"\tpowerD   : {g.power.readOp.dynamic * 1e9} (nJ)")
        print(f"\tPowerL   : {g.power.readOp.leakage} (mW)")
        print(f"\tPowerLgate : {g.power.readOp.gate_leakage} (mW)")
        print(f"\tWire width   : {Wire.wire_width_init * 2} microns (differential)")
        print(f"\tWire spacing : {Wire.wire_spacing_init * 2} microns (differential)\n")
        print()
