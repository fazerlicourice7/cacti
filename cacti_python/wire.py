import math

import sympy as sp

from .cacti_interface import PowerDef
from .component import Component, compute_gate_area
from .const import *
from . import parameter
from .parameter import gate_C, drain_C_, horowitz, tr_R_on
import os

class Wire(Component):
    global_ = Component()
    # global_5 = Component()
    # global_10 = Component()
    # global_20 = Component()
    # global_30 = Component()
    low_swing = Component()
    initialized = 0
    wire_width_init = None
    wire_spacing_init = None

    def __init__(self, g_ip, g_tp, wire_model="Global", wl=1, n=1, w_s=1, s_s=1, wp=parameter.outside_mat, resistivity=CU_RESISTIVITY, dt=None):
        super().__init__()
        self.g_ip = g_ip
        self.g_tp = g_tp
        self.wt = wire_model
        self.wire_length = wl * 1e-6
        self.nsense = n
        self.w_scale = w_s
        self.s_scale = s_s
        self.resistivity = resistivity
        self.deviceType = dt if dt is not None else g_tp.peri_global
        self.wire_placement = wp
        self.min_w_pmos = self.deviceType.n_to_p_eff_curr_drv_ratio * self.g_tp.min_w_nmos_
        self.in_rise_time = 0
        self.out_rise_time = 0
        self.repeated_wire = []

        ##
        import inspect
        current_frame = inspect.currentframe()
        caller_frame = inspect.getouterframes(current_frame, 2)
        # Extract caller information
        caller_info = caller_frame[1]
        filename = caller_info.filename
        filename = filename.replace("/", "_")
        line_number = caller_info.lineno
        function_name = caller_info.function
        write_to_debug(f"debugwirelength_{filename}_{line_number}_{function_name}", self.wire_length)
        ##

        self.transmitter = Component()
        self.l_wire = Component()
        self.sense_amp = Component()

        # CHECK
        self.repeater_spacing = 0
        self.wire_width = 0
        self.wire_spacing = 0
        self.repeater_size = 0 

        if Wire.initialized != 1:
            # print("Initializing Wire")
            self.__init_wire_simple(w_s, s_s, wp, resistivity, dt)

        self.calculate_wire_stats()

        # ISSUE? -> might need to delete -> rpeater spacing is probably messed up
        self.repeater_spacing *= 1e6  
        print(f"sp: {self.repeater_spacing}")
        print(f"si: {self.repeater_size}")
        # BOOGA Repeater Spacing: 1096.94
        # BOOGA Repeater Size: 182.636
        self.wire_length *= 1e6
        self.wire_width *= 1e6
        self.wire_spacing *= 1e6

        # assert self.wire_length > 0
        # assert self.power.readOp.dynamic > 0
        # assert self.power.readOp.leakage > 0
        # assert self.power.readOp.gate_leakage > 0

    def __init_wire_simple(self, w_s, s_s, wp, resis, dt):
        if self.wire_placement == parameter.outside_mat:
            self.wire_width = self.g_tp.wire_outside_mat.pitch / 2
        elif self.wire_placement == parameter.inside_mat:
            self.wire_width = self.g_tp.wire_inside_mat.pitch / 2
        else:
            self.wire_width = self.g_tp.wire_local.pitch / 2

        self.wire_spacing = self.wire_width

        self.wire_width *= (self.w_scale * 1e-6 / 2)
        self.wire_spacing *= (self.s_scale * 1e-6 / 2)

        Wire.initialized = 1
        self.init_wire()
        Wire.wire_width_init = self.wire_width
        Wire.wire_spacing_init = self.wire_spacing

        # assert self.power.readOp.dynamic > 0
        # assert self.power.readOp.leakage > 0
        # assert self.power.readOp.gate_leakage > 0

    def __del__(self):
        pass

    def calculate_wire_stats(self):
        # Issue
        # print(f"CALC WIRE STATS self.wt: {self.wt}")
        # self.print_wire()
        # print()
        # import time
        # time.sleep(20)
        if self.wire_placement == parameter.outside_mat:
            self.wire_width = self.g_tp.wire_outside_mat.pitch / 2
        elif self.wire_placement == parameter.inside_mat:
            self.wire_width = self.g_tp.wire_inside_mat.pitch / 2
        else:
            self.wire_width = self.g_tp.wire_local.pitch / 2

        self.wire_spacing = self.wire_width

        self.wire_width *= (self.w_scale * 1e-6 / 2)
        self.wire_spacing *= (self.s_scale * 1e-6 / 2)

        if self.wt != 'Low_swing':
            if self.wt == 'Global':
                self.delay = Wire.global_.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_.area.w
                self.repeater_size = Wire.global_.area.h

                write_to_debug("wire_length", self.wire_length)
                write_to_debug("org_dynamic", Wire.global_.power.readOp.dynamic)
                write_to_debug("org_leakage", Wire.global_.power.readOp.leakage)
                write_to_debug("org_gate_leakage", Wire.global_.power.readOp.gate_leakage)
                write_to_debug("org_gate_leakage", Wire.global_.area.w)
                write_to_debug("org_gate_leakage", Wire.global_.area.h)
                write_to_debug("final_dynamic", self.power.readOp.dynamic)
                write_to_debug("final_leakage", self.power.readOp.leakage)
                write_to_debug("final_gate_leakage", self.power.readOp.gate_leakage)

                self.area.set_area(
                    (self.wire_length / self.repeater_spacing)
                    * compute_gate_area(
                        self.g_ip,
                        self.g_tp,
                        INV,
                        1,
                        self.min_w_pmos * self.repeater_size,
                        self.g_tp.min_w_nmos_ * self.repeater_size,
                        self.g_tp.cell_h_def,
                    )
                )
            else: # Check wr wire type
                print(f"Oop self.wt is {self.wt}")
                raise AssertionError()

            self.out_rise_time = self.delay * self.repeater_spacing / self.deviceType.Vth
        elif self.wt == 'Low_swing':
            self.low_swing_model()
            self.repeater_spacing = self.wire_length
            self.repeater_size = 1
        else:
            raise AssertionError()

    def signal_fall_time(self):
        timeconst = (drain_C_(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def) +
                     drain_C_(self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def) +
                     gate_C(self.g_tp, self.min_w_pmos + self.g_tp.min_w_nmos_, 0)) * \
                    tr_R_on(self.g_tp, self.min_w_pmos, PCH, 1)
        rt = horowitz(self.g_ip, 0, timeconst, self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, FALL) / (self.deviceType.Vdd - self.deviceType.Vth)
        timeconst = (drain_C_(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def) +
                     drain_C_(self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def) +
                     gate_C(self.g_tp, self.min_w_pmos + self.g_tp.min_w_nmos_, 0)) * \
                    tr_R_on(self.g_tp, self.g_tp.min_w_nmos_, NCH, 1)
        ft = horowitz(self.g_ip, rt, timeconst, self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, RISE) / self.deviceType.Vth
        return ft

    def signal_rise_time(self):
        timeconst = (
            parameter.drain_C_(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def)
            + parameter.drain_C_(self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def)
            + parameter.gate_C(self.g_tp, self.min_w_pmos + self.g_tp.min_w_nmos_, 0)
        ) * parameter.tr_R_on(self.g_tp, self.g_tp.min_w_nmos_, NCH, 1)
        rt = (
            parameter.horowitz(self.g_ip, 
                0,
                timeconst,
                self.deviceType.Vth / self.deviceType.Vdd,
                self.deviceType.Vth / self.deviceType.Vdd,
                RISE,
            )
            / self.deviceType.Vth
        )
        timeconst = (
            parameter.drain_C_(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def)
            + parameter.drain_C_(self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def)
            + parameter.gate_C(self.g_tp, self.min_w_pmos + self.g_tp.min_w_nmos_, 0)
        ) * parameter.tr_R_on(self.g_tp, self.min_w_pmos, PCH, 1)
        ft = parameter.horowitz(self.g_ip, 
            rt,
            timeconst,
            self.deviceType.Vth / self.deviceType.Vdd,
            self.deviceType.Vth / self.deviceType.Vdd,
            FALL,
        ) / (self.deviceType.Vdd - self.deviceType.Vth)
        return ft

    def wire_cap(self, length, call_from_outside=False):
        epsilon0 = 8.8542e-12
        if self.wire_placement == 'outside_mat':
            aspect_ratio = self.g_tp.wire_outside_mat.aspect_ratio
            horiz_dielectric_constant = self.g_tp.wire_outside_mat.horiz_dielectric_constant
            vert_dielectric_constant = self.g_tp.wire_outside_mat.vert_dielectric_constant
            miller_value = self.g_tp.wire_outside_mat.miller_value
            ild_thickness = self.g_tp.wire_outside_mat.ild_thickness
        elif self.wire_placement == 'inside_mat':
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

        if call_from_outside:
            self.wire_width *= 1e-6
            self.wire_spacing *= 1e-6

        wire_height = self.wire_width / self.w_scale * aspect_ratio
        sidewall = miller_value * horiz_dielectric_constant * (wire_height / self.wire_spacing) * epsilon0
        adj = miller_value * vert_dielectric_constant * self.wire_width / (ild_thickness * 1e-6) * epsilon0
        tot_cap = (sidewall + adj + (self.g_tp.fringe_cap * 1e6))

        if call_from_outside:
            self.wire_width *= 1e6
            self.wire_spacing *= 1e6

        return tot_cap * length

    def wire_res(self, length):
        alpha_scatter = 1.05
        dishing_thickness = 0
        barrier_thickness = 0

        if self.wire_placement == 'outside_mat':
            aspect_ratio = self.g_tp.wire_outside_mat.aspect_ratio
        elif self.wire_placement == 'inside_mat':
            aspect_ratio = self.g_tp.wire_inside_mat.aspect_ratio
        else:
            aspect_ratio = self.g_tp.wire_local.aspect_ratio

        return (alpha_scatter * self.resistivity * 1e-6 * length /
                ((aspect_ratio * self.wire_width / self.w_scale - dishing_thickness - barrier_thickness) *
                 (self.wire_width - 2 * barrier_thickness)))

    def low_swing_model(self):
        len_ = self.wire_length
        beta = parameter.pmos_to_nmos_sz_ratio(self.g_tp,)

        inputrise = self.in_rise_time if self.in_rise_time != 0 else self.signal_rise_time()

        cwire = self.wire_cap(len_)
        rwire = self.wire_res(len_)

        RES_ADJ = 8.6
        driver_res = (-8 * self.g_tp.FO4 / (math.log(0.5) * cwire)) / RES_ADJ
        nsize = parameter.R_to_w(self.g_tp, driver_res, NCH)

        # CHANGE: MAX - can ignore to reduce expression length
        # nsize = sp.Min(nsize, self.g_tp.max_w_nmos_)
        # nsize = symbolic_convex_max(nsize, self.g_tp.min_w_nmos_)

        # CHANGE: RELATIONAL
        # if rwire * cwire > 8 * self.g_tp.FO4:
        #     nsize = self.g_tp.max_w_nmos_

        if self.g_ip.use_piecewise:
            nsize = sp.Piecewise(
                (self.g_tp.max_w_nmos_, rwire * cwire > 8 * self.g_tp.FO4),
                (nsize, True)
            )

        st_eff = sp.sqrt(
            (2 + beta / 1 + beta)
            * parameter.gate_C(self.g_tp, nsize, 0)
            / (
                parameter.gate_C(self.g_tp, 2 * self.g_tp.min_w_nmos_, 0)
                + parameter.gate_C(self.g_tp, 2 * self.min_w_pmos, 0)
            )
        )
        req_cin = ((2 + beta / 1 + beta) * parameter.gate_C(self.g_tp, nsize, 0)) / st_eff
        inv_size = req_cin / (
            parameter.gate_C(self.g_tp, self.min_w_pmos, 0) + parameter.gate_C(self.g_tp, self.g_tp.min_w_nmos_, 0)
        )

        # CHANGE: MAX - can ignore to reduce expression size
        inv_size = parameter.symbolic_convex_max(inv_size, 1)

        res_eq = 2 * parameter.tr_R_on(self.g_tp, self.g_tp.min_w_nmos_, NCH, 1)
        cap_eq = (
            2 * parameter.drain_C_(self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def)
            + parameter.drain_C_(self.g_ip, self.g_tp, 2 * self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def)
            + parameter.gate_C(self.g_tp, inv_size * self.g_tp.min_w_nmos_, 0)
            + parameter.gate_C(self.g_tp, inv_size * self.min_w_pmos, 0)
        )

        timeconst = res_eq * cap_eq
        self.delay = parameter.horowitz(self.g_ip, 
            inputrise,
            timeconst,
            self.deviceType.Vth / self.deviceType.Vdd,
            self.deviceType.Vth / self.deviceType.Vdd,
            RISE,
        )
        temp_power = cap_eq * self.deviceType.Vdd * self.deviceType.Vdd

        inputrise = self.delay / (self.deviceType.Vdd - self.deviceType.Vth)

        res_eq = parameter.tr_R_on(self.g_tp, inv_size * self.min_w_pmos, PCH, 1)
        cap_eq = (
            parameter.drain_C_(self.g_ip, self.g_tp, inv_size * self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def)
            + parameter.drain_C_(self.g_ip, self.g_tp, 
                inv_size * self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def
            )
            + parameter.gate_C(self.g_tp, nsize, 0)
        )
        timeconst = res_eq * cap_eq

        self.delay += parameter.horowitz(self.g_ip, 
            inputrise,
            timeconst,
            self.deviceType.Vth / self.deviceType.Vdd,
            self.deviceType.Vth / self.deviceType.Vdd,
            FALL,
        )
        temp_power += cap_eq * self.deviceType.Vdd * self.deviceType.Vdd

        self.transmitter.delay = self.delay
        self.transmitter.power.readOp.dynamic = temp_power * 2
        self.transmitter.power.readOp.leakage = self.deviceType.Vdd * (
            4
            * parameter.cmos_Isub_leakage(self.g_tp, self.g_tp.min_w_nmos_, self.min_w_pmos, 2, "nand")
            + 4
            * parameter.cmos_Isub_leakage(self.g_tp, self.g_tp.min_w_nmos_, self.min_w_pmos, 1, "inv")
        )

        self.transmitter.power.readOp.gate_leakage = self.deviceType.Vdd * (
            4 * parameter.cmos_Ig_leakage(self.g_tp, self.g_tp.min_w_nmos_, self.min_w_pmos, 2, "nand")
            + 4 * parameter.cmos_Ig_leakage(self.g_tp, self.g_tp.min_w_nmos_, self.min_w_pmos, 1, "inv")
        )

        inputrise = self.delay / self.deviceType.Vth

        cap_eq = (
            cwire
            + 2 * parameter.drain_C_(self.g_ip, self.g_tp, nsize, NCH, 1, 1, self.g_tp.cell_h_def)
            + self.nsense * self.sense_amp_input_cap()
        )
        timeconst = (
            (parameter.tr_R_on(self.g_tp, nsize, NCH, 1) * RES_ADJ)
            * (cwire + 2 * parameter.drain_C_(self.g_ip, self.g_tp, nsize, NCH, 1, 1, self.g_tp.cell_h_def))
            + rwire * cwire / 2
            + (parameter.tr_R_on(self.g_tp, nsize, NCH, 1) * RES_ADJ + rwire)
            * self.nsense
            * self.sense_amp_input_cap()
        )

        self.delay += parameter.horowitz(self.g_ip, 
            inputrise, timeconst, self.deviceType.Vth / self.deviceType.Vdd, 0.25, 0
        )
        VOL_SWING = 0.1
        temp_power += cap_eq * VOL_SWING * 0.400
        temp_power *= 2

        self.l_wire.delay = self.delay - self.transmitter.delay
        self.l_wire.power.readOp.dynamic = temp_power - self.transmitter.power.readOp.dynamic
        self.l_wire.power.readOp.leakage = self.deviceType.Vdd * (
            4 * parameter.cmos_Isub_leakage(self.g_tp, nsize, 0, 1, nmos)
        )

        self.l_wire.power.readOp.gate_leakage = self.deviceType.Vdd * (
            4 * parameter.cmos_Ig_leakage(self.g_tp, nsize, 0, 1, nmos)
        )

        self.delay += self.g_tp.sense_delay

        self.sense_amp.delay = self.g_tp.sense_delay
        self.out_rise_time = self.g_tp.sense_delay / self.deviceType.Vth
        self.sense_amp.power.readOp.dynamic = self.g_tp.sense_dy_power
        self.sense_amp.power.readOp.leakage = 0
        self.sense_amp.power.readOp.gate_leakage = 0

        self.power.readOp.dynamic = temp_power + self.sense_amp.power.readOp.dynamic
        self.power.readOp.leakage = self.transmitter.power.readOp.leakage + \
                                    self.l_wire.power.readOp.leakage + \
                                    self.sense_amp.power.readOp.leakage
        self.power.readOp.gate_leakage = self.transmitter.power.readOp.gate_leakage + \
                                         self.l_wire.power.readOp.gate_leakage + \
                                         self.sense_amp.power.readOp.gate_leakage

    def sense_amp_input_cap(self):
        return (
            parameter.drain_C_(self.g_ip, self.g_tp, self.g_tp.w_iso, PCH, 1, 1, self.g_tp.cell_h_def)
            + parameter.gate_C(self.g_tp, self.g_tp.w_sense_en + self.g_tp.w_sense_n, 0)
            + parameter.drain_C_(self.g_ip, self.g_tp, self.g_tp.w_sense_n, NCH, 1, 1, self.g_tp.cell_h_def)
            + parameter.drain_C_(self.g_ip, self.g_tp, self.g_tp.w_sense_p, PCH, 1, 1, self.g_tp.cell_h_def)
        )

    def delay_optimal_wire(self):
        len_ = self.wire_length
        beta = parameter.pmos_to_nmos_sz_ratio(self.g_tp, )
        switching = 0
        short_ckt = 0
        tc = 0
        input_cap = parameter.gate_C(self.g_tp, self.g_tp.min_w_nmos_ + self.min_w_pmos, 0)
        out_cap = parameter.drain_C_( 
            self.g_ip, self.g_tp, self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def
        ) + parameter.drain_C_(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def)
        out_res = (
            parameter.tr_R_on(self.g_tp, self.g_tp.min_w_nmos_, NCH, 1)
            + parameter.tr_R_on(self.g_tp, self.min_w_pmos, PCH, 1)
        ) / 2
        wr = self.wire_res(len_)
        wc = self.wire_cap(len_)
        repeater_scaling = sp.sqrt(out_res * wc / (wr * input_cap))
        self.repeater_spacing = sp.sqrt(2 * out_res * (out_cap + input_cap) / ((wr / len_) * (wc / len_)))
        self.repeater_size = repeater_scaling

        # since don't search over wires
        self.repeater_size = self.g_ip.repeater_size    # si
        self.repeater_spacing = self.g_ip.repeater_spacing * (1e-6)  # sp CHECK

        switching = (
            (repeater_scaling * (input_cap + out_cap) +
            self.repeater_spacing * (wc / len_)) *
            self.deviceType.Vdd * self.deviceType.Vdd
        )

        tc = (
            out_res * (input_cap + out_cap) +
            out_res * wc / len_ * self.repeater_spacing / repeater_scaling +
            wr / len_ * self.repeater_spacing * input_cap * repeater_scaling +
            0.5 * (wr / len_) * (wc / len_) * self.repeater_spacing * self.repeater_spacing
        )

        self.delay = 0.693 * tc * len_ / self.repeater_spacing

        Ishort_ckt = 65e-6
        short_ckt = (
            self.deviceType.Vdd * self.g_tp.min_w_nmos_ * Ishort_ckt * 1.0986 *
            repeater_scaling * tc
        )

        self.area.set_area(
            (len_ / self.repeater_spacing)
            * compute_gate_area(
                self.g_ip,
                self.g_tp,
                INV,
                1,
                self.min_w_pmos * repeater_scaling,
                self.g_tp.min_w_nmos_ * repeater_scaling,
                self.g_tp.cell_h_def,
            )
        )

        self.power.readOp.dynamic = (len_ / self.repeater_spacing) * (switching + short_ckt)
        self.power.readOp.leakage = (
            (len_ / self.repeater_spacing)
            * self.deviceType.Vdd
            * parameter.cmos_Isub_leakage(self.g_tp, 
                self.g_tp.min_w_nmos_ * repeater_scaling,
                beta * self.g_tp.min_w_nmos_ * repeater_scaling,
                1,
                inv,
            )
        )
        self.power.readOp.gate_leakage = (
            (len_ / self.repeater_spacing)
            * self.deviceType.Vdd
            * parameter.cmos_Ig_leakage(self.g_tp, 
                self.g_tp.min_w_nmos_ * repeater_scaling,
                beta * self.g_tp.min_w_nmos_ * repeater_scaling,
                1,
                inv,
            )
        )

    def init_wire(self):
        self.wire_length = 1 # SOURCE OF ALL EVIL
        self.delay_optimal_wire()

        # sp = self.repeater_spacing * 1e6  # in microns
        sp = int(self.g_ip.repeater_spacing)  # CHANGE: ARRAY LOGIC
        si = int(self.g_ip.repeater_size) # CHANGE: ARRAY LOGIC

        # CHANGE: ARRAY LOGIC - cannot index with symbolic expression, so we have to use value
        self.repeated_wire.append(Component())
        for j in range(int(sp), int(4 * sp), 100):
            for i in range(int(si), 1, -1):
                pow_, del_ = self.wire_model(j * 1e-6, i)

                if j == int(sp) and i == int(si):
                    Wire.global_.delay = del_
                    Wire.global_.power = pow_
                    Wire.global_.area.h = si
                    Wire.global_.area.w = sp * 1e-6  # m
                    # print(f"DYNAMIC: {Wire.global_.power.readOp.dynamic}")
                    # print(f"LEAKAGE: {Wire.global_.power.readOp.leakage}")
                    # print(f"GATE_LEAKAGE: {Wire.global_.power.readOp.gate_leakage}")

                self.repeated_wire[-1].delay = del_
                self.repeated_wire[-1].power.readOp = pow_.readOp
                self.repeated_wire[-1].area.w = j * 1e-6  # m
                self.repeated_wire[-1].area.h = i
                self.repeated_wire.append(Component())

        self.repeated_wire.pop()
        # self.update_fullswing()

        # Wire.global_.area.h = si 
        # Wire.global_.area.w = sp * 1e-6  # m

        l_wire = Wire(self.g_ip, self.g_tp, 'Low_swing', 0.001, 1)
        Wire.low_swing.delay = l_wire.delay
        Wire.low_swing.power = l_wire.power
        del l_wire

    # def update_fullswing(self):
    #     deltas = [
    #         self.global_.delay + self.global_.delay * 0.05,
    #         self.global_.delay + self.global_.delay * 0.1,
    #         self.global_.delay + self.global_.delay * 0.2,
    #         self.global_.delay + self.global_.delay * 0.3
    #     ]

    #     i = 4
    #     while i > 0:
    #         threshold = deltas[i - 1]
    #         cost = float('inf')
    #         for citer in list(self.repeated_wire):
    #             # CHANGE: RELATIONAL LOGIC
    #             # if citer.delay > threshold:
    #             #     self.repeated_wire.remove(citer)
    #             # else:
    #             ncost = citer.power.readOp.dynamic / self.global_.power.readOp.dynamic + \
    #                     citer.power.readOp.leakage / self.global_.power.readOp.leakage

    #             # CHANGE: RELATIONAL LOGIC
    #             # if ncost < cost:
    #             cost = ncost
    #             if i == 4:
    #                 Wire.global_30.delay = citer.delay
    #                 Wire.global_30.power = citer.power
    #                 Wire.global_30.area = citer.area
    #             elif i == 3:
    #                 Wire.global_20.delay = citer.delay
    #                 Wire.global_20.power = citer.power
    #                 Wire.global_20.area = citer.area
    #             elif i == 2:
    #                 Wire.global_10.delay = citer.delay
    #                 Wire.global_10.power = citer.power
    #                 Wire.global_10.area = citer.area
    #             elif i == 1:
    #                 Wire.global_5.delay = citer.delay
    #                 Wire.global_5.power = citer.power
    #                 Wire.global_5.area = citer.area
    #         i -= 1

    def wire_model(self, space, size):
        ptemp = PowerDef()
        len_ = 1
        beta = parameter.pmos_to_nmos_sz_ratio(self.g_tp,)
        switching = 0
        short_ckt = 0
        tc = 0
        input_cap = parameter.gate_C(self.g_tp, self.g_tp.min_w_nmos_ + self.min_w_pmos, 0)
        out_cap = parameter.drain_C_(self.g_ip, self.g_tp, 
            self.min_w_pmos, PCH, 1, 1, self.g_tp.cell_h_def
        ) + parameter.drain_C_(self.g_ip, self.g_tp, self.g_tp.min_w_nmos_, NCH, 1, 1, self.g_tp.cell_h_def)
        out_res = (
            parameter.tr_R_on(self.g_tp, self.g_tp.min_w_nmos_, NCH, 1)
            + parameter.tr_R_on(self.g_tp, self.min_w_pmos, PCH, 1)
        ) / 2
        wr = self.wire_res(len_)
        wc = self.wire_cap(len_)

        repeater_spacing = space
        repeater_size = size

        switching = (repeater_size * (input_cap + out_cap) +
                     repeater_spacing * (wc / len_)) * self.deviceType.Vdd * self.deviceType.Vdd

        tc = out_res * (input_cap + out_cap) + \
             out_res * wc / len_ * repeater_spacing / repeater_size + \
             wr / len_ * repeater_spacing * out_cap * repeater_size + \
             0.5 * (wr / len_) * (wc / len_) * repeater_spacing * repeater_spacing

        delay = 0.693 * tc * len_ / repeater_spacing

        Ishort_ckt = 65e-6
        short_ckt = self.deviceType.Vdd * self.g_tp.min_w_nmos_ * Ishort_ckt * 1.0986 * \
                    repeater_size * tc

        ptemp.readOp.dynamic = (len_ / repeater_spacing) * (switching + short_ckt)
        ptemp.readOp.leakage = (len_ / repeater_spacing) * \
                               self.deviceType.Vdd * \
                               parameter.cmos_Isub_leakage(self.g_tp, self.g_tp.min_w_nmos_ * repeater_size,
                                                      beta * self.g_tp.min_w_nmos_ * repeater_size, 1, inv)

        ptemp.readOp.gate_leakage = (
            (len_ / repeater_spacing)
            * self.deviceType.Vdd
            * parameter.cmos_Ig_leakage(self.g_tp, 
                self.g_tp.min_w_nmos_ * repeater_size,
                beta * self.g_tp.min_w_nmos_ * repeater_size,
                1,
                inv,
            )
        )

        return ptemp, delay

    def print_wire(self):
        print("\nWire Properties:\n")

        # Delay Optimal
        print("  Delay Optimal")
        print(f"\tRepeater size - {self.global_.area.h}")
        print(f"\tRepeater spacing - {self.global_.area.w * 1e3} (mm)")
        print(f"\tDelay - {self.global_.delay * 1e6} (ns/mm)")
        print(f"\tPowerD - {self.global_.power.readOp.dynamic * 1e6} (nJ/mm)")
        print(f"\tPowerL - {self.global_.power.readOp.leakage} (mW/mm)")
        print(f"\tPowerLgate - {self.global_.power.readOp.gate_leakage} (mW/mm)")

        # ISSUE! These two is none for some reason
        # print(f"\tWire width - {self.wire_width_init * 1e6} microns")
        # print(f"\tWire spacing - {self.wire_spacing_init * 1e6} microns\n")

        # 5% Overhead
        print("  5% Overhead")
        print(f"\tRepeater size - {self.global_5.area.h}")
        print(f"\tRepeater spacing - {self.global_5.area.w * 1e3} (mm)")
        print(f"\tDelay - {self.global_5.delay * 1e6} (ns/mm)")
        print(f"\tPowerD - {self.global_5.power.readOp.dynamic * 1e6} (nJ/mm)")
        print(f"\tPowerL - {self.global_5.power.readOp.leakage} (mW/mm)")
        print(f"\tPowerLgate - {self.global_5.power.readOp.gate_leakage} (mW/mm)")
        # print(f"\tWire width - {self.wire_width_init * 1e6} microns")
        # print(f"\tWire spacing - {self.wire_spacing_init * 1e6} microns\n")

        # 10% Overhead
        print("  10% Overhead")
        print(f"\tRepeater size - {self.global_10.area.h}")
        print(f"\tRepeater spacing - {self.global_10.area.w * 1e3} (mm)")
        print(f"\tDelay - {self.global_10.delay * 1e6} (ns/mm)")
        print(f"\tPowerD - {self.global_10.power.readOp.dynamic * 1e6} (nJ/mm)")
        print(f"\tPowerL - {self.global_10.power.readOp.leakage} (mW/mm)")
        print(f"\tPowerLgate - {self.global_10.power.readOp.gate_leakage} (mW/mm)")
        # print(f"\tWire width - {self.wire_width_init * 1e6} microns")
        # print(f"\tWire spacing - {self.wire_spacing_init * 1e6} microns\n")

        # 20% Overhead
        print("  20% Overhead")
        print(f"\tRepeater size - {self.global_20.area.h}")
        print(f"\tRepeater spacing - {self.global_20.area.w * 1e3} (mm)")
        print(f"\tDelay - {self.global_20.delay * 1e6} (ns/mm)")
        print(f"\tPowerD - {self.global_20.power.readOp.dynamic * 1e6} (nJ/mm)")
        print(f"\tPowerL - {self.global_20.power.readOp.leakage} (mW/mm)")
        print(f"\tPowerLgate - {self.global_20.power.readOp.gate_leakage} (mW/mm)")
        # print(f"\tWire width - {self.wire_width_init * 1e6} microns")
        # print(f"\tWire spacing - {self.wire_spacing_init * 1e6} microns\n")

        # 30% Overhead
        print("  30% Overhead")
        print(f"\tRepeater size - {self.global_30.area.h}")
        print(f"\tRepeater spacing - {self.global_30.area.w * 1e3} (mm)")
        print(f"\tDelay - {self.global_30.delay * 1e6} (ns/mm)")
        print(f"\tPowerD - {self.global_30.power.readOp.dynamic * 1e6} (nJ/mm)")
        print(f"\tPowerL - {self.global_30.power.readOp.leakage} (mW/mm)")
        print(f"\tPowerLgate - {self.global_30.power.readOp.gate_leakage} (mW/mm)")
        # print(f"\tWire width - {self.wire_width_init * 1e6} microns")
        # print(f"\tWire spacing - {self.wire_spacing_init * 1e6} microns\n")

        # Low-swing wire
        print("  Low-swing wire (1 mm) - Note: Unlike repeated wires, delay and power values of low-swing wires do not have a linear relationship with length.")
        print(f"\tDelay - {self.low_swing.delay * 1e9} (ns)")
        print(f"\tPowerD - {self.low_swing.power.readOp.dynamic * 1e9} (nJ)")
        print(f"\tPowerL - {self.low_swing.power.readOp.leakage} (mW)")
        print(f"\tPowerLgate - {self.low_swing.power.readOp.gate_leakage} (mW)")
        # print(f"\tWire width - {self.wire_width_init * 2} microns")
        # print(f"\tWire spacing - {self.wire_spacing_init * 2} microns\n")

    def set_in_rise_time(self, rt):
        self.in_rise_time = rt


def write_to_debug(name, value):
    output_dir = os.path.join(os.path.dirname(__file__), "debug_sympy_expressions")
    os.makedirs(output_dir, exist_ok=True)

    # Initialize the file path and counter
    counter = 1
    file_path = os.path.join(output_dir, f"wire_{name}.txt")
    
    # Check if the file already exists and increment the counter
    while os.path.exists(file_path):
        file_path = os.path.join(output_dir, f"wire_{name}_{counter}.txt")
        counter += 1
    
    # Write the value of the expression to the file
    with open(file_path, "w") as file:
        file.write(str(value))