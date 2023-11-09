import gymnasium as gym
env = gym.make('Pendulum-v1', g = 0.00, render_mode = "human")#-9.81
import random
import math
import sys
class Oracle:
    def __init__(self):
        self.max_int = (sys.maxsize - 10)
        self.min_int = -(self.max_int - 1)
        #_______________________________________________SETUP GYM DATA______________________________________________________________
        truncated_val = 16.0#-----------------------------------------------------------------------------------------------------HP
        # self.obs_indices = [0, 1, 2]#---------------------------------------------------------------------------------------------HP
        self.obs_indices = [0, 1]#------------------------------------------------------------------------------------------------HP
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
        # self.rew_delta_range_l = (self.rew_range_l - self.rew_range_h)
        # self.rew_delta_range_h = (self.rew_range_h - self.rew_range_l)
        self.rew_delta_range_l = -1.0
        self.rew_delta_range_h = 1.0
        # self.conf_range_l = 0.0
        # self.conf_range_h = 100.0
        self.rew_delta = self.episode_ct = self.episode_step_ct = self.cycle = self.cumul_rew = 0
        self.cumul_rew_delta = self.rew_prev = self.rew_metric = 0
        self.env_seed = 123456#---------------------------------------------------------------------------------------------------HP
        self.num_values = 9#-must be odd!!!
        self.enc_card = 3#-should be even???--------------------------------------------------------------------------------------HP
        #____________________________________________________DATA EMBEDDING_________________________________________________________
        gl_index = 0
        self.obs_vals = dict()
        for a in self.obs_indices:
            inc = (float(abs(self.obs_range_h[a] - self.obs_range_l[a])) / float(self.num_values - 1))
            td = dict()
            for b in range(self.num_values):
                td[b] = [(float(self.obs_range_l[a]) + (float(b) * inc)), {(gl_index + b + c) for c in range(self.enc_card)}]
            self.obs_vals[a] = td.copy()
            gl_index += (self.num_values + (self.enc_card - 1))
        self.act_vals = dict()
        for a in self.act_indices:
            inc = (float(abs(self.act_range_h[a] - self.act_range_l[a])) / float(self.num_values - 1))
            td = dict()
            for b in range(self.num_values):
                td[b] = [(float(self.act_range_l[a]) + (float(b) * inc)), {(gl_index + b + c) for c in range(self.enc_card)}]
            self.act_vals[a] = td.copy()
            gl_index += (self.num_values + (self.enc_card - 1))
        inc = (float(abs(self.rew_delta_range_h - self.rew_delta_range_l)) / float(self.num_values - 1))
        self.rew_vals = dict()
        for a in range(self.num_values):
            self.rew_vals[a] = [(float(self.rew_delta_range_l) + (float(a) * inc)), {(gl_index + a + b) for b in range(self.enc_card)}]
        gl_index += (self.num_values + (self.enc_card - 1))
        # inc = (float(abs(self.conf_range_h - self.conf_range_l)) / float(self.num_values - 1))
        # self.conf_vals = dict()
        # for a in range(self.num_values):
        #     self.conf_vals[a] = [(float(self.conf_range_l) + (float(a) * inc)), {(gl_index + a + b) for b in range(self.enc_card)}]
        # gl_index += (self.num_values + (self.enc_card - 1))
        #____________________________________________________________________________________________________________________________
        self.K = gl_index
        self.H = 3#----------------------------------------------------------------------------------------------------------------HP
        self.Z = 277#--------------------------------------------------------------------------------------------------------------HP
        self.pv_max = 500#--------------------------------------------------------------------------------------------------------HP
        self.pv_min = -self.pv_max
        self.pv_initial_pct = 0.20#------------------------------------------------------------------------------------------------HP
        self.pv_initial = round(float(self.pv_max) * self.pv_initial_pct)
        self.ex_act_val = []
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        env.reset(seed = self.env_seed)
        # env.reset()
        while (True):
            for a in self.m: a.update()
    def interface_env(self, eov_in):
        obs, rew, ter, tru, inf = env.step(self.decode_eov(eov_in.copy()))
        if (ter or tru):
            env.reset(seed = self.env_seed)
            # env.reset()
            norm = (self.rew_range_l * float(max(self.episode_step_ct, 1)))
            self.rew_metric = ((1.0 - (float(self.cumul_rew) / norm)) * 100.0)
            self.cumul_rew = self.episode_step_ct = self.cumul_rew_delta = 0
            # self.episode_ct += 1
            ter = False
            tru = False
        self.cumul_rew += rew
        self.episode_step_ct += 1
        self.rew_delta = (rew - self.rew_prev)
        self.rew_prev = rew
        self.cumul_rew_delta += self.rew_delta
        eiv = self.encode_eiv(obs, self.rew_delta)
        return eiv.copy()
    def encode_eiv(self, obs_in, rew_delta_in):
        out = set()
        for i, a in enumerate(obs_in):
            if (i in self.obs_vals.keys()):
                min_val = min(abs(value[0] - a) for value in self.obs_vals[i].values())
                for value in self.obs_vals[i].values():
                    if (abs(value[0] - a) == min_val): out |= value[1]
        min_val = min(abs(value[0] - rew_delta_in) for value in self.rew_vals.values())
        for value in self.rew_vals.values():
            if (abs(value[0] - rew_delta_in) == min_val): out |= value[1]
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
        self.context_dim = 2#----------------------------------------------------------------------------------------------------HP
        self.blank_av = ([0] * (self.po.K * self.context_dim))
        self.blank_cv = ([0] * self.po.K)
        self.read_v = self.blank_cv.copy()
        self.conf_v = self.blank_cv.copy()
        self.poss_indices = set(range(self.po.Z))
        self.mem = dict()
        self.iv = self.pev = self.Bv = self.Av = self.gt_cv = self.pv = self.vi = self.ppcv = set()
        self.r_max = 4#-----------------------------------------------------------------------------------------------------------HP
        self.num_samples_min = 5#-should be odd???!!!-----------------------------------------------------------------------------HP
        self.write_delta_max = 10#------------------------------------------------------------------------------------------------HP
        num_steps_to_max = 12#-7---------------------------------------------------------------------------------------------------HP
        self.cv_max = (num_steps_to_max * self.write_delta_max)
        self.cv_min = -(self.cv_max - 1)
        self.tp = 0
        self.agency = False
    def update(self):
        #-----TODO: attentional masking and explicit control of noise masking
        fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        # fbv = self.po.m[self.fbi].pv.copy()#--------------------------I think this is causing issues???YES!!!IT IS!!!because of mb!!!
        if (self.context_dim == 2): self.gt_cv = (self.iv | {(self.po.K + a) for a in fbv})
        if (self.context_dim == 3): self.gt_cv = (self.iv | {(self.po.K + a) for a in self.pv} | {((self.po.K * 2) + b) for b in fbv})
        self.Bv = self.gt_cv.copy()
        #_____________________________________________________________________________________________________________________________
        avail_indices = (self.poss_indices - set(self.mem.keys()) - self.vi)
        if (len(avail_indices) > 0):
            self.mem[random.choice(list(avail_indices))] = [self.gt_cv.copy(), self.blank_cv.copy(), self.po.pv_initial]
        #_____________________________________________________________________________________________________________________________
        # self.vi = set()
        # self.read_v = self.blank_cv.copy()
        while (len(self.Bv ^ self.Av) > 0):
            si = list(self.mem.keys())
            random.shuffle(si)
            self.vi = set()
            r = 0
            avg_av_list = self.blank_av.copy()
            self.read_v = self.blank_cv.copy()
            # while ((len(si) > 0) and (r < self.r_max)):
            while ((len(si) > 0) and (len(self.vi) < self.num_samples_min)):
                for a in si:
                    tav = self.mem[a][0]
                    d = len(tav ^ self.Bv)
                    if (d == r):
                        for i, b in enumerate(avg_av_list):
                            if (i in tav): avg_av_list[i] += 1
                            else: avg_av_list[i] -= 1
                        ##########################################################################################################
                        rew_delta_value = 0
                        rew_delta_ct = 0
                        for value in self.po.rew_vals.values():
                            seg = [self.mem[a][1][b] for b in value[1]]
                            if (sum(seg) > 0):
                                ov = 0
                                conf = 0
                                for b in seg:
                                    if (b > 0):
                                        conf += (float(b) / float(self.cv_max))
                                        ov += 1
                                    else:
                                        conf += (float(abs(b)) / float(self.cv_min))
                                conf /= float(max(1, len(seg)))
                                ov = (float(ov) / float(max(1, len(seg))))
                                rew_delta_value += (value[0] * conf * ov)
                                rew_delta_ct += 1
                        rew_delta_value /= float(max(1, rew_delta_ct))
                        policy_alignment_factor = 5.50#--------------------------------------------------------------------------HP
                        adj_val = (rew_delta_value * policy_alignment_factor)
                        if (adj_val != 0):
                            for b in self.po.act_vals.keys():
                                for value in self.po.act_vals[b].values():
                                    conf = 0
                                    for c in value[1]:
                                        val = self.mem[a][1][c]
                                        if (val > 0):
                                            conf += (float(val) / float(self.cv_max))
                                        else:
                                            conf += (float(abs(val)) / float(self.cv_min))
                                        val = (self.mem[a][1][c] + round(conf * adj_val))
                                        if (val < self.cv_min): val = self.cv_min
                                        if (val > self.cv_max): val = self.cv_max
                                        self.mem[a][1][c] = val
                        ###########################################################################################################
                        for i, b in enumerate(self.mem[a][1]):
                            if (self.read_v[i] >= 0): val = min((self.po.max_int - self.read_v[i]),  b)
                            else: val = max((self.po.min_int - self.read_v[i]),  b)
                            self.read_v[i] += val
                        self.mem[a][2] = min((self.mem[a][2] + 5), self.po.pv_max)#----------------------------------------------HP
                        self.vi.add(a)
                si = [c for c in si if (c not in self.vi)]
                r += 1
            self.Av = self.Bv.copy()
            self.Bv = {i for i, a in enumerate(avg_av_list) if (a > 0)}
        #___________________________________________________________________________________________________________________________
        dist = min(len(self.mem[a][0] ^ self.Bv) for a in self.mem.keys())
        if (dist > 0):
            avail_indices = (self.poss_indices - set(self.mem.keys()) - self.vi)
            if (len(avail_indices) > 0):
                self.mem[random.choice(list(avail_indices))] = [self.Bv.copy(), self.blank_cv.copy(), self.po.pv_initial]
        #___________________________________________________________________________________________________________________________
        conf_thresh = 0.10#-----------------------------------------------------------------------------------------------------HP
        self.pv = set()
        self.conf_v = []
        for i, a in enumerate(self.read_v):
            if (a > 0):
                val = (float(a) / float(self.cv_max))
                # if (val >= conf_thresh): self.pv.add(i)#--THIS MAY CAUSE ISSUES???
                self.pv.add(i)
                self.conf_v.append(val)
            else:
                val = (float(abs(a)) / float(self.cv_min))
                self.conf_v.append(val)
        #____________________________________________________________________________________________________________________________
        if (self.mi == 0):
            self.ppcv = set()
            for a in self.po.act_vals.keys():
                for value in self.po.act_vals[a].values(): self.ppcv |= (value[1] & self.pv)
            self.agency = (len(self.ppcv) > 0)
            if ((self.agency == False) and (random.randrange(1000000) < 500000)):#-motor babble-------HP
                riA = random.choice(list(self.po.act_vals.keys()))
                riB = random.choice(list(self.po.act_vals[riA].keys()))
                self.ppcv = self.po.act_vals[riA][riB][1].copy()
                self.pv |= self.ppcv
            #------TODO: embed RL signals and prediction confidence into input
            self.iv = self.po.interface_env(self.pv.copy()).copy()
            self.iv |= self.ppcv
            self.ppcv = set()
        else: self.iv = self.po.m[self.ffi].pev.copy()
        self.pev = (self.iv ^ self.pv)
        erm = ((float(len(self.pev)) / float(max(1, (len(self.iv) + len(self.pv))))) * 100.0)
        #____________________________________________________________________________________________________________________________
        for a in self.vi:
            for i, b in enumerate(self.mem[a][1]):
                write_delta = round((1.0 - self.conf_v[i]) * float(self.write_delta_max))
                # write_delta = 1
                if (write_delta != 0):
                    if (i in self.iv):
                        # write_delta = round((1.0 - self.conf_v[i]) * float(self.write_delta_max)) 
                        self.mem[a][1][i] = min(self.cv_max, (b + write_delta))
                    if (i not in self.iv):
                        # write_delta = round(self.conf_v[i] * float(self.write_delta_max)) 
                        self.mem[a][1][i] = max(self.cv_min, (b - write_delta))
        #____________________________________________________________________________________________________________________________
        self.tp = sum((len(self.mem[a][0]) + len(self.mem[a][1]) + 2) for a in self.mem.keys())
        agency_str = f"\tEX_ACT: {self.po.ex_act_val[0]:.4f}" if (self.agency) else ""
        # agency_str = f"\tEX_ACT: {self.po.ex_act_val[0]:.4f}" if (self.mi == 0) else ""
        print(f"M{self.mi}\tER: {erm:.2f}%\tTP: {self.tp}\tMEM: {len(self.mem.keys())}\tREW: {self.po.rew_metric:.2f}%" + agency_str)
        #____________________________________________________________________________________________________________________________
        indices = (set(self.mem.keys()) - self.vi)
        while ((len(indices) + 4) > self.po.Z):
            rv = min(self.mem[a][2] for a in indices)
            cands = [a for a in indices if (self.mem[a][2] == rv)]
            ri = random.choice(cands)
            indices.remove(ri)
            del self.mem[ri]
oracle = Oracle()
oracle.update()