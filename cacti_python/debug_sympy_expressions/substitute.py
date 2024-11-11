import os
import subprocess
import argparse
import sys
import logging
logger = logging.getLogger(__name__)

import yaml
import pandas as pd
import sympy as sp

from src import cacti_util
from src.cacti import CACTI_DIR, TRANSISTOR_SIZES

from src.cacti.cacti_python import parameter
from src.cacti.cacti_python.parameter import InputParameter
from src.cacti.cacti_python.Ucache import *
import src.cacti.cacti_python.get_dat as dat
import src.cacti.cacti_python.get_IO as IO
from collections import OrderedDict

def sub_values(cache_cfg, dat_file):
    """
    Generates absolute results from SymPy and Cacti, compares with C Cacti results, and writes to a CSV file.

    Inputs:
    sympy_file : str
        Path to the base SymPy expression file.
    cache_cfg : str
        Path to the cache configuration file.
    dat_file : str
        Path to the technology .dat file.

    Outputs:
    Logs and compares the results of SymPy expressions (access time, dynamic energy, leakage, IO properties) with C Cacti results.
    Results are appended to 'abs_validate_results.csv'.
    Returns the SymPy result and the C Cacti access time.
    """

    # print(f"top of gen_abs_results; sympy_file: {sympy_file}, cache_cfg: {cache_cfg}, dat_file: {dat_file}")

    # Get CACTI C results to verify
    # cfg_name = cache_cfg.replace(".cfg", "").replace("cfg/", "")
    # transistor_size = float(dat_file.split("/")[-1].split(".")[0][:-2])*1e-3
    # print(f"transistor size: {transistor_size}")
    # validate_vals = cacti_util.gen_vals(
    #     cfg_name,
    #     transistor_size=transistor_size,
    # )

    dat_file = os.path.join(CACTI_DIR, dat_file)

    g_ip = InputParameter()

    g_ip.parse_cfg(os.path.join(CACTI_DIR, cache_cfg))
    g_ip.error_checking()

    # get tech_param values
    tech_params = {}
    dat.scan_dat(tech_params, dat_file, g_ip.data_arr_ram_cell_tech_type, g_ip.data_arr_ram_cell_tech_type, g_ip.temp)
    tech_params = {k: (10**(-9) if v == 0 else v) for k, v in tech_params.items() if v is not None and not math.isnan(v)}

    # Prepare to process expressions in the current directory
    current_dir = os.path.dirname(__file__)
    # results = OrderedDict()  # Use OrderedDict to maintain insertion order

    # Clear or create the python_results.txt file
    output_file = os.path.join(current_dir, "python_results.txt")
    with open(output_file, "w") as f:
        pass  # Opens the file in write mode to clear it

    # Get list of .txt files (excluding this script and output file), sorted by creation date
    txt_files = [
        f for f in os.listdir(current_dir)
        if f.endswith(".txt") and f not in ["substitute.py", "python_results.txt", "python_results_copy.txt"]
    ]
    txt_files = sorted(txt_files, key=lambda f: os.path.getctime(os.path.join(current_dir, f)))

    # Process each file in order of creation date
    for sympy_file in txt_files:
        sympy_filename = os.path.join(current_dir, sympy_file)
        print(f"Substituting {sympy_filename}")

        # Read the expression and convert it to a sympy expression
        with open(sympy_filename, 'r') as file:
            expression_str = file.read()
        expression = sp.sympify(expression_str)
        print("Past sympify")

        # Substitute tech parameters and evaluate the expression
        result = expression.subs(tech_params)
        result_evaluated = result.subs(sp.I, 0).evalf()
        print("Past subs")

        # Write the evaluated result directly to the output file
        with open(output_file, "a") as f:
            f.write(f"{sympy_file.rstrip('.txt')}: {result_evaluated}\n")

def clear_txt_files():
    """Deletes all .txt files in the same directory as this script."""
    current_dir = os.path.dirname(__file__)  # Get the current directory of the script
    print(current_dir)
    import time
    time.sleep(2)
    # Iterate over all files in the directory
    for filename in os.listdir(current_dir):
        print(filename)
        # time.sleep(5)
        # Check if the file is a .txt file
        if filename.endswith(".txt"):
            file_path = os.path.join(current_dir, filename)
            os.remove(file_path)  # Delete the file
            print(f"Deleted: {file_path}")
    


if __name__ == "__main__":
    # clear_txt_files()
    sub_values("cfg/cache.cfg", "tech_params/90nm.dat")  