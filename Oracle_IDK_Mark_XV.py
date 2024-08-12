import random
import sys
from array import array
import math
import gymnasium as gym
env = gym.make('Pendulum-v1', g = 9.81, render_mode = "human")# 9.81
class Oracle:
    def __init__(self):
        self.H = 1#-----------------------------------------------------------------------------------------HP
        self.cy = 0
        ############################################################################################################################
        #_______________________________________________SETUP GYM DATA______________________________________________________________
        start_idx = 0
        self.run_continuous = False
        self.max_int = sys.maxsize# = 2**63 = 9.223372037E18
        self.env_seed = 123456
        truncated_val = 16.0#-----------------------------------------------------------------------------------------------------HP
        self.obs_indices = [0, 1, 2]#---------------------------------------------------------------------------------------------HP
        # self.obs_indices = [0, 1]#--------------------------------------------------------------------------------------------HP
        self.obs_range_l = [-truncated_val if (env.observation_space.low[a] == -math.inf)
                            else env.observation_space.low[a] for a in self.obs_indices]
        self.obs_range_h = [truncated_val if (env.observation_space.high[a] == math.inf)
                            else env.observation_space.high[a] for a in self.obs_indices]
        self.act_indices = [0]#------------------------------------------------------------------------------------------------HP
        self.act_range_l = [-truncated_val if (env.action_space.low[a] == -math.inf)
                            else env.action_space.low[a] for a in self.act_indices]
        self.act_range_h = [truncated_val if (env.action_space.high[a] == math.inf)
                            else env.action_space.high[a] for a in self.act_indices]
        # self.rew_range_l = -truncated_val if (env.reward_range[0] == -math.inf) else env.reward_range[0]
        # self.rew_range_h = truncated_val if (env.reward_range[1] == math.inf) else env.reward_range[1]
        self.rew_range_l = -16.2736044
        self.rew_range_h = 0
        self.rew_delta_range_l = (self.rew_range_l - self.rew_range_h)
        self.rew_delta_range_h = (self.rew_range_h - self.rew_range_l)
        self.rew_delta = self.episode_step_ct = self.cumul_rew = self.rew_prev = self.rew_metric = 0
        self.cumul_rew_delta_ct = 0
        self.cumul_rew_delta_period = 3
        self.cumul_rew_delta = 0
        ##############################################################################################################
        trc_card = 1#------------------------------------------------------------------------------------------------HP
        trc_num_values = 37#-----------------------------------------------------------------------------------------HP
        self.iv_trcs = []
        self.iv_mask = set()
        for a in self.obs_indices:
            trc = Transcoder(start_idx, self.obs_range_l[a], self.obs_range_h[a], trc_num_values, 1, trc_card, False)
            self.iv_mask |= trc.vec_set
            self.iv_trcs.append(trc)
            start_idx += len(trc.vec_set)
        self.bv_trc = Transcoder(start_idx, -2, 2, trc_num_values, 1, trc_card, False)
        self.bv_mask = self.bv_trc.vec_set.copy()
        start_idx += len(self.bv_mask)
        ##############################################################################################################
        # self.em_trc = Transcoder(start_idx, 0, 1, trc_num_values, 1, trc_card, False)
        # self.em_mask = self.em_trc.vec_set.copy()
        # start_idx += len(self.em_mask)
        ##############################################################################################################
        # self.rew_trc_A = Transcoder(start_idx, 0, 1, trc_num_values, 1, trc_card, False)#-----self.rew_metric
        # self.rew_mask_A = self.rew_trc_A.vec_set.copy()
        # start_idx += len(self.rew_mask_A)
        # self.rew_A_target_v = self.rew_trc_A.get_vector(1)
        # self.rew_A_target_v = set()
        # idx = -1
        # while len(self.rew_A_target_v) < 2:#-----------------------------------------------------------------HP
        #     self.rew_A_target_v |= set(self.rew_trc_A.sorted_vecs[idx])
        #     idx -= 1
        ##############################################################################################################
        # self.rew_trc_B = Transcoder(start_idx, -1, 1, trc_num_values, 1, trc_card, False)#---self.rew_delta
        # self.rew_mask_B = self.rew_trc_B.vec_set.copy()
        # start_idx += len(self.rew_mask_B)
        # self.rew_B_target_v = set()
        # for i, a in enumerate(self.rew_trc_B.sorted_vals):
        #     if (a > 0): self.rew_B_target_v |= set(self.rew_trc_B.sorted_vecs[i])
        ##############################################################################################################
        self.N = start_idx
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        env.reset(seed = self.env_seed)
        while True:
            for a in self.m: a.update()
            self.cy += 1
    def interface_env(self, val_in):
        obs, rew, ter, tru, inf = env.step(tuple([val_in]))
        if (ter or tru):
            if (not self.run_continuous):
                obs, inf = env.reset(seed = self.env_seed)
                # obs, inf = env.reset()
            # norm = (self.rew_range_l * max(self.episode_step_ct, 1))
            # self.rew_metric = (1.0 - (self.cumul_rew / norm))
            # self.cumul_rew = self.episode_step_ct = 0
            # self.rew_prev = rew
        if self.episode_step_ct == 1:#-------------------------------------------------------------------HP
            norm = (self.rew_range_l * max(self.episode_step_ct, 1))
            self.rew_metric = (1.0 - (self.cumul_rew / norm))
            self.cumul_rew = 0
            self.episode_step_ct = 0
        self.cumul_rew += rew
        self.episode_step_ct += 1
        self.rew_delta = ((rew - self.rew_prev) / -self.rew_range_l)
        self.rew_prev = rew
        # if self.cumul_rew_delta_ct == self.cumul_rew_delta_period:
        #     print(f"{self.cumul_rew_delta:.2f}")
        #     self.cumul_rew_delta = 0
        #     self.cumul_rew_delta_ct = 0
        # self.cumul_rew_delta += self.rew_delta
        # self.cumul_rew_delta_ct += 1
        eiv = set()
        for i, a in enumerate(obs):
            if (i in self.obs_indices): eiv |= self.iv_trcs[i].get_vector(a)
        return eiv.copy()
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.fbv = set()
        self.context_dim = 1#----------------------------------------------------------------------------HP
        self.M = (self.po.N * self.context_dim)
        self.exov = set()
        self.exov_prev = set()
        self.iv = set()
        self.iv_prev = set()
        self.ev = set()
        self.cv = set()
        self.pv = set()
        self.array_type_code = 'h'#-2 byte signed----------------------------------------------------------HP
        num_bytes = 2
        # self.array_type_code = 'b'#-1 byte signed----------------------------------------------------------HP
        # num_bytes = 1
        self.adc_max = 100#--------------------------------------------------------------------------------HP
        self.cv_max_card = 10000#----------------------------------------------------------------------------HP
        self.dv_mag_max = min(((2 ** ((num_bytes * 8) - 1)) - 1), round(self.po.max_int / self.cv_max_card))
        self.dv_mag_min = -(self.dv_mag_max - 1)
        self.mem_cap_max = 1000#----------------------------------------------------------------------------HP
        self.mem = dict()
        self.bv_mem_cap = 500#-----------------------------------------------------------------------------HP
        self.bv_mem = dict()
        self.em = self.em_prev = self.em_delta = self.num_gen = 0
        self.hist_depth = 1#-------------------------------------------------------------------------------HP
        self.hist = dict()
    def update(self):
        ####################################################################################################
        # self.fbv = self.po.m[self.fbi].pv.copy()#------------makes things worse?????
        self.fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        self.process_inference()#--------------------------------------------------------------HERE?????
        ####################################################################################################
        self.num_gen = 0
        self.iv_prev = self.iv.copy()
        self.exov_prev = self.exov.copy()
        if (self.ffi == -1):
            exov_raw = (self.pv & self.po.bv_mask)
            
            # num_ri = 1 if (random.randrange(1000000) < (100000 - round(100000 * self.po.rew_metric))) else 0
            num_ri = 1 if (len(exov_raw) == 0) else 0
            # num_ri = 0
            if num_ri > 0:
                rs = random.sample(list(self.po.bv_mask), num_ri)
                for a in rs:
                    if a in exov_raw: exov_raw.remove(a)
                    else: exov_raw.add(a)
            exov_prod = self.po.bv_trc.get_value(exov_raw)
            self.exov = exov_prod[1]
            self.iv = self.po.interface_env(exov_prod[0])
            # self.iv |= self.exov
            # rew_A_target_err_v = (self.po.rew_trc_A.get_vector(self.po.rew_metric) ^ self.po.rew_A_target_v)
            # rew_A_target_ove_v = (self.po.rew_trc_A.get_vector(self.po.rew_metric) & self.po.rew_A_target_v)
            # self.iv |= rew_A_target_err_v
            # rew_B_target_err_v = (self.po.rew_trc_B.get_vector(self.po.rew_delta) ^ self.po.rew_B_target_v)
            # rew_B_target_ove_v = (self.po.rew_trc_B.get_vector(self.po.rew_delta) & self.po.rew_B_target_v)
            # self.iv |= rew_B_target_err_v
            # self.iv |= self.po.rew_trc_B.get_vector(self.po.rew_delta)
            # card = self.po.bv_trc.card_val
            # rv = set(random.choice(list(self.po.bv_trc.sorted_vecs)))
            # while (len(rv & exov_raw) > 0): rv = set(random.choice(list(self.po.bv_trc.sorted_vecs)))
            # comb_err_v = (rew_A_target_err_v | rew_B_target_err_v)
            # comb_err_v = rew_B_target_err_v.copy()
            # wd_mod = len(comb_err_v)
            # print(len(comb_err_v))
            # self.hist[len(self.hist)] = [self.cv.copy(), exov_raw.copy(), self.po.rew_delta, self.po.rew_metric]
            self.hist[len(self.hist)] = [self.cv.copy(), self.exov.copy(), self.po.rew_delta, self.po.rew_metric]
            if (len(self.hist) == self.hist_depth):
                kA = 2000
                kB = 0
                for k, v in self.hist.items():
                    # wd_mod = round(kA * v[2] * (2 ** k))
                    wd_mod = round((kA * v[2] * (2 ** k)) + (kB * v[3]))
                    for a in v[0]:
                        if a not in self.mem:
                            self.mem[a] = [array(self.array_type_code, ([0] * self.M)), self.adc_max]
                            self.num_gen += 1
                        for b in v[1]:
                            val = (self.mem[a][0][b] + wd_mod)
                            if (val < self.dv_mag_min): val = self.dv_mag_min
                            if (val > self.dv_mag_max): val = self.dv_mag_max
                            self.mem[a][0][b] = val
                self.hist = dict()
                # for b in exov_raw: self.mem[a][0][b] = max(self.dv_mag_min, (self.mem[a][0][b] - 125))
                # for b in rv: self.mem[a][0][b] = min(self.dv_mag_max, (self.mem[a][0][b] + 10))
            # comb_ove_v = (rew_A_target_ove_v | rew_B_target_ove_v)
            # comb_ove_v = rew_B_target_ove_v.copy()
            # wd_mod = len(comb_ove_v)
            # for a in comb_ove_v:
            #     if a not in self.mem:
            #         self.mem[a] = [array(self.array_type_code, ([0] * self.M)), self.adc_max]
            #         self.num_gen += 1
                # for b in self.exov: self.mem[a][0][b] = min(self.dv_mag_max, (self.mem[a][0][b] + wd_mod))
                # for b in self.exov: self.mem[a][0][b] = min(self.dv_mag_max, (self.mem[a][0][b] + 70))
        # else: self.iv = self.po.m[self.ffi].ev.copy()
        else: self.iv = self.po.m[self.ffi].ev.copy()
        ####################################################################################################
        self.ev = (self.iv ^ self.pv)
        # self.ev -= self.fbv#----------------------------------------------------------------------?????
        self.em_prev = self.em
        self.em = (len(self.ev) / max(1, (len(self.iv) + len(self.pv))))
        self.em_delta = (self.em - self.em_prev)
        ####################################################################################################
        failed_pev = (self.iv - self.pv)
        false_pev = (self.pv - self.iv)
        wd = 1#------------------------------------------------------------------------------------------HP
        for a in self.cv:
            wd_mod = wd
            if (wd_mod != 0):
                for b in failed_pev: self.mem[a][0][b] = min(self.dv_mag_max, (self.mem[a][0][b] + wd_mod))
                for b in false_pev: self.mem[a][0][b] = max(self.dv_mag_min, (self.mem[a][0][b] - wd_mod))
        ####################################################################################################
        # self.process_inference()#---------------------------------------------------------------HERE?????
        print(f"M:{(self.ffi + 1)}  EM: {str(f'{self.em:.2f}').rjust(4)}  MEM: {str(len(self.mem)).rjust(3)}" +
              f"  NGEN: {str(self.num_gen).rjust(3)}  CV: {str(len(self.cv)).rjust(3)}" +
              f"  REW: {str(f'{self.po.rew_metric:.2f}').rjust(4)}")
    def process_inference(self):
        #############################################
        #---------------------------------------------------------------------------------WHICH FORMAT?????
        # fbv_mod = {-(a + 1) for a in self.fbv}
        offset = self.po.N
        fbv_offset = {(offset + a) for a in self.fbv}
        offset += self.po.N
        # pv_offset = {(offset + a) for a in self.pv}
        # offset += self.po.N
        # ev_offset = {(offset + a) for a in self.ev}
        # offset += self.po.N
        # iv_prev_offset = {(offset + a) for a in self.iv_prev}
        # offset += self.po.N
        self.cv = (self.iv | fbv_offset)
        # self.cv = (self.iv | iv_prev_offset | fbv_offset)
        # self.cv = (self.iv | ev_offset | fbv_mod)
        # self.cv = (self.iv | fbv_mod)
        ###########################################
        for a in self.cv:
            if a in self.mem: self.mem[a][1] = self.adc_max
            else:
                self.mem[a] = [array(self.array_type_code, ([0] * self.M)), self.adc_max]
                self.num_gen += 1
        diff = (len(self.mem) - self.mem_cap_max)
        if (diff > 0):
            pass
        #########################################
        # sum_v = array('l', ([0] * self.M))#-signed long type (4 bytes; 2**31 each side of 0)
        sum_v = ([0] * self.M)#-signed long long type (8 bytes; 2**63 each side of 0); system default
        for a in self.cv: sum_v = [(x + y) for x, y in zip(sum_v, self.mem[a][0])]
        self.pv = {i for i, a in enumerate(sum_v) if (a > 0)}
