import gymnasium as gym
env = gym.make('Pendulum-v1', g = 9.81, render_mode = "human")#-9.81
import random
class Oracle:
    def __init__(self):
        #_______________________________________________SETUP GYM DATA______________________________________________________________
        truncated_val = 6.0#-8.0-----------------------------------------------------------------------------------------------------HP
        # self.obs_indices = [0, 1, 2]#---------------------------------------------------------------------------------------------HP
        self.obs_indices = [0, 1]#---------------------------------------------------------------------------------------------HP
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
        self.rew_delta_range = 1.0#-----------------------------------------------------------------------------------------------HP
        self.rew_delta_min = -self.rew_delta_range
        self.rew_delta_max = self.rew_delta_range
        self.rew_delta_range = (self.rew_delta_max - self.rew_delta_min)
        self.rew_delta = 0
        total_dim = (len(self.obs_indices) + len(self.act_indices) + 1)
        self.episode_ct = self.episode_step_ct = self.cycle = self.cumul_rew = self.rew_prev = self.rew_metric = 0
        self.env_seed = 123456#----------------------------------------------------------------------------------------------------HP
        self.num_values = (int(truncated_val * 2.0) + 1)#----------------------------------------------------------------------------HP
        self.enc_card = 16#----------------------------------------------------------------------------------------------------------HP
        #______________________________________________________________________________________________________________________________
        self.H = 6#----------------------------------------------------------------------------------------------------------------HP
        self.K = (total_dim * (self.num_values + (self.enc_card - 1)))
        self.Z = 257#--------------------------------------------------------------------------------------------------------------HP
        self.pv_min = 71#-41------------------------------------------------------------------------------------------------------HP
        self.pv_range = 1.73#------------------------------------------------------------------------------------------------------HP
        self.pv_max = max((self.pv_min + 1), round(float(self.pv_min) * self.pv_range))
        #____________________________________________________DATA ENCODING___________________________________________________________
        gl_index = 0
        self.obs_vals = dict()
        for a in self.obs_indices:
            inc = (float(self.obs_range_h[a] - self.obs_range_l[a]) / float(self.num_values - 1))
            td = dict()
            for b in range(self.num_values):
                td[b] = [(float(self.obs_range_l[a]) + (float(b) * inc)), {(gl_index + b + c) for c in range(self.enc_card)}]
            self.obs_vals[a] = td.copy()
            gl_index += self.num_values
        self.act_vals = dict()
        for a in self.act_indices:
            inc = (float(self.act_range_h[a] - self.act_range_l[a]) / float(self.num_values - 1))
            td = dict()
            for b in range(self.num_values):
                td[b] = [(float(self.act_range_l[a]) + (float(b) * inc)), {(gl_index + b + c) for c in range(self.enc_card)}]
            self.act_vals[a] = td.copy()
            gl_index += self.num_values
        inc = (float(self.rew_delta_range) / float(self.num_values - 1))
        self.rew_vals = dict()
        for a in range(self.num_values):
            self.rew_vals[a] = [(float(self.rew_delta_min) + (float(a) * inc)), {(gl_index + a + b) for b in range(self.enc_card)}]
        #______________________________________________________________________________________________________________________________
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        env.reset(seed = self.env_seed)
        while (True):
            for a in self.m: a.update()
            print()
            # self.cycle += 1
    def interface_env(self, eov_in):
        obs, rew, ter, tru, inf = env.step(self.decode_eov(eov_in))
        if (ter or tru):
            env.reset(seed = self.env_seed)
            norm = (self.rew_range_l * float(max(self.episode_step_ct, 1)))
            self.rew_metric = ((float(self.cumul_rew) / norm) * 100.0)
            self.cumul_rew = self.rew_prev = self.episode_step_ct = 0
            self.episode_ct += 1
        # else:
        self.cumul_rew += rew
        self.episode_step_ct += 1
        self.rew_delta = (rew - self.rew_prev)
        # self.rew_delta = 0
        self.rew_prev = rew
        eiv = self.encode_eiv(obs, self.rew_delta, eov_in)
        return eiv.copy()
    def encode_eiv(self, obs_in, rew_delta_in, eov_in):
        out = set()
        for i, a in enumerate(obs_in):
            if (i in self.obs_vals.keys()):
                td = {key:abs(value[0] - a) for key, value in self.obs_vals[i].items()}
                cands = [key for key, value in td.items() if (value == min(td.values()))]
                rand_idx = random.choice(cands)
                for b in self.obs_vals[i][rand_idx][1]: out.add(b)
        # td = {key:abs(value[0] - rew_delta_in) for key, value in self.rew_vals.items()}
        # cands = [key for key, value in td.items() if (value == min(td.values()))]
        # rand_idx = random.choice(cands)
        # for b in self.rew_vals[rand_idx][1]: out.add(b)
        return out
    def decode_eov(self, eov_in):
        out = []
        for a in self.act_vals.keys():
            td = {key:len(value[1] ^ eov_in) for key, value in self.act_vals[a].items()}
            cands = [self.act_vals[a][key][0] for key, value in td.items() if (value == min(td.values()))]
            val = (float(sum(cands)) / float(max(1, len(cands))))
            out.append(val)
        return tuple(out)
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.mi = mi_in
        self.ffi = (self.mi - 1)
        self.fbi = ((self.mi + 1) % self.po.H)
        self.blank_cv = [0] * self.po.K
        # self.read_v = self.blank_cv.copy()
        self.read_comp_v = self.blank_cv.copy()
        self.poss_indices = set(range(self.po.Z))
        self.mem = dict()
        self.iv = self.ov = self.Bv = self.Av = self.pv = set()
        self.sample_min = 9#-13-musn't be set too high????!!!!--------------------------------------------------------------------HP
        self.sample_pct = 0.02#-0.04-0.05-----------------------------------------------------------------------------------------HP
        self.aa_factor = 1#-10---------------------------------------------------------------------------------------------------HP
        self.write_delta_max = 9#-musn't be set too low???!!!---------------------------------------------------------------HP
        num_steps_to_max = 167#-67-------------------------------------------------------------------------------------------------HP
        self.cv_max = (self.write_delta_max * num_steps_to_max)
        self.cv_min = -(self.write_delta_max * (num_steps_to_max - 1))
        self.ppc_signal = self.tp = self.rel_idx = 0
        self.agency = False
    def update(self):
        # fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        fbv = self.po.m[self.fbi].pv.copy()
        self.Bv = (self.iv | {(self.po.K + a) for a in fbv})
        #_____________________________________________________________________________________________________________________________
        avail_indices = (self.poss_indices - set(self.mem.keys()))
        self.mem[random.choice(list(avail_indices))] = [self.Bv.copy(), self.blank_cv.copy(), random.randrange(self.po.pv_min, self.po.pv_max)]
        #_____________________________________________________________________________________________________________________________
        aa_ct = 0
        num_samples_min = max(self.sample_min, round(float(len(self.mem)) * self.sample_pct))
        self.read_comp_v = self.blank_cv.copy()
        while((len(self.Bv ^ self.Av) > 0) and (aa_ct < self.aa_factor)):
            si = list(self.mem.keys())
            random.shuffle(si)
            skip = set()
            r = 0
            avg_vA_dict = dict()
            # self.read_v = self.blank_cv.copy()
            while ((len(si) > 0) and (len(skip) < num_samples_min)):
                for a in si:
                    tav = self.mem[a][0]
                    d = len(tav ^ self.Bv)
                    if (d == r):
                        for b in tav:
                            if (b in avg_vA_dict.keys()): avg_vA_dict[b] += 1
                            else: avg_vA_dict[b] = 1
                        for b in avg_vA_dict.keys():
                            if (b not in tav): avg_vA_dict[b] -= 1
                        # for i, b in enumerate(self.mem[a][1]): self.read_v[i] += b
                        for i, b in enumerate(self.mem[a][1]): self.read_comp_v[i] += b
                        self.mem[a][2] = random.randrange(self.po.pv_min, self.po.pv_max)
                        skip.add(a)
                si = [c for c in si if (c not in skip)]
                r += 1
            self.Av = self.Bv.copy()
            self.Bv = {key for key, value in avg_vA_dict.items() if (value > 0)}
            aa_ct += 1
        self.Av = self.Bv.copy()
        dist = min(len(self.mem[a][0] ^ self.Bv) for a in self.mem.keys())
        if (dist > 0):
            avail_indices = (self.poss_indices - set(self.mem.keys()))
            self.rel_idx = random.choice(list(avail_indices))
            self.mem[self.rel_idx] = [self.Bv.copy(), self.blank_cv.copy(), random.randrange(self.po.pv_min, self.po.pv_max)]
        else:
            cands = [a for a in self.mem.keys() if (len(self.mem[a][0] ^ self.Bv) == dist)]
            self.rel_idx = random.choice(cands)
        # ref_v = self.read_v.copy()#----------which one is better and why???
        ref_v = self.read_comp_v.copy()#----------which one is better and why???
        # norm = float(max(abs(min(ref_v)), abs(max(ref_v)), 1))
        # conf_v = [(float(abs(a)) / norm) for a in ref_v]
        self.pv = {i for i, a in enumerate(ref_v) if (a > 0)}
        #____________________________________________________________________________________________________________________________
        if (self.mi == 0):
            self.iv = self.po.interface_env(self.pv.copy()).copy()
            #--------------------------------------------------------------------------------------union ppc signal here?????????
        else: self.iv = self.po.m[self.ffi].ov.copy()
        #____________________________________________________________________________________________________________________________
        #-------TODO: modulate write_delta proportional to prediction confidence and RL signals
        write_delta = self.write_delta_max
        for i, a in enumerate(self.mem[self.rel_idx][1]):
            if ((i in self.iv) and ((a + write_delta) <= self.cv_max)): self.mem[self.rel_idx][1][i] += write_delta
            if ((i not in self.iv) and ((a - write_delta) >= self.cv_min)): self.mem[self.rel_idx][1][i] -= write_delta
        #____________________________________________________________________________________________________________________________
        self.ov = (self.iv ^ self.pv)
        erm = ((float(len(self.ov)) / float(max(1, (len(self.iv) + len(self.pv))))) * 100.0)
        self.tp = sum((len(self.mem[a][0]) + len(self.mem[a][1]) + 2) for a in self.mem.keys())
        agency_str = f"\tPPC: {self.ppc_signal}\t{self.rel_idx}" if ((self.mi == 0) and (self.agency)) else ""
        print(f"M{self.mi}\tER: {erm:.2f}%\tTP: {self.tp}\tMEM: {len(self.mem.keys())}" + agency_str)
        #___________________________________________________________________________________________________________________________
        thresh = 2
        while ((len(self.mem) + thresh) > self.po.Z):
            si = list(self.mem.keys())
            random.shuffle(si)
            for a in si:
                if (self.mem[a][2] > 0): self.mem[a][2] -= 1
                else:
                    if ((len(self.mem) + thresh) > self.po.Z): del self.mem[a]
oracle = Oracle()
oracle.update()