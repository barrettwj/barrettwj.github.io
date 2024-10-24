import gymnasium as gym
import random
env = gym.make("Pendulum-v1", render_mode = "human", g = 9.81)#-9.81
class Oracle:
    def __init__(self):        
        ###############################################################################
        self.H = 5#---------------------------------------------------------------------------------------------HP
        ###############################################################################
        self.env_seed = 123456#---------------------------------------------------------------------------------HP
        ###############################################################################
        self.trc = TRC()
        ###############################################################################
        self.act_card = 2#---------------------------------------------------------------------------------------HP
        self.act_num_values = 5#---------------------------------------------------------------------------------HP
        act_space_indices = {0}
        act_space = [(a[0], a[1]) for i, a in enumerate(zip(env.action_space.low,
                                                            env.action_space.high)) if i in act_space_indices]
        self.eff_mask = set()
        for i, a in enumerate(act_space):
            self.trc.add_trc(f"ACT_{i}", a[0], a[1], self.act_num_values, self.act_card)
            self.eff_mask |= self.trc.vec_ranges[f"ACT_{i}"]
        self.eff_dim = len(self.eff_mask)
        ##############################################################################
        self.obs_card = self.act_card#-----------------------------------------------------------------------------HP
        self.obs_num_values = self.act_num_values#-----------------------------------------------------------------HP
        self.obs_space_indices = {0, 1, 2}
        # self.obs_space_indices = {0, 1}
        obs_space = [(a[0], a[1]) for i, a in enumerate(zip(env.observation_space.low,
                                                            env.observation_space.high)) if i in self.obs_space_indices]
        self.aff_mask = set()
        for i, a in enumerate(obs_space):
            self.trc.add_trc(f"OBS_{i}", a[0], a[1], self.obs_num_values, self.obs_card)
            self.aff_mask |= self.trc.vec_ranges[f"OBS_{i}"]
        # print(self.trc.trcs["OBS_0"])
        # print(self.trc.get_value("OBS_0", {5, 4, 3}))
        ##############################################################################
        self.rew_max = 0
        self.rew_min = -16.2736044
        self.rm_period = 100#-------------------------------------------------------------------------------HP
        self.rm_samples = []
        self.rm = 0
        self.trc.add_trc("REWD", -1, 1, self.act_num_values, self.act_card)
        self.aff_mask |= self.trc.vec_ranges["REWD"]
        self.aff_dim = len(self.aff_mask)
        #############################################################################
        self.N = self.eff_dim + self.aff_dim
        self.rew_prev = self.rew = self.rew_delta = self.cy = 0
        self.rda_period = 100#-------------------------------------------------------------------------------HP
        self.rda = 0
        self.rda_samples = []
        self.rsA = random.sample(range(1000000), 1000000)
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        env.reset(seed = self.env_seed)
        while True:
            for a in self.m:
                if a.ffi == -1:
                    self.bv = a.pv & self.eff_mask
                    act = self.trc.get_value("ACT_0", self.bv)
                    if not act: act = 0
                    obse, rewa, term, trun, info = env.step([act])
                    self.rew_prev = self.rew
                    self.rew = 1 - (rewa / self.rew_min)
                    self.rew_delta = self.rew - self.rew_prev
                    self.rda_samples.append(self.rew_delta)
                    if len(self.rda_samples) == self.rda_period:
                        self.rda = sum(self.rda_samples) / len(self.rda_samples)
                        self.rda_samples = []
                    self.rm_samples.append(self.rew)
                    if len(self.rm_samples) == self.rm_period:
                        self.rm = sum(self.rm_samples) / len(self.rm_samples)
                        self.rm_samples = []
                    # if term or trun: obse, info = env.reset(seed = self.env_seed)
                    observation = [obse[b] for b in self.obs_space_indices]
                    iv = set()
                    for j, b in enumerate(observation): iv |= self.trc.get_vector(f"OBS_{j}", b)
                    iv |= self.bv
                    iv |= self.trc.get_vector("REWD", self.rda)
                else: iv = self.m[a.ffi].pv.copy()
                a.update(iv)
            self.cy += 1
class Matrix:
    def __init__(self, po_in, mi_in):
        #####################################################
        self.po = po_in
        self.ffi = mi_in - 1
        self.fbi = (mi_in + 1) % self.po.H
        #####################################################
        self.iv = set()
        self.fbv = set()
        self.pv = set()
        #####################################################
        self.trmp_dim = 10000#---------------------------------------------------------------------------------------------HP
        self.trmp = dict()
        # self.emdas_dim = 37#-----------------------------------------------------------------------------------------------HP
        # self.emdas = []
        self.em = self.em_prev = self.em_delta = self.emda = 0
        #####################################################
    def update(self, iv_in):
        ##############################################################################################
        self.fbv = self.po.m[self.fbi].pv.copy() if self.fbi != 0 else set()
        ev = iv_in - self.pv
        self.pv = ev ^ self.fbv
        ##############################################################################################
        self.em_prev = self.em
        self.em = len(ev) / self.po.N
        self.em_delta = self.em - self.em_prev
        # self.emdas.append(abs(self.em_delta))
        # if len(self.emdas) == self.emdas_dim:
        #     self.emda = sum(self.emdas) / self.emdas_dim
        #     self.emdas.pop(0)
        ###############################################################################################
        self.trmp[(frozenset(self.iv), frozenset(iv_in))] = self.em_delta
        self.iv = iv_in.copy()
        ###############################################################################################
        if (self.fbi == 0) and (self.po.rda < 0) and (self.po.rew < 0.95):#----------------------------------------------------HP
            ri = random.choice(list(self.po.eff_mask))
            if ri in self.pv: self.pv.remove(ri)
            else: self.pv.add(ri)
        ################################################################################################
        self.manage_print()
        ################################################################################################
    def manage_print(self):
        tl = [f"M{str(self.ffi + 1).rjust(1)}"]
        tl.append(f"EM: {f'{self.em:.4f}'.rjust(6)}")
        tl.append(f"PV: {str(len(self.pv)).rjust(3)}")
        tl.append(f"TRMP: {str(len(self.trmp)).rjust(6)}")
        tl.append(f"REW_M: {f'{self.po.rm:.2f}'.rjust(6)}")
        print(" | ".join(tl))
class TRC:
    def __init__(self):
        self.start_idx = 0
        self.trcs = dict()
        self.vec_ranges = dict()
    def add_trc(self, label_in, min_val_in, max_val_in, num_vals_in, card_in):
        range_idx_start = self.start_idx
        v_range = (max_val_in - min_val_in)
        v_inc = v_range / (num_vals_in - 1)
        self.trcs[label_in] = dict()
        for a in range(num_vals_in):
            self.trcs[label_in][frozenset({self.start_idx + b for b in range(card_in)})] = min_val_in + (a * v_inc)
            self.start_idx += 1
        self.start_idx += card_in - 1
        self.vec_ranges[label_in] = set(range(range_idx_start, self.start_idx))
    def get_value(self, label_in, vec_in):
        val = ct = 0
        for k, v in self.trcs[label_in].items():
            for _ in (k & vec_in):
                val += v
                ct += 1
        return val / ct if ct > 0 else None
    def get_vector(self, label_in, val_in):
        min_d = 1000000
        min_k = {}
        for k, v in self.trcs[label_in].items():
            dist = abs(val_in - v)
            if dist < min_d:
                min_k = set(k)
                min_d = dist
        return min_k.copy()
oracle = Oracle()
oracle.update()
env.close()