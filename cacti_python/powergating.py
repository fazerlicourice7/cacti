import math
import sys

from .area import Area
from .cacti_interface import PowerDef
from .component import Component, compute_gate_area
from .const import *
from . import parameter

class SleepTx(Component):
    def __init__(self, g_ip, g_tp, perf_with_sleep_tx, active_Isat, is_footer, c_circuit_wakeup, V_delta, num_sleep_tx, cell):
        super().__init__()
        self.g_ip = g_ip
        self.g_tp = g_tp
        self.perf_with_sleep_tx = perf_with_sleep_tx
        self.active_Isat = active_Isat
        self.is_footer = is_footer
        self.c_circuit_wakeup = c_circuit_wakeup
        self.V_delta = V_delta
        self.num_sleep_tx = num_sleep_tx
        self.cell = cell
        self.is_sleep_tx = True

        # Initialize other variables
        self.vdd = g_tp.peri_global.Vdd
        self.vt_circuit = g_tp.peri_global.Vth
        self.vt_sleep_tx = g_tp.sleep_tx.Vth
        self.mobility = g_tp.sleep_tx.Mobility_n
        self.c_ox = g_tp.sleep_tx.C_ox

        p_to_n_sz_ratio = parameter.pmos_to_nmos_sz_ratio(self.g_tp, False, False, True)
        self.width = active_Isat / (perf_with_sleep_tx * self.mobility * self.c_ox * (self.vdd - self.vt_circuit) * (self.vdd - self.vt_sleep_tx)) * self.g_ip.F_sz_um
        self.width /= num_sleep_tx

        raw_area = compute_gate_area(self.g_ip, self.g_tp, INV, 1, self.width, p_to_n_sz_ratio * self.width, self.cell.w * 2) / 2
        raw_width = self.cell.w
        raw_height = raw_area / self.cell.w
        self.area = Area()
        self.area.set_h(raw_height)
        self.area.set_w(raw_width)

        self.compute_penalty()

    def compute_penalty(self):
        p_to_n_sz_ratio = parameter.pmos_to_nmos_sz_ratio(self.g_tp, False, False, True)

        if self.is_footer:
            self.c_intrinsic_sleep = parameter.drain_C_(self.g_ip, self.g_tp, self.width, NCH, 1, 1, self.area.h, False, False, False, self.is_sleep_tx)
            self.wakeup_delay = (self.c_circuit_wakeup + self.c_intrinsic_sleep) * self.V_delta / (parameter.simplified_nmos_Isat(self.g_tp, self.width, False, False, False, self.is_sleep_tx) / Ilinear_to_Isat_ratio)
            self.wakeup_power = PowerDef()
            self.wakeup_power.readOp.dynamic = (self.c_circuit_wakeup + self.c_intrinsic_sleep) * self.g_tp.sram_cell.Vdd * self.V_delta
        else:
            self.c_intrinsic_sleep = parameter.drain_C_(self.g_ip, self.g_tp, self.width * p_to_n_sz_ratio, PCH, 1, 1, self.area.h, False, False, False, self.is_sleep_tx)
            self.wakeup_delay = (self.c_circuit_wakeup + self.c_intrinsic_sleep) * self.V_delta / (parameter.simplified_pmos_Isat(self.g_tp, self.width, False, False, False, self.is_sleep_tx) / Ilinear_to_Isat_ratio)
            self.wakeup_power = PowerDef()
            self.wakeup_power.readOp.dynamic = (self.c_circuit_wakeup + self.c_intrinsic_sleep) * self.g_tp.sram_cell.Vdd * self.V_delta

        return self.wakeup_delay

    def leakage_feedback(self, temperature):
        pass

    def __del__(self):
        pass
