/*****************************************************************************
 *                                CACTI 7.0
 *                      SOFTWARE LICENSE AGREEMENT
 *            Copyright 2015 Hewlett-Packard Development Company, L.P.
 *                          All Rights Reserved
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.

 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.”
 *
 ***************************************************************************/



#include "bank.h"
#include <iostream>

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <sys/stat.h>
#include <sys/types.h>


Bank::Bank(const DynamicParameter & dyn_p):
  dp(dyn_p), mat(dp),
  num_addr_b_mat(dyn_p.number_addr_bits_mat),
  num_mats_hor_dir(dyn_p.num_mats_h_dir), num_mats_ver_dir(dyn_p.num_mats_v_dir),
  array_leakage(0),
  wl_leakage(0),
  cl_leakage(0)
{
//  Mat temp(dyn_p);
  int RWP;
  int ERP;
  int EWP;
  int SCHP;

  if (dp.use_inp_params)
  {
    RWP  = dp.num_rw_ports;
    ERP  = dp.num_rd_ports;
    EWP  = dp.num_wr_ports;
    SCHP = dp.num_search_ports;
  }
  else
  {
    RWP  = g_ip->num_rw_ports;
    ERP  = g_ip->num_rd_ports;
    EWP  = g_ip->num_wr_ports;
    SCHP = g_ip->num_search_ports;
  }

  int total_addrbits = (dp.number_addr_bits_mat + dp.number_subbanks_decode)*(RWP+ERP+EWP);
  int datainbits     = dp.num_di_b_bank_per_port * (RWP + EWP);
  int dataoutbits    = dp.num_do_b_bank_per_port * (RWP + ERP);
  int searchinbits;
  int searchoutbits;

  if (dp.fully_assoc || dp.pure_cam)
  {
	  datainbits   = dp.num_di_b_bank_per_port * (RWP + EWP);
	  dataoutbits  = dp.num_do_b_bank_per_port * (RWP + ERP);
	  searchinbits    = dp.num_si_b_bank_per_port * SCHP;
	  searchoutbits   = dp.num_so_b_bank_per_port * SCHP;
  }

  if (!(dp.fully_assoc || dp.pure_cam))
    {
    if (g_ip->fast_access && dp.is_tag == false)
    {
        dataoutbits *= g_ip->data_assoc;
    }
			 
  htree_in_add   = new Htree2 (dp.wtype/*g_ip->wt*/,(double) mat.area.w, (double)mat.area.h,
      total_addrbits, datainbits, 0,dataoutbits,0, num_mats_ver_dir*2, num_mats_hor_dir*2, Add_htree);
  htree_in_data  = new Htree2 (dp.wtype/*g_ip->wt*/,(double) mat.area.w, (double)mat.area.h,
      total_addrbits, datainbits, 0,dataoutbits,0, num_mats_ver_dir*2, num_mats_hor_dir*2, Data_in_htree);
  htree_out_data = new Htree2 (dp.wtype/*g_ip->wt*/,(double) mat.area.w, (double)mat.area.h,
      total_addrbits, datainbits, 0,dataoutbits,0, num_mats_ver_dir*2, num_mats_hor_dir*2, Data_out_htree);

//  htree_out_data = new Htree2 (g_ip->wt,(double) 100, (double)100,
//		  total_addrbits, datainbits, 0,dataoutbits,0, num_mats_ver_dir*2, num_mats_hor_dir*2, Data_out_htree);

  area.w = htree_in_data->area.w;
  area.h = htree_in_data->area.h;
  }
  else
  {
	  htree_in_add   = new Htree2 (dp.wtype/*g_ip->wt*/,(double) mat.area.w, (double)mat.area.h,
			  total_addrbits, datainbits, searchinbits,dataoutbits,searchoutbits, num_mats_ver_dir*2, num_mats_hor_dir*2, Add_htree);
	  htree_in_data  = new Htree2 (dp.wtype/*g_ip->wt*/,(double) mat.area.w, (double)mat.area.h,
			  total_addrbits, datainbits,searchinbits, dataoutbits, searchoutbits, num_mats_ver_dir*2, num_mats_hor_dir*2, Data_in_htree);
	  htree_out_data = new Htree2 (dp.wtype/*g_ip->wt*/,(double) mat.area.w, (double)mat.area.h,
			  total_addrbits, datainbits,searchinbits, dataoutbits, searchoutbits,num_mats_ver_dir*2, num_mats_hor_dir*2, Data_out_htree);
	  htree_in_search  = new Htree2 (dp.wtype/*g_ip->wt*/,(double) mat.area.w, (double)mat.area.h,
			  total_addrbits, datainbits,searchinbits, dataoutbits, searchoutbits, num_mats_ver_dir*2, num_mats_hor_dir*2, Data_in_htree,true, true);
	  htree_out_search = new Htree2 (dp.wtype/*g_ip->wt*/,(double) mat.area.w, (double)mat.area.h,
			  total_addrbits, datainbits,searchinbits, dataoutbits, searchoutbits,num_mats_ver_dir*2, num_mats_hor_dir*2, Data_out_htree,true);

      area.w = htree_in_data->area.w;
      area.h = htree_in_data->area.h;
  }

  num_addr_b_row_dec = _log2(mat.subarray.num_rows);
  num_addr_b_routed_to_mat_for_act = num_addr_b_row_dec;
  num_addr_b_routed_to_mat_for_rd_or_wr = num_addr_b_mat - num_addr_b_row_dec;
}



