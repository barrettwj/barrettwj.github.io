import random
import math
import gymnasium as gym
env = gym.make('Pendulum-v1', g = 1.00, render_mode = "human")#-9.81
class Oracle:
    def __init__(self):
        self.H = 3#-----------------------------------------------------------------------------------------HP
        self.M = 103#-53-------------------------------------------------------------------------------------HP
        self.adc_max = 797#-37------------------------------------------------------------------------------HP
        self.cy = start_idx = 0
        self.run_continuous = True
        # self.max_int = sys.maxsize# = 2^63 = 9.223372037E18
        ##############################################################################################################
        self.env_seed = 123456
        #_______________________________________________SETUP GYM DATA______________________________________________________________
        truncated_val = 16.0#-----------------------------------------------------------------------------------------------------HP
        self.obs_indices = [0, 1, 2]#---------------------------------------------------------------------------------------------HP
        # self.obs_indices = [0, 1]#------------------------------------------------------------------------------------------------HP
        self.obs_range_l = [-truncated_val if (env.observation_space.low[a] == -math.inf)
                            else env.observation_space.low[a] for a in self.obs_indices]
        self.obs_range_h = [truncated_val if (env.observation_space.high[a] == math.inf)
                            else env.observation_space.high[a] for a in self.obs_indices]
        self.act_indices = [0]#---------------------------------------------------------------------------------------------------HP
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
        # self.conf_range_l = 0.0
        # self.conf_range_h = 100.0
        self.rew_delta = self.rew_delta_mod = self.episode_ct = self.episode_step_ct = self.cycle = self.cumul_rew = 0
        self.rew_prev = self.rew_metric = self.rew_mod_val = 0
        ##############################################################################################################
        """
        self.transcoder = Transcoder(12, 0, 1, 6, 2, 3, False)
        self.transcoder.print_trcd()
        print(f"{self.transcoder.get_value({14, 15, 17}):.4f}")
        print(self.transcoder.get_vector(0.00))
        print(self.transcoder.get_vector(1.00))
        """
        trc_card = 3#------------------------------------------------------------------------------------------------HP
        trc_num_values = 11#-----------------------------------------------------------------------------------------HP
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
        self.em_trc = Transcoder(start_idx, 0, 1, trc_num_values, 1, trc_card, False)
        self.em_mask = self.em_trc.vec_set.copy()
        start_idx += len(self.em_mask)
        ##############################################################################################################
        # self.rew_trc = Transcoder(start_idx, self.rew_delta_range_l, self.rew_delta_range_h, trc_num_values, 1, trc_card, False)
        self.rew_trc = Transcoder(start_idx, -1, 1, trc_num_values, 1, trc_card, False)
        self.rew_mask = self.rew_trc.vec_set.copy()
        start_idx += len(self.rew_mask)
        ##############################################################################################################
        self.reset_hist = False
        self.matrix_dim_offset = ((start_idx * self.M) + 10)
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        env.reset(seed = self.env_seed)
        # env.reset()
        while True:
            for a in self.m: a.update()
            self.cy += 1
    def interface_env(self, eov_in):
        obs, rew, ter, tru, inf = env.step(tuple([self.bv_trc.get_value(eov_in)]))
        if (ter or tru):
            if (not self.run_continuous):
                obs, inf = env.reset(seed = self.env_seed)
                # obs, inf = env.reset()
            # norm = (self.rew_range_l * max(self.episode_step_ct, 1))
            # self.rew_metric = (1.0 - (self.cumul_rew / norm))
            # self.cumul_rew = self.episode_step_ct = 0
            # self.rew_prev = rew
            # self.reset_hist = True
        if self.episode_step_ct == 100:
            norm = (self.rew_range_l * max(self.episode_step_ct, 1))
            self.rew_metric = (1.0 - (self.cumul_rew / norm))
            self.cumul_rew = self.episode_step_ct = 0
        self.cumul_rew += rew
        self.episode_step_ct += 1
        # self.rew_delta = (rew - self.rew_prev)
        self.rew_delta = ((rew - self.rew_prev) / -self.rew_range_l)
        self.rew_prev = rew
        eiv = set()
        for i, a in enumerate(obs):
            if (i in self.obs_indices): eiv |= self.iv_trcs[i].get_vector(a)
        return eiv.copy()
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.MV = self.po.M
        self.cv = self.iv = self.ov = self.av = self.pv = set()
        self.e = self.fbvm = dict()
        self.em = self.em_prev = self.em_delta_abs = self.forget_period_ct = 0
        self.hist_depth = 1#---------------------------------------------------------------------------------HP
        self.pv_hist = []
        self.rewd_hist = []
        self.cv_hist = []
        self.fbvm_hist = []
    def update(self):
        if self.ffi == -1:
            bv = {(a // self.MV) for a in self.pv if ((a // self.MV) in self.po.bv_mask)}
            self.iv = self.po.interface_env(bv)
            self.iv |= bv
            self.iv |= self.po.rew_trc.get_vector(self.po.rew_delta)
            # self.iv |= self.po.em_trc.get_vector(self.em_delta_abs)
        else: self.iv = self.po.m[self.ffi].ov.copy()
        ##############################################################################################################
        self.em_prev = self.em
        self.em = 0
        self.ov = set()
        if self.po.reset_hist == True:
            self.pv_hist = []
            self.cv_hist = []
            self.fbvm_hist = []
            if self.fbi == 0: self.po.reset_hist = False
        zr = 0
        self.av = set()
        pv_ack = set()
        for a in self.iv:
            ci = set(range((a * self.MV), ((a + 1) * self.MV)))
            ovl = (ci & self.pv)
            if len(ovl) == 0:
                self.em += 1
                zr += 1
                cav = (ci - self.e.keys())
                if not cav:
                    tl = (ci & self.e.keys())
                    # data = [(sum(self.e[b][c] for c in self.e[b].keys()), b) for b in tl]
                    data = [((sum(self.e[b][c] for c in self.e[b].keys()) / max(1, len(self.e[b].keys()))), b) for b in tl]
                    rs = random.sample(range(len(data)), len(data))
                    tls = sorted(data, key = lambda x: (x[0], rs.pop()))
                    del self.e[tls[0][1]]
                    cav = (ci - self.e.keys())
                wi = random.choice(list(cav))
                self.ov.add(a)
            else:
                pv_ack |= ovl
                wi = ovl.pop()
            tv = self.cv.copy()
            # if a in self.fbvm: tv.add(self.fbvm[a])
            if wi in self.e:
                for b in tv:
                    if b in self.e[wi]: val = max(self.e[wi][b], self.po.adc_max)
                    else: val = self.po.adc_max
                    self.e[wi][b] = val
            else: self.e[wi] = {b:self.po.adc_max for b in tv}
            self.av.add(wi)
        self.em /= max(1, len(self.iv))
        zr /= max(1, len(self.iv))
        pv_ex = (self.pv - pv_ack)
        ##############################################################################################################
        """
        for a in pv_ex:
            cli = (a // self.MV)
            if cli in self.fbvm:
                if a in self.e: self.e[a][self.fbvm[cli]] = self.po.adc_max
                else: self.e[a] = {self.fbvm[cli]:self.po.adc_max}
            self.ov.add(cli)
        """
        ##############################################################################################################
        # if ((len(self.pv_hist) == self.hist_depth) and (abs(self.po.rew_delta) > 0.02)):
        if (len(self.pv_hist) == self.hist_depth):
            for i, j in enumerate(self.pv_hist):
                bv_mod = {a for a in j if ((a // self.MV) in self.po.bv_mask)}
                # mod = (self.po.rew_delta * 1000 * (i / max(1, (len(self.pv_hist) - 1))))
                mod = (self.po.rew_delta * 50 * (1 / (len(self.pv_hist) - i)))
                # mod = (self.po.rew_delta * 10000 * (1 / (1.10 ** ((len(self.pv_hist) - 1) - i))))
                for a in bv_mod:
                    tv = self.cv_hist[i].copy()
                    # cli = (a // self.MV)
                    # if cli in self.fbvm_hist[i]: tv.add(self.fbvm_hist[i][cli])
                    for b in tv:
                        if b in self.e[a]: val = (self.e[a][b] + mod)                            
                        else: val = (mod * 8)#-----------------------------------------------------------------HP
                        if val < 0: val = 0
                        if val > 1000: val = 1000
                        self.e[a][b] = round(val)
        ##############################################################################################################
        tl = list(self.e.keys())
        for a in tl:
            self.e[a] = {k:(v - 1) for k, v in self.e[a].items() if (v > 0)}
            if not self.e[a]: del self.e[a]
        ##############################################################################################################
        # fbv = set()
        # fbv = self.po.m[self.fbi].pv.copy()
        fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        # fbv = self.po.m[self.fbi].av.copy()
        # fbv = self.po.m[self.fbi].av.copy() if (self.fbi != 0) else set()
        self.fbvm = {(a // self.MV):-(a + 1) for a in fbv}
        self.fbvm_hist.append(self.fbvm.copy())
        if len(self.fbvm_hist) > self.hist_depth: self.fbvm_hist.pop(0)
        ##############################################################################################################
        self.cv = self.av.copy()
        # self.cv |= {(self.po.matrix_dim_offset + a) for a in self.iv}#----------------------------------CAUSES ISSUES!!!???
        self.cv_hist.append(self.cv.copy())
        if len(self.cv_hist) > self.hist_depth: self.cv_hist.pop(0)
        acts = dict()
        for a in self.e.keys():
            val = (len(self.e[a].keys() ^ self.cv) / max(1, (len(self.e[a]) + len(self.cv))))
            cli = (a // self.MV)
            if cli in self.fbvm:
                self.e[a][self.fbvm[cli]] = self.po.adc_max
                val += 0.20#------------------------------------------------------------------------------------------HP
            # else: acts[a] = (len(self.e[a].keys() ^ self.cv) / max(1, (len(self.e[a]) + len(self.cv))))
            acts[a] = val
        le = len(acts)
        vi = dict()
        alpha = 3.50#-musn't be too large!!!--------------------------------------------------------------------------HP
        if le > 0:
            mu = (sum(acts.values()) / le)
            vari = (sum(((v - mu) ** 2) for v in acts.values()) / le)
            sigma = (vari ** (1 / 2))
            thresh = max(0, (mu - (sigma * alpha)))
            elite = [(k, v) for k, v in acts.items() if (v <= thresh)]
            rs = random.sample(range(len(elite)), len(elite))
            aks = [a[0] for a in sorted(elite, key = lambda x: (x[1], rs.pop()))]
            for a in aks:
                cli = (a // self.MV)
                if cli in vi:
                    vi[cli][1].add(a)
                    if cli in self.fbvm: self.e[a][self.fbvm[cli]] = self.po.adc_max
                    if cli not in self.ov: self.ov.add(cli)
                else: vi[cli] = [a, set()]
        self.rewd_hist.append(self.po.rew_delta)
        if len(self.rewd_hist) > self.hist_depth: self.rewd_hist.pop(0)
        self.pv = {v[0] for v in vi.values()}
        self.pv_hist.append(self.pv.copy())
        if len(self.pv_hist) > self.hist_depth: self.pv_hist.pop(0)
        mr = sum((len(v[1]) / (self.MV - 1)) for v in vi.values())
        mr /= max(1, len(vi))
        self.em += mr
        self.em_delta_abs = abs(self.em - self.em_prev)
        ##############################################################################################################
        print(f"M{(self.ffi + 1)}  EM: {self.em:.2f}  EMDA: {self.em_delta_abs:.2f}" +
        f"  ES: {len(self.e):6d}  PV: {len(self.pv):4d}  ZR: {zr:.2f}  MR: {mr:.2f}  PVEX: {len(pv_ex):4d}" +
        f"  REWM: {self.po.rew_metric:.2f}")
class Transcoder:
    def __init__(self, start_idx_in, min_val_in, max_val_in, num_values_in, enc_step_in, enc_card_in, cyclic_in = False):
        self.vec_set = set()
        self.sorted_vecs = []
        self.sorted_vals = []
        inc = (abs(max_val_in - min_val_in) / (num_values_in - 1))
        if enc_step_in > enc_card_in: enc_step_in = enc_card_in
        if (cyclic_in and (enc_card_in % 2 != 0)): enc_card_in += 1
        limit_idx = (num_values_in * enc_step_in)
        self.card_val = enc_card_in
        for a in range(num_values_in):
            if cyclic_in: ts = [(start_idx_in + ((b + (a * enc_step_in)) % limit_idx)) for b in range(enc_card_in)]
            else: ts = [(start_idx_in + (b + (a * enc_step_in))) for b in range(enc_card_in)]
            self.vec_set |= set(ts)
            self.sorted_vecs.append(ts.copy())
            val = (min_val_in + (a * inc))
            self.sorted_vals.append(val)
        self.sorted_vec_set = sorted(list(self.vec_set))
        self.min_val = min_val_in
        self.max_val = max_val_in
        self.val_range = abs(self.max_val - self.min_val)
        tc = enc_step_in if cyclic_in else enc_card_in
        self.avail_start_idcs = [a for a in range(len(self.sorted_vec_set) + 1 - tc)]
    def get_value(self, vector_in):
        data = [((len(set(k) ^ vector_in) / max(1, (len(k) + len(vector_in)))),
                 (i / (len(self.sorted_vecs) - 1))) for i, k in enumerate(self.sorted_vecs)]
        rs = random.sample(range(len(data)), len(data))
        data_sorted = sorted(data, key = lambda x: (x[0], rs.pop()))
        split_val = ((data_sorted[0][1] + data_sorted[1][1]) / 2)
        return (self.min_val + (split_val * self.val_range))
    def get_vector(self, value_in):
        data = [(abs(v - value_in), (i / (len(self.sorted_vals) - 1))) for i, v in enumerate(self.sorted_vals)]
        rs = random.sample(range(len(data)), len(data))
        data_sorted = sorted(data, key = lambda x: (x[0], rs.pop()))
        split_val = ((data_sorted[0][1] + data_sorted[1][1]) / 2)
        tidx = self.avail_start_idcs[math.ceil(split_val * (len(self.avail_start_idcs) - 1))]#------REPLACE math.ceil() with better solution!!!!
        return {self.sorted_vec_set[((tidx + a) % len(self.sorted_vec_set))] for a in range(self.card_val)}
    def print_trcd(self):
        print(self.sorted_vec_set)
        print(self.avail_start_idcs)
        for i, a in enumerate(self.sorted_vecs): print(f"{a}:  {self.sorted_vals[i]:.4f}")
oracle = Oracle()
oracle.update()
