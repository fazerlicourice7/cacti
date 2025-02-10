# htree2.py
"""
Python translation of htree2.h and htree2.cc from CACTI.

Requires:
    - Wire_type, Wire
    - powerDef, RISE, FALL
    - cmos_Isub_leakage, cmos_Ig_leakage, drain_C_, gate_C, tr_R_on, horowitz
    - self.g_tp (global tech parameter)
    - DeviceType
    - Some definition of Htree_type enumerations:
        Add_htree       = 0
        Data_in_htree   = 1
        Data_out_htree  = 2
        Search_in_htree = 3
        Search_out_htree= 4
    - Some math utilities (log, pow, etc.)
    - A 'Component' base class that has fields like self.power, self.area, etc.
"""

import math
from math import log2, pow
from .const import *

from .basic_circuit import (
    is_pow2, _log2, is_equal,
    wire_resistance, wire_capacitance, tsv_resistance, tsv_capacitance, tsv_area,
    pmos_to_nmos_sz_ratio, gate_C, gate_C_pass, tr_R_on, drain_C_, cmos_Ig_leakage,
    horowitz, cmos_Isub_leakage, simplified_nmos_Isat
)
from .wire import Wire
from .cacti_interface import powerDef
from .component import Component

import sympy as sp

def is_symbolic(x):
    """Return True if x is a sympy symbolic expression."""
    return isinstance(x, sp.Basic)


# Example enumerations - define or import as needed
# (You can change them if you already have them in a separate file)
# class Htree_type:
#     Add_htree       = 0
#     Data_in_htree   = 1
#     Data_out_htree  = 2
#     Search_in_htree = 3
#     Search_out_htree= 4

# For convenience, ensure you have these enumerations or constants
# e.g. "NCH=1, PCH=0, nand=2, nor=1, inv=0"
# or import them from const.py

# from basic_circuit import ...
# from component import Component
# from wire import Wire
# from const import RISE, FALL
# from cacti_interface import powerDef
# from parameter import g_tp  # or however you keep the global tech parameters

# If you have your own definitions, just align references accordingly.