class Transcoder:
    def __init__(self, start_idx_in, min_val_in, max_val_in, num_values_in, enc_step_in, enc_card_in, cyclic_in = False):
        self.vec_set = set()
        self.sorted_vecs = []
        self.sorted_vals = []
        self.min_val = min_val_in
        self.max_val = max_val_in
        self.card_val = enc_card_in
        self.val_range = (self.max_val - self.min_val)
        self.norm = (num_values_in - 1)
        inc = (self.val_range / self.norm)
        if enc_step_in > self.card_val: enc_step_in = self.card_val
        if (cyclic_in and (self.card_val % 2 != 0)): self.card_val += 1
        limit_idx = (num_values_in * enc_step_in)
        for a in range(num_values_in):
            if cyclic_in: ts = [(start_idx_in + ((b + (a * enc_step_in)) % limit_idx)) for b in range(self.card_val)]
            else: ts = [(start_idx_in + (b + (a * enc_step_in))) for b in range(self.card_val)]
            self.vec_set |= set(ts)
            self.sorted_vecs.append(ts.copy())
            self.sorted_vals.append((self.min_val + (a * inc)))
        self.rsA = random.sample(range(num_values_in), num_values_in)
    def get_value(self, vector_in):
        d = [(len(set(k) ^ vector_in), i, set(k)) for i, k in enumerate(self.sorted_vecs)]
        rs = self.rsA.copy()
        # rs = random.sample(range(len(d)), len(d))
        ds = sorted(d, key = lambda x: (x[0], rs.pop()))
        return (self.sorted_vals[ds[0][1]], ds[0][2].copy())
    def get_vector(self, value_in):
        d = [(abs(v - value_in), i) for i, v in enumerate(self.sorted_vals)]
        rs = self.rsA.copy()
        # rs = random.sample(range(len(d)), len(d))
        ds = sorted(d, key = lambda x: (x[0], rs.pop()))
        return set(self.sorted_vecs[ds[0][1]])
    def print_trcd(self):
        for i, a in enumerate(self.sorted_vecs): print(f"{a}:  {self.sorted_vals[i]:.4f}")
oracle = Oracle()
oracle.update()
env.close()