from parameter import g_ip
from parameter import g_tp
from cacti_interface import uca_org_t
from Ucache import *
from parameter import sympy_var

if __name__ == "__main__":
  g_ip.parse_cfg("/Users/dw/Documents/codesign/cacti/cache.cfg")
  g_ip.display_ip()
  g_ip.error_checking()

  fin_res = uca_org_t()

  diff_a = sp.diff(solve_single(fin_res), sympy_var["C_g_ideal"])
  print(diff_a)

  print(fin_res.access_time)

  # g_tp.init(.022, False)

  # fin_res = uca_org_t()



