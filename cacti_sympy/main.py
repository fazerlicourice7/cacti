from cacti_python.parameter import g_ip
from cacti_python.parameter import g_tp
from cacti_python.cacti_interface import uca_org_t
from cacti_python.Ucache import *
from cacti_python.parameter import sympy_var

from cacti_python.mat import Mat
from cacti_python.bank import Bank
import pickle

def cacti_gen_sympy(name, cache_cfg):
    g_ip.parse_cfg(cache_cfg)
    g_ip.error_checking()

    # make it so that cache cfg has Ndwl and Ndbl > 2
    g_ip.ndwl = 2
    g_ip.ndbl = 2

    fin_res = uca_org_t()
    fin_res = solve_single(fin_res)

    # diff_a = sp.diff(solve_single(fin_res), sympy_var["C_g_ideal"])
    # print(diff_a)
    with open(f'{name}.txt', 'w') as file:
        file.write(f"{fin_res.access_time}")

def validate(sympy_file, cfg_file, dat_file):
    return