class Htree2:  # or class Htree2(Component) if your code expects that
    """
    Python version of the C++ Htree2 class.
    """
    def __init__(self,
                 g_ip,
                 g_tp,
                 wire_model,            # enum Wire_type
                 mat_w: float,
                 mat_h: float,
                 a_bits: int,
                 d_inbits: int,
                 search_data_in_bits: int,
                 d_outbits: int,
                 search_data_out_bits: int,
                 bl: int,
                 wl: int,
                 htree_type,           # enum Htree_type
                 uca_tree_: bool = False,
                 search_tree_: bool = False,
                 dt=None):
        """
        Constructor matches the usage in htree2.cc:

        wire_model:  e.g. Wire_type.Global_
        mat_w:       horizontal dimension of the mat
        mat_h:       vertical dimension of the mat
        a_bits:      number of address bits
        d_inbits:    number of data_in bits
        search_data_in_bits:  bits for "search" data in
        d_outbits:   number of data_out bits
        search_data_out_bits: bits for "search" data out
        bl:          ndbl
        wl:          ndwl
        htree_type:  e.g. Add_htree, Data_in_htree, ...
        uca_tree_:   boolean
        search_tree_: boolean
        dt:          DeviceType (defaults to g_tp.peri_global if None)
        """
        super().__init__()  # If inheriting from a custom Component class
        self.g_tp = g_tp

        # If no dt given, default to g_tp.peri_global
        # from const import RISE
        # from const import NCH, PCH, nand, nor, inv
        # from parameter import g_tp
        # from cacti_interface import powerDef
        # from component import Component
        if dt is None:
            dt = self.g_tp.peri_global

        # Required to store a few references if your base class uses them:
        self.power = powerDef()   # total dynamic/leak/gate
        self.delay = 0.0
        self.area = Component()   # or just store self.area as some object with .h, .w
        self.area.w = 0.0
        self.area.h = 0.0

        self.in_rise_time = 0.0
        self.out_rise_time= 0.0
        self.max_unpipelined_link_delay = 0.0
        self.power_bit = powerDef()

        self.tree_type = htree_type
        self.mat_width = mat_w
        self.mat_height= mat_h
        self.add_bits  = a_bits
        self.data_in_bits = d_inbits
        self.search_data_in_bits  = search_data_in_bits
        self.data_out_bits= d_outbits
        self.search_data_out_bits = search_data_out_bits
        self.ndbl      = bl
        self.ndwl      = wl
        self.uca_tree  = uca_tree_
        self.search_tree = search_tree_
        self.wt        = wire_model
        self.deviceType= dt

        self.min_w_nmos = self.g_tp.min_w_nmos_
        self.min_w_pmos = dt.n_to_p_eff_curr_drv_ratio * self.min_w_nmos

        # For bus width at the root. We'll adapt as we go
        self.wire_bw     = 0.0
        self.init_wire_bw= 0.0

        # For the usage, we require (ndbl >= 2) and (ndwl >= 2).
        assert self.ndbl >= 2 and self.ndwl >= 2

        if   self.tree_type == Htree_type.Add_htree:
            self.wire_bw      = self.init_wire_bw = self.add_bits
            self.in_htree()
        elif self.tree_type == Htree_type.Data_in_htree:
            self.wire_bw      = self.init_wire_bw = self.data_in_bits
            self.in_htree()
        elif self.tree_type == Htree_type.Data_out_htree:
            self.wire_bw      = self.init_wire_bw = self.data_out_bits
            self.out_htree()
        elif self.tree_type == Htree_type.Search_in_htree:
            self.wire_bw      = self.init_wire_bw = self.search_data_in_bits
            self.in_htree()
        elif self.tree_type == Htree_type.Search_out_htree:
            self.wire_bw      = self.init_wire_bw = self.search_data_out_bits
            self.out_htree()
        else:
            raise ValueError("Invalid Htree_type passed to Htree2 constructor.")

        # The power_bit is the per-bit cost, so the final total is scaled by init_wire_bw
        self.power_bit = self.power
        self.power.readOp.dynamic *= self.init_wire_bw

        # Basic sanity checks
        if not is_symbolic(self.power.readOp.dynamic):
            assert self.power.readOp.dynamic >= 0
        if not is_symbolic(self.power.readOp.leakage):
            assert self.power.readOp.leakage >= 0
        if not is_symbolic(self.power.readOp.gate_leakage):
            assert self.power.readOp.gate_leakage >= 0

    def set_in_rise_time(self, rt: float):
        """
        Store the input rising time for the h-tree.
        """
        self.in_rise_time = rt

    def input_nand(self, s1: float, s2: float, l_eff: float):
        """
        The "input_nand" helper from C++.
        A NAND gate is used at each node to limit the signal.

        s1, s2  => sizing factors
        l_eff   => length to next stage
        """
        # from basic_circuit import tr_R_on, drain_C_, gate_C, horowitz, cmos_Isub_leakage, cmos_Ig_leakage
        # from const import nand, RISE, NCH, PCH

        # We treat the wire as well:
        # from wire import Wire
        w1 = Wire(self.wt, l_eff)  # create a local wire to get out_rise_time

        pton_size = self.deviceType.n_to_p_eff_curr_drv_ratio
        # input capacitance of a repeater = input capacitance of nand
        nsize = s1*(1 + pton_size)/(2 + pton_size)
        if nsize < 1.0:
            nsize = 1.0

        # Equivalent to the c++ code
        # Resistive path for the nsize*NCH transistors
        # plus gate load of the next stage (which is s2*(min_w_nmos+min_w_pmos))
        # "2 * tr_R_on(...)" => NAND with 2 stacked nmos
        rn = tr_R_on(nsize*self.min_w_nmos, NCH, 1, is_dram_=False)
        c_intrinsic = (drain_C_(nsize*self.min_w_nmos, NCH, 1, 1, self.deviceType.cell_h_def) * 2
                       + 2*gate_C(s2*(self.min_w_nmos + self.min_w_pmos), 0))
        tc = 2*rn * c_intrinsic

        # Use Horowitz model
        self.delay += horowitz(w1.out_rise_time, tc,
                               self.deviceType.Vth/self.deviceType.Vdd,
                               self.deviceType.Vth/self.deviceType.Vdd,
                               RISE)

        # dynamic power: 0.5 * (cap) * V^2
        cap_nand = (2*drain_C_(pton_size*nsize*self.min_w_pmos, PCH, 1, 1, self.deviceType.cell_h_def)
                    + drain_C_(nsize*self.min_w_nmos, NCH, 1, 1, self.deviceType.cell_h_def)
                    + 2*gate_C(s2*(self.min_w_nmos + self.min_w_pmos), 0))
        d_power = 0.5 * cap_nand * (self.deviceType.Vdd**2)
        self.power.readOp.dynamic  += d_power
        self.power.searchOp.dynamic+= d_power * self.wire_bw

        # leakage
        sub_leak = cmos_Isub_leakage(self.min_w_nmos*(nsize*2),
                                     self.min_w_pmos*(nsize*2),
                                     fanin=2,
                                     gate_type=nand) * self.deviceType.Vdd
        ig_leak  = cmos_Ig_leakage(self.min_w_nmos*(nsize*2),
                                   self.min_w_pmos*(nsize*2),
                                   fanin=2,
                                   gate_type=nand) * self.deviceType.Vdd

        self.power.readOp.leakage      += (self.wire_bw * sub_leak)
        self.power.readOp.gate_leakage += (self.wire_bw * ig_leak)


    def output_buffer(self, s1: float, s2: float, l_eff: float):
        """
        The "output_buffer" helper from the C++ code.
        A tri-state buffer model consisting of not, nand, nor, driver transistors, etc.
        """
        # from basic_circuit import tr_R_on, drain_C_, gate_C, horowitz, cmos_Isub_leakage, cmos_Ig_leakage
        # from const import nand, nor, inv, RISE, NCH, PCH
        # from wire import Wire

        w1 = Wire(self.wt, l_eff)
        pton_size = self.deviceType.n_to_p_eff_curr_drv_ratio

        # input capacitance of repeater = input cap of nand + nor
        # The code sets "size = s1*(1 + pton_size)/(2 + pton_size + 1 + 2*pton_size)"
        size = s1*(1+pton_size)/(2+pton_size + 1 + 2*pton_size)
        if size < 1.0:
            size = 1.0

        # stage_eff is from original code (not used heavily, but we replicate)
        # Resistances:
        res_nor = 2*tr_R_on(size*self.min_w_pmos, PCH, 1, is_dram_=False)
        # transistor controlling output:
        # we define a "tr_size" for the pass transistor size
        s_eff = (gate_C(s2*(self.min_w_nmos + self.min_w_pmos), 0) +
                 w1.wire_cap(l_eff*1e-6, True)) / gate_C(s2*(self.min_w_nmos + self.min_w_pmos), 0)
        # This line from CACTI is somewhat approximate:
        tr_size = gate_C(s1*(self.min_w_nmos + self.min_w_pmos), 0) * 1/2 / (s_eff*gate_C(self.min_w_pmos, 0))

        res_ptrans = tr_R_on(tr_size*self.min_w_nmos, NCH, 1, is_dram_=False)
        cap_nand_out = (drain_C_(size*self.min_w_nmos, NCH, 1, 1, self.deviceType.cell_h_def)
                        + 2*drain_C_(size*self.min_w_pmos, PCH, 1, 1, self.deviceType.cell_h_def)
                        + gate_C(tr_size*self.min_w_pmos, 0))
        cap_ptrans_out = (2 * (drain_C_(tr_size*self.min_w_pmos, PCH, 1, 1, self.deviceType.cell_h_def)
                               + drain_C_(tr_size*self.min_w_nmos, NCH, 1, 1, self.deviceType.cell_h_def))
                          + gate_C(s1*(self.min_w_nmos + self.min_w_pmos), 0))

        tc = res_nor * cap_nand_out + (res_nor + res_ptrans)*cap_ptrans_out

        self.delay += horowitz(w1.out_rise_time,
                               tc,
                               self.deviceType.Vth/self.deviceType.Vdd,
                               self.deviceType.Vth/self.deviceType.Vdd,
                               RISE)

        Vdd_sq = (self.deviceType.Vdd**2)

        # NAND dynamic
        c_nand = (2*drain_C_(size*self.min_w_pmos, PCH, 1, 1, self.deviceType.cell_h_def)
                  + drain_C_(size*self.min_w_nmos, NCH, 1, 1, self.deviceType.cell_h_def)
                  + gate_C(tr_size*self.min_w_pmos, 0))
        E_nand = 0.5 * c_nand * Vdd_sq
        self.power.readOp.dynamic += E_nand
        self.power.searchOp.dynamic+= E_nand * self.init_wire_bw

        # Inverter dynamic
        c_inv = (drain_C_(size*self.min_w_pmos, PCH, 1, 1, self.deviceType.cell_h_def)
                 + drain_C_(size*self.min_w_nmos, NCH, 1, 1, self.deviceType.cell_h_def)
                 + gate_C(size*(self.min_w_nmos + self.min_w_pmos), 0))
        E_inv = 0.5 * c_inv * Vdd_sq
        self.power.readOp.dynamic += E_inv
        self.power.searchOp.dynamic+= E_inv * self.init_wire_bw

        # NOR dynamic
        c_nor = (drain_C_(size*self.min_w_pmos, PCH, 1, 1, self.deviceType.cell_h_def)
                 + 2*drain_C_(size*self.min_w_nmos, NCH, 1, 1, self.deviceType.cell_h_def)
                 + gate_C(tr_size*(self.min_w_nmos + self.min_w_pmos), 0))
        E_nor = 0.5 * c_nor * Vdd_sq
        self.power.readOp.dynamic += E_nor
        self.power.searchOp.dynamic+= E_nor * self.init_wire_bw

        # output transistor dynamic
        c_out_tr = (2*(drain_C_(tr_size*self.min_w_pmos, PCH, 1, 1, self.deviceType.cell_h_def)
                       + drain_C_(tr_size*self.min_w_nmos, NCH, 1, 1, self.deviceType.cell_h_def))
                    + gate_C(s1*(self.min_w_nmos + self.min_w_pmos), 0))
        E_out = 0.5 * c_out_tr * Vdd_sq
        self.power.readOp.dynamic += E_out
        self.power.searchOp.dynamic+= E_out * self.init_wire_bw

        # LEAKAGE
        # We replicate the code:
        #   if(uca_tree) { same formula } else { same formula }
        # Actually both branches are the same, so we unify:
        # from const import inv
        # inverter + output tr => fanin=1
        sub_inv = cmos_Isub_leakage(self.min_w_nmos*tr_size*2,
                                    self.min_w_pmos*tr_size*2,
                                    1, inv) * self.deviceType.Vdd
        ig_inv  = cmos_Ig_leakage(self.min_w_nmos*tr_size*2,
                                  self.min_w_pmos*tr_size*2,
                                  1, inv) * self.deviceType.Vdd
        # nand => fanin=2
        sub_nand= cmos_Isub_leakage(self.min_w_nmos*size*3,
                                    self.min_w_pmos*size*3,
                                    2, nand) * self.deviceType.Vdd
        ig_nand = cmos_Ig_leakage(self.min_w_nmos*size*3,
                                  self.min_w_pmos*size*3,
                                  2, nand) * self.deviceType.Vdd
        # nor => also fanin=2 in CACTI code
        sub_nor = cmos_Isub_leakage(self.min_w_nmos*size*3,
                                    self.min_w_pmos*size*3,
                                    2, nor) * self.deviceType.Vdd
        ig_nor  = cmos_Ig_leakage(self.min_w_nmos*size*3,
                                  self.min_w_pmos*size*3,
                                  2, nor) * self.deviceType.Vdd

        # Multiply by wire_bw
        self.power.readOp.leakage += (sub_inv + sub_nand + sub_nor)*self.wire_bw
        self.power.readOp.gate_leakage += (ig_inv + ig_nand + ig_nor)*self.wire_bw


    def in_htree(self):
        """
        The main routine from Htree2::in_htree() that calculates
        the input H-tree delay/power/area.
        """
        # from wire import Wire
        # from const import nand

        self.delay = 0.0
        self.power.readOp.dynamic = 0.0
        self.power.readOp.leakage = 0.0
        self.power.readOp.gate_leakage = 0.0
        self.power.searchOp.dynamic = 0.0

        # We create local copies for H and V expansions
        h = int(math.log2(self.ndwl/2))
        v = int(math.log2(self.ndbl/2))

        # Calculate half-height/width to estimate area
        # The original code does many if/else to handle 'uca_tree' and row/col differences
        # We'll replicate that logic:

        if self.uca_tree:
            # "since uca_tree models interbank tree, mat_height => bank height"
            ht_temp = (self.mat_height*self.ndbl/2 +
                       ((self.add_bits + self.data_in_bits + self.data_out_bits +
                         (self.search_data_in_bits + self.search_data_out_bits))
                        * self.deviceType.wire_outside_mat.pitch
                        * 2*(1-pow(0.5,h))))/2
            len_temp= (self.mat_width*self.ndwl/2 +
                       ((self.add_bits + self.data_in_bits + self.data_out_bits +
                         (self.search_data_in_bits + self.search_data_out_bits))
                        * self.deviceType.wire_outside_mat.pitch
                        * 2*(1-pow(0.5,v))))/2
        else:
            # More complicated if ndwl == ndbl, or ndwl>ndbl, or ndwl<ndbl
            if self.ndwl == self.ndbl:
                ht_temp = ((self.mat_height*self.ndbl/2) +
                           ((self.add_bits + (self.search_data_in_bits+self.search_data_out_bits))
                            * (self.ndbl/2-1)*self.deviceType.wire_outside_mat.pitch) +
                           ((self.data_in_bits + self.data_out_bits)
                            * self.deviceType.wire_outside_mat.pitch * h))/2
                len_temp= ( (self.mat_width*self.ndwl/2) +
                            ((self.add_bits + (self.search_data_in_bits+self.search_data_out_bits))
                             *(self.ndwl/2-1)*self.deviceType.wire_outside_mat.pitch) +
                            ((self.data_in_bits + self.data_out_bits)
                             * self.deviceType.wire_outside_mat.pitch * v))/2
            elif self.ndwl > self.ndbl:
                excess_part = (math.log2(self.ndwl/2) - math.log2(self.ndbl/2))
                ht_temp = ((self.mat_height*self.ndbl/2) +
                           ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits))
                            * ((self.ndbl/2-1) + excess_part) * self.deviceType.wire_outside_mat.pitch ) +
                           (self.data_in_bits + self.data_out_bits)*self.deviceType.wire_outside_mat.pitch*
                           (2*(1-pow(0.5, (h-v))) + pow(0.5,(v-h))*v))/2
                len_temp= ((self.mat_width*self.ndwl/2) +
                           ((self.add_bits + (self.search_data_in_bits+self.search_data_out_bits))
                            *(self.ndwl/2-1)*self.deviceType.wire_outside_mat.pitch) +
                           ((self.data_in_bits + self.data_out_bits)
                            * self.deviceType.wire_outside_mat.pitch * v))/2
            else:
                # ndwl < ndbl
                excess_part = (math.log2(self.ndbl/2) - math.log2(self.ndwl/2))
                ht_temp = ((self.mat_height*self.ndbl/2) +
                           ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits))
                            * ((self.ndwl/2-1) + excess_part)*self.deviceType.wire_outside_mat.pitch)
                           + (self.data_in_bits + self.data_out_bits)*self.deviceType.wire_outside_mat.pitch * h)/2
                len_temp= ((self.mat_width*self.ndwl/2) +
                           ((self.add_bits + (self.search_data_in_bits+self.search_data_out_bits))
                            * ((self.ndwl/2-1)+excess_part) * self.deviceType.wire_outside_mat.pitch)
                           + (self.data_in_bits + self.data_out_bits)*self.deviceType.wire_outside_mat.pitch*
                           (h + 2*(1-pow(0.5, v-h)) ))/2

        self.area.h = ht_temp*2
        self.area.w = len_temp*2

        # local iteration variables
        len_ = len_temp
        ht_  = ht_temp/2

        while (v>0 or h>0):
            # build wires for each link
            wtemp1 = None
            wtemp2 = None
            wtemp3 = None
            option = 0

            if h>v:
                # only one horizontal link
                wtemp1 = Wire(self.wt, length=len_)
                wtemp2 = Wire(self.wt, length=len_/2)
                len_temp2 = len_
                len_ /= 2
                option = 0
                h -= 1
            elif (v>0 and h>0):
                # one horizontal, one vertical
                wtemp1 = Wire(self.wt, length=len_)
                wtemp2 = Wire(self.wt, length=ht_)
                wtemp3 = Wire(self.wt, length=len_/2)
                len_temp2 = len_
                ht_temp2  = ht_
                len_ /= 2
                ht_  /= 2
                v -= 1
                h -= 1
                option = 1
            else:
                # only vertical link
                # h==0
                wtemp1 = Wire(self.wt, length=ht_)
                wtemp2 = Wire(self.wt, length=ht_/2)
                ht_temp2 = ht_
                ht_ /= 2
                v -= 1
                option = 2

            self.delay += wtemp1.delay
            self.power.readOp.dynamic   += wtemp1.power.readOp.dynamic
            self.power.searchOp.dynamic += wtemp1.power.readOp.dynamic*self.wire_bw
            self.power.readOp.leakage   += wtemp1.power.readOp.leakage*self.wire_bw
            self.power.readOp.gate_leakage += wtemp1.power.readOp.gate_leakage*self.wire_bw

            # If not a uca_tree and we have a vertical link => wire_bw doubles
            # or if search_tree is True => also doubles
            if ((not self.uca_tree) and (option==2)) or self.search_tree:
                self.wire_bw *= 2

            if not self.uca_tree:
                # sized in "repeater_size" increments
                # s1, s2, ...
                if len_temp2 > wtemp1.repeater_spacing:
                    s1 = wtemp1.repeater_size
                    l_eff = wtemp1.repeater_spacing
                else:
                    s1 = (len_temp2 / wtemp1.repeater_spacing)*wtemp1.repeater_size
                    l_eff = len_temp2

                if wtemp2 is not None and (ht_temp2 > wtemp2.repeater_spacing):
                    s2 = wtemp2.repeater_size
                elif wtemp2 is not None:
                    s2 = (len_temp2 / wtemp2.repeater_spacing)*wtemp2.repeater_size
                else:
                    s2 = 0.0

                # first stage is a NAND
                self.input_nand(s1, s2, l_eff)

            if option!=1:
                # no second level
                continue

            # second level
            self.delay += wtemp2.delay
            self.power.readOp.dynamic   += wtemp2.power.readOp.dynamic
            self.power.searchOp.dynamic += wtemp2.power.readOp.dynamic*self.wire_bw
            self.power.readOp.leakage   += wtemp2.power.readOp.leakage*self.wire_bw
            self.power.readOp.gate_leakage += wtemp2.power.readOp.gate_leakage*self.wire_bw

            if self.uca_tree:
                self.power.readOp.leakage      += wtemp2.power.readOp.leakage*self.wire_bw
                self.power.readOp.gate_leakage += wtemp2.power.readOp.gate_leakage*self.wire_bw
            else:
                self.power.readOp.leakage      += wtemp2.power.readOp.leakage*self.wire_bw
                self.power.readOp.gate_leakage += wtemp2.power.readOp.gate_leakage*self.wire_bw
                self.wire_bw*=2

                if wtemp3 is not None:
                    if ht_temp2 > wtemp3.repeater_spacing:
                        s3 = wtemp3.repeater_size
                        l_eff = wtemp3.repeater_spacing
                    else:
                        s3 = (len_temp2/wtemp3.repeater_spacing)*wtemp3.repeater_size
                        l_eff = ht_temp2
                    self.input_nand(s2, s3, l_eff)

        # end while

    def out_htree(self):
        """
        The main routine for data out h-tree, using tri-state buffers.
        Very similar logic but calls output_buffer() for each wire node.
        """
        # from wire import Wire
        self.delay = 0.0
        self.power.readOp.dynamic = 0.0
        self.power.readOp.leakage = 0.0
        self.power.readOp.gate_leakage = 0.0
        self.power.searchOp.dynamic = 0.0

        # local expansions
        h = int(math.log2(self.ndwl/2))
        v = int(math.log2(self.ndbl/2))

        if self.uca_tree:
            ht_temp = (self.mat_height*self.ndbl/2 +
                       ((self.add_bits + self.data_in_bits + self.data_out_bits +
                         (self.search_data_in_bits + self.search_data_out_bits))
                        * self.deviceType.wire_outside_mat.pitch
                        * 2*(1-pow(0.5, h))))/2
            len_temp= (self.mat_width*self.ndwl/2 +
                       ((self.add_bits + self.data_in_bits + self.data_out_bits +
                         (self.search_data_in_bits + self.search_data_out_bits))
                        * self.deviceType.wire_outside_mat.pitch
                        * 2*(1-pow(0.5, v))))/2
        else:
            if self.ndwl == self.ndbl:
                ht_temp= ((self.mat_height*self.ndbl/2) +
                          ((self.add_bits+(self.search_data_in_bits+self.search_data_out_bits))
                           *(self.ndbl/2-1)*self.deviceType.wire_outside_mat.pitch)
                          + ((self.data_in_bits+self.data_out_bits)
                             *self.deviceType.wire_outside_mat.pitch*h))/2
                len_temp=((self.mat_width*self.ndwl/2) +
                          ((self.add_bits+(self.search_data_in_bits+self.search_data_out_bits))
                           *(self.ndwl/2-1)*self.deviceType.wire_outside_mat.pitch)
                          +((self.data_in_bits+self.data_out_bits)*self.deviceType.wire_outside_mat.pitch*v))/2
            elif self.ndwl>self.ndbl:
                excess_part = (math.log2(self.ndwl/2) - math.log2(self.ndbl/2))
                ht_temp= ((self.mat_height*self.ndbl/2) +
                          ((self.add_bits+(self.search_data_in_bits+self.search_data_out_bits))
                           *((self.ndbl/2-1)+excess_part)*self.deviceType.wire_outside_mat.pitch)
                          + (self.data_in_bits+self.data_out_bits)*self.deviceType.wire_outside_mat.pitch*
                          (2*(1-pow(0.5,(h-v))) + pow(0.5,(v-h))*v))/2
                len_temp=((self.mat_width*self.ndwl/2)+
                          ((self.add_bits+(self.search_data_in_bits+self.search_data_out_bits))
                           *(self.ndwl/2-1)*self.deviceType.wire_outside_mat.pitch)
                          + (self.data_in_bits+self.data_out_bits)*self.deviceType.wire_outside_mat.pitch*v)/2
            else:
                # ndwl < ndbl
                excess_part = (math.log2(self.ndbl/2) - math.log2(self.ndwl/2))
                ht_temp= ((self.mat_height*self.ndbl/2) +
                          ((self.add_bits+(self.search_data_in_bits+self.search_data_out_bits))
                           *((self.ndwl/2-1)+excess_part)*self.deviceType.wire_outside_mat.pitch)
                          + (self.data_in_bits+self.data_out_bits)*self.deviceType.wire_outside_mat.pitch*h)/2
                len_temp=((self.mat_width*self.ndwl/2) +
                          ((self.add_bits+(self.search_data_in_bits+self.search_data_out_bits))
                           *((self.ndwl/2-1)+excess_part)*self.deviceType.wire_outside_mat.pitch)
                          + (self.data_in_bits+self.data_outbits)*self.deviceType.wire_outside_mat.pitch*
                          (h + 2*(1-pow(0.5,(v-h)))))/2

        self.area.h = ht_temp*2
        self.area.w = len_temp*2

        # local iteration
        len_ = len_temp
        ht_  = ht_temp/2
        while (v>0 or h>0):
            wtemp1 = None
            wtemp2 = None
            wtemp3 = None
            option = 0

            if h>v:
                wtemp1 = Wire(self.wt, len_)
                wtemp2 = Wire(self.wt, len_/2)
                len_temp2 = len_
                len_ /= 2
                h -= 1
                option = 0
            elif (v>0 and h>0):
                wtemp1 = Wire(self.wt, len_)
                wtemp2 = Wire(self.wt, ht_)
                wtemp3 = Wire(self.wt, len_/2)
                len_temp2 = len_
                ht_temp2  = ht_
                len_ /= 2
                ht_  /= 2
                v -= 1
                h -= 1
                option = 1
            else:
                # only vertical
                wtemp1 = Wire(self.wt, ht_)
                wtemp2 = Wire(self.wt, ht_/2)
                ht_temp2 = ht_
                ht_ /= 2
                v -= 1
                option = 2

            self.delay += wtemp1.delay
            self.power.readOp.dynamic   += wtemp1.power.readOp.dynamic
            self.power.searchOp.dynamic += wtemp1.power.readOp.dynamic*self.init_wire_bw
            self.power.readOp.leakage   += wtemp1.power.readOp.leakage*self.wire_bw
            self.power.readOp.gate_leakage += wtemp1.power.readOp.gate_leakage*self.wire_bw

            # Possibly double wire_bw if vertical or search
            if ((not self.uca_tree) and (option==2)) or self.search_tree:
                self.wire_bw *= 2

            # tri-state buffer at each node for out H-tree
            if not self.uca_tree:
                if len_temp2> wtemp1.repeater_spacing:
                    s1 = wtemp1.repeater_size
                    l_eff = wtemp1.repeater_spacing
                else:
                    s1 = (len_temp2/wtemp1.repeater_spacing)*wtemp1.repeater_size
                    l_eff = len_temp2
                if ht_temp2> wtemp2.repeater_spacing:
                    s2 = wtemp2.repeater_size
                else:
                    s2 = (len_temp2/wtemp2.repeater_spacing)*wtemp2.repeater_size
                self.output_buffer(s1, s2, l_eff)

            if option!=1:
                continue

            # second level
            self.delay += wtemp2.delay
            self.power.readOp.dynamic   += wtemp2.power.readOp.dynamic
            self.power.searchOp.dynamic += wtemp2.power.readOp.dynamic*self.init_wire_bw
            self.power.readOp.leakage   += wtemp2.power.readOp.leakage*self.wire_bw
            self.power.readOp.gate_leakage += wtemp2.power.readOp.gate_leakage*self.wire_bw

            if self.uca_tree:
                self.power.readOp.leakage      += wtemp2.power.readOp.leakage*self.wire_bw
                self.power.readOp.gate_leakage += wtemp2.power.readOp.gate_leakage*self.wire_bw
            else:
                self.power.readOp.leakage      += wtemp2.power.readOp.leakage*self.wire_bw
                self.power.readOp.gate_leakage += wtemp2.power.readOp.gate_leakage*self.wire_bw
                self.wire_bw*=2

                if wtemp3 is not None:
                    if ht_temp2> wtemp3.repeater_spacing:
                        s3 = wtemp3.repeater_size
                        l_eff = wtemp3.repeater_spacing
                    else:
                        s3 = (len_temp2/wtemp3.repeater_spacing)*wtemp3.repeater_size
                        l_eff = ht_temp2
                    self.output_buffer(s2, s3, l_eff)
        # end while
