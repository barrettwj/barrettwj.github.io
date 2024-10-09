import gymnasium as gym
import random
import numpy as np
env = gym.make("Pendulum-v1", render_mode = "human", g = 9.81)
class Oracle:
    def __init__(self):        
        ###############################################################################
        self.H = 3#---------------------------------------------------------------------------------------------HP
        self.N = 16#--------------------------------------------------------------------------------------------HP
        self.N_range = range(self.N)
        self.sparsity = 0.02#-0.02------------------------------------------------------------------------------HP
        self.M = round(1 / self.sparsity)
        self.K_pct = 0.50#--------------------------------------------------------------------------------------HP
        self.K = round(self.N * self.K_pct)
        self.eff_pct = 0.50#------------------------------------------------------------------------------------HP
        self.eff_dim = round(self.N * self.eff_pct)
        self.eff_mask = set(range(self.eff_dim))
        self.eff_card = round(len(self.eff_mask) * self.K_pct)
        self.aff_mask = set(self.N_range) - self.eff_mask
        self.aff_dim = len(self.aff_mask)
        self.aff_card = self.K - self.eff_card
        ###############################################################################
        self.env_seed = 123456#---------------------------------------------------------------------------------HP
        ###############################################################################
        self.act_start_idx = 0
        self.act_card = 1
        self.act_bin_dim = self.eff_dim - self.act_card + 1
        act_space_indices = {0}
        act_space = [(a[0], a[1]) for i, a in enumerate(zip(env.action_space.low, env.action_space.high))
                     if i in act_space_indices]
        sub_dim = (self.act_bin_dim // len(act_space))
        self.act_bins = [np.linspace(a[0], a[1], sub_dim, True) for a in act_space]
        # print(self.act_bins)
        # encv = self.encode_vector([2], self.act_bins, self.act_card, self.act_start_idx) 
        # print(encv)
        # print(self.decode_vector(encv, self.act_bins[0]))
        ##############################################################################
        self.obs_start_idx = self.eff_dim
        self.obs_card = self.act_card
        self.obs_bin_dim = self.aff_dim - self.obs_card + 1
        obs_space_indices = {0}
        obs_space = [(a[0], a[1]) for i, a in enumerate(zip(env.observation_space.low, env.observation_space.high))
                     if i in obs_space_indices]
        sub_dim = (self.obs_bin_dim // len(obs_space))
        self.obs_bins = [np.linspace(a[0], a[1], sub_dim, True) for a in obs_space]
        # print(self.obs_bins)
        # print(self.encode_vector([-1, 1], self.obs_bins, self.obs_card, self.obs_start_idx))
        ##############################################################################
        self.bv_map_max = 500#--------------------------------------------------------------------------------HP
        self.bv_map = dict()
        ##############################################################################
        self.rsA = random.sample(range(1000000), 1000000)
        self.cy = 0
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        env.reset(seed = self.env_seed)
        while True:
            for i, a in enumerate(self.m):
                if i == 0:
                    # clpv_mod = a.clpv & self.eff_mask
                    clpv_mod = {1}
                    act = self.decode_vector(clpv_mod, self.act_bins[0])
                    # act = 0.20
                    obse, rewa, term, trun, info = env.step([act])
                    # if term or trun: obse, info = env.reset(seed = self.env_seed)
                    # iv = self.encode_vector(obse, self.obs_bins, self.obs_card, self.obs_start_idx)
                    iv = {8, 9, 10}
                    iv |= clpv_mod
                else: iv = self.m[i - 1].clpv.copy()
                a.update(iv.copy())
            self.cy += 1        
    def encode_vector(self, observation, bins, card, start_idx):
        d = [np.digitize(obs, bin_edges) for obs, bin_edges in zip(observation, bins)]
        dm = set()
        sm = 0
        for i, a in enumerate(d):
            dm |= {(start_idx + sm + a - 1) + b for b in range(card)}
            sm += len(bins[i]) + card - 1
        return dm.copy()
    def decode_vector(self, vec_in, bins):
        if vec_in:
            ta = np.array([min(min(vec_in), (self.eff_dim - self.act_card))], dtype = int)
            bs = bins[ta]
            return sum(bs) / max(1, len(bs))
        else: return 0
    # def cyclic_linspace(self, start, stop, num, endpoint = True):
    #     linear_space = np.linspace(start, stop, num, endpoint = endpoint)
    #     period = stop - start
    #     cyclic_values = (linear_space - start) % period + start
    #     return cyclic_values
class Matrix:
    def __init__(self, po_in, mi_in):
        #####################################################
        self.po = po_in
        self.ffi = mi_in - 1
        self.fbi = (mi_in + 1) % self.po.H
        #####################################################
        self.adc_max = 1000000
        self.e = dict()
        self.exv = set()
        self.clpv = set()
        self.elpv = set()
        self.av_prev = set()
        self.av = set()
        #####################################################
        self.em = self.em_delta = 0
    def update(self, iv_in):
        for vA in self.e.values():
            for vB in vA.values():
                if vB[1] < self.adc_max: vB[1] += 1
        ###########################################################################################################################
        fb = self.po.m[self.fbi].clpv.copy() if self.fbi != 0 else set()#-reflection
        # fb = self.po.m[self.fbi].clpv.copy() if self.fbi != 0 else {0, 2, 4}#-innate prior?
        # fb = self.po.m[self.fbi].clpv.copy() if self.fbi != 0 else self.exv.copy()#-autoresonance?
        ###########################################################################################################################
        """
        fs = frozenset(iv_in)
        if fs in self.po.bv_map: self.exv = self.po.bv_map[fs].copy()
        else:
            if len(self.po.bv_map) < self.po.bv_map_max:#------make changes to aff signals proportional to changes in eff signals!!!!
                na_max = 1000
                na = 0
                # nv = set(random.sample(self.po.N_range, self.po.K))
                if self.po.bv_map: nv = random.choice(list(self.po.bv_map.values())).copy()
                else: nv = set(random.sample(self.po.N_range, self.po.K))
                while na < na_max and nv in self.po.bv_map.values():
                    ri = random.choice(list(self.po.N_range))
                    if ri in nv: nv.remove(ri)
                    else: nv.add(ri)
                    na += 1
                self.exv = nv.copy()
                self.po.bv_map[fs] = nv.copy()
            else:
                pass#--------cull the most infrequently used mapping here!!!
        self.exv |= iv_in
        """
        self.exv = iv_in.copy()
        # self.exv ^= iv_in
        ###############################################################################################################################
        ev = self.exv - self.clpv
        self.clpv = ev ^ fb
        ###############################################################################################################################
        self.em_delta = self.em
        self.em = zr = mr = 0
        self.av_prev = self.av.copy()
        self.av = set()
        for a in self.clpv:
            ci = set(range((a * self.po.M), ((a + 1) * self.po.M)))
            ov = self.elpv & ci
            le = len(ov)
            if le == 0:
                zr += 1
                self.em += 1
                ciav = ci - self.e.keys()
                if not ciav:
                    cinv = ci & self.e.keys()
                    d = [(kA, sum(self.e[kA][kB][0] for kB in self.e[kA].keys())) for kA in cinv]
                    rs = self.po.rsA.copy()
                    d = sorted(d, key = lambda x: (x[1], rs.pop()), reverse = True)
                    del self.e[d[0][0]]
                    ciav = ci - self.e.keys()
                wi = random.choice(list(ciav))
            if le > 1:
                mr += 1
                self.em += (le - 1) / (self.po.M - 1)
                d = [(kA, sum(self.e[kA][kB][1] if kB in self.e[kA] else self.adc_max for kB in self.av_prev)) for kA in ov]
                rs = self.po.rsA.copy()
                d = sorted(d, key = lambda x: (x[1], rs.pop()), reverse = True)
                wi = d[0][0]
            if le == 1: wi = ov.pop()
            if wi in self.e:
                for b in self.av_prev:
                    if b in self.e[wi]:
                        self.e[wi][b][0] = self.e[wi][b][1]
                        self.e[wi][b][1] = 0
                    else: self.e[wi][b] = [0, 0]
            else: self.e[wi] = {b:[0, 0] for b in self.av_prev}
            self.av.add(wi)
        self.em /= max(1, len(self.clpv))
        ###############################################################################################################################
        self.elpv = set()
        d = [(k, len(self.e[k].keys() ^ self.av)) for k in self.e.keys()]
        alpha = 0#----------------------------------------------------------------------------------------------------------HP
        mean = var = stdev = -1
        if d:
            led = len(d)
            mean = sum(a[1] for a in d) / led
            var = sum((a[1] - mean) ** 2 for a in d) / led
            stdev = var ** (1 / 2)
            thresh = mean - (stdev * alpha)
            self.elpv = {a[0] for a in d if a[1] <= thresh}
        ###############################################################################################################################
        if self.em < 0.01 and self.em_delta < 0.01 and len(self.po.bv_map) < self.po.bv_map_max:#---------------------------HP
            # ri = random.choice(list(self.po.N_range))
            ri = random.choice(list(self.po.eff_mask))
            if ri in self.clpv: self.clpv.remove(ri)
            else: self.clpv.add(ri)
        ###############################################################################################################################
        tl = [f"M{str(self.ffi + 1).rjust(1)}"]
        tl.append(f"EM: {f'{self.em:.2f}'.rjust(4)}")
        tl.append(f"ZR: {str(zr).rjust(2)}")
        tl.append(f"MR: {str(mr).rjust(2)}")
        tl.append(f"CLPV: {str(len(self.clpv)).rjust(3)}")
        tl.append(f"ELPV: {str(len(self.elpv)).rjust(3)}")
        tl.append(f"MEM: {str(len(self.e)).rjust(3)}")
        tl.append(f"MEAN: {f'{mean:.2f}'.rjust(8)}")
        tl.append(f"VAR: {f'{var:.2f}'.rjust(8)}")
        tl.append(f"BL: {str(len(self.po.bv_map)).rjust(3)}")
        print(" | ".join(tl))
        ###############################################################################################################################
oracle = Oracle()
oracle.update()
env.close()