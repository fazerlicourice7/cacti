
#include <fstream>
#include <iostream>
#include <sstream>


#include "io.h"
#include "area.h"
#include "basic_circuit.h"
#include "parameter.h"
#include "Ucache.h"
#include "nuca.h"
#include "crossbar.h"
#include "arbiter.h"
//#include "highradix.h"
#include "TSV.h"
#include "memorybus.h"
#include "version_cacti.h"

#include "extio.h"
#include "extio_technology.h"
#include "memcad.h"

#include "klee_io.h"

using namespace std;



uca_org_t klee_cacti_interface(const string & infile_name)
{

  uca_org_t fin_res;
  fin_res.valid = false;

  printf("-> create g_ip global\n");
  g_ip = new InputParameter();
  g_ip->print_detail_debug = false;
  printf("-> parse %s to g_ip\n", infile_name.c_str());
  g_ip->tsv_os_bank_type = 0;
  g_ip->tsv_is_subarray_type= 0;
  g_ip->parse_cfg(infile_name);
  if(!g_ip->error_checking()) exit(0);
  
  //g_ip->display_ip();
  printf("-> init tech parameters\n");
  init_tech_params(g_ip->F_sz_um, false);
  Wire winit; // Do not delete this line. It initializes wires.

  printf("-> set TSV parameters\n");
  g_ip->tsv_is_subarray_type = g_ip->TSV_proj_type;
  g_ip->tsv_os_bank_type = g_ip->TSV_proj_type;
  printf("-> create TSV test object\n");
  TSV tsv_test(Coarse);// ********* double len_ /* in um*/, 	double diam_, 	double TSV_pitch_,
  if(g_ip->print_detail_debug)
  {
	tsv_test.print_TSV();
  }

  printf("-> NUCA simulation\n");
  if (g_ip->nuca == 1)
  {
    Nuca n(&g_tp.peri_global);
    n.sim_nuca();
  }
  
	
   
  printf("-> instantiate IO Tech Parameters\n");
  IOTechParam iot(g_ip, g_ip->io_type, g_ip->num_mem_dq, g_ip->mem_data_width, g_ip->num_dq,g_ip->dram_dimm, 1,g_ip->bus_freq ); 
  printf("-> instantiate Extended IO Tech Parameters\n");
  Extio testextio(&iot);  
  printf("-> run IO tests\n");
  testextio.extio_area();
  testextio.extio_eye();
  testextio.extio_power_dynamic();
  testextio.extio_power_phy();
  testextio.extio_power_term();	   
  
  
  printf("-> solve\n");
  solve(&fin_res);

  printf("-> output UCA paramters\n");
  klee_output_UCA(&fin_res);
  printf("-> output UCA paramters to file\n");
  output_data_csv(fin_res, infile_name + ".out");


  // Memcad Optimization
  MemCadParameters memcad_params(g_ip);
  solve_memcad(&memcad_params);


  delete (g_ip);
  return fin_res;
}


