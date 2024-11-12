import math
from enum import Enum
from typing import List

from .cacti_interface import PowerDef
from .component import Component, compute_gate_area
from .const import *
from . import parameter
from .parameter import gate_C, drain_C_, horowitz, tr_R_on

# Placeholder constants and functions (to be implemented)
CU_RESISTIVITY = 1.68e-8  # Copper resistivity (Ohm*m), placeholder value
BIGNUM = 1e30  # Large number used in comparisons, placeholder value

# Enums for Wire type and placement
class WireType(Enum):
    Global = 0
    Global_5 = 1
    Global_10 = 2
    Global_20 = 3
    Global_30 = 4
    Low_swing = 5

class WirePlacement(Enum):
    outside_mat = 0
    inside_mat = 1
    local = 2  # Added for default case

# Wire class
class Wire(Component):
    # Static variables
    initialized = 0
    global_wire = Component()
    global_5 = Component()
    global_10 = Component()
    global_20 = Component()
    global_30 = Component()
    low_swing_wire = Component()
    wire_width_init = 0.0
    wire_spacing_init = 0.0

    def __init__(self, g_ip, g_tp, wire_model="Global", wl=None, n=1, w_s=1.0, s_s=1.0,
                 wire_placement=WirePlacement.outside_mat, resistivity=CU_RESISTIVITY, dt=None):
        super().__init__()
        self.deviceType = dt if dt else g_tp.peri_global
        self.min_w_pmos = self.deviceType.n_to_p_eff_curr_drv_ratio * g_tp.min_w_nmos_
        self.in_rise_time = 0.0
        self.out_rise_time = 0.0

        if wire_model is not None and wl is not None:
            # Constructor for calculating wire stats
            self.wt = wire_model
            self.wire_length = wl * 1e-6  # Convert from microns to meters
            self.nsense = n
            self.w_scale = w_s
            self.s_scale = s_s
            self.wire_placement = wire_placement
            self.resistivity = resistivity
            if Wire.initialized != 1:
                print("Wire not initialized. Initializing it with default values")
                Wire(w_s=1.0, s_s=1.0, wire_placement=WirePlacement.outside_mat,
                     resistivity=CU_RESISTIVITY, dt=g_tp.peri_global)
            self.calculate_wire_stats()
            # Convert back to microns
            self.repeater_spacing *= 1e6
            self.wire_length *= 1e6
            self.wire_width *= 1e6
            self.wire_spacing *= 1e6

            assert self.wire_length > 0
            assert self.power.readOp.dynamic > 0
            assert self.power.readOp.leakage > 0
            assert self.power.readOp.gate_leakage > 0
        else:
            # Constructor for initializing static members
            self.w_scale = w_s
            self.s_scale = s_s
            self.wire_placement = wire_placement
            self.resistivity = resistivity
            self.wire_width = 0.0
            self.wire_spacing = 0.0
            if self.wire_placement == WirePlacement.outside_mat:
                self.wire_width = g_tp.wire_outside_mat.pitch / 2
            elif self.wire_placement == WirePlacement.inside_mat:
                self.wire_width = g_tp.wire_inside_mat.pitch / 2
            else:
                self.wire_width = g_tp.wire_local.pitch / 2

            self.wire_spacing = self.wire_width

            self.wire_width *= (self.w_scale * 1e-6 / 2)  # (m)
            self.wire_spacing *= (self.s_scale * 1e-6 / 2)  # (m)

            Wire.initialized = 1
            self.init_wire()
            Wire.wire_width_init = self.wire_width
            Wire.wire_spacing_init = self.wire_spacing

            assert self.power.readOp.dynamic > 0
            assert self.power.readOp.leakage > 0
            assert self.power.readOp.gate_leakage > 0

    def init_wire(self):
        self.wire_length = 1.0  # Unit length
        self.delay_optimal_wire()
        sp = self.repeater_spacing
        si = self.repeater_size
        sp *= 1e6  # Convert to microns

        print(f"Repeater Spacing: {sp}")
        print(f"Repeater Size: {si}")

        # Keep track of repeater metrics
        g_ip.repeater_spacing = sp
        g_ip.repeater_size = si

        repeated_wire = []
        repeated_wire.append(Component())

        for j in range(int(sp), int(4 * sp), 100):
            for i in range(int(si), 1, -1):
                delay = 0.0
                pow = self.wire_model(j * 1e-6, i, delay)
                if j == sp and i == si:
                    Wire.global_wire.delay = delay
                    Wire.global_wire.power = pow
                    Wire.global_wire.area.h = si
                    Wire.global_wire.area.w = sp * 1e-6  # m
                repeated_wire[-1].delay = delay
                repeated_wire[-1].power.readOp = pow.readOp
                repeated_wire[-1].area.w = j * 1e-6  # m
                repeated_wire[-1].area.h = i
                repeated_wire.append(Component())
        repeated_wire.pop()
        self.update_fullswing(repeated_wire)
        l_wire = Wire(WireType.Low_swing, 0.001, 1)
        Wire.low_swing_wire.delay = l_wire.delay
        Wire.low_swing_wire.power = l_wire.power

    def update_fullswing(self, repeated_wire: List[Component]):
        del_thresholds = [
            Wire.global_wire.delay + Wire.global_wire.delay * 0.05,
            Wire.global_wire.delay + Wire.global_wire.delay * 0.1,
            Wire.global_wire.delay + Wire.global_wire.delay * 0.2,
            Wire.global_wire.delay + Wire.global_wire.delay * 0.3,
        ]
        for i in range(4, 0, -1):
            threshold = del_thresholds[i - 1]
            cost = BIGNUM
            for component in repeated_wire:
                if component.delay > threshold:
                    repeated_wire.remove(component)
                else:
                    ncost = (component.power.readOp.dynamic / Wire.global_wire.power.readOp.dynamic +
                             component.power.readOp.leakage / Wire.global_wire.power.readOp.leakage)
                    if ncost < cost:
                        cost = ncost
                        if i == 4:
                            Wire.global_30.delay = component.delay
                            Wire.global_30.power = component.power
                            Wire.global_30.area = component.area
                        elif i == 3:
                            Wire.global_20.delay = component.delay
                            Wire.global_20.power = component.power
                            Wire.global_20.area = component.area
                        elif i == 2:
                            Wire.global_10.delay = component.delay
                            Wire.global_10.power = component.power
                            Wire.global_10.area = component.area
                        elif i == 1:
                            Wire.global_5.delay = component.delay
                            Wire.global_5.power = component.power
                            Wire.global_5.area = component.area

    def calculate_wire_stats(self):
        if self.wire_placement == WirePlacement.outside_mat:
            self.wire_width = g_tp.wire_outside_mat.pitch / 2
        elif self.wire_placement == WirePlacement.inside_mat:
            self.wire_width = g_tp.wire_inside_mat.pitch / 2
        else:
            self.wire_width = g_tp.wire_local.pitch / 2

        self.wire_spacing = self.wire_width

        self.wire_width *= (self.w_scale * 1e-6 / 2)  # (m)
        self.wire_spacing *= (self.s_scale * 1e-6 / 2)  # (m)

        if self.wt != WireType.Low_swing:
            # Delay optimal wire calculations (omitted for brevity)
            if self.wt == WireType.Global:
                self.delay = Wire.global_wire.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_wire.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_wire.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_wire.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_wire.area.w
                self.repeater_size = Wire.global_wire.area.h
                self.area.set_area((self.wire_length / self.repeater_spacing) *
                                   compute_gate_area('INV', 1,
                                                     self.min_w_pmos * self.repeater_size,
                                                     g_tp.min_w_nmos_ * self.repeater_size,
                                                     g_tp.cell_h_def))
            # Similar handling for other WireType values (Global_5, Global_10, etc.)
            self.out_rise_time = self.delay * self.repeater_spacing / self.deviceType.Vth
        elif self.wt == WireType.Low_swing:
            self.low_swing_model()
            self.repeater_spacing = self.wire_length
            self.repeater_size = 1
        else:
            assert False, "Invalid WireType"

    def wire_cap(self, length, call_from_outside=False):
        # Capacitance calculations (omitted for brevity)
        # Returns capacitance (F)
        return 0.0

    def wire_res(self, length):
        # Resistance calculations (omitted for brevity)
        # Returns resistance (Ohms)
        return 0.0

    def low_swing_model(self):
        # Low swing wire model calculations (omitted for brevity)
        pass

    def delay_optimal_wire(self):
        # Optimal wire delay calculations (omitted for brevity)
        pass

    def signal_fall_time(self):
        # Signal fall time calculations (omitted for brevity)
        return 0.0

    def signal_rise_time(self):
        # Signal rise time calculations (omitted for brevity)
        return 0.0

    def sense_amp_input_cap(self):
        # Sense amplifier input capacitance (omitted for brevity)
        return 0.0

    def wire_model(self, space, size, delay):
        # Wire model calculations (omitted for brevity)
        # Returns PowerDef object
        return PowerDef()

    def set_in_rise_time(self, rt):
        self.in_rise_time = rt

    def print_wire(self):
        # Method to print wire details (omitted for brevity)
        pass
