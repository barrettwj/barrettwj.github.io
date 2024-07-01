import random
import math
import gymnasium as gym
env = gym.make('Pendulum-v1', g = 0.00, render_mode = "human")#-9.81
class Oracle:
    def __init__(self):
        self.H = 3#-----------------------------------------------------------------------------------------HP
        self.M = 53#-53-------------------------------------------------------------------------------------HP
        self.adc_max = 567#-37------------------------------------------------------------------------------HP
        self.adc_min = math.ceil(self.adc_max * 0.85)
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
        self.rew_delta_mag = (self.rew_range_h - self.rew_range_l)
        # self.rew_delta_range_l = (self.rew_range_l - self.rew_range_h)
        # self.rew_delta_range_h = (self.rew_range_h - self.rew_range_l)
        # self.rew_delta_range_l = -1.0
        self.rew_delta_range_l = 0.0
        self.rew_delta_range_h = 1.0
        # self.conf_range_l = 0.0
        # self.conf_range_h = 100.0
        self.rew_delta = self.rew_delta_mod = self.episode_ct = self.episode_step_ct = self.cycle = self.cumul_rew = 0
        self.rew_prev = self.rew_metric = self.rew_mod_val = 0
        ##############################################################################################################
        """
        self.transcoder = Transcoder(start_idx, -2.0, 2.0, 20, 2, 9, False)
        self.transcoder.print_trcd()
        # print(f"{self.transcoder.get_value({3, 4, 5, 6}):.4f}")
        print(f"{self.transcoder.get_value({19, 20, 21, 22, 23, 24, 25, 26, 27}):.4f}")
        print(self.transcoder.get_vector(0.00))
        """
        self.tsp_dim = 3#------------------------------------------------------------------------------------HP
        ts_dim = 50#-----------------------------------------------------------------------------------------HP
        self.iv_trcs = []
        self.iv_mask = set()
        for a in self.obs_indices:
            trc = Transcoder(start_idx, self.obs_range_l[a], self.obs_range_h[a], ts_dim, 1, self.tsp_dim, False)
            self.iv_mask |= trc.vec_set
            self.iv_trcs.append(trc)
        start_idx += len(self.iv_mask)
        self.bv_trc = Transcoder(start_idx, -2.0, 2.0, ts_dim, 1, self.tsp_dim, False)
        self.bv_mask = self.bv_trc.vec_set.copy()
        start_idx += len(self.bv_mask)
        # self.iv_bv_map = {frozenset(random.sample(list(self.iv_mask), self.tsp_dim)):
        #                   frozenset(random.sample(list(self.bv_mask), self.tsp_dim)) for _ in range(ts_dim)}
        ##############################################################################################################
        self.em_trc = Transcoder(start_idx, 0, 1, ts_dim, 1, self.tsp_dim, False)
        self.em_mask = self.em_trc.vec_set.copy()
        start_idx += len(self.em_mask)
        ##############################################################################################################
        self.matrix_dim_offset = (start_idx * self.M)
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        env.reset(seed = self.env_seed)
        # env.reset()
        while True:
            for a in self.m: a.update()
            self.cy += 1
    def interface_env(self, eov_in):
        obs, rew, ter, tru, inf = env.step(tuple([self.bv_trc.get_value(eov_in)]))
        # obs, rew, ter, tru, inf = env.step(tuple([0]))
        if (ter or tru):
            if (not self.run_continuous):
                env.reset(seed = self.env_seed)
                # env.reset()
            norm = (self.rew_range_l * float(max(self.episode_step_ct, 1)))
            self.rew_metric = (1.0 - (float(self.cumul_rew) / norm))
            self.cumul_rew = self.episode_step_ct = 0
            # self.rew_prev = rew#-------------------------HELPFUL???-----NECESSARY????
            # self.episode_ct += 1
        self.cumul_rew += rew
        self.episode_step_ct += 1
        self.rew_delta = (rew - self.rew_prev)
        self.rew_prev = rew
        self.rew_delta_mod = (self.rew_delta / self.rew_delta_mag)
        self.rew_mod_val = (rew / self.rew_range_l)
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
        self.iv = self.ov = self.av = self.pv = set()
        self.e = self.fbvm = dict()
        self.em = self.em_prev = self.em_delta_abs = self.forget_period_ct = 0
        # self.forget_period = 1#->=1----------------------------------------------------------------------------HP
        self.bv_list = []
    def update(self):
        # # fbv = self.po.m[self.fbi].pv.copy()
        # fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        # fbv = self.po.m[self.fbi].av.copy()
        fbv = self.po.m[self.fbi].av.copy() if (self.fbi != 0) else set()
        self.fbvm = {(a // self.MV):-(a + 1) for a in fbv}
        ##############################################################################################################
        cv = self.av.copy()
        cv |= {(self.po.matrix_dim_offset + (a * self.MV)) for a in self.iv}#-------------------------CAUSES ISSUES!!!???
        acts = dict()
        for a in self.e.keys():
            tv = cv.copy()
            cli = (a // self.MV)
            if cli in self.fbvm: tv.add(self.fbvm[cli])
            acts[a] = (len(self.e[a].keys() ^ tv) / max(1, (len(self.e[a]) + len(tv))))
        le = len(acts)
        self.ov = set()
        vi = dict()
        alpha = 1#-musn't be too large!!!--------------------------------------------------------------------------HP
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
                    if cli not in self.ov: self.ov.add(cli)
                else: vi[cli] = [a, set()]
        self.pv = {v[0] for v in vi.values()}
        self.em_prev = self.em
        self.em = sum((len(v[1]) / (self.MV - 1)) for v in vi.values())
        em_norm = len(vi)
        mr = (self.em / max(1, em_norm))
        ##############################################################################################################
        if self.ffi == -1:
            bv = {(a // self.MV) for a in self.pv if ((a // self.MV) in self.po.bv_mask)}
            self.iv = self.po.interface_env(bv)
            self.iv |= bv
            """
            data = [((len(v ^ bv) / max(1, (len(v) + len(bv)))), k, v) for k, v in self.po.iv_bv_map.items()]
            rs = random.sample(range(len(data)), len(data))
            bv_sorted = sorted(data, key = lambda x: (x[0], rs.pop()))
            d, iv_found, bv_found = bv_sorted.pop(0)
            bv_idx = self.bv_list.index(bv_found) if (bv_found in self.bv_list) else -1
            if bv_idx == -1:
                bv_idx = len(self.bv_list)
                self.bv_list.append(bv_found)
            self.iv = {a for a in iv_found}
            self.iv |= {a for a in bv_found}
            """
            self.iv |= self.po.em_trc.get_vector(self.em_delta_abs)
        else: self.iv = self.po.m[self.ffi].ov.copy()
        ##############################################################################################################
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
                    data = [((sum(self.e[b][c] for c in self.e[b].keys()) / len(self.e[b].keys())), b) for b in tl]
                    rs = random.sample(range(len(data)), len(data))
                    tls = sorted(data, key = lambda x: (x[0], rs.pop()))
                    del self.e[tls[0][1]]
                    cav = (ci - self.e.keys())
                wi = random.choice(list(cav))
                self.ov.add(a)
            else:
                pv_ack |= ovl
                wi = ovl.pop()
            tv = cv.copy()
            if a in self.fbvm: tv.add(self.fbvm[a])
            if wi in self.e:
                for b in tv: self.e[wi][b] = random.randrange(self.po.adc_min, self.po.adc_max)
            else: self.e[wi] = {b:random.randrange(self.po.adc_min, self.po.adc_max) for b in tv}
            self.av.add(wi)
        self.em /= max(1, (em_norm + len(self.iv)))
        zr /= max(1, len(self.iv))
        self.em_delta_abs = abs(self.em - self.em_prev)
        pv_ex = (self.pv - pv_ack)
        ##############################################################################################################
        """
        for a in pv_ex:
            cli = (a // self.MV)
            if cli in self.fbvm:
                if a in self.e: self.e[a][self.fbvm[cli]] = random.randrange(self.po.adc_min, self.po.adc_max)
                else: self.e[a] = {self.fbvm[cli]:random.randrange(self.po.adc_min, self.po.adc_max)}
            self.ov.add(cli)
        """
        ##############################################################################################################
        # self.forget_period_ct += 1
        # if self.forget_period_ct == self.forget_period:
        #"""
        tl = list(self.e.keys())
        for a in tl:
            # if len(self.e[a]) < 250:#---------------------------------------------------------------------HP
            self.e[a] = {k:(v - 1) for k, v in self.e[a].items() if (v > 0)}
            if not self.e[a]: del self.e[a]
        #"""
        # self.forget_period_ct = 0
        ##############################################################################################################
        # bv_string = f"  BVL: {len(self.bv_list):2d}  BVID: {bv_idx:2d}" if self.ffi == -1 else ""
        # print(f"M{(self.ffi + 1)}  EM: {self.em:.2f}  EMDA: {self.em_delta_abs:.2f}" +
        # f"  ES: {len(self.e):6d}  PV: {len(self.pv):4d}  ZR: {zr:.2f}  MR: {mr:.2f}  PVEX: {len(pv_ex):4d}" + bv_string)
        print(f"M{(self.ffi + 1)}  EM: {self.em:.2f}  EMDA: {self.em_delta_abs:.2f}" +
        f"  ES: {len(self.e):6d}  PV: {len(self.pv):4d}  ZR: {zr:.2f}  MR: {mr:.2f}  PVEX: {len(pv_ex):4d}")
class Transcoder:
    def __init__(self, start_idx_in, min_val_in, max_val_in, num_values_in, enc_step_in, enc_card_in, cyclic_in = False):
        self.vec_set = set()
        self.codes = dict()
        self.sorted_vecs = []
        self.is_cyclic = cyclic_in
        inc = (abs(max_val_in - min_val_in) / (num_values_in - 1))
        if enc_step_in > enc_card_in: enc_step_in = enc_card_in
        if cyclic_in: enc_card_in = (enc_step_in * 2)
        limit_idx = (num_values_in * enc_step_in)
        self.card_val = enc_card_in
        self.offset = math.ceil(self.card_val / 2)
        self.remainder = (self.card_val - self.offset)
        self.max_val_dist = 0
        val_prev = 0
        for a in range(num_values_in):
            if cyclic_in: ts = {(start_idx_in + ((b + (a * enc_step_in)) % limit_idx)) for b in range(enc_card_in)}
            else: ts = {(start_idx_in + (b + (a * enc_step_in))) for b in range(enc_card_in)}
            self.vec_set |= ts
            self.sorted_vecs.append(ts.copy())
            val = (min_val_in + (a * inc))
            vd = abs(val - val_prev)
            if vd > self.max_val_dist: self.max_val_dist = vd
            val_prev = val 
            self.codes[frozenset(ts)] = val
        self.sorted_vec_set = sorted(list(self.vec_set))
        self.sorted_vals = sorted([v for v in self.codes.values()])
        self.min_val = min_val_in
        self.max_val = max_val_in
        self.val_range = (self.max_val - self.min_val)
    def get_value(self, vector_in):
        data = [((len(k ^ vector_in) / max(1, (len(k) + len(vector_in)))),
                 (i / (len(self.sorted_vecs) - 1))) for i, k in enumerate(self.sorted_vecs)]
        rs = random.sample(range(len(data)), len(data))
        data_sorted = sorted(data, key = lambda x: (x[0], rs.pop()))
        split_val = ((data_sorted[0][1] + data_sorted[1][1]) / 2)
        return (self.min_val + (split_val * self.val_range))
    def get_vector(self, value_in):
        data = [(abs(v - value_in), (i / (len(self.sorted_vals) - 1))) for i, v in enumerate(self.sorted_vals)]
        rs = random.sample(range(len(data)), len(data))
        data_sorted = sorted(data, key = lambda x: (x[0], rs.pop()))
        if self.is_cyclic: avail_idcs = [a for a in range(len(self.sorted_vec_set))]
        else:
            le = (len(self.sorted_vec_set) - self.offset - self.remainder + 1)
            avail_idcs = [(self.offset + a) for a in range(le)]
        split_val = ((data_sorted[0][1] + data_sorted[1][1]) / 2)
        tidx = self.sorted_vec_set[avail_idcs[math.ceil(split_val * (len(avail_idcs) - 1))]]
        limit_val = (max(self.sorted_vec_set) + 1)
        return {(((tidx - self.offset) + a) % limit_val) for a in range(self.card_val)}
    def print_trcd(self):
        for k, v in self.codes.items(): print(f"{v:.4f}:\t{k}")
oracle = Oracle()
oracle.update()
