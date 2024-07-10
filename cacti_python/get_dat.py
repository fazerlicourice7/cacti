import re
from .const import *
tech_params = {}
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from hw_symbols import *

def scan_dat(tech_dict, dat_file, tech_flavor, cell_type, temperature):
    
    print_detail_debug = False
    try:
        with open(dat_file, "r") as fp:
            lines = fp.readlines()
    except FileNotFoundError:
        print(f"{dat_file} is missing!")
        exit(-1)

    for line in lines:
        if line.startswith("-Vdd"):
            tech_dict["Vdd"] = scan_five_input_double(line, "-Vdd", "V", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-vdd_cell"):
            scan_res = scan_five_input_double_mem_type(line, "-vdd_cell", "V", tech_flavor, cell_type, print_detail_debug)
            vdd_cell = scan_res
            continue
        if line.startswith("-Wmemcella"):
            scan_res = scan_five_input_double_mem_type(line, "-Wmemcella", "V", tech_flavor, cell_type, print_detail_debug)
            tech_dict["Wmemcella"] = scan_res if scan_res != None else tech_dict.get("Wmemcella")
            continue
        if line.startswith("-Wmemcellpmos"):
            scan_res = scan_five_input_double_mem_type(line, "-Wmemcellpmos", "V", tech_flavor, cell_type, print_detail_debug)
            tech_dict["Wmemcellpmos"] = scan_res if scan_res != None else tech_dict.get("Wmemcellpmos")
            continue
        if line.startswith("-Wmemcellnmos"):
            scan_res = scan_five_input_double_mem_type(line, "-Wmemcellnmos", "V", tech_flavor, cell_type, print_detail_debug)
            tech_dict["Wmemcellnmos"] = scan_res if scan_res != None else tech_dict.get("Wmemcellnmos")
            continue
        if line.startswith("-area_cell"):
            scan_res = scan_five_input_double_mem_type(line, "-area_cell", "V", tech_flavor, cell_type, print_detail_debug)
            tech_dict["area_cell"] = scan_res if scan_res != None else tech_dict.get("area_cell")
            continue
        if line.startswith("-asp_ratio_cell"):
            scan_res = scan_five_input_double_mem_type(line, "-asp_ratio_cell", "V", tech_flavor, cell_type, print_detail_debug)
            tech_dict["asp_ratio_cell"] = scan_res if scan_res != None else tech_dict.get("asp_ratio_cell")
            continue

        ic_proj_type = 0
        tsv_type = 0
        if line.startswith("-tsv_pitch"):
            tech_dict["tsv_pitch"] = scan_input_double_tsv_type(line, "-tsv_pitch", "F/um", ic_proj_type, tsv_type, print_detail_debug)
        elif line.startswith("-tsv_diameter"):
            tech_dict["tsv_diameter"] = scan_input_double_tsv_type(line, "-tsv_diameter", "F/um", ic_proj_type, tsv_type, print_detail_debug)
        elif line.startswith("-tsv_length"):
            tech_dict["tsv_length"] = scan_input_double_tsv_type(line, "-tsv_length", "F/um", ic_proj_type, tsv_type, print_detail_debug)
        elif line.startswith("-tsv_dielec_thickness"):
            tech_dict["tsv_dielec_thickness"] = scan_input_double_tsv_type(line, "-tsv_dielec_thickness", "F/um", ic_proj_type, tsv_type, print_detail_debug)
        elif line.startswith("-tsv_contact_resistance"):
            tech_dict["tsv_contact_resistance"] = scan_input_double_tsv_type(line, "-tsv_contact_resistance", "F/um", ic_proj_type, tsv_type, print_detail_debug)
        elif line.startswith("-tsv_depletion_width"):
            tech_dict["tsv_depletion_width"] = scan_input_double_tsv_type(line, "-tsv_depletion_width", "F/um", ic_proj_type, tsv_type, print_detail_debug)
        elif line.startswith("-tsv_liner_dielectric_cons"):
            tech_dict["tsv_liner_dielectric_cons"] = scan_input_double_tsv_type(line, "-tsv_liner_dielectric_cons", "F/um", ic_proj_type, tsv_type, print_detail_debug)

        ram_cell_tech_type = 0
        if line.startswith("-dram_cell_I_on"):
            tech_dict["dram_cell_I_on"] = scan_five_input_double(line, "-dram_cell_I_on", "F/um", ram_cell_tech_type, print_detail_debug)
        elif line.startswith("-dram_cell_Vdd"):
            tech_dict["dram_cell_Vdd"] = scan_five_input_double(line, "-dram_cell_Vdd", "F/um", ram_cell_tech_type, print_detail_debug)
        elif line.startswith("-dram_cell_C"):
            tech_dict["dram_cell_C"] = scan_five_input_double(line, "-dram_cell_C", "F/um", ram_cell_tech_type, print_detail_debug)
        elif line.startswith("-dram_cell_I_off_worst_case_len_temp"):
            tech_dict["dram_cell_I_off_worst_case_len_temp"] = scan_five_input_double(line, "-dram_cell_I_off_worst_case_len_temp", "F/um", ram_cell_tech_type, print_detail_debug)
        elif line.startswith("-vpp"):
            tech_dict["vpp"] = scan_five_input_double(line, "-vpp", "F/um", ram_cell_tech_type, print_detail_debug)
        elif line.startswith("-sckt_co_eff"):
            tech_dict["sckt_co_eff"] = scan_single_input_double(line, "-sckt_co_eff", "F/um", print_detail_debug)
        elif line.startswith("-chip_layout_overhead"):
            tech_dict["chip_layout_overhead"] = scan_single_input_double(line, "-chip_layout_overhead", "F/um", print_detail_debug)
        elif line.startswith("-macro_layout_overhead"):
            tech_dict["macro_layout_overhead"] = scan_single_input_double(line, "-macro_layout_overhead", "F/um", print_detail_debug)

        if line.startswith("-sense_delay"):
            tech_dict["sense_delay"] = scan_single_input_double(line, "-sense_delay", "F/um", print_detail_debug)
        elif line.startswith("-sense_dy_power"):
            tech_dict["sense_dy_power"] = scan_single_input_double(line, "-sense_dy_power", "F/um", print_detail_debug)
        elif line.startswith("-sckt_co_eff"):
            tech_dict["sckt_co_eff"] = scan_single_input_double(line, "-sckt_co_eff", "F/um", print_detail_debug)
        elif line.startswith("-chip_layout_overhead"):
            tech_dict["chip_layout_overhead"] = scan_single_input_double(line, "-chip_layout_overhead", "F/um", print_detail_debug)
        elif line.startswith("-macro_layout_overhead"):
            tech_dict["macro_layout_overhead"] = scan_single_input_double(line, "-macro_layout_overhead", "F/um", print_detail_debug)
        elif line.startswith("-dram_cell_I_on"):
            tech_dict["dram_cell_I_on"] = scan_five_input_double(line, "-dram_cell_I_on", "F/um", ram_cell_tech_type, print_detail_debug)
        elif line.startswith("-dram_cell_Vdd"):
            tech_dict["dram_cell_Vdd"] = scan_five_input_double(line, "-dram_cell_Vdd", "F/um", ram_cell_tech_type, print_detail_debug)
        elif line.startswith("-dram_cell_C"):
            tech_dict["dram_cell_C"] = scan_five_input_double(line, "-dram_cell_C", "F/um", ram_cell_tech_type, print_detail_debug)
        elif line.startswith("-dram_cell_I_off_worst_case_len_temp"):
            tech_dict["dram_cell_I_off_worst_case_len_temp"] = scan_five_input_double(line, "-dram_cell_I_off_worst_case_len_temp", "F/um", ram_cell_tech_type, print_detail_debug)
        elif line.startswith("-vpp"):
            tech_dict["vpp"] = scan_five_input_double(line, "-vpp", "F/um", ram_cell_tech_type, print_detail_debug)

        if line.startswith("-C_g_ideal"):
            tech_dict["C_g_ideal"] = scan_five_input_double(line, "-C_g_ideal", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-C_fringe"):
            tech_dict["C_fringe"] = scan_five_input_double(line, "-C_fringe", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-C_junc_sw"):
            tech_dict["C_junc_sw"] = scan_five_input_double(line, "-C_junc_sw", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-C_junc"):
            tech_dict["C_junc"] = scan_five_input_double(line, "-C_junc", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-l_phy"):
            tech_dict["l_phy"] = scan_five_input_double(line, "-l_phy", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-l_elec"):
            tech_dict["l_elec"] = scan_five_input_double(line, "-l_elec", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-nmos_effective_resistance_multiplier"):
            tech_dict["nmos_effective_resistance_multiplier"] = scan_five_input_double(line, "-nmos_effective_resistance_multiplier", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-Vdd"):
            tech_dict["Vdd"] = scan_five_input_double(line, "-Vdd", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-Vth"):
            tech_dict["Vth"] = scan_five_input_double(line, "-Vth", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-Vdsat"):
            tech_dict["Vdsat"] = scan_five_input_double(line, "-Vdsat", "V", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-I_on_n"):
            tech_dict["I_on_n"] = scan_five_input_double(line, "-I_on_n", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-I_on_p"):
            tech_dict["I_on_p"] = scan_five_input_double(line, "-I_on_p", "F/um", tech_flavor, print_detail_debug)
            continue

        if line.startswith("-I_off_n"):
            tech_dict["I_off_n"] = scan_five_input_double_temperature(line, "-I_off_n", "F/um", tech_flavor, temperature, print_detail_debug, 0)
            continue
        if line.startswith("-I_g_on_n"):
            tech_dict["I_g_on_n"] = scan_five_input_double_temperature(line, "-I_g_on_n", "F/um", tech_flavor, temperature, print_detail_debug, 0)
            continue
        if line.startswith("-C_ox"):
            tech_dict["C_ox"] = scan_five_input_double(line, "-C_ox", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-t_ox"):
            tech_dict["t_ox"] = scan_five_input_double(line, "-t_ox", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-n2p_drv_rt"):
            tech_dict["n2p_drv_rt"] = scan_five_input_double(line, "-n2p_drv_rt", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-lch_lk_rdc"):
            tech_dict["lch_lk_rdc"] = scan_five_input_double(line, "-lch_lk_rdc", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-Mobility_n"):
            tech_dict["Mobility_n"] = scan_five_input_double(line, "-Mobility_n", "F/um", tech_flavor, print_detail_debug)
            continue
        if line.startswith("-gmp_to_gmn_multiplier"):
            tech_dict["gmp_to_gmn_multiplier"] = scan_five_input_double(line, "-gmp_to_gmn_multiplier", "F/um", tech_flavor, print_detail_debug)
            continue

        if line.startswith("-wire_pitch"):
            tech_dict["wire_pitch"] = scan_input_double_inter_type(line, "-wire_pitch", "um", ic_proj_type, tech_flavor, print_detail_debug)
            continue
        if line.startswith("-barrier_thickness"):
            tech_dict["barrier_thickness"] = scan_input_double_inter_type(line, "-barrier_thickness", "ohm", ic_proj_type, tech_flavor, print_detail_debug)
            continue
        if line.startswith("-dishing_thickness"):
            tech_dict["dishing_thickness"] = scan_input_double_inter_type(line, "-dishing_thickness", "um", ic_proj_type, tech_flavor, print_detail_debug)
            continue
        if line.startswith("-alpha_scatter"):
            tech_dict["alpha_scatter"] = scan_input_double_inter_type(line, "-alpha_scatter", "um", ic_proj_type, tech_flavor, print_detail_debug)
            continue
        if line.startswith("-aspect_ratio"):
            tech_dict["aspect_ratio"] = scan_input_double_inter_type(line, "-aspect_ratio", "um", ic_proj_type, tech_flavor, print_detail_debug)
            continue
        if line.startswith("-miller_value"):
            tech_dict["miller_value"] = scan_input_double_inter_type(line, "-miller_value", "um", ic_proj_type, tech_flavor, print_detail_debug)
            continue
        if line.startswith("-horiz_dielectric_constant"):
            tech_dict["horiz_dielectric_constant"] = scan_input_double_inter_type(line, "-horiz_dielectric_constant", "um", ic_proj_type, tech_flavor, print_detail_debug)
            continue
        if line.startswith("-vert_dielectric_constant"):
            tech_dict["vert_dielectric_constant"] = scan_input_double_inter_type(line, "-vert_dielectric_constant", "um", ic_proj_type, tech_flavor, print_detail_debug)
            continue
        if line.startswith("-ild_thickness"):
            tech_dict["ild_thickness"] = scan_input_double_inter_type(line, "-ild_thickness", "um", ic_proj_type, tech_flavor, print_detail_debug)
            continue
        if line.startswith("-fringe_cap"):
            tech_dict["fringe_cap"] = scan_input_double_inter_type(line, "-fringe_cap", "um", ic_proj_type, tech_flavor, print_detail_debug)
            continue
        if line.startswith("-wire_r_per_micron"):
            tech_dict["wire_r_per_micron"] = scan_input_double_inter_type(line, "-wire_r_per_micron", "um", ic_proj_type, tech_flavor, print_detail_debug)
            continue
        if line.startswith("-wire_c_per_micron"):
            tech_dict["wire_c_per_micron"] = scan_input_double_inter_type(line, "-wire_c_per_micron", "um", ic_proj_type, tech_flavor, print_detail_debug)
            continue
        if line.startswith("-resistivity"):
            tech_dict["resistivity"] = scan_input_double_inter_type(line, "-resistivity", "um", ic_proj_type, tech_flavor, print_detail_debug)
            continue

        if line.startswith("-logic_scaling_co_eff"):
            tech_dict["logic_scaling_co_eff"] = scan_single_input_double(line, "-logic_scaling_co_eff", "F/um", print_detail_debug)
            continue
        if line.startswith("-core_tx_density"):
            tech_dict["core_tx_density"] = scan_single_input_double(line, "-core_tx_density", "F/um", print_detail_debug)
            continue



def scan_single_input_double(line, name, unit_name, print_output):
    match = re.search(f"{name}\s+([^\s]+)\s+([^\s]+)", line)
    if match:
        unit = match.group(1)
        temp = float(match.group(2))
        if print_output:
            print(f"{name}: {temp} {unit}")
        return temp
    return 0.0

def scan_five_input_double(line, name, unit_name, flavor, print_output):
    match = re.search(f"{name}\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)", line)
    if match:
        unit = match.group(1)
        temp = [float(match.group(i)) for i in range(2, 7)]
        if print_output:
            print(f"{name}[{flavor}]: {temp[flavor]} {unit}")
        return temp[flavor]
    return 0.0

def scan_five_input_double_temperature(line, name, unit_name, flavor, temperature, print_output, result):
    match = re.search(f"{name}\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)", line)
    if match:
        unit = match.group(1)
        thermal_temp = int(match.group(2))
        temp = [float(match.group(i)) for i in range(3, 8)]
        if thermal_temp == (temperature - 300):
            if print_output:
                print(f"{name}: {temp[flavor]} {unit}")
            result = temp[flavor]
    return result

def scan_input_double_inter_type(line, name, unit_name, proj_type, tech_flavor, print_output):
    assert proj_type < NUMBER_INTERCONNECT_PROJECTION_TYPES
    index = proj_type * NUMBER_WIRE_TYPES + tech_flavor
    match = re.search(f"{name}\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)", line)
    if match:
        unit = match.group(1)
        temp = [float(match.group(i)) for i in range(2, 10)]
        if print_output:
            print(f"{name} {temp[index]} {unit}")
        return temp[index]
    return 0.0

def scan_five_input_double_mem_type(line, name, unit_name, flavor, cell_type, print_flag):
    temp = [0.0] * 5
    unit = ""
    
    # Extract the relevant part of the line
    relevant_line = line[len(name):].strip()

    # print(line)
    # print(relevant_line)
    
    # Scan the input line and extract values
    parts = relevant_line.split()
    # print(parts)
    # print(cell_type)
    
    unit = parts[0]
    cell_type_temp = int(parts[1])
    temp[0] = float(parts[2])
    temp[1] = float(parts[3])
    temp[2] = float(parts[4])
    temp[3] = float(parts[5])
    temp[4] = float(parts[6])
    
    result = None
    if cell_type_temp == cell_type:
        if print_flag:
            print(f"{name}: {temp[flavor]} {unit}")
        result = temp[flavor]
    
    return result

def scan_input_double_tsv_type(line, name, unit_name, proj_type, tsv_type, print_flag):
    assert proj_type < NUMBER_INTERCONNECT_PROJECTION_TYPES
    index = proj_type * NUMBER_TSV_TYPES + tsv_type
    temp = [0.0] * 6
    unit = ""
    
    # Extracting the values using regular expressions
    match = re.search(rf"{name}\s+(\S+)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)", line)
    
    if match:
        unit = match.group(1)
        temp[0] = float(match.group(2))
        temp[1] = float(match.group(3))
        temp[2] = float(match.group(4))
        temp[3] = float(match.group(5))
        temp[4] = float(match.group(6))
        temp[5] = float(match.group(7))
        
        if print_flag:
            print(f"{name}: {temp[index]} {unit}")
            
        return temp[index]
    else:
        raise ValueError("Line does not match the expected format")
    

if __name__ == "__main__" :
    file = "../tech_params/180nm.dat"
    scan_dat(tech_params, file, 0, 0, 360)
    print(tech_params)
