import gymnasium as gym
env = gym.make('Pendulum-v1', g = 0.00, render_mode = "human")#-9.81
import random
class Oracle:
    def __init__(self):
        #_______________________________________________SETUP GYM DATA______________________________________________________________
        truncated_val = 36.0#-8.0-------------------------------------------------------------------------------------------------HP
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
        self.rew_delta_mag = 1.0#-------------------------------------------------------------------------------------------------HP
        self.rew_delta_min = -self.rew_delta_mag
        self.rew_delta_max = self.rew_delta_mag
        self.rew_delta_range = (self.rew_delta_max - self.rew_delta_min)
        self.rew_delta = 0
        self.episode_ct = self.episode_step_ct = self.cycle = self.cumul_rew = self.rew_prev = self.rew_metric = 0
        self.env_seed = 123456#---------------------------------------------------------------------------------------------------HP
        self.num_values = 7#-should always be odd!!!------------------------------------------------------------------------------HP
        self.enc_card = 6#--------------------------------------------------------------------------------------------------------HP
        #____________________________________________________DATA EMBEDDING_________________________________________________________
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
        gl_index += self.num_values
        #____________________________________________________________________________________________________________________________
        self.K = (gl_index + (self.enc_card - 1))
        self.H = 3#----------------------------------------------------------------------------------------------------------------HP
        self.ex_act_val = []
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        env.reset(seed = self.env_seed)
        while (True):
            for a in self.m: a.update()
            # self.cycle += 1
    def interface_env(self, eov_in):
        obs, rew, ter, tru, inf = env.step(self.decode_eov(eov_in))
        if (ter or tru):
            env.reset(seed = self.env_seed)
            norm = (self.rew_range_l * float(max(self.episode_step_ct, 1)))
            self.rew_metric = ((float(self.cumul_rew) / norm) * 100.0)
            self.cumul_rew = self.rew_prev = self.episode_step_ct = 0
            self.episode_ct += 1
        # else:#--????
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
        return out.copy()
    def decode_eov(self, eov_in):
        out = []
        for a in self.act_vals.keys():
            td = {key:len(value[1] ^ eov_in) for key, value in self.act_vals[a].items()}
            cands = [self.act_vals[a][key][0] for key, value in td.items() if (value == min(td.values()))]
            val = (float(sum(cands)) / float(max(1, len(cands))))
            out.append(val)
        self.ex_act_val = out.copy()
        return tuple(out)
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.mi = mi_in
        self.ffi = (self.mi - 1)
        self.fbi = ((self.mi + 1) % self.po.H)
        self.blank_cv = {a for a in range((self.po.K * 2))}
        tl = [0] * (self.po.K * 2)
        self.e = {a:tl.copy() for a in range(self.po.K)}
        self.read_v = dict()
        self.iv = self.ov = self.pv = self.Av = set()
        self.aa_factor = 3#-10-----------------------------------------------------------------------------------------------------HP
        num_steps_to_max = 67#-67--------------------------------------------------------------------------------------------------HP
        self.cv_max = num_steps_to_max
        self.cv_min = -(num_steps_to_max - 1)
        self.tp = (len(self.e.keys()) * (len(tl) + 1))
        self.agency = False
    def update(self):
        # fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        fbv = self.po.m[self.fbi].pv.copy()
        cv = (self.iv | {(self.po.K + a) for a in fbv})
        Bv = cv.copy()
        #_____________________________________________________________________________________________________________________________
        aa_ct = 0
        while ((len(Bv ^ self.Av) > 0) and (aa_ct < self.aa_factor)):
            r = max(sum(self.e[a][b] for b in Bv) for a in self.e.keys())
            si = list(self.e.keys())
            random.shuffle(si)
            self.read_v = dict()
            while (r > 0):
                for a in si:
                    if (a not in self.read_v.keys()):
                         av = sum(self.e[a][b] for b in Bv)
                         if (av == r): self.read_v[a] = av
                r -= 1
            self.Av = Bv.copy()
            Bv = self.blank_cv.copy()
            for a in self.read_v.keys(): Bv &= {i for i, b in enumerate(self.e[a]) if (b > 0)}
            aa_ct += 1
        #___________________________________________________________________________________________________________________________        
        # norm = float(max(abs(min(ref_v)), abs(max(ref_v)), 1))
        # conf_v = [(float(abs(a)) / norm) for a in ref_v]
        self.pv = set(self.read_v.keys())
        #____________________________________________________________________________________________________________________________
        if (self.mi == 0):
            ppc_v = set()
            for a in self.po.act_vals.keys():
                for value in self.po.act_vals[a].values():
                    ppc_v |= (self.pv & value[1])
            self.agency = (len(ppc_v) > 0)
            if ((random.randrange(1000000) < 10000) and (self.agency == False)):#-motor babble------------------------------------HP
                riA = random.choice(list(self.po.act_vals.keys()))
                riB = random.choice(list(self.po.act_vals[riA].keys()))
                self.pv |= self.po.act_vals[riA][riB][1]
            #------TODO: embed RL signals and prediction confidence into input
            self.iv = self.po.interface_env(self.pv.copy()).copy()
            self.iv |= ppc_v
        else: self.iv = self.po.m[self.ffi].ov.copy()
        self.ov = (self.iv ^ self.pv)
        failed_pev = (self.iv - self.pv)
        false_pev = (self.pv - self.iv)
        #____________________________________________________________________________________________________________________________
        #-------TODO: modulate write_delta proportional to prediction confidence and RL signals
        write_delta = 1#-----------------------------------------------------------------------------------------------------------HP
        for a in cv:
            for b in failed_pev:
                if ((self.e[b][a] + write_delta) <= self.cv_max): self.e[b][a] += write_delta
            for b in false_pev:
                if ((self.e[b][a] - write_delta) >= self.cv_min): self.e[b][a] -= write_delta
        #____________________________________________________________________________________________________________________________
        erm = ((float(len(self.ov)) / float(max(1, (len(self.iv) + len(self.pv))))) * 100.0)
        agency_str = f"\tEX_ACT: {self.po.ex_act_val[0]:.2f}" if (self.agency) else ""
        print(f"M{self.mi}\tER: {erm:.2f}%\tTP: {self.tp}" + agency_str)
oracle = Oracle()
oracle.update()