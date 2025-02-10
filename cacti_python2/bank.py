# bank.py
"""
Python translation of bank.h and bank.cc from CACTI.

Requires:
    - A DynamicParameter class (dp) that holds necessary parameters.
    - The Mat class (from mat.py).
    - The Htree2 class (from htree2.py).
    - The Component base class (from component.py), which provides self.area, self.power, etc.
    - Access to some global input struct or direct fields (dp.use_inp_params, dp.num_rw_ports, etc.).
    - The c++ code references "g_ip->num_rw_ports" if dp.use_inp_params is false.
      In Python, you can pass g_ip as needed or embed that logic in dp.
"""

import math
from .component import Component
from .decoder import _log2    # or from basic_circuit if that’s where _log2 is defined
from .mat import Mat
from .htree2 import Htree2
from .cacti_interface import powerDef
# from .const import Add_htree, Data_in_htree, Data_out_htree   # or Htree_type enumerations
from .const import *
# If you have separate enumerations or references, adjust or import as needed.


class Bank(Component):
    """
    Python version of the C++ Bank class.
    Inherits from Component, so it has self.area and self.power objects.
    """
    def __init__(self, dp, g_ip, g_tp):
        """
        dp  : DynamicParameter instance (contains needed fields)
        g_ip: global input parameter object (used if dp.use_inp_params == False)
        g_tp: global technology parameter
        """
        super().__init__()
        self.dp = dp
        # Create a Mat object with dp, or pass (dp, g_ip, g_tp) if your Mat class requires it.
        self.mat = Mat(dp)

        # The bank has some references to the number of address bits
        self.num_addr_b_mat    = dp.number_addr_bits_mat
        self.num_mats_hor_dir  = dp.num_mats_h_dir
        self.num_mats_ver_dir  = dp.num_mats_v_dir

        self.array_leakage = 0.0
        self.wl_leakage    = 0.0
        self.cl_leakage    = 0.0

        # Decide whether to use dp fields or g_ip fields for the #ports
        if dp.use_inp_params:
            RWP  = dp.num_rw_ports
            ERP  = dp.num_rd_ports
            EWP  = dp.num_wr_ports
            SCHP = dp.num_search_ports
        else:
            # Use the global input struct
            RWP  = g_ip.num_rw_ports
            ERP  = g_ip.num_rd_ports
            EWP  = g_ip.num_wr_ports
            SCHP = g_ip.num_search_ports

        total_addrbits = (dp.number_addr_bits_mat + dp.number_subbanks_decode) * (RWP + ERP + EWP)
        datainbits     = dp.num_di_b_bank_per_port * (RWP + EWP)
        dataoutbits    = dp.num_do_b_bank_per_port * (RWP + ERP)

        # For CAM / fully-associative
        searchinbits   = 0
        searchoutbits  = 0
        if (dp.fully_assoc or dp.pure_cam):
            searchinbits  = dp.num_si_b_bank_per_port * SCHP
            searchoutbits = dp.num_so_b_bank_per_port * SCHP

        # Additional special-case for "fast_access" path:
        if not (dp.fully_assoc or dp.pure_cam):
            if g_ip.fast_access and (dp.is_tag == False):
                dataoutbits *= g_ip.data_assoc

        # Now instantiate the H-tree objects
        # (num_mats_ver_dir*2, num_mats_hor_dir*2) are the vertical/horizontal expansions
        if not (dp.fully_assoc or dp.pure_cam):
            # Create three standard H-trees
            self.htree_in_add = Htree2(
                g_ip, g_tp,
                dp.wtype,
                float(self.mat.area.w),
                float(self.mat.area.h),
                total_addrbits, datainbits, 0,
                dataoutbits, 0,
                self.num_mats_ver_dir*2,
                self.num_mats_hor_dir*2,
                Htree_type.Add_htree
            )

            self.htree_in_data = Htree2(
                g_ip, g_tp,
                dp.wtype,
                float(self.mat.area.w),
                float(self.mat.area.h),
                total_addrbits, datainbits, 0,
                dataoutbits, 0,
                self.num_mats_ver_dir*2,
                self.num_mats_hor_dir*2,
                Htree_type.Data_in_htree
            )

            self.htree_out_data = Htree2(
                g_ip, g_tp,
                dp.wtype,
                float(self.mat.area.w),
                float(self.mat.area.h),
                total_addrbits, datainbits, 0,
                dataoutbits, 0,
                self.num_mats_ver_dir*2,
                self.num_mats_hor_dir*2,
                Htree_type.Data_out_htree
            )

            # The bank area follows the largest of these H-tree areas (in practice, they match)
            self.area.w = self.htree_in_data.area.w
            self.area.h = self.htree_in_data.area.h

            # If fully-assoc or pure_cam is false, set these to None or skip creation
            self.htree_in_search  = None
            self.htree_out_search = None

        else:
            # The fully-associative / CAM case => create 5 H-trees
            self.htree_in_add = Htree2(
                g_ip, g_tp,
                dp.wtype,
                float(self.mat.area.w),
                float(self.mat.area.h),
                total_addrbits,
                datainbits,
                searchinbits,
                dataoutbits,
                searchoutbits,
                self.num_mats_ver_dir*2,
                self.num_mats_hor_dir*2,
                Htree_type.Add_htree
            )

            self.htree_in_data = Htree2(
                g_ip, g_tp,
                dp.wtype,
                float(self.mat.area.w),
                float(self.mat.area.h),
                total_addrbits,
                datainbits,
                searchinbits,
                dataoutbits,
                searchoutbits,
                self.num_mats_ver_dir*2,
                self.num_mats_hor_dir*2,
                Htree_type.Data_in_htree
            )

            self.htree_out_data = Htree2(
                g_ip, g_tp,
                dp.wtype,
                float(self.mat.area.w),
                float(self.mat.area.h),
                total_addrbits,
                datainbits,
                searchinbits,
                dataoutbits,
                searchoutbits,
                self.num_mats_ver_dir*2,
                self.num_mats_hor_dir*2,
                Htree_type.Data_out_htree
            )

            # Additional search htrees
            self.htree_in_search = Htree2(
                g_ip, g_tp,
                dp.wtype,
                float(self.mat.area.w),
                float(self.mat.area.h),
                total_addrbits,
                datainbits,
                searchinbits,
                dataoutbits,
                searchoutbits,
                self.num_mats_ver_dir*2,
                self.num_mats_hor_dir*2,
                Htree_type.Data_in_htree,
                True,   # uca_tree_=True
                True    # search_tree_=True
            )

            self.htree_out_search = Htree2(
                g_ip, g_tp,
                dp.wtype,
                float(self.mat.area.w),
                float(self.mat.area.h),
                total_addrbits,
                datainbits,
                searchinbits,
                dataoutbits,
                searchoutbits,
                self.num_mats_ver_dir*2,
                self.num_mats_hor_dir*2,
                Htree_type.Data_out_htree,
                True,   # uca_tree_=True
                False
            )

            self.area.w = self.htree_in_data.area.w
            self.area.h = self.htree_in_data.area.h

        # Address bits used in the mat’s row decoder, etc.
        self.num_addr_b_row_dec            = _log2(self.mat.subarray.num_rows)
        self.num_addr_b_routed_to_mat_for_act      = self.num_addr_b_row_dec
        self.num_addr_b_routed_to_mat_for_rd_or_wr = (self.num_addr_b_mat
                                                      - self.num_addr_b_row_dec)

    def __del__(self):
        """
        Python's garbage collector handles memory, but if you want to free references explicitly:
        """
        # If we want to mirror C++ ~Bank() destructor:
        # (No real need to do this in Python, but you can if desired)
        if self.dp.fully_assoc or self.dp.pure_cam:
            if self.htree_in_search is not None:
                del self.htree_in_search
            if self.htree_out_search is not None:
                del self.htree_out_search

        if hasattr(self, 'htree_in_add'):
            del self.htree_in_add
        if hasattr(self, 'htree_in_data'):
            del self.htree_in_data
        if hasattr(self, 'htree_out_data'):
            del self.htree_out_data
        # Then let GC do the rest

    def compute_delays(self, inrisetime: float) -> float:
        """
        Return the output rise time after the mat’s compute_delays.
        """
        return self.mat.compute_delays(inrisetime)

    def compute_power_energy(self):
        """
        Summation of the mat and h-tree power/energy.
        Also accumulates array_leakage, wl_leakage, cl_leakage from the mat.
        """
        # Compute mat-level power first
        self.mat.compute_power_energy()

        # If not a fully-assoc / pure-CAM
        if not (self.dp.fully_assoc or self.dp.pure_cam):
            # scale mat power by number of active mats horizontally
            self.power.readOp.dynamic  += self.mat.power.readOp.dynamic * self.dp.num_act_mats_hor_dir
            self.power.readOp.leakage  += self.mat.power.readOp.leakage * self.dp.num_mats
            self.power.readOp.gate_leakage += self.mat.power.readOp.gate_leakage * self.dp.num_mats

            # Add the additional dynamic power from h-tree signals
            self.power.readOp.dynamic  += self.htree_in_add.power.readOp.dynamic
            self.power.readOp.dynamic  += self.htree_out_data.power.readOp.dynamic
            # (In C++, htree_in_data power is sometimes not added here; your design may vary)

            # Summation of array/wl/cl leakage
            self.array_leakage += self.mat.array_leakage * self.dp.num_mats
            self.wl_leakage    += self.mat.wl_leakage    * self.dp.num_mats
            self.cl_leakage    += self.mat.cl_leakage    * self.dp.num_mats

            # If needed, you can also add the htree_in_add, htree_in_data, htree_out_data leakages
            # commented out in the original code, but here's how you might do it:
            # self.power.readOp.leakage      += self.htree_in_add.power.readOp.leakage
            # self.power.readOp.leakage      += self.htree_in_data.power.readOp.leakage
            # self.power.readOp.leakage      += self.htree_out_data.power.readOp.leakage
            # self.power.readOp.gate_leakage += self.htree_in_add.power.readOp.gate_leakage
            # self.power.readOp.gate_leakage += self.htree_in_data.power.readOp.gate_leakage
            # self.power.readOp.gate_leakage += self.htree_out_data.power.readOp.gate_leakage

        else:
            # The fully-associative / pure-cam path
            # mat power
            self.power.readOp.dynamic  += self.mat.power.readOp.dynamic
            self.power.readOp.leakage  += self.mat.power.readOp.leakage * self.dp.num_mats
            self.power.readOp.gate_leakage += self.mat.power.readOp.gate_leakage * self.dp.num_mats

            self.power.searchOp.dynamic += ( self.mat.power.searchOp.dynamic * self.dp.num_mats
                                             + self.mat.power_bl_precharge_eq_drv.searchOp.dynamic
                                             + self.mat.power_sa.searchOp.dynamic
                                             + self.mat.power_bitline.searchOp.dynamic
                                             + self.mat.power_subarray_out_drv.searchOp.dynamic
                                             + self.mat.ml_to_ram_wl_drv.power.readOp.dynamic )

            # H-tree read power
            self.power.readOp.dynamic  += self.htree_in_add.power.readOp.dynamic
            self.power.readOp.dynamic  += self.htree_out_data.power.readOp.dynamic

            # H-tree search power
            if self.htree_in_search is not None:
                self.power.searchOp.dynamic += self.htree_in_search.power.searchOp.dynamic
            if self.htree_out_search is not None:
                self.power.searchOp.dynamic += self.htree_out_search.power.searchOp.dynamic

            # H-tree read leakages
            self.power.readOp.leakage      += self.htree_in_add.power.readOp.leakage
            self.power.readOp.leakage      += self.htree_in_data.power.readOp.leakage
            self.power.readOp.leakage      += self.htree_out_data.power.readOp.leakage
            if self.htree_in_search:
                self.power.readOp.leakage  += self.htree_in_search.power.readOp.leakage
            if self.htree_out_search:
                self.power.readOp.leakage  += self.htree_out_search.power.readOp.leakage

            # gate leakage
            self.power.readOp.gate_leakage += self.htree_in_add.power.readOp.gate_leakage
            self.power.readOp.gate_leakage += self.htree_in_data.power.readOp.gate_leakage
            self.power.readOp.gate_leakage += self.htree_out_data.power.readOp.gate_leakage
            if self.htree_in_search:
                self.power.readOp.gate_leakage += self.htree_in_search.power.readOp.gate_leakage
            if self.htree_out_search:
                self.power.readOp.gate_leakage += self.htree_out_search.power.readOp.gate_leakage
