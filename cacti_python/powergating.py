import math
import sys
from .const import *
from .decoder import *
from .parameter import g_tp
from .parameter import g_ip
from .parameter import *
from .const import *
from .component import compute_gate_area
from .component import *
from .cacti_interface import *
from .area import *


class SleepTx(Component):
    def __init__(self, perf_with_sleep_tx, active_Isat, is_footer, c_circuit_wakeup, V_delta, num_sleep_tx, cell):
        super().__init__()
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

        p_to_n_sz_ratio = pmos_to_nmos_sz_ratio(False, False, True)
        self.width = active_Isat / (perf_with_sleep_tx * self.mobility * self.c_ox * (self.vdd - self.vt_circuit) * (self.vdd - self.vt_sleep_tx)) * g_ip.F_sz_um
        self.width /= num_sleep_tx

        raw_area = compute_gate_area(INV, 1, self.width, p_to_n_sz_ratio * self.width, self.cell.w * 2) / 2
        raw_width = self.cell.w
        raw_height = raw_area / self.cell.w
        self.area = Area()
        self.area.set_h(raw_height)
        self.area.set_w(raw_width)

        self.compute_penalty()

    def compute_penalty(self):
        p_to_n_sz_ratio = pmos_to_nmos_sz_ratio(False, False, True)

        if self.is_footer:
            self.c_intrinsic_sleep = drain_C_(self.width, NCH, 1, 1, self.area.h, False, False, False, self.is_sleep_tx)
            self.wakeup_delay = (self.c_circuit_wakeup + self.c_intrinsic_sleep) * self.V_delta / (simplified_nmos_Isat(self.width, False, False, False, self.is_sleep_tx) / Ilinear_to_Isat_ratio)
            self.wakeup_power = PowerDef()
            self.wakeup_power.readOp.dynamic = (self.c_circuit_wakeup + self.c_intrinsic_sleep) * g_tp.sram_cell.Vdd * self.V_delta
        else:
            self.c_intrinsic_sleep = drain_C_(self.width * p_to_n_sz_ratio, PCH, 1, 1, self.area.h, False, False, False, self.is_sleep_tx)
            self.wakeup_delay = (self.c_circuit_wakeup + self.c_intrinsic_sleep) * self.V_delta / (simplified_pmos_Isat(self.width, False, False, False, self.is_sleep_tx) / Ilinear_to_Isat_ratio)
            self.wakeup_power = PowerDef()
            self.wakeup_power.readOp.dynamic = (self.c_circuit_wakeup + self.c_intrinsic_sleep) * g_tp.sram_cell.Vdd * self.V_delta

        return self.wakeup_delay

    def leakage_feedback(self, temperature):
        pass

    def __del__(self):
        pass