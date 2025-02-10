# router.py

import math
import sys

from .component import Component
from .basic_circuit import (
    gate_C,
    drain_C_,
    cmos_Isub_leakage,
    cmos_Ig_leakage,
    tr_R_on,
    horowitz
)
from .const import *
from .cacti_interface import powerDef
from .wire import Wire
from .crossbar import Crossbar
from .arbiter import Arbiter
from .mat import Mat, DynamicParameter


class Router(Component):
    """
    Python translation of router.h/router.cc.

    The constructor parameters:
      g_ip, g_tp: InputParameter, TechnologyParameter
      flit_size_: double
      vc_buf: double (the 'vc_buffer_size' factor)
      vc_count: number of VCs
      dt: optional DeviceType* (defaults to g_tp.peri_global)
      I_: number of crossbar input ports
      O_: number of crossbar output ports
      M_: network load factor
    """

    def __init__(
        self,
        g_ip,     # InputParameter
        g_tp,     # TechnologyParameter
        flit_size_,
        vc_buf,   # buffer size in units of flit
        vc_c,
        dt=None,
        I_=5,
        O_=5,
        M_=0.6
    ):
        super().__init__()

        self.g_ip = g_ip
        self.g_tp = g_tp

        # store constructor args
        self.flit_size = flit_size_
        self.vc_buffer_size = vc_buf
        self.vc_count = vc_c

        if dt is None:
            dt = g_tp.peri_global
        self.deviceType = dt

        self.I = I_
        self.O = O_
        self.M = M_

        # from router.cc
        self.min_w_pmos = (
            self.deviceType.n_to_p_eff_curr_drv_ratio * self.g_tp.min_w_nmos_
        )
        technology = self.g_ip.F_sz_um
        self.Vdd = self.deviceType.Vdd

        # crossbar parameters
        # Double => multiply by (technology*1e-6/2)
        self.NTtr = 10 * technology * 1e-6 / 2.0
        self.PTtr = 20 * technology * 1e-6 / 2.0
        self.wt = 15 * technology * 1e-6 / 2.0
        self.ht = 15 * technology * 1e-6 / 2.0

        self.NTi = 12.5 * technology * 1e-6 / 2.0
        self.PTi = 25.0 * technology * 1e-6 / 2.0

        self.NTid = 60.0 * technology * 1e-6 / 2.0
        self.PTid = 120.0 * technology * 1e-6 / 2.0
        self.NTod = 60.0 * technology * 1e-6 / 2.0
        self.PTod = 120.0 * technology * 1e-6 / 2.0

        # create local Components for arbiter, crossbar, buffer
        self.arbiter = Component()
        self.crossbar = Component()
        self.buffer = Component()

        # define some placeholders
        self.cycle_time = 0.0
        self.max_cyc = 0.0

        # final step => calc_router_parameters
        self.calc_router_parameters()

    def __del__(self):
        """
        Equivalent to ~Router() in C++. Usually not needed in Python.
        """
        pass

    # -------------- The private methods from router.cc --------------

    def Cw3(self, length: float) -> float:
        """
        wire cap with triple spacing. 
        "Wire wc(g_ip->wt, length, 1, 3, 3);" => we pass spacing scaling=3, width scaling=3
        Then call wc.wire_cap(length).
        """
        wc = Wire(
            self.g_ip,
            self.g_tp,
            wire_model=self.g_ip.wt,
            wire_length=length,
            nsense=1,
            width_scaling=3.0,
            spacing_scaling=3.0
        )
        return wc.wire_cap(length)

    def gate_cap(self, w: float) -> float:
        """
        gate cap for width w (in micro?), calls gate_C(...).
        In the C++ code: gate_C(w*1e6, 0)
        """
        # gate_C expects a transistor width in absolute dimension if your basic_circuit is consistent
        return float(gate_C(self.g_ip, self.g_tp, w * 1e6, 0.0))

    def diff_cap(self, w: float, type_: int, stack: float) -> float:
        """
        diffusion capacitance, calling drain_C_ with w in micro?
        from router.cc: drain_C_(w*1e6, type, (int) s, 1, g_tp.cell_h_def).
        """
        return float(
            drain_C_(
                self.g_ip,
                self.g_tp,
                w * 1e6,
                type_,
                int(stack),
                1,
                self.g_tp.cell_h_def
            )
        )

    # -------------- crossbar-related sub-models --------------

    def transmission_buf_inpcap(self) -> float:
        """
        from router.cc: 
        transmission_buf_inpcap = diff_cap(NTtr, 0, 1) + diff_cap(PTtr, 1, 1);
        """
        return self.diff_cap(self.NTtr, 0, 1) + self.diff_cap(self.PTtr, 1, 1)

    def transmission_buf_outcap(self) -> float:
        """
        same as inpcap
        """
        return (self.diff_cap(self.NTtr, 0, 1)
                + self.diff_cap(self.PTtr, 1, 1))

    def transmission_buf_ctrcap(self) -> float:
        """
        from router.cc: gate_cap(NTtr) + gate_cap(PTtr)
        """
        return self.gate_cap(self.NTtr) + self.gate_cap(self.PTtr)

    def crossbar_inpline(self) -> float:
        """
        crossbar_inpline = Cw3(O*flit_size*wt) + O*transmission_buf_inpcap() + 
                           gate_cap(NTid) + gate_cap(PTid) + diff_cap(NTid,0,1) + diff_cap(PTid,1,1)
        """
        return (
            self.Cw3(self.O * self.flit_size * self.wt)
            + self.O * self.transmission_buf_inpcap()
            + self.gate_cap(self.NTid)
            + self.gate_cap(self.PTid)
            + self.diff_cap(self.NTid, 0, 1)
            + self.diff_cap(self.PTid, 1, 1)
        )

    def crossbar_outline(self) -> float:
        """
        crossbar_outline = Cw3(I*flit_size*ht) + I*transmission_buf_outcap() + 
                           gate_cap(NTod) + gate_cap(PTod) + diff_cap(NTod,0,1)+ diff_cap(PTod,1,1)
        """
        return (
            self.Cw3(self.I * self.flit_size * self.ht)
            + self.I * self.transmission_buf_outcap()
            + self.gate_cap(self.NTod)
            + self.gate_cap(self.PTod)
            + self.diff_cap(self.NTod, 0, 1)
            + self.diff_cap(self.PTod, 1, 1)
        )

    def crossbar_ctrline(self) -> float:
        """
        crossbar_ctrline = Cw3(0.5*O*flit_size*wt) + flit_size*transmission_buf_ctrcap() +
                           diff_cap(NTi,0,1) + diff_cap(PTi,1,1) + gate_cap(NTi) + gate_cap(PTi)
        """
        return (
            self.Cw3(0.5 * self.O * self.flit_size * self.wt)
            + self.flit_size * self.transmission_buf_ctrcap()
            + self.diff_cap(self.NTi, 0, 1)
            + self.diff_cap(self.PTi, 1, 1)
            + self.gate_cap(self.NTi)
            + self.gate_cap(self.PTi)
        )

    def tr_crossbar_power(self) -> float:
        """
        from router.cc => 
        return (crossbar_inpline()*Vdd*Vdd*flit_size/2 + crossbar_outline()*Vdd*Vdd*flit_size/2) *2
        """
        return (
            (
                self.crossbar_inpline() * self.Vdd * self.Vdd * self.flit_size / 2.0
                + self.crossbar_outline() * self.Vdd * self.Vdd * self.flit_size / 2.0
            )
            * 2.0
        )

    # -------------- buffer model --------------
    def buffer_stats(self):
        """
        from router.cc: buffer_stats() => build a DynamicParameter, 
        make a Mat, get power & area => store in self.buffer.
        """
        dyn_p = DynamicParameter()
        dyn_p.is_tag      = False
        dyn_p.pure_cam    = False
        dyn_p.fully_assoc = False
        dyn_p.pure_ram    = True
        dyn_p.is_dram     = False
        dyn_p.is_main_mem = False
        dyn_p.num_subarrays = 1
        dyn_p.num_mats   = 1
        dyn_p.Ndbl       = 1
        dyn_p.Ndwl       = 1
        dyn_p.Nspd       = 1
        dyn_p.deg_bl_muxing = 1
        dyn_p.deg_senseamp_muxing_non_associativity = 1
        dyn_p.Ndsam_lev_1 = 1
        dyn_p.Ndsam_lev_2 = 1
        dyn_p.Ndcm        = 1
        dyn_p.number_addr_bits_mat           = 8
        dyn_p.number_way_select_signals_mat  = 1
        dyn_p.number_subbanks_decode         = 0
        dyn_p.num_act_mats_hor_dir           = 1
        # This is a hack for sense-voltage
        dyn_p.V_b_sense = self.Vdd

        dyn_p.ram_cell_tech_type = 0  # itrs_hp, presumably

        dyn_p.num_r_subarray = int(self.vc_buffer_size)
        dyn_p.num_c_subarray = int(self.flit_size) * int(self.vc_count)

        dyn_p.num_mats_h_dir = 1
        dyn_p.num_mats_v_dir = 1

        dyn_p.num_do_b_subbank = int(self.flit_size)
        dyn_p.num_di_b_subbank = int(self.flit_size)
        dyn_p.num_do_b_mat     = int(self.flit_size)
        dyn_p.num_di_b_mat     = int(self.flit_size)
        dyn_p.num_do_b_bank_per_port = int(self.flit_size)
        dyn_p.num_di_b_bank_per_port = int(self.flit_size)
        dyn_p.out_w = int(self.flit_size)

        dyn_p.use_inp_params = 1
        dyn_p.num_wr_ports   = int(self.vc_count)
        dyn_p.num_rd_ports   = 1  # or vc_count => "based on Bill Dally's book" 
        dyn_p.num_rw_ports   = 0
        dyn_p.num_se_rd_ports= 0
        dyn_p.num_search_ports=0

        # cell geometry
        # from code: 
        #  cell.h = sram.b_h + 2 * wire_outside_mat.pitch*(num_wr_ports + num_rw_ports -1 +num_rd_ports)
        #  cell.w = ...
        dyn_p.cell.h = (self.g_tp.sram.b_h
                        + 2.0 * self.g_tp.wire_outside_mat.pitch
                          * (dyn_p.num_wr_ports + dyn_p.num_rw_ports - 1 + dyn_p.num_rd_ports))
        dyn_p.cell.w = (self.g_tp.sram.b_w
                        + 2.0 * self.g_tp.wire_outside_mat.pitch
                          * (dyn_p.num_rw_ports -1
                             + (dyn_p.num_rd_ports - dyn_p.num_se_rd_ports)
                             + dyn_p.num_wr_ports)
                        + self.g_tp.wire_outside_mat.pitch * dyn_p.num_se_rd_ports)

        buff = Mat(dyn_p)
        buff.compute_delays(0.0)
        buff.compute_power_energy()

        # store in self.buffer component
        self.buffer.power.readOp  = buff.power.readOp
        # code sets: buffer.power.writeOp = buffer.power.readOp => "FIXME"
        self.buffer.power.writeOp = self.buffer.power.readOp
        self.buffer.area = buff.area

    def cb_stats(self):
        """
        from router.cc => if(1) use Crossbar c_b, else do manual tr crossbar power
        """
        # "Crossbar c_b(I, O, flit_size)" => we pass g_ip, g_tp
        c_b = Crossbar(
            self.g_ip,
            self.g_tp,
            n_inp_=self.I,
            n_out_=self.O,
            flit_size_=self.flit_size
        )
        c_b.compute_power()
        self.crossbar.delay = c_b.delay
        self.crossbar.power.readOp.dynamic     = c_b.power.readOp.dynamic
        self.crossbar.power.readOp.leakage     = c_b.power.readOp.leakage
        self.crossbar.power.readOp.gate_leakage= c_b.power.readOp.gate_leakage
        self.crossbar.area = c_b.area

    # --------------  arbiter + final power --------------
    def get_router_power(self):
        """
        from router.cc => get_router_power():
        1) buffer_stats()
        2) cb_stats()
        3) arbiter => vcarb + cbarb => store in self.arbiter
        4) total => self.power
        """
        # 1) buffer
        self.buffer_stats()

        # 2) crossbar
        self.cb_stats()

        # 3) arbiter
        #   Arbiter vcarb(vc_count, flit_size, buffer.area.w)
        #   Arbiter cbarb(I, flit_size, crossbar.area.w)
        # We'll assume your Arbiter constructor is: Arbiter(g_ip, g_tp, vc_count, flit_size, some_dim)
        # But from the snippet: "Arbiter vcarb(vc_count, flit_size, buffer.area.w);" => let's do that
        vcarb = Arbiter(self.g_ip, self.g_tp, self.vc_count, self.flit_size, self.buffer.area.w)
        cbarb = Arbiter(self.g_ip, self.g_tp, self.I, self.flit_size, self.crossbar.area.w)

        vcarb.compute_power()
        cbarb.compute_power()

        self.arbiter.power.readOp.dynamic = (
            vcarb.power.readOp.dynamic * self.I
            + cbarb.power.readOp.dynamic * self.O
        )
        self.arbiter.power.readOp.leakage = (
            vcarb.power.readOp.leakage * self.I
            + cbarb.power.readOp.leakage * self.O
        )
        self.arbiter.power.readOp.gate_leakage = (
            vcarb.power.readOp.gate_leakage * self.I
            + cbarb.power.readOp.gate_leakage * self.O
        )

        # 4) final power
        # router power => ( (buffer.power.readOp.dynamic + buffer.power.writeOp.dynamic)
        #                   + crossbar.power + arbiter.power)* MIN(I,O)*M
        # plus some partial => "power = power + (buffer.power*pppm_t + crossbar.power + arbiter.power)*pppm_lkg;"
        # We'll approximate the same logic in python
        buff_rdyn = self.buffer.power.readOp.dynamic
        buff_wdyn = self.buffer.power.writeOp.dynamic
        cross_rdyn= self.crossbar.power.readOp.dynamic
        arb_rdyn  = self.arbiter.power.readOp.dynamic

        self.power.readOp.dynamic = ((buff_rdyn + buff_wdyn) + cross_rdyn + arb_rdyn) \
                                    * MIN(self.I, self.O) * self.M

        # The line "double pppm_t[4] = {1, I, I, 1}; power = power + (buffer.power*pppm_t + crossbar.power + arbiter.power)* pppm_lkg;"
        # is a partial Weighted sum. 
        # For simplicity, we add up leakage from buffer + crossbar + arbiter:
        leak_sum = (self.buffer.power.readOp.leakage
                    + self.crossbar.power.readOp.leakage
                    + self.arbiter.power.readOp.leakage)
        # gate leak likewise
        gate_leak_sum = (self.buffer.power.readOp.gate_leakage
                         + self.crossbar.power.readOp.gate_leakage
                         + self.arbiter.power.readOp.gate_leakage)
        self.power.readOp.leakage += leak_sum
        self.power.readOp.gate_leakage += gate_leak_sum

    def get_router_delay(self):
        """
        from router.cc => 
          FREQUENCY=5;
          cycle_time = (1/FREQUENCY)*1e3 => ps
          delay=4
          max_cyc=17*g_tp.FO4 => s => times 1e12 => ps
          if(cycle_time < max_cyc) => freq= (1/max_cyc)*1e3
        """
        self.FREQUENCY = 5.0  # in GHz
        self.cycle_time = (1.0 / self.FREQUENCY) * 1e3  # ps

        self.delay = 4.0
        self.max_cyc = 17.0 * self.g_tp.FO4  # seconds
        self.max_cyc *= 1e12  # convert to ps
        if self.cycle_time < self.max_cyc:
            self.FREQUENCY = (1.0 / self.max_cyc) * 1e3  # => GHz

    def get_router_area(self):
        """
        from router.cc => 
        area.h = I*buffer.area.h
        area.w = buffer.area.w + crossbar.area.w
        """
        self.area.h = self.I * self.buffer.area.h
        self.area.w = self.buffer.area.w + self.crossbar.area.w

    def calc_router_parameters(self):
        """
        from router.cc => 
        get_router_delay()
        get_router_power()
        get_router_area()
        """
        self.get_router_delay()
        self.get_router_power()
        self.get_router_area()

    def print_router(self):
        """
        from router.cc => print_router()
        """
        print("\n\nRouter stats:")
        print(f"\tRouter Area - {self.area.get_area() * 1e-6} (mm^2)")
        print(f"\tMaximum possible network frequency - {(1/self.max_cyc)*1e3} GHz")
        print(f"\tNetwork frequency - {self.FREQUENCY} GHz")
        print(f"\tNo. of Virtual channels - {self.vc_count}")
        print(f"\tNo. of pipeline stages - {self.delay}")
        print(f"\tLink bandwidth - {self.flit_size} (bits)")
        print(f"\tNo. of buffer entries per virtual channel - {self.vc_buffer_size}")
        print(f"\tSimple buffer Area - {self.buffer.area.get_area() * 1e-6} (mm^2)")
        print(f"\tSimple buffer access (Read) - {self.buffer.power.readOp.dynamic * 1e9} (nJ)")
        print(f"\tSimple buffer leakage - {self.buffer.power.readOp.leakage * 1e3} (mW)")
        print(f"\tCrossbar Area - {self.crossbar.area.get_area() * 1e-6} (mm^2)")
        print(f"\tCross bar access energy - {self.crossbar.power.readOp.dynamic * 1e9} (nJ)")
        print(f"\tCross bar leakage power - {self.crossbar.power.readOp.leakage * 1e3} (mW)")
        print(f"\tArbiter access energy (VC arb + Crossbar arb) - {self.arbiter.power.readOp.dynamic * 1e9} (nJ)")
        print(f"\tArbiter leakage (VC arb + Crossbar arb) - {self.arbiter.power.readOp.leakage * 1e3} (mW)")