void klee_output_UCA(uca_org_t *fr)
{
	if(g_ip->is_3d_mem)
	{

		cout<<"-------  CACTI (version "<< VER_MAJOR_CACTI <<"."<< VER_MINOR_CACTI<<"." << VER_COMMENT_CACTI
								<< " of " << VER_UPDATE_CACTI << ") 3D DRAM Main Memory  -------"<<endl;

		cout << "\nMemory Parameters:\n";
		cout << "	Total memory size (Gb): " <<
				(int) (g_ip->cache_sz) << endl;
		if(g_ip->num_die_3d>1)
		{
			cout << "	Stacked die count: " << (int) g_ip->num_die_3d << endl;
			if(g_ip->TSV_proj_type == 1)
				cout << "	TSV projection: industrial conservative"  << endl;
			else
				cout << "	TSV projection: ITRS aggressive"  << endl;
		}
		cout << "	Number of banks: " << (int) g_ip->nbanks << endl;
		cout << "	Technology size (nm): " << g_ip->F_sz_nm << endl;
		cout << "	Page size (bits): " << g_ip->page_sz_bits << endl;
		cout << "	Burst depth: " << g_ip->burst_depth << endl;
		cout << "	Chip IO width: " << g_ip->io_width << endl;
		cout << "	Best Ndwl: " << fr->data_array2->Ndwl << endl;
		cout << "	Best Ndbl: " << fr->data_array2->Ndbl << endl;
		cout << "	# rows in subarray: " << fr->data_array2->num_row_subarray << endl;
		cout << "	# columns in subarray: " << fr->data_array2->num_col_subarray << endl;

		cout <<"\nResults:\n";
		cout<<"Timing Components:"<<endl;
	    cout<<"	   t_RCD (Row to column command delay): "<< fr->data_array2->t_RCD * 1e9 << " ns" <<endl;
		cout<<"	   t_RAS (Row access strobe latency): "<< fr->data_array2->t_RAS * 1e9  << " ns" <<endl;
		cout<<"	   t_RC (Row cycle): "<< fr->data_array2->t_RC * 1e9  << " ns" <<endl;
		cout<<"	   t_CAS (Column access strobe latency): "<< fr->data_array2->t_CAS * 1e9  << " ns" <<endl;
		cout<<"	   t_RP (Row precharge latency): "<< fr->data_array2->t_RP* 1e9  << " ns" <<endl;
		//cout<<"	   t_RRD (Rank to rank latency): "<< fr->data_array2->t_RRD* 1e9  << " ns" <<endl;
		cout<<"	   t_RRD (Row activation to row activation delay): "<< fr->data_array2->t_RRD * 1e9 << " ns"<<endl;

		cout<<"Power Components:"<<endl;
		cout<<"	   Activation energy: "<< fr->data_array2->activate_energy * 1e9  << " nJ" <<endl;
		cout<<"	   Read energy: "<< fr->data_array2->read_energy * 1e9  << " nJ" <<endl;
		cout<<"	   Write energy: "<< fr->data_array2->write_energy * 1e9  << " nJ" <<endl;
		cout<<"	   Precharge energy: "<< fr->data_array2->precharge_energy * 1e9  << " nJ" <<endl;
		//cout<<"	Activation power: "<<  fr->data_array2->activate_power * 1e3   << " mW" <<endl;
		//cout<<"	Read power: "<<  fr->data_array2->read_power * 1e3 << " mW" <<endl;
		//cout<<"	Write power: "<<  fr->data_array2->write_power * 1e3  << " mW" <<endl;
		//cout<<"	Peak read power: "<< read_energy/((g_ip->burst_depth)/(g_ip->sys_freq_MHz*1e6)/2) * 1e3  << " mW" <<endl;
		cout<<"Area Components:"<<endl;
		//cout<<"	Height: "<<area.h/1e3<<" mm"<<endl;
		//cout<<"	Length: "<<area.w/1e3<<" mm"<<endl;
		//cout<<"	DRAM+peri Area: "<< fr->data_array2->area/1e6<<" mm2"<<endl;

		//double DRAM_area_per_die = (g_ip->partition_gran>0) ? fr->data_array2->area : (fr->data_array2->area/0.5);
		double DRAM_area_per_die = (g_ip->partition_gran>0) ? fr->data_array2->area : (fr->data_array2->area + fr->data_array2->area_ram_cells*0.65);
		//double DRAM_area_per_die = (g_ip->partition_gran>0) ? fr->data_array2->area : (fr->data_array2->area + 2.5e9*(double)(g_ip->F_sz_um)*(g_ip->F_sz_um));
		double area_efficiency_per_die = (g_ip->partition_gran>0) ? fr->data_array2->area_efficiency : (fr->data_array2->area_ram_cells / DRAM_area_per_die *100);
		double DRAM_width = (g_ip->partition_gran>0) ? fr->data_array2->all_banks_width : (fr->data_array2->all_banks_width + (DRAM_area_per_die-fr->data_array2->area)/fr->data_array2->all_banks_height);
		cout<<"	   DRAM core area: "<< fr->data_array2->area/1e6 <<" mm2"<<endl;
		if (g_ip->partition_gran == 0)
			cout<<"	   DRAM area per die: "<< DRAM_area_per_die/1e6 <<" mm2"<<endl;
		cout<<"	   Area efficiency: "<< area_efficiency_per_die <<"%"<<endl;
		cout<<"	   DRAM die width: "<< DRAM_width/1e3 <<" mm"<<endl;
		cout<<"	   DRAM die height: "<< fr->data_array2->all_banks_height/1e3 <<" mm"<<endl;
		if (g_ip->num_die_3d>1)
		{
			cout<<"TSV Components:"<<endl;
			cout<<"	   TSV area overhead: "<< fr->data_array2->area_TSV_tot /1e6 <<" mm2"<<endl;
			cout<<"	   TSV latency overhead: "<< fr->data_array2->delay_TSV_tot * 1e9 <<" ns"<<endl;
			cout<<"	   TSV energy overhead per access: "<< fr->data_array2->dyn_pow_TSV_per_access * 1e9 <<" nJ"<<endl;
		}
	}
	else // if(!g_ip->is_3d_mem)
	{
  //    if (NUCA)
  if (0) {
    cout << "\n\n Detailed Bank Stats:\n";
    cout << "    Bank Size (bytes): %d\n" <<
                                     (int) (g_ip->cache_sz);
  }
  else {
    if (g_ip->data_arr_ram_cell_tech_type == 3) {
      cout << "\n---------- CACTI (version "<< VER_MAJOR_CACTI <<"."<< VER_MINOR_CACTI<<"." << VER_COMMENT_CACTI
								<< " of " << VER_UPDATE_CACTI << "), Uniform Cache Access " <<
        "Logic Process Based DRAM Model ----------\n";
    }
    else if (g_ip->data_arr_ram_cell_tech_type == 4) {
      cout << "\n---------- CACTI (version "<< VER_MAJOR_CACTI <<"."<< VER_MINOR_CACTI<<"." << VER_COMMENT_CACTI
								<< " of " << VER_UPDATE_CACTI << "), Uniform" <<
        "Cache Access Commodity DRAM Model ----------\n";
    }
    else {
      cout << "\n---------- CACTI (version "<< VER_MAJOR_CACTI <<"."<< VER_MINOR_CACTI<<"." << VER_COMMENT_CACTI
								<< " of " << VER_UPDATE_CACTI << "), Uniform Cache Access "
        "SRAM Model ----------\n";
    }
    cout << "\nCache Parameters:\n";
    cout << "    Total cache size (bytes): " <<
      (int) (g_ip->cache_sz) << endl;
  }

  cout << "    Number of banks: " << (int) g_ip->nbanks << endl;
  if (g_ip->fully_assoc|| g_ip->pure_cam)
    cout << "    Associativity: fully associative\n";
  else {
    if (g_ip->tag_assoc == 1)
      cout << "    Associativity: direct mapped\n";
    else
      cout << "    Associativity: " <<
        g_ip->tag_assoc << endl;
  }


  cout << "    Block size (bytes): " << g_ip->line_sz << endl;
  cout << "    Read/write Ports: " <<
    g_ip->num_rw_ports << endl;
  cout << "    Read ports: " <<
    g_ip->num_rd_ports << endl;
  cout << "    Write ports: " <<
    g_ip->num_wr_ports << endl;
  if (g_ip->fully_assoc|| g_ip->pure_cam)
	  cout << "    search ports: " <<
	      g_ip->num_search_ports << endl;
  cout << "    Technology size (nm): " <<
    g_ip->F_sz_nm << endl << endl;

  cout << "    Access time (ns): " << fr->access_time*1e9 << endl;
  cout << "    Cycle time (ns):  " << fr->cycle_time*1e9 << endl;
  if (g_ip->data_arr_ram_cell_tech_type >= 4) {
    cout << "    Precharge Delay (ns): " << fr->data_array2->precharge_delay*1e9 << endl;
    cout << "    Activate Energy (nJ): " << fr->data_array2->activate_energy*1e9 << endl;
    cout << "    Read Energy (nJ): " << fr->data_array2->read_energy*1e9 << endl;
    cout << "    Write Energy (nJ): " << fr->data_array2->write_energy*1e9 << endl;
    cout << "    Precharge Energy (nJ): " << fr->data_array2->precharge_energy*1e9 << endl;
    cout << "    Leakage Power Closed Page (mW): " << fr->data_array2->leak_power_subbank_closed_page*1e3 << endl;
    cout << "    Leakage Power Open Page (mW): " << fr->data_array2->leak_power_subbank_open_page*1e3 << endl;
    cout << "    Leakage Power I/O (mW): " << fr->data_array2->leak_power_request_and_reply_networks*1e3 << endl;
    cout << "    Refresh power (mW): " <<
      fr->data_array2->refresh_power*1e3 << endl;
  }
  else {
	  if ((g_ip->fully_assoc|| g_ip->pure_cam))
	  {
		  cout << "    Total dynamic associative search energy per access (nJ): " <<
		  fr->power.searchOp.dynamic*1e9 << endl;
//		  cout << "    Total dynamic read energy per access (nJ): " <<
//		  fr->power.readOp.dynamic*1e9 << endl;
//		  cout << "    Total dynamic write energy per access (nJ): " <<
//		  fr->power.writeOp.dynamic*1e9 << endl;
	  }
//	  else
//	  {
		  cout << "    Total dynamic read energy per access (nJ): " <<
		  fr->power.readOp.dynamic*1e9 << endl;
		  cout << "    Total dynamic write energy per access (nJ): " <<
		  fr->power.writeOp.dynamic*1e9 << endl;
//	  }
	  cout << "    Total leakage power of a bank"
	  " (mW): " << fr->power.readOp.leakage*1e3 << endl;
	  cout << "    Total gate leakage power of a bank"
	  " (mW): " << fr->power.readOp.gate_leakage*1e3 << endl;
  }

  if (g_ip->data_arr_ram_cell_tech_type ==3 || g_ip->data_arr_ram_cell_tech_type ==4)
  {
  }
  cout <<  "    Cache height x width (mm): " <<
    fr->cache_ht*1e-3 << " x " << fr->cache_len*1e-3 << endl << endl;


  cout << "    Best Ndwl : " << fr->data_array2->Ndwl << endl;
  cout << "    Best Ndbl : " << fr->data_array2->Ndbl << endl;
  cout << "    Best Nspd : " << fr->data_array2->Nspd << endl;
  cout << "    Best Ndcm : " << fr->data_array2->deg_bl_muxing << endl;
  cout << "    Best Ndsam L1 : " << fr->data_array2->Ndsam_lev_1 << endl;
  cout << "    Best Ndsam L2 : " << fr->data_array2->Ndsam_lev_2 << endl << endl;

  if ((!(g_ip->pure_ram|| g_ip->pure_cam || g_ip->fully_assoc)) && !g_ip->is_main_mem)
  {
    cout << "    Best Ntwl : " << fr->tag_array2->Ndwl << endl;
    cout << "    Best Ntbl : " << fr->tag_array2->Ndbl << endl;
    cout << "    Best Ntspd : " << fr->tag_array2->Nspd << endl;
    cout << "    Best Ntcm : " << fr->tag_array2->deg_bl_muxing << endl;
    cout << "    Best Ntsam L1 : " << fr->tag_array2->Ndsam_lev_1 << endl;
    cout << "    Best Ntsam L2 : " << fr->tag_array2->Ndsam_lev_2 << endl;
  }

  switch (fr->data_array2->wt) {
    case (0):
      cout <<  "    Data array, H-tree wire type: Delay optimized global wires\n";
      break;
    case (1):
      cout <<  "    Data array, H-tree wire type: Global wires with 5\% delay penalty\n";
      break;
    case (2):
      cout <<  "    Data array, H-tree wire type: Global wires with 10\% delay penalty\n";
      break;
    case (3):
      cout <<  "    Data array, H-tree wire type: Global wires with 20\% delay penalty\n";
      break;
    case (4):
      cout <<  "    Data array, H-tree wire type: Global wires with 30\% delay penalty\n";
      break;
    case (5):
      cout <<  "    Data array, wire type: Low swing wires\n";
      break;
    default:
      cout << "ERROR - Unknown wire type " << (int) fr->data_array2->wt <<endl;
      exit(0);
  }

  if (!(g_ip->pure_ram|| g_ip->pure_cam || g_ip->fully_assoc)) {
    switch (fr->tag_array2->wt) {
      case (0):
        cout <<  "    Tag array, H-tree wire type: Delay optimized global wires\n";
        break;
      case (1):
        cout <<  "    Tag array, H-tree wire type: Global wires with 5\% delay penalty\n";
        break;
      case (2):
        cout <<  "    Tag array, H-tree wire type: Global wires with 10\% delay penalty\n";
        break;
      case (3):
        cout <<  "    Tag array, H-tree wire type: Global wires with 20\% delay penalty\n";
        break;
      case (4):
        cout <<  "    Tag array, H-tree wire type: Global wires with 30\% delay penalty\n";
        break;
      case (5):
        cout <<  "    Tag array, wire type: Low swing wires\n";
        break;
      default:
        cout << "ERROR - Unknown wire type " << (int) fr->tag_array2->wt <<endl;
        exit(-1);
    }
  }
	} //end if(!g_ip->is_3d_mem)
  if (g_ip->print_detail)
  {
    //if(g_ip->fully_assoc) return;

	  if (g_ip->is_3d_mem)
	  {
		  cout << endl << endl << "3D DRAM Detail Components:" << endl << endl;
		  cout << endl << "Time Components:" << endl << endl;
		  cout << "\t row activation bus delay (ns): "  << fr->data_array2->delay_row_activate_net*1e9 << endl;
		  cout << "\t row predecoder delay (ns): "  << fr->data_array2->delay_row_predecode_driver_and_block*1e9 << endl;
		  cout << "\t row decoder delay (ns): "  << fr->data_array2->delay_row_decoder*1e9 << endl;
		  cout << "\t local wordline delay (ns): "  << fr->data_array2->delay_local_wordline*1e9 << endl;
		  cout << "\t bitline delay (ns): "  << fr->data_array2->delay_bitlines*1e9 << endl;
		  cout << "\t sense amp delay (ns): "  << fr->data_array2->delay_sense_amp*1e9 << endl;
		  cout << "\t column access bus delay (ns): "  << fr->data_array2->delay_column_access_net*1e9 << endl;
		  cout << "\t column predecoder delay (ns): "  << fr->data_array2->delay_column_predecoder*1e9 << endl;
		  cout << "\t column decoder delay (ns): "  << fr->data_array2->delay_column_decoder*1e9 << endl;
		  //cout << "\t column selectline delay (ns): "  << fr->data_array2->delay_column_selectline*1e9 << endl;
		  cout << "\t datapath bus delay (ns): "  << fr->data_array2->delay_datapath_net*1e9 << endl;
		  cout << "\t global dataline delay (ns): "  << fr->data_array2->delay_global_data*1e9 << endl;
		  cout << "\t local dataline delay (ns): "  << fr->data_array2->delay_local_data_and_drv*1e9 << endl;
		  cout << "\t data buffer delay (ns): "  << fr->data_array2->delay_data_buffer*1e9 << endl;
		  cout << "\t subarray output driver delay (ns): "  << fr->data_array2->delay_subarray_output_driver*1e9 << endl;

		  cout << endl << "Energy Components:" << endl << endl;
		  cout << "\t row activation bus energy (nJ): "  << fr->data_array2->energy_row_activate_net*1e9 << endl;
		  cout << "\t row predecoder energy (nJ): "  << fr->data_array2->energy_row_predecode_driver_and_block*1e9 << endl;
		  cout << "\t row decoder energy (nJ): "  << fr->data_array2->energy_row_decoder*1e9 << endl;
		  cout << "\t local wordline energy (nJ): "  << fr->data_array2->energy_local_wordline*1e9 << endl;
		  cout << "\t bitline energy (nJ): "  << fr->data_array2->energy_bitlines*1e9 << endl;
		  cout << "\t sense amp energy (nJ): "  << fr->data_array2->energy_sense_amp*1e9 << endl;
		  cout << "\t column access bus energy (nJ): "  << fr->data_array2->energy_column_access_net*1e9 << endl;
		  cout << "\t column predecoder energy (nJ): "  << fr->data_array2->energy_column_predecoder*1e9 << endl;
		  cout << "\t column decoder energy (nJ): "  << fr->data_array2->energy_column_decoder*1e9 << endl;
		  cout << "\t column selectline energy (nJ): "  << fr->data_array2->energy_column_selectline*1e9 << endl;
		  cout << "\t datapath bus energy (nJ): "  << fr->data_array2->energy_datapath_net*1e9 << endl;
		  cout << "\t global dataline energy (nJ): "  << fr->data_array2->energy_global_data*1e9 << endl;
		  cout << "\t local dataline energy (nJ): "  << fr->data_array2->energy_local_data_and_drv*1e9 << endl;
		  cout << "\t data buffer energy (nJ): "  << fr->data_array2->energy_subarray_output_driver*1e9 << endl;
		  //cout << "\t subarray output driver energy (nJ): "  << fr->data_array2->energy_data_buffer*1e9 << endl;

		  cout << endl << "Area Components:" << endl << endl;
		  //cout << "\t subarray area (mm2): "  << fr->data_array2->area_subarray/1e6 << endl;
		  cout << "\t DRAM cell area (mm2): "  << fr->data_array2->area_ram_cells/1e6 << endl;
		  cout << "\t local WL driver area (mm2): "  << fr->data_array2->area_lwl_drv/1e6 << endl;
		  cout << "\t subarray sense amp area (mm2): "  << fr->data_array2->area_sense_amp/1e6 << endl;
		  cout << "\t row predecoder/decoder area (mm2): "  << fr->data_array2->area_row_predec_dec/1e6 << endl;
		  cout << "\t column predecoder/decoder area (mm2): "  << fr->data_array2->area_col_predec_dec/1e6 << endl;
		  cout << "\t center stripe bus area (mm2): "  << fr->data_array2->area_bus/1e6 << endl;
		  cout << "\t address bus area (mm2): "  << fr->data_array2->area_address_bus/1e6 << endl;
		  cout << "\t data bus area (mm2): "  << fr->data_array2->area_data_bus/1e6 << endl;
		  cout << "\t data driver area (mm2): "  << fr->data_array2->area_data_drv/1e6 << endl;
		  cout << "\t IO secondary sense amp area (mm2): "  << fr->data_array2->area_IOSA/1e6 << endl;
		  cout << "\t TSV area (mm2): "<< fr->data_array2->area_TSV_tot /1e6 << endl;

	  }
	  else //if (!g_ip->is_3d_mem)
	  {
	  if (g_ip->power_gating)
	  {
		  /* Energy/Power stats */
		  cout << endl << endl << "Power-gating Components:" << endl << endl;
		  /* Data array power-gating stats */
		  if (!(g_ip->pure_cam || g_ip->fully_assoc))
			  cout <<  "  Data array: " << endl;
		  else if (g_ip->pure_cam)
			  cout <<  "  CAM array: " << endl;
		  else
			  cout <<  "  Fully associative cache array: " << endl;

		  cout <<  "\t Sub-array Sleep Tx size (um) - " <<
		  fr->data_array2->sram_sleep_tx_width << endl;

		  //    cout <<  "\t Sub-array Sleep Tx total size (um) - " <<
		  //      fr->data_array2->sram_sleep_tx_width << endl;

		  cout <<  "\t Sub-array Sleep Tx total area (mm^2) - " <<
		  fr->data_array2->sram_sleep_tx_area*1e-6 << endl;

		  cout <<  "\t Sub-array wakeup time (ns) - " <<
		  fr->data_array2->sram_sleep_wakeup_latency*1e9 << endl;

		  cout <<  "\t Sub-array Tx energy (nJ) - " <<
		  fr->data_array2->sram_sleep_wakeup_energy*1e9 << endl;
		  //+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
		  cout << endl;
		  cout <<  "\t WL Sleep Tx size (um) - " <<
		  fr->data_array2->wl_sleep_tx_width << endl;

		  //    cout <<  "\t WL Sleep total Tx size (um) - " <<
		  //      fr->data_array2->wl_sleep_tx_width << endl;

		  cout <<  "\t WL Sleep Tx total area (mm^2) - " <<
		  fr->data_array2->wl_sleep_tx_area*1e-6 << endl;

		  cout <<  "\t WL wakeup time (ns) - " <<
		  fr->data_array2->wl_sleep_wakeup_latency*1e9 << endl;

		  cout <<  "\t WL Tx energy (nJ) - " <<
		  fr->data_array2->wl_sleep_wakeup_energy*1e9 << endl;
		  //+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
		  cout << endl;
		  cout <<  "\t BL floating wakeup time (ns) - " <<
		  fr->data_array2->bl_floating_wakeup_latency*1e9 << endl;

		  cout <<  "\t BL floating Tx energy (nJ) - " <<
		  fr->data_array2->bl_floating_wakeup_energy*1e9 << endl;
		  //+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

		  cout << endl;

		  cout <<  "\t Active mats per access - " << fr->data_array2->num_active_mats<<endl;
		  cout <<  "\t Active subarrays per mat - " << fr->data_array2->num_submarray_mats<<endl;
		  cout << endl;
		  /* Tag array area stats */
		  if ((!(g_ip->pure_ram|| g_ip->pure_cam || g_ip->fully_assoc)) && !g_ip->is_main_mem)
		  {
			  cout <<  "  Tag array: " << endl;
			  cout <<  "\t Sub-array Sleep Tx size (um) - " <<
			  fr->tag_array2->sram_sleep_tx_width << endl;

			  //    cout <<  "\t Sub-array Sleep Tx total size (um) - " <<
			  //      fr->tag_array2->sram_sleep_tx_width << endl;

			  cout <<  "\t Sub-array Sleep Tx total area (mm^2) - " <<
			  fr->tag_array2->sram_sleep_tx_area*1e-6 << endl;

			  cout <<  "\t Sub-array wakeup time (ns) - " <<
			  fr->tag_array2->sram_sleep_wakeup_latency*1e9 << endl;

			  cout <<  "\t Sub-array Tx energy (nJ) - " <<
			  fr->tag_array2->sram_sleep_wakeup_energy*1e9 << endl;
			  //+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
			  cout << endl;
			  cout <<  "\t WL Sleep Tx size (um) - " <<
			  fr->tag_array2->wl_sleep_tx_width << endl;

			  //    cout <<  "\t WL Sleep total Tx size (um) - " <<
			  //      fr->tag_array2->wl_sleep_tx_width << endl;

			  cout <<  "\t WL Sleep Tx total area (mm^2) - " <<
			  fr->tag_array2->wl_sleep_tx_area*1e-6 << endl;

			  cout <<  "\t WL wakeup time (ns) - " <<
			  fr->tag_array2->wl_sleep_wakeup_latency*1e9 << endl;

			  cout <<  "\t WL Tx energy (nJ) - " <<
			  fr->tag_array2->wl_sleep_wakeup_energy*1e9 << endl;
			  //+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
			  cout << endl;
			  cout <<  "\t BL floating wakeup time (ns) - " <<
			  fr->tag_array2->bl_floating_wakeup_latency*1e9 << endl;

			  cout <<  "\t BL floating Tx energy (nJ) - " <<
			  fr->tag_array2->bl_floating_wakeup_energy*1e9 << endl;
			  //+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
			  cout << endl;

			  cout <<  "\t Active mats per access - " << fr->tag_array2->num_active_mats<<endl;
			  cout <<  "\t Active subarrays per mat - " << fr->tag_array2->num_submarray_mats<<endl;
			  cout << endl;
		  }
	  }

    /* Delay stats */
    /* data array stats */
    cout << endl << "Time Components:" << endl << endl;

    cout << "  Data side (with Output driver) (ns): " <<
      fr->data_array2->access_time/1e-9 << endl;

    cout <<  "\tH-tree input delay (ns): " <<
      fr->data_array2->delay_route_to_bank * 1e9 +
      fr->data_array2->delay_input_htree * 1e9 << endl;

    if (!(g_ip->pure_cam || g_ip->fully_assoc))
    {
      cout <<  "\tDecoder + wordline delay (ns): " <<
        fr->data_array2->delay_row_predecode_driver_and_block * 1e9 +
        fr->data_array2->delay_row_decoder * 1e9 << endl;
    }
    else
    {
        cout <<  "\tCAM search delay (ns): " <<
          fr->data_array2->delay_matchlines * 1e9 << endl;
    }

    cout <<  "\tBitline delay (ns): " <<
      fr->data_array2->delay_bitlines/1e-9 << endl;

    cout <<  "\tSense Amplifier delay (ns): " <<
      fr->data_array2->delay_sense_amp * 1e9 << endl;


    cout <<  "\tH-tree output delay (ns): " <<
      fr->data_array2->delay_subarray_output_driver * 1e9 +
      fr->data_array2->delay_dout_htree * 1e9 << endl;

    if ((!(g_ip->pure_ram|| g_ip->pure_cam || g_ip->fully_assoc)) && !g_ip->is_main_mem)
    {
      /* tag array stats */
      cout << endl << "  Tag side (with Output driver) (ns): " <<
        fr->tag_array2->access_time/1e-9 << endl;

      cout <<  "\tH-tree input delay (ns): " <<
        fr->tag_array2->delay_route_to_bank * 1e9 +
        fr->tag_array2->delay_input_htree * 1e9 << endl;

      cout <<  "\tDecoder + wordline delay (ns): " <<
        fr->tag_array2->delay_row_predecode_driver_and_block * 1e9 +
        fr->tag_array2->delay_row_decoder * 1e9 << endl;

      cout <<  "\tBitline delay (ns): " <<
        fr->tag_array2->delay_bitlines/1e-9 << endl;

      cout <<  "\tSense Amplifier delay (ns): " <<
        fr->tag_array2->delay_sense_amp * 1e9 << endl;

      cout <<  "\tComparator delay (ns): " <<
        fr->tag_array2->delay_comparator * 1e9 << endl;

      cout <<  "\tH-tree output delay (ns): " <<
        fr->tag_array2->delay_subarray_output_driver * 1e9 +
        fr->tag_array2->delay_dout_htree * 1e9 << endl;
    }



    /* Energy/Power stats */
    cout << endl << endl << "Power Components:" << endl << endl;

    if (!(g_ip->pure_cam || g_ip->fully_assoc))
    {
    	cout << "  Data array: Total dynamic read energy/access  (nJ): " <<
    	      fr->data_array2->power.readOp.dynamic * 1e9 << endl;

    	cout << "\tTotal energy in H-tree (that includes both "
    	      "address and data transfer) (nJ): " <<
    	        (fr->data_array2->power_addr_input_htree.readOp.dynamic +
    	         fr->data_array2->power_data_output_htree.readOp.dynamic +
    	         fr->data_array2->power_routing_to_bank.readOp.dynamic) * 1e9 << endl;

    	cout << "\tOutput Htree inside bank Energy (nJ): " <<
    	   fr->data_array2->power_data_output_htree.readOp.dynamic * 1e9 << endl;
    	cout <<  "\tDecoder (nJ): " <<
    	   fr->data_array2->power_row_predecoder_drivers.readOp.dynamic * 1e9 +
    	   fr->data_array2->power_row_predecoder_blocks.readOp.dynamic * 1e9 << endl;
    	cout <<  "\tWordline (nJ): " <<
    	   fr->data_array2->power_row_decoders.readOp.dynamic * 1e9 << endl;
    	cout <<  "\tBitline mux & associated drivers (nJ): " <<
    	   fr->data_array2->power_bit_mux_predecoder_drivers.readOp.dynamic * 1e9 +
    	   fr->data_array2->power_bit_mux_predecoder_blocks.readOp.dynamic * 1e9 +
    	   fr->data_array2->power_bit_mux_decoders.readOp.dynamic * 1e9 << endl;
    	cout <<  "\tSense amp mux & associated drivers (nJ): " <<
    	   fr->data_array2->power_senseamp_mux_lev_1_predecoder_drivers.readOp.dynamic * 1e9 +
    	   fr->data_array2->power_senseamp_mux_lev_1_predecoder_blocks.readOp.dynamic * 1e9 +
    	   fr->data_array2->power_senseamp_mux_lev_1_decoders.readOp.dynamic * 1e9  +
    	   fr->data_array2->power_senseamp_mux_lev_2_predecoder_drivers.readOp.dynamic * 1e9 +
    	   fr->data_array2->power_senseamp_mux_lev_2_predecoder_blocks.readOp.dynamic * 1e9 +
    	   fr->data_array2->power_senseamp_mux_lev_2_decoders.readOp.dynamic * 1e9 << endl;

    	cout <<  "\tBitlines precharge and equalization circuit (nJ): " <<
    	    	   fr->data_array2->power_prechg_eq_drivers.readOp.dynamic * 1e9 << endl;
    	cout <<  "\tBitlines (nJ): " <<
    	   fr->data_array2->power_bitlines.readOp.dynamic * 1e9 << endl;
    	cout <<  "\tSense amplifier energy (nJ): " <<
    	   fr->data_array2->power_sense_amps.readOp.dynamic * 1e9 << endl;
    	cout <<  "\tSub-array output driver (nJ): " <<
    	   fr->data_array2->power_output_drivers_at_subarray.readOp.dynamic * 1e9 << endl;

    	cout << "\tTotal leakage power of a bank (mW): " <<
    	        fr->data_array2->power.readOp.leakage * 1e3 << endl;
    	cout << "\tTotal leakage power in H-tree (that includes both "
    	      "address and data network) ((mW)): " <<
    	        (fr->data_array2->power_addr_input_htree.readOp.leakage +
    	         fr->data_array2->power_data_output_htree.readOp.leakage +
    	         fr->data_array2->power_routing_to_bank.readOp.leakage) * 1e3 << endl;

    	cout << "\tTotal leakage power in cells (mW): " <<
    	        (fr->data_array2->array_leakage) * 1e3 << endl;
    	cout << "\tTotal leakage power in row logic(mW): " <<
    	        (fr->data_array2->wl_leakage) * 1e3 << endl;
    	cout << "\tTotal leakage power in column logic(mW): " <<
    	        (fr->data_array2->cl_leakage) * 1e3 << endl;

    	cout << "\tTotal gate leakage power in H-tree (that includes both "
    	      "address and data network) ((mW)): " <<
    	        (fr->data_array2->power_addr_input_htree.readOp.gate_leakage +
    	         fr->data_array2->power_data_output_htree.readOp.gate_leakage +
    	         fr->data_array2->power_routing_to_bank.readOp.gate_leakage) * 1e3 << endl;
    }

        else if (g_ip->pure_cam)
        {

           	cout << "  CAM array:"<<endl;
            	cout << "  Total dynamic associative search energy/access  (nJ): " <<
                      fr->data_array2->power.searchOp.dynamic * 1e9 << endl;
    	        cout << "\tTotal energy in H-tree (that includes both "
    	            	      "match key and data transfer) (nJ): " <<
    	              (fr->data_array2->power_htree_in_search.searchOp.dynamic +
    	               fr->data_array2->power_htree_out_search.searchOp.dynamic +
    	               fr->data_array2->power_routing_to_bank.searchOp.dynamic) * 1e9 << endl;
    	        cout << "\tKeyword input and result output Htrees inside bank Energy (nJ): " <<
    	              (fr->data_array2->power_htree_in_search.searchOp.dynamic +
    	       	               fr->data_array2->power_htree_out_search.searchOp.dynamic) * 1e9 << endl;
    	        cout <<  "\tSearchlines (nJ): " <<
    	          	   fr->data_array2->power_searchline.searchOp.dynamic * 1e9 +
    	          	   fr->data_array2->power_searchline_precharge.searchOp.dynamic * 1e9 << endl;
    	        cout <<  "\tMatchlines  (nJ): " <<
    	               fr->data_array2->power_matchlines.searchOp.dynamic * 1e9 +
    	        	   fr->data_array2->power_matchline_precharge.searchOp.dynamic * 1e9 << endl;
    	        cout <<  "\tSub-array output driver (nJ): " <<
    	          	   fr->data_array2->power_output_drivers_at_subarray.searchOp.dynamic * 1e9 << endl;


            	cout <<endl<< "  Total dynamic read energy/access  (nJ): " <<
            	      fr->data_array2->power.readOp.dynamic * 1e9 << endl;
    	        cout << "\tTotal energy in H-tree (that includes both "
    	            	      "address and data transfer) (nJ): " <<
    	              (fr->data_array2->power_addr_input_htree.readOp.dynamic +
    	               fr->data_array2->power_data_output_htree.readOp.dynamic +
    	               fr->data_array2->power_routing_to_bank.readOp.dynamic) * 1e9 << endl;
    	        cout << "\tOutput Htree inside bank Energy (nJ): " <<
    	          	   fr->data_array2->power_data_output_htree.readOp.dynamic * 1e9 << endl;
    	        cout <<  "\tDecoder (nJ): " <<
    	          	   fr->data_array2->power_row_predecoder_drivers.readOp.dynamic * 1e9 +
    	          	   fr->data_array2->power_row_predecoder_blocks.readOp.dynamic * 1e9 << endl;
    	        cout <<  "\tWordline (nJ): " <<
    	          	   fr->data_array2->power_row_decoders.readOp.dynamic * 1e9 << endl;
    	        cout <<  "\tBitline mux & associated drivers (nJ): " <<
    	          	   fr->data_array2->power_bit_mux_predecoder_drivers.readOp.dynamic * 1e9 +
    	          	   fr->data_array2->power_bit_mux_predecoder_blocks.readOp.dynamic * 1e9 +
    	           	   fr->data_array2->power_bit_mux_decoders.readOp.dynamic * 1e9 << endl;
    	        cout <<  "\tSense amp mux & associated drivers (nJ): " <<
    	         	   fr->data_array2->power_senseamp_mux_lev_1_predecoder_drivers.readOp.dynamic * 1e9 +
    	          	   fr->data_array2->power_senseamp_mux_lev_1_predecoder_blocks.readOp.dynamic * 1e9 +
    	          	   fr->data_array2->power_senseamp_mux_lev_1_decoders.readOp.dynamic * 1e9  +
    	           	   fr->data_array2->power_senseamp_mux_lev_2_predecoder_drivers.readOp.dynamic * 1e9 +
    	           	   fr->data_array2->power_senseamp_mux_lev_2_predecoder_blocks.readOp.dynamic * 1e9 +
    	          	   fr->data_array2->power_senseamp_mux_lev_2_decoders.readOp.dynamic * 1e9 << endl;
    	        cout <<  "\tBitlines (nJ): " <<
    	          	   fr->data_array2->power_bitlines.readOp.dynamic * 1e9 +
    	          	   fr->data_array2->power_prechg_eq_drivers.readOp.dynamic * 1e9<< endl;
    	        cout <<  "\tSense amplifier energy (nJ): " <<
    	          	   fr->data_array2->power_sense_amps.readOp.dynamic * 1e9 << endl;
    	        cout <<  "\tSub-array output driver (nJ): " <<
    	          	   fr->data_array2->power_output_drivers_at_subarray.readOp.dynamic * 1e9 << endl;

            	cout << endl <<"  Total leakage power of a bank (mW): " <<
                      fr->data_array2->power.readOp.leakage * 1e3 << endl;
        }
        else
        {
        	cout << "  Fully associative array:"<<endl;
        	cout << "  Total dynamic associative search energy/access  (nJ): " <<
                  fr->data_array2->power.searchOp.dynamic * 1e9 << endl;
	        cout << "\tTotal energy in H-tree (that includes both "
	            	      "match key and data transfer) (nJ): " <<
	              (fr->data_array2->power_htree_in_search.searchOp.dynamic +
	               fr->data_array2->power_htree_out_search.searchOp.dynamic +
	               fr->data_array2->power_routing_to_bank.searchOp.dynamic) * 1e9 << endl;
	        cout << "\tKeyword input and result output Htrees inside bank Energy (nJ): " <<
	              (fr->data_array2->power_htree_in_search.searchOp.dynamic +
	       	               fr->data_array2->power_htree_out_search.searchOp.dynamic) * 1e9 << endl;
	        cout <<  "\tSearchlines (nJ): " <<
	          	   fr->data_array2->power_searchline.searchOp.dynamic * 1e9 +
	          	   fr->data_array2->power_searchline_precharge.searchOp.dynamic * 1e9 << endl;
	        cout <<  "\tMatchlines  (nJ): " <<
	               fr->data_array2->power_matchlines.searchOp.dynamic * 1e9 +
	        	   fr->data_array2->power_matchline_precharge.searchOp.dynamic * 1e9 << endl;
	        cout <<  "\tData portion wordline (nJ): " <<
	          	   fr->data_array2->power_matchline_to_wordline_drv.searchOp.dynamic * 1e9 << endl;
	        cout <<  "\tData Bitlines (nJ): " <<
	          	   fr->data_array2->power_bitlines.searchOp.dynamic * 1e9 +
	          	   fr->data_array2->power_prechg_eq_drivers.searchOp.dynamic * 1e9 << endl;
	        cout <<  "\tSense amplifier energy (nJ): " <<
	          	   fr->data_array2->power_sense_amps.searchOp.dynamic * 1e9 << endl;
	        cout <<  "\tSub-array output driver (nJ): " <<
	          	   fr->data_array2->power_output_drivers_at_subarray.searchOp.dynamic * 1e9 << endl;


        	cout <<endl<< "  Total dynamic read energy/access  (nJ): " <<
        	      fr->data_array2->power.readOp.dynamic * 1e9 << endl;
	        cout << "\tTotal energy in H-tree (that includes both "
	            	      "address and data transfer) (nJ): " <<
	              (fr->data_array2->power_addr_input_htree.readOp.dynamic +
	               fr->data_array2->power_data_output_htree.readOp.dynamic +
	               fr->data_array2->power_routing_to_bank.readOp.dynamic) * 1e9 << endl;
	        cout << "\tOutput Htree inside bank Energy (nJ): " <<
	          	   fr->data_array2->power_data_output_htree.readOp.dynamic * 1e9 << endl;
	        cout <<  "\tDecoder (nJ): " <<
	          	   fr->data_array2->power_row_predecoder_drivers.readOp.dynamic * 1e9 +
	          	   fr->data_array2->power_row_predecoder_blocks.readOp.dynamic * 1e9 << endl;
	        cout <<  "\tWordline (nJ): " <<
	          	   fr->data_array2->power_row_decoders.readOp.dynamic * 1e9 << endl;
	        cout <<  "\tBitline mux & associated drivers (nJ): " <<
	          	   fr->data_array2->power_bit_mux_predecoder_drivers.readOp.dynamic * 1e9 +
	          	   fr->data_array2->power_bit_mux_predecoder_blocks.readOp.dynamic * 1e9 +
	           	   fr->data_array2->power_bit_mux_decoders.readOp.dynamic * 1e9 << endl;
	        cout <<  "\tSense amp mux & associated drivers (nJ): " <<
	         	   fr->data_array2->power_senseamp_mux_lev_1_predecoder_drivers.readOp.dynamic * 1e9 +
	          	   fr->data_array2->power_senseamp_mux_lev_1_predecoder_blocks.readOp.dynamic * 1e9 +
	          	   fr->data_array2->power_senseamp_mux_lev_1_decoders.readOp.dynamic * 1e9  +
	           	   fr->data_array2->power_senseamp_mux_lev_2_predecoder_drivers.readOp.dynamic * 1e9 +
	           	   fr->data_array2->power_senseamp_mux_lev_2_predecoder_blocks.readOp.dynamic * 1e9 +
	          	   fr->data_array2->power_senseamp_mux_lev_2_decoders.readOp.dynamic * 1e9 << endl;
	        cout <<  "\tBitlines (nJ): " <<
	          	   fr->data_array2->power_bitlines.readOp.dynamic * 1e9 +
	          	   fr->data_array2->power_prechg_eq_drivers.readOp.dynamic * 1e9<< endl;
	        cout <<  "\tSense amplifier energy (nJ): " <<
	          	   fr->data_array2->power_sense_amps.readOp.dynamic * 1e9 << endl;
	        cout <<  "\tSub-array output driver (nJ): " <<
	          	   fr->data_array2->power_output_drivers_at_subarray.readOp.dynamic * 1e9 << endl;

        	cout << endl <<"  Total leakage power of a bank (mW): " <<
                  fr->data_array2->power.readOp.leakage * 1e3 << endl;
      }


    if ((!(g_ip->pure_ram|| g_ip->pure_cam || g_ip->fully_assoc)) && !g_ip->is_main_mem)
    {
      cout << endl << "  Tag array:  Total dynamic read energy/access (nJ): " <<
        fr->tag_array2->power.readOp.dynamic * 1e9 << endl;
      cout << "\tTotal leakage read/write power of a bank (mW): " <<
          fr->tag_array2->power.readOp.leakage * 1e3 << endl;
      cout << "\tTotal energy in H-tree (that includes both "
        "address and data transfer) (nJ): " <<
          (fr->tag_array2->power_addr_input_htree.readOp.dynamic +
           fr->tag_array2->power_data_output_htree.readOp.dynamic +
           fr->tag_array2->power_routing_to_bank.readOp.dynamic) * 1e9 << endl;

      cout << "\tOutput Htree inside a bank Energy (nJ): " <<
        fr->tag_array2->power_data_output_htree.readOp.dynamic * 1e9 << endl;
      cout <<  "\tDecoder (nJ): " <<
        fr->tag_array2->power_row_predecoder_drivers.readOp.dynamic * 1e9 +
        fr->tag_array2->power_row_predecoder_blocks.readOp.dynamic * 1e9 << endl;
      cout <<  "\tWordline (nJ): " <<
        fr->tag_array2->power_row_decoders.readOp.dynamic * 1e9 << endl;
      cout <<  "\tBitline mux & associated drivers (nJ): " <<
        fr->tag_array2->power_bit_mux_predecoder_drivers.readOp.dynamic * 1e9 +
        fr->tag_array2->power_bit_mux_predecoder_blocks.readOp.dynamic * 1e9 +
        fr->tag_array2->power_bit_mux_decoders.readOp.dynamic * 1e9 << endl;
      cout <<  "\tSense amp mux & associated drivers (nJ): " <<
        fr->tag_array2->power_senseamp_mux_lev_1_predecoder_drivers.readOp.dynamic * 1e9 +
        fr->tag_array2->power_senseamp_mux_lev_1_predecoder_blocks.readOp.dynamic * 1e9 +
        fr->tag_array2->power_senseamp_mux_lev_1_decoders.readOp.dynamic * 1e9  +
        fr->tag_array2->power_senseamp_mux_lev_2_predecoder_drivers.readOp.dynamic * 1e9 +
        fr->tag_array2->power_senseamp_mux_lev_2_predecoder_blocks.readOp.dynamic * 1e9 +
        fr->tag_array2->power_senseamp_mux_lev_2_decoders.readOp.dynamic * 1e9 << endl;
      cout <<  "\tBitlines precharge and equalization circuit (nJ): " <<
        fr->tag_array2->power_prechg_eq_drivers.readOp.dynamic * 1e9 << endl;
      cout <<  "\tBitlines (nJ): " <<
        fr->tag_array2->power_bitlines.readOp.dynamic * 1e9 << endl;
      cout <<  "\tSense amplifier energy (nJ): " <<
        fr->tag_array2->power_sense_amps.readOp.dynamic * 1e9 << endl;
      cout <<  "\tSub-array output driver (nJ): " <<
        fr->tag_array2->power_output_drivers_at_subarray.readOp.dynamic * 1e9 << endl;

    	cout << "\tTotal leakage power of a bank (mW): " <<
    	        fr->tag_array2->power.readOp.leakage * 1e3 << endl;
    	cout << "\tTotal leakage power in H-tree (that includes both "
    	      "address and data network) ((mW)): " <<
    	        (fr->tag_array2->power_addr_input_htree.readOp.leakage +
    	         fr->tag_array2->power_data_output_htree.readOp.leakage +
    	         fr->tag_array2->power_routing_to_bank.readOp.leakage) * 1e3 << endl;

    	cout << "\tTotal leakage power in cells (mW): " <<
    	        (fr->tag_array2->array_leakage) * 1e3 << endl;
    	cout << "\tTotal leakage power in row logic(mW): " <<
    	        (fr->tag_array2->wl_leakage) * 1e3 << endl;
    	cout << "\tTotal leakage power in column logic(mW): " <<
    	        (fr->tag_array2->cl_leakage) * 1e3 << endl;
    	cout << "\tTotal gate leakage power in H-tree (that includes both "
    	      "address and data network) ((mW)): " <<
    	        (fr->tag_array2->power_addr_input_htree.readOp.gate_leakage +
    	         fr->tag_array2->power_data_output_htree.readOp.gate_leakage +
    	         fr->tag_array2->power_routing_to_bank.readOp.gate_leakage) * 1e3 << endl;
    }

    cout << endl << endl <<  "Area Components:" << endl << endl;
    /* Data array area stats */
    if (!(g_ip->pure_cam || g_ip->fully_assoc))
    	cout <<  "  Data array: Area (mm2): " << fr->data_array2->area * 1e-6 << endl;
    else if (g_ip->pure_cam)
    	cout <<  "  CAM array: Area (mm2): " << fr->data_array2->area * 1e-6 << endl;
    else
    	cout <<  "  Fully associative cache array: Area (mm2): " << fr->data_array2->area * 1e-6 << endl;
    cout <<  "\tHeight (mm): " <<
      fr->data_array2->all_banks_height*1e-3 << endl;
    cout <<  "\tWidth (mm): " <<
      fr->data_array2->all_banks_width*1e-3 << endl;
    if (g_ip->print_detail) {
      cout <<  "\tArea efficiency (Memory cell area/Total area) - " <<
        fr->data_array2->area_efficiency << " %" << endl;
      cout << "\t\tMAT Height (mm): " <<
        fr->data_array2->mat_height*1e-3 << endl;
      cout << "\t\tMAT Length (mm): " <<
        fr->data_array2->mat_length*1e-3 << endl;
      cout << "\t\tSubarray Height (mm): " <<
        fr->data_array2->subarray_height*1e-3 << endl;
      cout << "\t\tSubarray Length (mm): " <<
        fr->data_array2->subarray_length*1e-3 << endl;
    }

    /* Tag array area stats */
    if ((!(g_ip->pure_ram|| g_ip->pure_cam || g_ip->fully_assoc)) && !g_ip->is_main_mem)
    {
      cout << endl << "  Tag array: Area (mm2): " << fr->tag_array2->area * 1e-6 << endl;
      cout <<  "\tHeight (mm): " <<
        fr->tag_array2->all_banks_height*1e-3 << endl;
      cout <<  "\tWidth (mm): " <<
        fr->tag_array2->all_banks_width*1e-3 << endl;
      if (g_ip->print_detail)
      {
        cout <<  "\tArea efficiency (Memory cell area/Total area) - " <<
          fr->tag_array2->area_efficiency << " %" << endl;
      cout << "\t\tMAT Height (mm): " <<
        fr->tag_array2->mat_height*1e-3 << endl;
      cout << "\t\tMAT Length (mm): " <<
        fr->tag_array2->mat_length*1e-3 << endl;
      cout << "\t\tSubarray Height (mm): " <<
        fr->tag_array2->subarray_height*1e-3 << endl;
      cout << "\t\tSubarray Length (mm): " <<
        fr->tag_array2->subarray_length*1e-3 << endl;
      }
    }

	  }//if (!g_ip->is_3d_mem)



    Wire wpr;
    wpr.print_wire();

    //cout << "FO4 = " << g_tp.FO4 << endl;
  }
}
