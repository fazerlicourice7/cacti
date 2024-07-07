from .htree import Htree2
from .parameter import g_ip
from .parameter import _log2
from .parameter import *
from .area import Area
from .mat import Mat
import enum
from .component import Component

class HtreeType(enum.Enum):
    Add_htree = 1
    Data_in_htree = 2
    Data_out_htree = 3
    Search_in_htree = 4
    Search_out_htree = 5

class Bank(Component):
    def __init__(self, dyn_p):
        super().__init__()
        self.dp = dyn_p
        self.mat = Mat(self.dp)
        self.num_addr_b_mat = dyn_p.number_addr_bits_mat
        self.num_mats_hor_dir = dyn_p.num_mats_h_dir
        self.num_mats_ver_dir = dyn_p.num_mats_v_dir
        self.array_leakage = 0
        self.wl_leakage = 0
        self.cl_leakage = 0

        if self.dp.use_inp_params:
            RWP = self.dp.num_rw_ports
            ERP = self.dp.num_rd_ports
            EWP = self.dp.num_wr_ports
            SCHP = self.dp.num_search_ports
        else:
            RWP = g_ip.num_rw_ports
            ERP = g_ip.num_rd_ports
            EWP = g_ip.num_wr_ports
            SCHP = g_ip.num_search_ports

        total_addrbits = (self.dp.number_addr_bits_mat + self.dp.number_subbanks_decode) * (RWP + ERP + EWP)
        datainbits = self.dp.num_di_b_bank_per_port * (RWP + EWP)
        dataoutbits = self.dp.num_do_b_bank_per_port * (RWP + ERP)
        searchinbits = 0
        searchoutbits = 0

        if self.dp.fully_assoc or self.dp.pure_cam:
            datainbits = self.dp.num_di_b_bank_per_port * (RWP + EWP)
            dataoutbits = self.dp.num_do_b_bank_per_port * (RWP + ERP)
            searchinbits = self.dp.num_si_b_bank_per_port * SCHP
            searchoutbits = self.dp.num_so_b_bank_per_port * SCHP

        if not (self.dp.fully_assoc or self.dp.pure_cam):
            if g_ip.fast_access and not self.dp.is_tag:
                dataoutbits *= g_ip.data_assoc

            self.htree_in_add = Htree2(self.dp.wtype, self.mat.area.w, self.mat.area.h,
                                       total_addrbits, datainbits, 0, dataoutbits, 0,
                                       self.num_mats_ver_dir * 2, self.num_mats_hor_dir * 2, Add_htree)
            self.htree_in_data = Htree2(self.dp.wtype, self.mat.area.w, self.mat.area.h,
                                        total_addrbits, datainbits, 0, dataoutbits, 0,
                                        self.num_mats_ver_dir * 2, self.num_mats_hor_dir * 2, Data_in_htree)
            self.htree_out_data = Htree2(self.dp.wtype, self.mat.area.w, self.mat.area.h,
                                         total_addrbits, datainbits, 0, dataoutbits, 0,
                                         self.num_mats_ver_dir * 2, self.num_mats_hor_dir * 2, Data_out_htree)

            self.area = Area()
            self.area.w, self.area.h = self.htree_in_data.area.w, self.htree_in_data.area.h
        else:
            self.htree_in_add = Htree2(self.dp.wtype, self.mat.area.w, self.mat.area.h,
                                       total_addrbits, datainbits, searchinbits, dataoutbits, searchoutbits,
                                       self.num_mats_ver_dir * 2, self.num_mats_hor_dir * 2, Add_htree)
            self.htree_in_data = Htree2(self.dp.wtype, self.mat.area.w, self.mat.area.h,
                                        total_addrbits, datainbits, searchinbits, dataoutbits, searchoutbits,
                                        self.num_mats_ver_dir * 2, self.num_mats_hor_dir * 2, Data_in_htree)
            self.htree_out_data = Htree2(self.dp.wtype, self.mat.area.w, self.mat.area.h,
                                         total_addrbits, datainbits, searchinbits, dataoutbits, searchoutbits,
                                         self.num_mats_ver_dir * 2, self.num_mats_hor_dir * 2, Data_out_htree)
            self.htree_in_search = Htree2(self.dp.wtype, self.mat.area.w, self.mat.area.h,
                                          total_addrbits, datainbits, searchinbits, dataoutbits, searchoutbits,
                                          self.num_mats_ver_dir * 2, self.num_mats_hor_dir * 2, Data_in_htree, True, True)
            self.htree_out_search = Htree2(self.dp.wtype, self.mat.area.w, self.mat.area.h,
                                           total_addrbits, datainbits, searchinbits, dataoutbits, searchoutbits,
                                           self.num_mats_ver_dir * 2, self.num_mats_hor_dir * 2, Data_out_htree, True)

            self.area = Area()
            self.area.w, self.area.h = self.htree_in_data.area.w, self.htree_in_data.area.h

        self.num_addr_b_row_dec = sp.log(self.mat.subarray.num_rows, 2)
        self.num_addr_b_routed_to_mat_for_act = self.num_addr_b_row_dec
        self.num_addr_b_routed_to_mat_for_rd_or_wr = self.num_addr_b_mat - self.num_addr_b_row_dec

    # def __del__(self):
    #     del self.htree_in_add
    #     del self.htree_out_data
    #     del self.htree_in_data
    #     if self.dp.fully_assoc or self.dp.pure_cam:
    #         del self.htree_in_search
    #         del self.htree_out_search

    def compute_delays(self, inrisetime):
        return self.mat.compute_delays(inrisetime)

    def compute_power_energy(self):
        self.mat.compute_power_energy()

        if not (self.dp.fully_assoc or self.dp.pure_cam):
            self.power.readOp.dynamic += self.mat.power.readOp.dynamic * self.dp.num_act_mats_hor_dir
            self.power.readOp.leakage += self.mat.power.readOp.leakage * self.dp.num_mats
            self.power.readOp.gate_leakage += self.mat.power.readOp.gate_leakage * self.dp.num_mats

            self.power.readOp.dynamic += self.htree_in_add.power.readOp.dynamic
            self.power.readOp.dynamic += self.htree_out_data.power.readOp.dynamic

            self.array_leakage += self.mat.array_leakage * self.dp.num_mats
            self.wl_leakage += self.mat.wl_leakage * self.dp.num_mats
            self.cl_leakage += self.mat.cl_leakage * self.dp.num_mats
        else:
            self.power.readOp.dynamic += self.mat.power.readOp.dynamic
            self.power.readOp.leakage += self.mat.power.readOp.leakage * self.dp.num_mats
            self.power.readOp.gate_leakage += self.mat.power.readOp.gate_leakage * self.dp.num_mats

            self.power.searchOp.dynamic += self.mat.power.searchOp.dynamic * self.dp.num_mats
            self.power.searchOp.dynamic += (
                self.mat.power_bl_precharge_eq_drv.searchOp.dynamic +
                self.mat.power_sa.searchOp.dynamic +
                self.mat.power_bitline.searchOp.dynamic +
                self.mat.power_subarray_out_drv.searchOp.dynamic +
                self.mat.ml_to_ram_wl_drv.power.readOp.dynamic
            )

            self.power.readOp.dynamic += self.htree_in_add.power.readOp.dynamic
            self.power.readOp.dynamic += self.htree_out_data.power.readOp.dynamic

            self.power.searchOp.dynamic += self.htree_in_search.power.searchOp.dynamic
            self.power.searchOp.dynamic += self.htree_out_search.power.searchOp.dynamic

            self.power.readOp.leakage += self.htree_in_add.power.readOp.leakage
            self.power.readOp.leakage += self.htree_in_data.power.readOp.leakage
            self.power.readOp.leakage += self.htree_out_data.power.readOp.leakage
            self.power.readOp.leakage += self.htree_in_search.power.readOp.leakage
            self.power.readOp.leakage += self.htree_out_search.power.readOp.leakage

            self.power.readOp.gate_leakage += self.htree_in_add.power.readOp.gate_leakage
            self.power.readOp.gate_leakage += self.htree_in_data.power.readOp.gate_leakage
            self.power.readOp.gate_leakage += self.htree_out_data.power.readOp.gate_leakage
            self.power.readOp.gate_leakage += self.htree_in_search.power.readOp.gate_leakage
            self.power.readOp.gate_leakage += self.htree_out_search.power.readOp.gate_leakage