Bank::~Bank()
{
  delete htree_in_add;
  delete htree_out_data;
  delete htree_in_data;
  if (dp.fully_assoc || dp.pure_cam)
  {
	  delete htree_in_search;
	  delete htree_out_search;
  }
}



double Bank::compute_delays(double inrisetime)
{
  return mat.compute_delays(inrisetime);
}

// Function to create the directory if it doesn't exist
void bank_create_directory(const char *path) {
    mkdir(path, 0777);
}

// Function to append a value to the output file
void bank_append_value_to_file(const char *filename, const char *label, double value) {
    FILE *file = fopen(filename, "a"); // Append mode
    if (file != NULL) {
        fprintf(file, "%s: %f\n", label, value);
        fclose(file);
    } else {
        perror("Error opening file");
    }
}

void Bank::compute_power_energy()
{
  // Define directory
	const char *output_dir = "debug_sympy_validate";
	bank_create_directory(output_dir);
	const char *output_file = "debug_sympy_validate/debug_sympy_validate.txt";

  mat.compute_power_energy();

  if (!(dp.fully_assoc || dp.pure_cam))
  {
	  power.readOp.dynamic += mat.power.readOp.dynamic * dp.num_act_mats_hor_dir;
	  power.readOp.leakage += mat.power.readOp.leakage * dp.num_mats;
	  power.readOp.gate_leakage += mat.power.readOp.gate_leakage * dp.num_mats;

	  power.readOp.dynamic += htree_in_add->power.readOp.dynamic;
	  power.readOp.dynamic += htree_out_data->power.readOp.dynamic;

	  array_leakage  += mat.array_leakage*dp.num_mats;
	  wl_leakage     += mat.wl_leakage*dp.num_mats;
	  cl_leakage     += mat.cl_leakage*dp.num_mats;

    // Write individual values for power.readOp.dynamic, power.readOp.leakage, and power.readOp.gate_leakage
    bank_append_value_to_file(output_file, "thisbank_mat_power_readOp_dynamic_mul_num_act_mats_hor_dir", mat.power.readOp.dynamic * dp.num_act_mats_hor_dir);
    bank_append_value_to_file(output_file, "thisbank_mat_power_readOp_leakage_mul_num_mats", mat.power.readOp.leakage * dp.num_mats);
    bank_append_value_to_file(output_file, "thisbank_mat_power_readOp_gate_leakage_mul_num_mats", mat.power.readOp.gate_leakage * dp.num_mats);

    bank_append_value_to_file(output_file, "thisbank_htree_in_add_power_readOp_dynamic", htree_in_add->power.readOp.dynamic);
    bank_append_value_to_file(output_file, "thisbank_htree_out_data_power_readOp_dynamic", htree_out_data->power.readOp.dynamic);

    // Additional leakage terms
    bank_append_value_to_file(output_file, "thisbank_mat_array_leakage_mul_num_mats", mat.array_leakage * dp.num_mats);
    bank_append_value_to_file(output_file, "thisbank_mat_wl_leakage_mul_num_mats", mat.wl_leakage * dp.num_mats);
    bank_append_value_to_file(output_file, "thisbank_mat_cl_leakage_mul_num_mats", mat.cl_leakage * dp.num_mats);
//
//	  power.readOp.leakage += htree_in_add->power.readOp.leakage;
//	  power.readOp.leakage += htree_in_data->power.readOp.leakage;
//	  power.readOp.leakage += htree_out_data->power.readOp.leakage;
//	  power.readOp.gate_leakage += htree_in_add->power.readOp.gate_leakage;
//	  power.readOp.gate_leakage += htree_in_data->power.readOp.gate_leakage;
//	  power.readOp.gate_leakage += htree_out_data->power.readOp.gate_leakage;
  }
  else
  {

	  power.readOp.dynamic += mat.power.readOp.dynamic ;//for fa and cam num_act_mats_hor_dir is 1 for plain r/w
	  power.readOp.leakage += mat.power.readOp.leakage * dp.num_mats;
	  power.readOp.gate_leakage += mat.power.readOp.gate_leakage * dp.num_mats;

	  power.searchOp.dynamic += mat.power.searchOp.dynamic * dp.num_mats;
	  power.searchOp.dynamic += mat.power_bl_precharge_eq_drv.searchOp.dynamic +
	  	                        mat.power_sa.searchOp.dynamic +
	  	                        mat.power_bitline.searchOp.dynamic +
	  	                        mat.power_subarray_out_drv.searchOp.dynamic+
	  	                        mat.ml_to_ram_wl_drv->power.readOp.dynamic;

	  power.readOp.dynamic += htree_in_add->power.readOp.dynamic;
	  power.readOp.dynamic += htree_out_data->power.readOp.dynamic;

	  power.searchOp.dynamic += htree_in_search->power.searchOp.dynamic;
	  power.searchOp.dynamic += htree_out_search->power.searchOp.dynamic;

	  power.readOp.leakage += htree_in_add->power.readOp.leakage;
	  power.readOp.leakage += htree_in_data->power.readOp.leakage;
	  power.readOp.leakage += htree_out_data->power.readOp.leakage;
	  power.readOp.leakage += htree_in_search->power.readOp.leakage;
	  power.readOp.leakage += htree_out_search->power.readOp.leakage;


	  power.readOp.gate_leakage += htree_in_add->power.readOp.gate_leakage;
	  power.readOp.gate_leakage += htree_in_data->power.readOp.gate_leakage;
	  power.readOp.gate_leakage += htree_out_data->power.readOp.gate_leakage;
	  power.readOp.gate_leakage += htree_in_search->power.readOp.gate_leakage;
	  power.readOp.gate_leakage += htree_out_search->power.readOp.gate_leakage;

    // Fully associative or CAM configuration calculations
    bank_append_value_to_file(output_file, "thisbank_mat_power_readOp_dynamic", mat.power.readOp.dynamic);
    bank_append_value_to_file(output_file, "thisbank_mat_power_readOp_leakage_mul_num_mats", mat.power.readOp.leakage * dp.num_mats);
    bank_append_value_to_file(output_file, "thisbank_num_mats", dp.num_mats);
    bank_append_value_to_file(output_file, "thisbank_mat_power_readOp_gate_leakage_mul_num_mats", mat.power.readOp.gate_leakage * dp.num_mats);

    bank_append_value_to_file(output_file, "thisbank_mat_power_searchOp_dynamic_mul_num_mats", mat.power.searchOp.dynamic * dp.num_mats);
    bank_append_value_to_file(output_file, "thisbank_mat_power_bl_precharge_eq_drv_searchOp_dynamic", mat.power_bl_precharge_eq_drv.searchOp.dynamic);
    bank_append_value_to_file(output_file, "thisbank_mat_power_sa_searchOp_dynamic", mat.power_sa.searchOp.dynamic);
    bank_append_value_to_file(output_file, "thisbank_mat_power_bitline_searchOp_dynamic", mat.power_bitline.searchOp.dynamic);
    bank_append_value_to_file(output_file, "thisbank_mat_power_subarray_out_drv_searchOp_dynamic", mat.power_subarray_out_drv.searchOp.dynamic);
    bank_append_value_to_file(output_file, "thisbank_mat_ml_to_ram_wl_drv_power_readOp_dynamic", mat.ml_to_ram_wl_drv->power.readOp.dynamic);

    bank_append_value_to_file(output_file, "thisbank_htree_in_add_power_readOp_dynamic", htree_in_add->power.readOp.dynamic);
    bank_append_value_to_file(output_file, "thisbank_htree_out_data_power_readOp_dynamic", htree_out_data->power.readOp.dynamic);

    bank_append_value_to_file(output_file, "thisbank_htree_in_search_power_searchOp_dynamic", htree_in_search->power.searchOp.dynamic);
    bank_append_value_to_file(output_file, "thisbank_htree_out_search_power_searchOp_dynamic", htree_out_search->power.searchOp.dynamic);

    // Leakage components for associative or CAM configuration
    bank_append_value_to_file(output_file, "thisbank_htree_in_add_power_readOp_leakage", htree_in_add->power.readOp.leakage);
    bank_append_value_to_file(output_file, "thisbank_htree_in_data_power_readOp_leakage", htree_in_data->power.readOp.leakage);
    bank_append_value_to_file(output_file, "thisbank_htree_out_data_power_readOp_leakage", htree_out_data->power.readOp.leakage);
    bank_append_value_to_file(output_file, "thisbank_htree_in_search_power_readOp_leakage", htree_in_search->power.readOp.leakage);
    bank_append_value_to_file(output_file, "thisbank_htree_out_search_power_readOp_leakage", htree_out_search->power.readOp.leakage);

    // Gate leakage components
    bank_append_value_to_file(output_file, "thisbank_htree_in_add_power_readOp_gate_leakage", htree_in_add->power.readOp.gate_leakage);
    bank_append_value_to_file(output_file, "thisbank_htree_in_data_power_readOp_gate_leakage", htree_in_data->power.readOp.gate_leakage);
    bank_append_value_to_file(output_file, "thisbank_htree_out_data_power_readOp_gate_leakage", htree_out_data->power.readOp.gate_leakage);
    bank_append_value_to_file(output_file, "thisbank_htree_in_search_power_readOp_gate_leakage", htree_in_search->power.readOp.gate_leakage);
    bank_append_value_to_file(output_file, "thisbank_htree_out_search_power_readOp_gate_leakage", htree_out_search->power.readOp.gate_leakage);
  }

}




