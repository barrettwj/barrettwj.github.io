import gymnasium as gym
env = gym.make('Pendulum-v1', g = 0.00, render_mode = "human")#-9.81
import random
class Oracle:
    def __init__(self):
        #_______________________________________________SETUP GYM DATA______________________________________________________________
        truncated_val = 16.0#-----------------------------------------------------------------------------------------------------HP
        self.obs_indices = [0, 1, 2]#---------------------------------------------------------------------------------------------HP
        # self.obs_indices = [0, 1]#------------------------------------------------------------------------------------------------HP
        self.obs_range_l = [-truncated_val if (env.observation_space.low[a] == float('-inf'))
                            else env.observation_space.low[a] for a in self.obs_indices]
        self.obs_range_h = [truncated_val if (env.observation_space.high[a] == float('inf'))
                            else env.observation_space.high[a] for a in self.obs_indices]
        self.act_indices = [0]#---------------------------------------------------------------------------------------------------HP
        self.act_range_l = [-truncated_val if (env.action_space.low[a] == float('-inf'))
                            else env.action_space.low[a] for a in self.act_indices]
        self.act_range_h = [truncated_val if (env.action_space.high[a] == float('inf'))
                            else env.action_space.high[a] for a in self.act_indices]
        # self.rew_range_l = -truncated_val if (env.reward_range[0] == float('-inf')) else env.reward_range[0]
        # self.rew_range_h = truncated_val if (env.reward_range[1] == float('inf')) else env.reward_range[1]
        self.rew_range_l = -16.2736044
        self.rew_range_h = 0
        self.rew_delta_range_l = (self.rew_range_l - self.rew_range_h)
        self.rew_delta_range_h = (self.rew_range_h - self.rew_range_l)
        # self.conf_range_l = 0.0
        # self.conf_range_h = 100.0
        self.rew_delta = self.episode_ct = self.episode_step_ct = self.cycle = self.cumul_rew = self.rew_prev = self.rew_metric = 0
        self.env_seed = 123456#---------------------------------------------------------------------------------------------------HP
        # self.num_values = (round(truncated_val * 2.0) + 1)
        self.num_values = 7
        self.enc_card = 4#-9-should be even???------------------------------------------------------------------------------------HP
        #____________________________________________________DATA EMBEDDING_________________________________________________________
        gl_index = 0
        self.obs_vals = dict()
        for a in self.obs_indices:
            inc = (float(abs(self.obs_range_h[a] - self.obs_range_l[a])) / float(self.num_values - 1))
            td = dict()
            for b in range(self.num_values):
                td[b] = [(float(self.obs_range_l[a]) + (float(b) * inc)), {(gl_index + b + c) for c in range(self.enc_card)}]
            self.obs_vals[a] = td.copy()
            gl_index += self.num_values
        self.act_vals = dict()
        for a in self.act_indices:
            inc = (float(abs(self.act_range_h[a] - self.act_range_l[a])) / float(self.num_values - 1))
            td = dict()
            for b in range(self.num_values):
                td[b] = [(float(self.act_range_l[a]) + (float(b) * inc)), {(gl_index + b + c) for c in range(self.enc_card)}]
            self.act_vals[a] = td.copy()
            gl_index += self.num_values
        inc = (float(abs(self.rew_delta_range_h - self.rew_delta_range_l)) / float(self.num_values - 1))
        self.rew_vals = dict()
        for a in range(self.num_values):
            self.rew_vals[a] = [(float(self.rew_delta_range_l) + (float(a) * inc)), {(gl_index + a + b) for b in range(self.enc_card)}]
        gl_index += self.num_values
        # inc = (float(abs(self.conf_range_h - self.conf_range_l)) / float(self.num_values - 1))
        # self.conf_vals = dict()
        # for a in range(self.num_values):
        #     self.conf_vals[a] = [(float(self.conf_range_l) + (float(a) * inc)), {(gl_index + a + b) for b in range(self.enc_card)}]
        # gl_index += self.num_values
        #____________________________________________________________________________________________________________________________
        self.K = (gl_index + (self.enc_card - 1))
        self.H = 3#----------------------------------------------------------------------------------------------------------------HP
        self.Z = 177#--------------------------------------------------------------------------------------------------------------HP
        self.pv_min = 971#-171-----------------------------------------------------------------------------------------------------HP
        self.pv_range = 1.13#------------------------------------------------------------------------------------------------------HP
        self.pv_max = max((self.pv_min + 1), round(float(self.pv_min) * self.pv_range))
        self.ex_act_val = []
        self.m = [Matrix(self, a) for a in range(self.H)]
        self.ppcv = set()
    def update(self):
        env.reset(seed = self.env_seed)
        while (True):
            for a in self.m: a.update()
    def interface_env(self, eov_in):
        obs, rew, ter, tru, inf = env.step(self.decode_eov(eov_in.copy()))
        if (ter or tru):
            env.reset(seed = self.env_seed)
            # norm = (self.rew_range_l * float(max(self.episode_step_ct, 1)))
            # self.rew_metric = ((float(self.cumul_rew) / norm) * 100.0)
            self.cumul_rew = self.episode_step_ct = 0
            self.episode_ct += 1
        self.cumul_rew += rew
        self.episode_step_ct += 1
        self.rew_delta = (rew - self.rew_prev)
        self.rew_prev = rew
        eiv = self.encode_eiv(obs, self.rew_delta)
        return eiv.copy()
    def encode_eiv(self, obs_in, rew_delta_in):
        out = set()
        for i, a in enumerate(obs_in):
            if (i in self.obs_vals.keys()):
                td = {key:abs(value[0] - a) for key, value in self.obs_vals[i].items()}
                cands = [key for key, value in td.items() if (value == min(td.values()))]
                for b in cands: out |= self.obs_vals[i][b][1]
        td = {key:abs(value[0] - rew_delta_in) for key, value in self.rew_vals.items()}
        cands = [key for key, value in td.items() if (value == min(td.values()))]
        for b in cands: out |= self.rew_vals[b][1]
        return out.copy()
    def decode_eov(self, eov_in):
        out = []
        for a in self.act_vals.keys():
            sum_v = [(value[0] * (float(len(value[1] & eov_in)) /
                                  float(len(value[1])))) for value in self.act_vals[a].values() if (len(value[1] & eov_in) > 0)]
            out.append((sum(sum_v) / float(max(1, len(sum_v)))))
        self.ex_act_val = out.copy()
        return tuple(out)
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.mi = mi_in
        self.ffi = (self.mi - 1)
        self.fbi = ((self.mi + 1) % self.po.H)
        self.blank_cv = ([0] * self.po.K)
        self.read_v = self.blank_cv.copy()
        self.conf_v = self.blank_cv.copy()
        self.poss_indices = set(range(self.po.Z))
        self.mem = dict()
        self.iv = self.ov = self.Bv = self.Av = self.gt_cv = self.pv = self.vi = set()
        self.sample_min = 10#-10!!!should be odd???!!!-musn't be set too high????!!!!----------------------------------------------HP
        self.aa_factor = 10#-10----------------------------------------------------------------------------------------------------HP
        self.write_delta_max = 100#------------------------------------------------------------------------------------------------HP
        num_steps_to_max = 73#-7-27---------------------------------------------------------------------------------------------------HP
        self.cv_max = (num_steps_to_max * self.write_delta_max)
        self.cv_min = -(self.cv_max - 1)
        self.tp = self.rel_idx = self.Bv_index = 0
        self.agency = False
    def update(self):
        fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        # fbv = self.po.m[self.fbi].pv.copy()#--------------------------I think this is causing issues???YES!!!IT IS!!!because of mb!!!
        self.gt_cv = (self.iv | {(self.po.K + a) for a in fbv})
        self.Bv = self.gt_cv.copy()
        self.vi = set()
        #_____________________________________________________________________________________________________________________________
        avail_indices = (self.poss_indices - set(self.mem.keys()))
        self.rel_idx = random.choice(list(avail_indices))
        self.mem[self.rel_idx] = [self.gt_cv.copy(), self.blank_cv.copy(), random.randrange(self.po.pv_min, self.po.pv_max)]
        self.vi.add(self.rel_idx)
        #_____________________________________________________________________________________________________________________________
        aa_ct = 0
        # self.read_v = self.blank_cv.copy()
        while ((len(self.Bv ^ self.Av) > 0) and (aa_ct < self.aa_factor)):
            si = list(self.mem.keys())
            random.shuffle(si)
            skip = set()
            r = 0
            avg_vA_list = ([0] * (self.po.K * 2))
            self.read_v = self.blank_cv.copy()
            while ((len(si) > 0) and (len(skip) < self.sample_min)):
                for a in si:
                    tav = self.mem[a][0]
                    d = len(tav ^ self.Bv)
                    if (d == r):
                        for i, b in enumerate(avg_vA_list):
                            if (i in tav): avg_vA_list[i] += 1
                            else: avg_vA_list[i] -= 1
                        for i, b in enumerate(self.mem[a][1]):
                            val = (self.read_v[i] + b)
                            if (val < self.cv_min): val = self.cv_min
                            if (val > self.cv_max): val = self.cv_max
                            self.read_v[i] = val
                        self.mem[a][2] = random.randrange(self.po.pv_min, self.po.pv_max)
                        skip.add(a)
                        self.vi.add(a)
                si = [c for c in si if (c not in skip)]
                r += 1
            self.Av = self.Bv.copy()
            self.Bv = {i for i, a in enumerate(avg_vA_list) if (a > 0)}
            aa_ct += 1
        # print(aa_ct)
        self.Av = self.Bv.copy()#---necessary????--appropriate????
        #___________________________________________________________________________________________________________________________
        norm = float(self.cv_max - 1)
        conf_thresh = 0.50#-----------------------------------------------------------------------------------------------------HP
        self.pv = set()
        self.conf_v = []
        for i, a in enumerate(self.read_v):
            if (a > 0):
                val = (float(abs(a) - 1) / norm)
                # if (val >= conf_thresh): self.pv.add(i)
                self.pv.add(i)
                self.conf_v.append(val)
            else:
                val = (float(abs(a)) / norm)
                self.conf_v.append(val)
        # print(self.conf_v)
        #____________________________________________________________________________________________________________________________
        if (self.mi == 0):
            self.po.ppcv = set()
            for a in self.po.act_vals.keys():
                for value in self.po.act_vals[a].values(): self.po.ppcv |= (value[1] & self.pv)
            self.agency = (len(self.po.ppcv) > 0)
            if ((self.agency == False) and (random.randrange(1000000) < 500000)):#-motor babble------------------------------------HP
                riA = random.choice(list(self.po.act_vals.keys()))
                riB = random.choice(list(self.po.act_vals[riA].keys()))
                self.po.ppcv = self.po.act_vals[riA][riB][1].copy()
                self.pv |= self.po.ppcv
            #------TODO: embed RL signals and prediction confidence into input
            self.iv = self.po.interface_env(self.pv.copy()).copy()
            if (self.po.rew_delta > 0): self.iv |= self.po.ppcv
            else:
                self.pv -= self.po.ppcv
                # self.conf_v = ([1.0] * self.po.K)#----------I THINK THIS CAUSES ISSUES????!!!!!
        else: self.iv = self.po.m[self.ffi].ov.copy()
        self.ov = (self.iv ^ self.pv)
        erm = ((float(len(self.ov)) / float(max(1, (len(self.iv) + len(self.pv))))) * 100.0)
        #____________________________________________________________________________________________________________________________
        for a in self.vi:
            for i, b in enumerate(self.mem[a][1]):
                # write_delta = round((1.0 - self.conf_v[i]) * float(self.write_delta_max))
                if (i in self.iv):
                    write_delta = round((1.0 - self.conf_v[i]) * float(self.write_delta_max)) 
                    self.mem[a][1][i] = min(self.cv_max, (self.mem[a][1][i] + write_delta))
                if (i not in self.iv):
                    write_delta = round(self.conf_v[i] * float(self.write_delta_max)) 
                    self.mem[a][1][i] = max(self.cv_min, (self.mem[a][1][i] - write_delta))
        #____________________________________________________________________________________________________________________________
        self.tp = sum((len(self.mem[a][0]) + len(self.mem[a][1]) + 2) for a in self.mem.keys())
        agency_str = f"\tEX_ACT: {self.po.ex_act_val[0]:.4f}" if (self.agency) else ""
        # agency_str = f"\tEX_ACT: {self.po.ex_act_val[0]:.4f}" if (self.mi == 0) else ""
        print(f"M{self.mi}\tER: {erm:.2f}%\tTP: {self.tp}\tMEM: {len(self.mem.keys())}" + agency_str)
        #____________________________________________________________________________________________________________________________
        while ((len(self.mem) + 2) > self.po.Z):
            si = list(self.mem.keys())
            random.shuffle(si)
            for a in si:
                if ((len(self.mem) + 2) > self.po.Z):
                    if (self.mem[a][2] > 0): self.mem[a][2] -= 1
                    else: del self.mem[a]
oracle = Oracle()
oracle.update()