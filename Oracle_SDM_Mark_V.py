import gymnasium as gym
env = gym.make('Pendulum-v1', g = 9.81, render_mode = "human")#-9.81
import random
import math
import sys
class Oracle:
    def __init__(self):
        self.max_int = (sys.maxsize - 10)
        self.min_int = -(self.max_int - 1)
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
        self.env_seed = 123456#---------------------------------------------------------------------------------------------------HP
        self.num_values = 7#-must be odd!!!
        self.enc_card = 7#-7-must be odd!!!!!!!!----------------------------------------------------------------------------------HP
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
        self.H = 2#----------------------------------------------------------------------------------------------------------------HP
        self.Z = 577#--------------------------------------------------------------------------------------------------------------HP
        self.pv_max = 10000#--------------------------------------------------------------------------------------------------------HP
        self.ex_act_val = []
        self.run_continuous = True
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        env.reset(seed = self.env_seed)
        # env.reset()
        while (True):
            for a in self.m: a.update()
    def interface_env(self, eov_in):
        obs, rew, ter, tru, inf = env.step(self.decode_eov(eov_in))
        if (ter or tru):
            if (not self.run_continuous):
                env.reset(seed = self.env_seed)
                # env.reset()
            norm = (self.rew_range_l * float(max(self.episode_step_ct, 1)))
            self.rew_metric = (1.0 - (float(self.cumul_rew) / norm))
            self.cumul_rew = self.episode_step_ct = 0
            # self.rew_prev = rew#-------------------------HELPFUL???-----NECESSARY????
            # self.episode_ct += 1
            ter = False
            tru = False
        self.cumul_rew += rew
        self.episode_step_ct += 1
        self.rew_delta = (rew - self.rew_prev)
        self.rew_prev = rew
        self.rew_delta_mod = (self.rew_delta / self.rew_delta_mag)
        # eiv = self.encode_eiv(obs, self.rew_delta_mod)
        self.rew_mod_val = (rew / self.rew_range_l)
        eiv = self.encode_eiv(obs, self.rew_mod_val)
        return eiv.copy()
    def encode_eiv(self, obs_in, rew_delta_in):
        out = set()
        for i, a in enumerate(obs_in):
            if (i in self.obs_vals.keys()):
                min_val = min(abs(value[0] - a) for value in self.obs_vals[i].values())
                # cands = [value[1].copy() for value in self.obs_vals[i].values() if (abs(value[0] - a) == min_val)]
                # out |= random.choice(cands)
                for value in self.obs_vals[i].values():
                    if (abs(value[0] - a) == min_val): out |= value[1]
        min_val = min(abs(value[0] - rew_delta_in) for value in self.rew_vals.values())
        # cands = [value[1].copy() for value in self.rew_vals.values() if (abs(value[0] - rew_delta_in) == min_val)]
        # out |= random.choice(cands)
        for value in self.rew_vals.values():
            if (abs(value[0] - rew_delta_in) == min_val): out |= value[1]
        return out.copy()
    def decode_eov(self, eov_in):
        out = []
        for a in self.act_vals.keys():
            sum_v = [(value[0] * (float(len(value[1] & eov_in)) /
                                  float(len(value[1])))) for value in self.act_vals[a].values() if (len(value[1] & eov_in) > 0)]
            out.append((float(sum(sum_v)) / float(max(1, len(sum_v)))))
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
        self.num_samples_min = 5#-should be odd and not set too high!!!--------------------------------------------------------HP
        self.cv_max = 2000#-musn't be too low!!!!!-------------------------------------------------------------------------------HP
        self.cv_min = -(self.cv_max - 1)
        self.tp = self.gt_cv_index = self.novel_index = 0
        self.agency = False
        self.target_v = self.po.rew_vals[(self.po.num_values - 1)][1].copy()
        self.target_v_error = self.target_v_error_prev = self.novelty_factor = 0
        self.act_mask = set()
        for a in self.po.act_vals.keys():
            for value in self.po.act_vals[a].values(): self.act_mask |= value[1]
    def update(self):
        #-----TODO: attentional masking and explicit control of noise masking
        # fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        fbv = self.po.m[self.fbi].pv.copy()#--------------------------I think this is causing issues???YES!!!IT IS!!!because of mb!!!
        if (self.context_dim == 2): self.gt_cv = (self.iv | {(self.po.K + a) for a in fbv})
        if (self.context_dim == 3): self.gt_cv = (self.iv | {(self.po.K + a) for a in self.pv} | {((self.po.K * 2) + b) for b in fbv})
        self.Bv = self.gt_cv.copy()
        self.vi = set()
        #_____________________________________________________________________________________________________________________________
        avail_indices = (self.poss_indices - set(self.mem.keys()) - self.vi)
        if (len(avail_indices) > 0):
            self.gt_cv_index = random.choice(list(avail_indices))
            self.mem[self.gt_cv_index] = [self.gt_cv.copy(), self.blank_cv.copy(), self.po.pv_max]
            self.vi.add(self.gt_cv_index)
        #_____________________________________________________________________________________________________________________________
        self.read_v = self.blank_cv.copy()
        self.r_sc_factor = 2.0#----------------------------------------------------------------------------------------------------HP
        while (len(self.Av ^ self.Bv) > 0):
            si = list(self.mem.keys())
            random.shuffle(si)
            self.vi = set()
            r = 0
            avg_av_list = self.blank_av.copy()
            self.read_v = self.blank_cv.copy()
            num_attempts = 0
            num_attempts_max = 100#--------------------------------------------------------------------------------------------------HP
            sc = 1
            # while ((len(si) > 0) and (len(self.vi) < self.num_samples_min)):
            # while ((len(si) > 0) and (len(self.vi) < self.num_samples_min) and (num_attempts < num_attempts_max)):
            # while ((len(si) > 0) and (len(self.vi) < self.num_samples_min) and (sc > 0) and (num_attempts < num_attempts_max)):
            while ((len(si) > 0) and (len(self.vi) < self.num_samples_min) and (sc > 0)):
                # sc = round(10.0 / float(r + 1))
                sc = round(50.0 / math.pow(self.r_sc_factor, float(r)))
                for a in si:
                    tav = self.mem[a][0]
                    d = len(tav ^ self.Bv)
                    if (d == r):
                        for i, b in enumerate(avg_av_list): avg_av_list[i] += (sc if (i in tav) else -sc)
                        # for i, b in enumerate(avg_av_list): avg_av_list[i] += 1 if (i in tav) else -1
                        for i, b in enumerate(self.mem[a][1]):
                            if (self.read_v[i] > 0): val = min((self.po.max_int - self.read_v[i]),  (b * sc))
                            else: val = max((self.po.min_int - self.read_v[i]),  (b * sc))
                            self.read_v[i] += val
                        self.mem[a][2] = self.po.pv_max
                        self.vi.add(a)
                si = [c for c in si if (c not in self.vi)]
                r += 1
                num_attempts += 1
            self.Av = self.Bv.copy()
            self.Bv = {i for i, a in enumerate(avg_av_list) if (a > 0)}
        #___________________________________________________________________________________________________________________________
        self.novelty_factor = min(len(self.mem[a][0] ^ self.Bv) for a in self.mem.keys())
        #--------------------------TODO: use novelty_factor to optimize...
        self.novel_index = -1
        if (self.novelty_factor > 0):
            avail_indices = (self.poss_indices - set(self.mem.keys()) - self.vi)
            if (len(avail_indices) > 0):
                self.novel_index = random.choice(list(avail_indices))
                self.mem[self.novel_index] = [self.Bv.copy(), self.blank_cv.copy(), self.po.pv_max]
                self.vi.add(self.novel_index)
        #___________________________________________________________________________________________________________________________
        self.pv = {i for i, a in enumerate(self.read_v) if (a > 0)}
        # self.pv = set()
        # conf_thresh = 0.10#-musn't be set too high!!!!!-------------------------------------------------------------------------HP
        # self.conf_v = []
        # upper = [a for a in self.read_v if (a > 0)]
        # if (len(upper) == 0): upper = [1]
        # norm_max = float(max(upper))
        # lower = [abs(a) for a in self.read_v if (a <= 0)]
        # if (len(lower) == 0): lower = [1]
        # norm_min = float(max(1, max(lower)))
        # for i, a in enumerate(self.read_v):
        #     if (a > 0):
        #         val = (float(a) / norm_max)
        #         if (val >= conf_thresh): self.pv.add(i)#--THIS MAY CAUSE ISSUES???
        #     else:
        #         val = (float(abs(a)) / norm_min)
        #     self.conf_v.append(val)
        #____________________________________________________________________________________________________________________________
        target_belief = (float(len(self.target_v & self.pv)) / float(len(self.target_v)))
        # if (self.mi == 0): self.pv |= self.target_v#-----------IDK IF THIS IS A GOOD IDEA OR EVEN NECESSARY?????????????
        #____________________________________________________________________________________________________________________________
        if (self.mi == 0):#---TODO:--------------------------extend this or something like it to all matrices!!!!
            self.ppcv = (self.act_mask & self.pv)
            self.agency = (len(self.ppcv) > 0)
            # if ((not self.agency) and random.randrange(1000000) < 100000)):
            if (random.randrange(1000000) < 500000):
                self.agency = False
                if (len(self.ppcv) > 0): self.pv -= self.ppcv
                riA = random.choice(list(self.po.act_vals.keys()))
                riB = random.choice(list(self.po.act_vals[riA].keys()))
                self.ppcv = self.po.act_vals[riA][riB][1].copy()
                self.pv |= self.ppcv
            #------TODO: embed RL signals and prediction confidence into input
            self.iv = self.po.interface_env(self.pv).copy()
            self.iv |= self.ppcv#-------THIS MAY BE CAUSING ISSUES!!!!!!!!!!TODO: FIGURE OUT IF I NEED THIS HERE!!!!!!!
        else: self.iv = self.po.m[self.ffi].pev.copy()
        self.pev = (self.iv ^ self.pv)
        self.target_v_error = (float(len(self.target_v & self.iv)) / float(len(self.target_v)))
        target_v_error_delta = (self.target_v_error - self.target_v_error_prev)#-only changes by (1 / len(self.target_v)) at a time!!!!
        target_v_error_delta_sign = 1.0 if (target_v_error_delta >= 0) else -1.0
        self.target_v_error_prev = self.target_v_error
        erm = ((float(len(self.pev)) / float(max(1, (len(self.iv) + len(self.pv))))) * 100.0)
        #____________________________________________________________________________________________________________________________
        norm = float(self.cv_max - 1)
        conf = 0
        for a in self.vi:
            for i, b in enumerate(self.mem[a][1]):
                # if (self.mem[a][1][i] > 0): conf = (float(self.mem[a][1][i] - 1) / norm)
                # else: conf = (float(abs(self.mem[a][1][i])) / norm)
                # conf = self.conf_v[i]
                if (i in self.ppcv):
                    write_delta = round(target_v_error_delta_sign * (1.0 - self.target_v_error) * 50.0)#--------------------------HP
                    # write_delta = round((1.0 - conf) * target_v_error_delta_sign * (1.0 - self.target_v_error) * 15.0)#-----------HP
                    # print(write_delta)
                    if (write_delta != 0):
                        val = (self.mem[a][1][i] + write_delta)
                        if (val < self.cv_min): val = self.cv_min
                        if (val > self.cv_max): val = self.cv_max
                        self.mem[a][1][i] = val
                else:
                    # write_delta = round((1.0 - conf) * 10.0)#--------------------------------------------------------------------HP
                    # write_delta = 50
                    write_delta = 1
                    # print(write_delta)
                    if (write_delta != 0):
                        if (i in self.iv):
                            self.mem[a][1][i] = min(self.cv_max, (b + write_delta))
                        else:
                            self.mem[a][1][i] = max(self.cv_min, (b - write_delta))
        #____________________________________________________________________________________________________________________________
        self.tp = sum((len(self.mem[a][0]) + len(self.mem[a][1]) + 2) for a in self.mem.keys())
        agency_str = f"\tEX_ACT: {self.po.ex_act_val[0]:.4f}" if (self.agency) else ""
        # agency_str = f"\tEX_ACT: {self.po.ex_act_val[0]:.4f}" if (self.mi == 0) else ""
        print(f"M{self.mi}\tER: {erm:.2f}%\tTP: {self.tp}\tMEM: {len(self.mem.keys())}\tTB: {target_belief:.2f}%" +
              f"\tTA: {self.target_v_error:.2f}%\tREW: {(self.po.rew_metric * 100.0):.2f}%\tNOV: {self.novelty_factor}" +
              agency_str)
        #____________________________________________________________________________________________________________________________
        indices = (set(self.mem.keys()) - self.vi)
        # indices = set(self.mem.keys())
        for a in indices:
            if (self.mem[a][2] > 0): self.mem[a][2] -= 1
        while ((len(indices) + 2) > self.po.Z):
            rv = min(self.mem[a][2] for a in indices)
            cands = [a for a in indices if (self.mem[a][2] == rv)]
            ri = random.choice(cands)
            indices.remove(ri)
            del self.mem[ri]
random.seed(123456)#-------------------------------------------------------------------------------------------------HP
oracle = Oracle()
oracle.update()