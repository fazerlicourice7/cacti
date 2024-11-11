import enum

import sympy as sp

from .area import Area
from .component import Component
from .htree import Htree2
from .mat import Mat
from . import parameter

class HtreeType(enum.Enum):
    Add_htree = 1
    Data_in_htree = 2
    Data_out_htree = 3
    Search_in_htree = 4
    Search_out_htree = 5

class Bank(Component):
    def __init__(self, dyn_p, g_ip, g_tp):
        super().__init__()
        self.dp = dyn_p
        self.g_ip = g_ip
        self.g_tp = g_tp
        self.mat = Mat(self.dp, self.g_ip, self.g_tp)
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
            RWP = self.g_ip.num_rw_ports
            ERP = self.g_ip.num_rd_ports
            EWP = self.g_ip.num_wr_ports
            SCHP = self.g_ip.num_search_ports

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
            if self.g_ip.fast_access and not self.dp.is_tag:
                dataoutbits *= self.g_ip.data_assoc

            self.htree_in_add = Htree2(
                self.g_ip,
                self.g_tp,
                self.dp.wtype,
                self.mat.area.w,
                self.mat.area.h,
                total_addrbits,
                datainbits,
                0,
                dataoutbits,
                0,
                self.num_mats_ver_dir * 2,
                self.num_mats_hor_dir * 2,
                parameter.Add_htree,
            )
            self.htree_in_data = Htree2(
                self.g_ip,
                self.g_tp,
                self.dp.wtype,
                self.mat.area.w,
                self.mat.area.h,
                total_addrbits,
                datainbits,
                0,
                dataoutbits,
                0,
                self.num_mats_ver_dir * 2,
                self.num_mats_hor_dir * 2,
                parameter.Data_in_htree,
            )
            self.htree_out_data = Htree2(
                self.g_ip,
                self.g_tp,
                self.dp.wtype,
                self.mat.area.w,
                self.mat.area.h,
                total_addrbits,
                datainbits,
                0,
                dataoutbits,
                0,
                self.num_mats_ver_dir * 2,
                self.num_mats_hor_dir * 2,
                parameter.Data_out_htree,
            )

            self.area = Area()
            self.area.w, self.area.h = self.htree_in_data.area.w, self.htree_in_data.area.h
        else:
            self.htree_in_add = Htree2(self.g_ip, self.g_tp, self.dp.wtype, self.mat.area.w, self.mat.area.h,
                                       total_addrbits, datainbits, searchinbits, dataoutbits, searchoutbits,
                                       self.num_mats_ver_dir * 2, self.num_mats_hor_dir * 2, parameter.Add_htree)
            self.htree_in_data = Htree2(
                self.g_ip,
                self.g_tp,
                self.dp.wtype,
                self.mat.area.w,
                self.mat.area.h,
                total_addrbits,
                datainbits,
                searchinbits,
                dataoutbits,
                searchoutbits,
                self.num_mats_ver_dir * 2,
                self.num_mats_hor_dir * 2,
                parameter.Data_in_htree,
            )
            self.htree_out_data = Htree2(
                self.g_ip,
                self.g_tp,
                self.dp.wtype,
                self.mat.area.w,
                self.mat.area.h,
                total_addrbits,
                datainbits,
                searchinbits,
                dataoutbits,
                searchoutbits,
                self.num_mats_ver_dir * 2,
                self.num_mats_hor_dir * 2,
                parameter.Data_out_htree,
            )
            self.htree_in_search = Htree2(
                self.g_ip,
                self.g_tp,
                self.dp.wtype,
                self.mat.area.w,
                self.mat.area.h,
                total_addrbits,
                datainbits,
                searchinbits,
                dataoutbits,
                searchoutbits,
                self.num_mats_ver_dir * 2,
                self.num_mats_hor_dir * 2,
                parameter.Data_in_htree,
                True,
                True,
            )
            self.htree_out_search = Htree2(
                self.g_ip,
                self.g_tp,
                self.dp.wtype,
                self.mat.area.w,
                self.mat.area.h,
                total_addrbits,
                datainbits,
                searchinbits,
                dataoutbits,
                searchoutbits,
                self.num_mats_ver_dir * 2,
                self.num_mats_hor_dir * 2,
                parameter.Data_out_htree,
                True,
            )

            self.area = Area()
            self.area.w, self.area.h = self.htree_in_data.area.w, self.htree_in_data.area.h

        self.num_addr_b_row_dec = sp.log(self.mat.subarray.num_rows, 2)
        self.num_addr_b_routed_to_mat_for_act = self.num_addr_b_row_dec
        self.num_addr_b_routed_to_mat_for_rd_or_wr = self.num_addr_b_mat - self.num_addr_b_row_dec

    def compute_delays(self, inrisetime):
        return self.mat.compute_delays(inrisetime)

    def compute_power_energy(self):
        # Write files to the cacti/sympy directory
        # Define the output directory
        import os
        output_dir = os.path.join(os.path.dirname(__file__), "debug_sympy_expressions")
        os.makedirs(output_dir, exist_ok=True)

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
            expressions = {
            # Direct expressions without "_self" prefix for self attributes
                "thisbank_mat_power_readOp_dynamic_mul_num_act_mats_hor_dir": self.mat.power.readOp.dynamic * self.dp.num_act_mats_hor_dir,
                "thisbank_mat_power_readOp_leakage_mul_num_mats": self.mat.power.readOp.leakage * self.dp.num_mats,
                "thisbank_mat_power_readOp_gate_leakage_mul_num_mats": self.mat.power.gate_leakage * self.dp.num_mats,
                
                "thisbank_htree_in_add_power_readOp_dynamic": self.htree_in_add.power.readOp.dynamic,
                "thisbank_htree_out_data_power_readOp_dynamic": self.htree_out_data.power.readOp.dynamic,

                # Leakage values without "_self" prefix
                "thisbank_array_leakage": self.array_leakage,
                "thisbank_mat_array_leakage_mul_num_mats": self.mat.array_leakage * self.dp.num_mats,
                "thisbank_wl_leakage": self.wl_leakage,
                "thisbank_mat_wl_leakage_mul_num_mats": self.mat.wl_leakage * self.dp.num_mats,
                "thisbank_cl_leakage": self.cl_leakage,
                "thisbank_mat_cl_leakage_mul_num_mats": self.mat.cl_leakage * self.dp.num_mats,
            }

            # Define the output directory
            output_dir = os.path.join(os.path.dirname(__file__), "debug_sympy_expressions")
            os.makedirs(output_dir, exist_ok=True)

            # Write the values of each expression to a separate file
            for expr_name, value in expressions.items():
                file_path = os.path.join(output_dir, f"{expr_name}.txt")
                
                # Write the value of the expression to the file
                with open(file_path, "w") as file:
                    file.write(str(value))
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

            expressions = {
                # ReadOp Dynamic and Leakage terms
                "thisbank_mat_power_readOp_dynamic": self.mat.power.readOp.dynamic,
                "thisbank_mat_power_readOp_leakage_mul_num_mats": self.mat.power.readOp.leakage * self.dp.num_mats,
                "thisbank_num_mats": self.dp.num_mats,
                "thisbank_mat_power_readOp_gate_leakage_mul_num_mats": self.mat.power.readOp.gate_leakage * self.dp.num_mats,

                # SearchOp Dynamic terms
                "thisbank_mat_power_searchOp_dynamic_mul_num_mats": self.mat.power.searchOp.dynamic * self.dp.num_mats,
                "thisbank_mat_power_bl_precharge_eq_drv_searchOp_dynamic": self.mat.power_bl_precharge_eq_drv.searchOp.dynamic,
                "thisbank_mat_power_sa_searchOp_dynamic": self.mat.power_sa.searchOp.dynamic,
                "thisbank_mat_power_bitline_searchOp_dynamic": self.mat.power_bitline.searchOp.dynamic,
                "thisbank_mat_power_subarray_out_drv_searchOp_dynamic": self.mat.power_subarray_out_drv.searchOp.dynamic,
                "thisbank_mat_ml_to_ram_wl_drv_power_readOp_dynamic": self.mat.ml_to_ram_wl_drv.power.readOp.dynamic,

                # Additional Dynamic terms for htree
                "thisbank_htree_in_add_power_readOp_dynamic": self.htree_in_add.power.readOp.dynamic,
                "thisbank_htree_out_data_power_readOp_dynamic": self.htree_out_data.power.readOp.dynamic,
                "thisbank_htree_in_search_power_searchOp_dynamic": self.htree_in_search.power.searchOp.dynamic,
                "thisbank_htree_out_search_power_searchOp_dynamic": self.htree_out_search.power.searchOp.dynamic,

                # ReadOp Leakage terms for htree
                "thisbank_htree_in_add_power_readOp_leakage": self.htree_in_add.power.readOp.leakage,
                "thisbank_htree_in_data_power_readOp_leakage": self.htree_in_data.power.readOp.leakage,
                "thisbank_htree_out_data_power_readOp_leakage": self.htree_out_data.power.readOp.leakage,
                "thisbank_htree_in_search_power_readOp_leakage": self.htree_in_search.power.readOp.leakage,
                "thisbank_htree_out_search_power_readOp_leakage": self.htree_out_search.power.readOp.leakage,

                # Gate Leakage terms for htree
                "thisbank_htree_in_add_power_readOp_gate_leakage": self.htree_in_add.power.readOp.gate_leakage,
                "thisbank_htree_in_data_power_readOp_gate_leakage": self.htree_in_data.power.readOp.gate_leakage,
                "thisbank_htree_out_data_power_readOp_gate_leakage": self.htree_out_data.power.readOp.gate_leakage,
                "thisbank_htree_in_search_power_readOp_gate_leakage": self.htree_in_search.power.readOp.gate_leakage,
                "thisbank_htree_out_search_power_readOp_gate_leakage": self.htree_out_search.power.readOp.gate_leakage,

                "thisbank_self_power_readOp_gate_leakage": self.power.readOp.gate_leakage,
            }

            # Define the output directory
            output_dir = os.path.join(os.path.dirname(__file__), "debug_sympy_expressions")
            os.makedirs(output_dir, exist_ok=True)

            # Write the values of each expression to a separate file
            for expr_name, value in expressions.items():
                file_path = os.path.join(output_dir, f"{expr_name}.txt")
                
                # Write the value of the expression to the file
                with open(file_path, "w") as file:
                    file.write(str(value))
        
        

        # # Define each expression to be evaluated
        # expressions = {
        #     "thisbank_self_power_readOp_dynamic": self.power.readOp.dynamic,
        #     "thisbank_self_mat_power_readOp_dynamic_mul_num_act_mats_hor_dir": self.mat.power.readOp.dynamic * self.dp.num_act_mats_hor_dir,
        #     "thisbank_self_power_readOp_leakage": self.power.readOp.leakage,
        #     "thisbank_self_mat_power_readOp_leakage_mul_num_mats": self.mat.power.readOp.leakage * self.dp.num_mats,
        #     "thisbank_self_dp_num_mats": self.dp.num_mats,
        #     "thisbank_self_power_readOp_gate_leakage": self.power.readOp.gate_leakage,
        #     "thisbank_self_mat_power_readOp_gate_leakage_mul_num_mats": self.mat.power.readOp.gate_leakage * self.dp.num_mats,
        #     "thisbank_self_htree_in_add_power_readOp_dynamic": self.htree_in_add.power.readOp.dynamic,
        #     "thisbank_self_htree_out_data_power_readOp_dynamic": self.htree_out_data.power.readOp.dynamic,
        #     "thisbank_self_array_leakage": self.array_leakage,
        #     "thisbank_self_mat_array_leakage_mul_num_mats": self.mat.array_leakage * self.dp.num_mats,
        #     "thisbank_self_wl_leakage": self.wl_leakage,
        #     "thisbank_self_mat_wl_leakage_mul_num_mats": self.mat.wl_leakage * self.dp.num_mats,
        #     "thisbank_self_cl_leakage": self.cl_leakage,
        #     "thisbank_self_mat_cl_leakage_mul_num_mats": self.mat.cl_leakage * self.dp.num_mats,
        #     "thisbank_self_power_searchOp_dynamic": self.power.searchOp.dynamic,
        #     "thisbank_self_mat_power_searchOp_dynamic_mul_num_mats": self.mat.power.searchOp.dynamic * self.dp.num_mats,
        #     "thisbank_self_mat_power_bl_precharge_eq_drv_searchOp_dynamic": self.mat.power_bl_precharge_eq_drv.searchOp.dynamic,
        #     "thisbank_self_mat_power_sa_searchOp_dynamic": self.mat.power_sa.searchOp.dynamic,
        #     "thisbank_self_mat_power_bitline_searchOp_dynamic": self.mat.power_bitline.searchOp.dynamic,
        #     "thisbank_self_mat_power_subarray_out_drv_searchOp_dynamic": self.mat.power_subarray_out_drv.searchOp.dynamic,
        #     "thisbank_self_mat_ml_to_ram_wl_drv_power_readOp_dynamic": self.mat.ml_to_ram_wl_drv.power.readOp.dynamic,
        #     "thisbank_self_htree_in_search_power_searchOp_dynamic": self.htree_in_search.power.searchOp.dynamic,
        #     "thisbank_self_htree_out_search_power_searchOp_dynamic": self.htree_out_search.power.searchOp.dynamic,
        #     "thisbank_self_htree_in_data_power_readOp_leakage": self.htree_in_data.power.readOp.leakage,
        #     "thisbank_self_htree_out_data_power_readOp_leakage": self.htree_out_data.power.readOp.leakage,
        #     "thisbank_self_htree_in_search_power_readOp_leakage": self.htree_in_search.power.readOp.leakage,
        #     "thisbank_self_htree_out_search_power_readOp_leakage": self.htree_out_search.power.readOp.leakage,
        #     "thisbank_self_htree_in_add_power_readOp_gate_leakage": self.htree_in_add.power.readOp.gate_leakage,
        #     "thisbank_self_htree_in_data_power_readOp_gate_leakage": self.htree_in_data.power.readOp.gate_leakage,
        #     "thisbank_self_htree_out_data_power_readOp_gate_leakage": self.htree_out_data.power.readOp.gate_leakage,
        #     "thisbank_self_htree_in_search_power_readOp_gate_leakage": self.htree_in_search.power.readOp.gate_leakage,
        #     "thisbank_self_htree_out_search_power_readOp_gate_leakage": self.htree_out_search.power.readOp.gate_leakage,
        # }

        # # Write the values of each expression to a separate file
        # for expr_name, value in expressions.items():
        #     file_path = os.path.join(output_dir, f"{expr_name}.txt")
            
        #     # Write the value of the expression to the file
        #     with open(file_path, "w") as file:
        #         file.write(str(value))


# DO one run, save expressions 32 -d 32nm
# DO run where does first 22 then 32, then save expresssions 1
