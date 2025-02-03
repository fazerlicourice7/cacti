# powergating.py
import math
import sympy as sp

from .component import Component
from .basic_circuit import (pmos_to_nmos_sz_ratio,
                            drain_C_, 
                            simplified_nmos_Isat,
                            simplified_pmos_Isat)

# Possibly from your python "parameter.py" or "component.py"
# for computing gate area:
from .component import compute_gate_area
from .area import Area
from .cacti_interface import powerDef
from .const import *

################################################################################
# Sleep_tx class in Python
################################################################################

class Sleep_tx(Component):
    def __init__(self,
                 g_ip,
                 g_tp,
                 perf_with_sleep_tx,     # double  _perf_with_sleep_tx
                 active_Isat,           # double  _active_Isat (of circuit block, not sleep tx)
                 is_footer,             # bool    _is_footer
                 c_circuit_wakeup,      # double _c_circuit_wakeup
                 V_delta,               # double _V_delta
                 num_sleep_tx,          # int     _num_sleep_tx
                 cell_area:Area):            # const  Area & cell_
        super().__init__()  # calls Component.__init__()

        # Store constructor parameters
        self.perf_with_sleep_tx   = perf_with_sleep_tx
        self.active_Isat          = active_Isat
        self.is_footer            = is_footer
        self.c_circuit_wakeup     = c_circuit_wakeup
        self.V_delta              = V_delta
        self.num_sleep_tx         = num_sleep_tx
        self.cell                 = cell_area  # "cell" is a reference to an Area object
        self.is_sleep_tx          = True

        # We read device-level parameters from g_tp and g_ip
        self.vdd         = g_tp.peri_global.Vdd
        self.vt_circuit  = g_tp.peri_global.Vth
        self.vt_sleep_tx = g_tp.sleep_tx.Vth
        self.mobility    = g_tp.sleep_tx.Mobility_n
        self.c_ox        = g_tp.sleep_tx.C_ox

        # ratio p->n for sleep transistor sizing 
        p_to_n = pmos_to_nmos_sz_ratio(g_tp, False, False, True)

        # Width = active_Isat / [perf * mobility * c_ox * (vdd - vt_circuit)*(vdd - vt_sleep_tx)] * F_sz_um
        # Then we divide by num_sleep_tx
        numerator = self.active_Isat
        denominator = (self.perf_with_sleep_tx *
                       self.mobility *
                       self.c_ox *
                       (self.vdd - self.vt_circuit) *
                       (self.vdd - self.vt_sleep_tx))
        self.width = numerator / denominator * g_ip.F_sz_um
        self.width = self.width / self.num_sleep_tx

        # Now compute some approximate area for the sleep device 
        #   raw_area = compute_gate_area(INV, 1, width, p_to_n_sz_ratio*width, cell.w*2)/2
        #   because "Only single device, assuming device is laid on the side"
        #   We do it in two steps:
        raw_area = compute_gate_area(g_ip, g_tp,
                                     gate_type='INV',
                                     num_inputs=1,
                                     w_pmos=p_to_n*self.width,
                                     w_nmos=self.width,
                                     h_gate=self.cell.w * 2)
        raw_area /= 2.0

        # The final area is wide = cell.w, height = raw_area / cell.w
        # Then we store it in self.area
        raw_width  = self.cell.w
        raw_height = raw_area / self.cell.w
        self.area.set_w(raw_width)
        self.area.set_h(raw_height)

        # Finally, compute penalty 
        self.compute_penalty(g_ip, g_tp)

    def compute_penalty(self, g_ip, g_tp):
        p_to_n = pmos_to_nmos_sz_ratio(g_tp, False, False, True)
        # we define some local references
        if self.is_footer:
            # NMOS-based Sleep transistor
            self.c_intrinsic_sleep = drain_C_(g_ip, g_tp,
                                              width=self.width,
                                              nchannel=1,  # NCH
                                              stack=1,
                                              fold_parameter=1,
                                              fold_dimension=self.area.h,
                                              is_dram=False,
                                              is_cell=False,
                                              is_wl_tr=False,
                                              is_sleep_tx=True)
            # wakeup_delay
            # (c_circuit_wakeup + c_intrinsic_sleep)*V_delta / (Isat/Ilinear_to_Isat_ratio)
            isat_n = simplified_nmos_Isat(g_tp,
                                          self.width,
                                          is_dram=False,
                                          is_cell=False,
                                          is_wl_tr=False,
                                          is_sleep_tx=True)
            self.wakeup_delay = ((self.c_circuit_wakeup + self.c_intrinsic_sleep)
                                 * self.V_delta
                                 / (isat_n / Ilinear_to_Isat_ratio))

            # dynamic wakeup power
            #   = (c_circuit_wakeup + c_intrinsic_sleep) * g_tp.sram_cell.Vdd * V_delta
            self.wakeup_power = powerDef()
            self.wakeup_power.readOp = powerDef().readOp  # or define real usage
            self.wakeup_power.readOp.dynamic = ((self.c_circuit_wakeup + self.c_intrinsic_sleep)
                                                * g_tp.sram_cell.Vdd
                                                * self.V_delta)

        else:
            # PMOS-based Sleep transistor
            self.c_intrinsic_sleep = drain_C_(g_ip, g_tp,
                                              width=self.width * p_to_n,
                                              nchannel=0,  # PCH
                                              stack=1,
                                              fold_parameter=1,
                                              fold_dimension=self.area.h,
                                              is_dram=False,
                                              is_cell=False,
                                              is_wl_tr=False,
                                              is_sleep_tx=True)
            isat_p = simplified_pmos_Isat(g_tp,
                                          self.width,
                                          is_dram=False,
                                          is_cell=False,
                                          is_wl_tr=False,
                                          is_sleep_tx=True)
            self.wakeup_delay = ((self.c_circuit_wakeup + self.c_intrinsic_sleep)
                                 * self.V_delta
                                 / (isat_p / Ilinear_to_Isat_ratio))
            self.wakeup_power = powerDef()
            self.wakeup_power.readOp.dynamic = ((self.c_circuit_wakeup + self.c_intrinsic_sleep)
                                                * g_tp.sram_cell.Vdd
                                                * self.V_delta)

        return self.wakeup_delay

    def leakage_feedback(self, temperature):
        """
        (the original code was empty).
        """
        pass

#
# End of Sleep_tx class
#
