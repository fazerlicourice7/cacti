from parameter import g_ip
from parameter import g_tp
from cacti_interface import uca_org_t
from Ucache import *
from parameter import sympy_var

from mat import Mat
from bank import Bank
import pickle

if __name__ == "__main__":
    g_ip.parse_cfg("/Users/dw/Documents/codesign/cacti/cache.cfg")
    g_ip.display_ip()
    g_ip.error_checking()

    Ndwl = g_ip.ndwl
    Ndbl = g_ip.ndbl
    Ndcm = g_ip.ndcm

    Nspd = g_ip.nspd
    Ndsam_lev_1 = g_ip.ndsam1
    Ndsam_lev_2 = g_ip.ndsam2

    #   if g_ip.nspd != 0:
    #       Nspd = g_ip.nspd
    #   if g_ip.ndsam1 != 0:
    #       Ndsam_lev_1 = g_ip.ndsam1
    #       Ndsam_lev_2 = g_ip.ndsam2

    # FOR CAM
    # Ndwl = 1
    # Ndbl = 1

    #For DATA
    Ndwl = 2
    Ndbl = 2

    print(f"Ndwl = {Ndwl}, Ndbl = {Ndbl}, Ndcm = {Ndcm}, Nspd = {Nspd}, Ndsam_lev_1 = {Ndsam_lev_1}, Ndsam_lev_2 = {Ndsam_lev_2}")
    
    is_tag = False
    pure_ram = g_ip.pure_ram
    pure_cam = g_ip.pure_cam
    is_main_mem = g_ip.is_main_mem

    print(f"**is_tag = {is_tag}, pure_ram = {pure_ram}, pure_cam = {pure_cam}, is_main_mem = {is_main_mem}")

    wt = sp.symbols("wt")

    print("hello-1?")

    # g_tp.init(.022, is_tag)

    # print ("SETUP DYNAMIC PARAM")
    # dyn_p = DynamicParameter(is_tag, pure_ram, pure_cam, Nspd, Ndwl, Ndbl, Ndcm, Ndsam_lev_1, Ndsam_lev_2, wt, is_main_mem)

    # print("SETUP MAT")
    # mat = Mat(dyn_p)

    # with open('mat_instance_cache-1.pkl', 'wb') as f:
    #     pickle.dump(mat, f)

    # print(f'**delay_bitline: {mat.delay_bitline}')
    # print("SANITY CEHCK")
    # print(mat.delay_writeback)
    # print(mat.delay_sa)
    # print(mat.delay_subarray_out_drv)
    # print(mat.delay_comparator)

    # with open('mat_instance_cache-1.pkl', 'rb') as f:
    #     mat = pickle.load(f)

    # print(f"SANITY CHECK {mat.row_dec.nodes_DSTN}")
    # print(f"mat {mat.area.w}")
    # print(mat.delay_sa)
    # print(mat.delay_subarray_out_drv)
    # print(mat.delay_comparator)
    # print("HUHHH???????")

    # print("COMPUTE DELAYS")
    # mat.compute_delays(0)
    # print(f'num_rows {mat.subarray.num_rows}')

    # print(mat.delay_fa_tag)
    # print(mat.delay_cam)
    # print(mat.delay_before_decoder)
    # print(mat.delay_bitline)
    # print(mat.delay_wl_reset)
    # print(mat.delay_bl_restore)
    # print(mat.delay_searchline)
    # print(mat.delay_matchchline)
    # print(mat.delay_cam_sl_restore)
    # print(mat.delay_cam_ml_reset)
    # print(mat.delay_fa_ram_wl)
    # print(mat.delay_hit_miss_reset)
    # print(mat.delay_hit_miss)

    # print(mat.delay_writeback)
    # print(mat.delay_sa)
    # print(mat.delay_subarray_out_drv)
    # print(mat.delay_comparator)

    # print(f'**delay_fa_tag: {mat.delay_fa_tag}')
    # print(f'**delay_cam: {mat.delay_cam}')
    # print(f'**delay_before_decoder: {mat.delay_before_decoder}')

    # # #This printed
    # print(f'**delay_bitline: {mat.delay_bitline}')
    # print(f'**delay_wl_reset: {mat.delay_wl_reset}')
    # print(f'**delay_bl_restore: {mat.delay_bl_restore}')


    # # FOR CAM AND FA
    # print(f'**delay_searchline: {mat.delay_searchline}') #Doesn't do anyhting huh
    # print(f'**delay_matchchline: {mat.delay_matchchline}') # Only for cam
    # print(f'**delay_cam_sl_restore: {mat.delay_cam_sl_restore}')
    # print(f'**delay_cam_ml_reset: {mat.delay_cam_ml_reset}')
    # print(f'**delay_fa_ram_wl: {mat.delay_fa_ram_wl}')
    # print(f'**delay_hit_miss_reset: {mat.delay_hit_miss_reset}')
    # print(f'**delay_hit_miss: {mat.delay_hit_miss}')
    
    # print(f'**delay_writeback: {mat.delay_writeback}') # FOR DRAM

    # #This printed
    # print(f'**delay_sa: {mat.delay_sa}')
    # print(f'**delay_subarray_out_drv: {mat.delay_subarray_out_drv}')

    # print(f'**delay_comparator: {mat.delay_comparator}') #for tag and not FA

    # print(f"self.bank.mat.r_predec.delay: {mat.r_predec.delay}")
    # print(f"self.bank.mat.b_mux_predec.delay: {mat.b_mux_predec.delay}")
    # print(f"self.bank.mat.sa_mux_lev_1_predec.delay: {mat.sa_mux_lev_1_predec.delay}")
    # print(f"self.bank.mat.sa_mux_lev_2_predec.delay: {mat.sa_mux_lev_2_predec.delay}")

    # print(f"self.bank.mat.row_dec.delay: {mat.row_dec.delay}")

    ### END MAT

    # bank = Bank(dyn_p, mat)
    # print("Comptue bank")
    # print(bank.mat.r_predec.delay)
    # print(f"self.bank.mat.r_predec.delay: {bank.mat.r_predec.delay}")
    # print(f"self.bank.mat.b_mux_predec.delay: {bank.mat.b_mux_predec.delay}")
    # print(f"self.bank.mat.sa_mux_lev_1_predec.delay: {bank.mat.sa_mux_lev_1_predec.delay}")
    # print(f"self.bank.mat.sa_mux_lev_2_predec.delay: {bank.mat.sa_mux_lev_2_predec.delay}")

    # uca = UCA(dyn_p, bank)

    # with open('uca_cache.pkl', 'wb') as f:
    #     pickle.dump(uca, f)

    print("hello0?")
    with open('uca_cache.pkl', 'rb') as f:
        uca = pickle.load(f)    

    # print(uca.access_time)
    # print(f"power read: {uca.power.readOp.dynamic}")
    # print(f"energy read: {uca.read_energy}")
    # # bank.compute_delays(0)

    # print("DONE")

    fin_res = uca_org_t()
    print("hello1?")
    fin_res = solve_single(fin_res, uca)

    # diff_a = sp.diff(solve_single(fin_res), sympy_var["C_g_ideal"])
    # print(diff_a)
    with open('sympy_access_time.txt', 'w') as file:
        file.write(f"{fin_res.access_time}")

    print(fin_res.access_time)

    # g_tp.init(.022, False)

    # fin_res = uca_org_t()


