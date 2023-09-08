import gymnasium as gym
env = gym.make('Pendulum-v1', g = 0, render_mode = "human")
import random
class Oracle:
    def __init__(self):
        #_______________________________________________SETUP GYM DATA______________________________________________________________
        truncated_val = 8.0#------------------------------------------------------------------------------------------------------HP
        self.obs_indices = [0, 1, 2]#---------------------------------------------------------------------------------------------HP
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
        self.episode_ct = self.episode_step_ct = 0
        self.cumul_rew = 0
        #____________________________________________________ORACLE RESOURCES________________________________________________________
        self.H = 3#----------------------------------------------------------------------------------------------------------------HP
        self.K = (total_dim * (int(truncated_val * 2.0) + 1))#---------------------------------------------------------------------HP
        self.M = 50#---------------------------------------------------------------------------------------------------------------HP
        self.adc_val = 807#--------------------------------------------------------------------------------------------------------HP
        self.env_seed = 123456#----------------------------------------------------------------------------------------------------HP
        self.N = (self.K * self.M)
        self.rew_prev = self.rew_metric = self.cycle = 0
        self.m = [Matrix(self, a) for a in range(self.H)]
        #____________________________________________________SETUP DATA______________________________________________________________
        equi = (self.K // total_dim)
        gl_index = 0
        self.obs_vals = dict()
        for a in self.obs_indices:
            inc = (float(self.obs_range_h[a] - self.obs_range_l[a]) / float(equi - 1))
            td = dict()
            for b in range(equi):
                td[gl_index] = (float(self.obs_range_l[a]) + (float(b) * inc))
                gl_index += 1
            self.obs_vals[a] = td.copy()
        self.act_vals = dict()
        for a in self.act_indices:
            inc = (float(self.act_range_h[a] - self.act_range_l[a]) / float(equi - 1))
            td = dict()
            for b in range(equi):
                td[gl_index] = (float(self.act_range_l[a]) + (float(b) * inc))
                gl_index += 1
            self.act_vals[a] = td.copy()
        inc = (float(self.rew_delta_range) / float(equi - 1))
        self.rew_vals = dict()
        for a in range(equi):
            self.rew_vals[gl_index] = (float(self.rew_delta_min) + (float(a) * inc))
            gl_index += 1
    def update(self):
        env.reset(seed = self.env_seed)
        while (True):
            for a in self.m: a.update()
            self.cycle += 1
    def interface_env(self, eov_in):
        eiv = set()
        act = self.decode_eov(eov_in)
        obs, rew, ter, tru, inf = env.step(act)
        if (ter or tru):
            env.reset(seed = self.env_seed)
            norm = (self.rew_range_l * float(max(self.episode_step_ct, 1)))
            self.rew_metric = ((float(self.cumul_rew) / norm) * 100.0)
            self.cumul_rew = self.rew_prev = self.episode_step_ct = 0
            # for a in self.m:
            #     a.av = set()
            #     a.eov = set()
            #     a.ov = set()
            self.episode_ct += 1
        # else:
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
                td = {key:abs(value - a) for key, value in self.obs_vals[i].items()}
                cands = [key for key, value in td.items() if (value == min(td.values()))]
                out.add(random.choice(cands))
        td = {key:abs(value - rew_delta_in) for key, value in self.rew_vals.items()}
        cands = [key for key, value in td.items() if (value == min(td.values()))]
        out.add(random.choice(cands))
        return out.copy()
    def decode_eov(self, eov_in):
        out = []
        for a in self.act_vals.keys():
            cands = [value for key, value in self.act_vals[a].items() if (key in eov_in)]
            val = random.choice(cands) if (len(cands) > 0) else random.choice(list(self.act_vals[a].values()))
            out.append(val)
        return tuple(out)
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.mi = mi_in
        self.ffi = (self.mi - 1)
        self.fbi = ((self.mi + 1) % self.po.H)
        self.e = dict()
        self.ov = self.av = self.eov = set()
        self.tp = 0
    def update(self):
        if (self.mi == 0):
            if ((self.po.rew_delta < 0) and (len(self.av) > 0)):
                av_sub = set()
                for a in self.po.act_vals.keys():
                    for b in self.po.act_vals[a].keys():
                        ci = set(range((self.po.M * b), (self.po.M * (b + 1))))
                        tv = (self.av & ci & set(self.e.keys()))
                        if (len(tv) == 1): av_sub |= tv
                if (len(av_sub) > 0):
                    riA = random.choice(list(av_sub))
                    tv = (self.av & set(self.e[riA].keys()))
                    le = max((len(tv) - 8), 0)#-------------------------------------------------------------------------------HP
                    while (len(tv) > le):
                        riB = random.choice(list(tv))
                        tv.remove(riB)
                        del self.e[riA][riB]
        #___________________________GENERATE CONTEXT VECTOR AND COMPUTE PREDICTIVE ACTIVATION____________________________________
        # fbv = self.po.m[self.fbi].av.copy() if (self.fbi != 0) else set()
        fbv = self.po.m[self.fbi].av.copy()
        fbtv = set()
        for a in fbv:
            cli = (a // self.po.M)
            if (len(fbv & set(range((self.po.M * cli), (self.po.M * (cli + 1))))) == 1): fbtv.add(cli)
        fbv = fbtv.copy()
        fbv = {(a + self.po.N) for a in fbv}
        avs = {a:(len(set(self.e[a].keys()) & self.av) - len(set(self.e[a].keys()) & fbv)) for a in self.e.keys()}
        self.av = {a for a in avs.keys() if (avs[a] == max(avs.values()))}
        #_______________________________________MANIFEST ACTION AND STORE SELECTED INPUT__________________________________________
        if (self.mi == 0):
            cli_sub = set()
            for a in self.po.act_vals.keys():
                for b in self.po.act_vals[a].keys():
                    ci = set(range((self.po.M * b), (self.po.M * (b + 1))))
                    tv = (self.av & ci & set(self.e.keys()))
                    if (len(tv) == 1): cli_sub.add(b)
            if ((len(cli_sub) == 0) and (len(self.av) > 0) and (random.randrange(1000000) < 100000)):#-motor babble--------------HP
            # if ((len(cli_sub) == 0) and (len(self.av) > 0)):#-motor babble--------------------------------------------------HP
                riA = random.choice(list(self.po.act_vals.keys()))
                riB = random.choice(list(self.po.act_vals[riA].keys()))
                cli_sub.add(riB)
                ci = set(range((self.po.M * riB), (self.po.M * (riB + 1))))
                riC = random.choice(list(ci))
                ci_modA = (ci - set(self.e.keys()))
                ci_modB = {a for a in (ci & set(self.e.keys())) if (len(self.e[a].keys()) == 0)}
                if (len(ci_modA) > 0): riC = random.choice(list(ci_modA))
                if (len(ci_modB) > 0): riC = random.choice(list(ci_modB))
                temp_adc = 4#---------------------------------------------------------------------------------------------------HP
                if (riC in self.e.keys()):
                    for a in self.av: self.e[riC][a] = temp_adc
                else: self.e[riC] = {a:temp_adc for a in self.av}
            self.eov = cli_sub.copy()
            iv = self.po.interface_env(self.eov.copy()).copy()
        else: iv = self.po.m[self.ffi].ov.copy()
        #_____________________________________COMPUTE PREDICTION ERROR AND OPTIMIZE CONNECTIONS___________________________________
        exp = set()
        self.ov = set()
        em = zr = mr = 0
        for a in iv:
            ci = set(range((self.po.M * a), (self.po.M * (a + 1))))
            pv = (self.av & ci)
            exp |= pv
            if (len(pv) == 0):
                em += 1.0
                zr += 1.0
                ci_mod = [b for b in (ci & set(self.e.keys())) if (len(self.e[b].keys()) == 0)]
                wi = random.choice(list(ci)) if (len(ci_mod) == 0) else random.choice(ci_mod)
            if (len(pv) > 1):
                self.ov.add(a)
                em += (float(len(pv) - 1) / float(self.po.M - 1))
                mr += 1.0
                cands = [b for b in pv if (len(self.e[b].keys()) == min(len(self.e[b].keys()) for b in pv))]
                wi = random.choice(list(pv)) if (len(cands) == 0) else random.choice(cands)
                for b in pv:
                    if (b != wi):
                        if (len(fbv) > 0):
                            self.e[b][random.choice(list(fbv))] = self.po.adc_val
                        else:
                            ovA = (self.av & set(self.e[wi].keys()) & set(self.e[b].keys()))
                            if (len(ovA) > 0): del self.e[b][random.choice(list(ovA))]
            if (len(pv) == 1): wi = random.choice(list(pv))
            if wi in self.e.keys():
                for b in self.av: self.e[wi][b] = self.po.adc_val
            else: self.e[wi] = {b:self.po.adc_val for b in self.av}
        #_______________________________________PRUNE NETWORK AND COMPUTE METRICS_________________________________________________
        den = float(max(1, len(iv)))
        em /= den
        zr /= den
        mr /= den
        exp = (self.av - exp)
        for a in self.e.keys(): self.e[a] = {key:(value - 1) for key, value in self.e[a].items() if (value > 0)}
        if (len(self.e.keys()) > 500): self.e = {key:value for key, value in self.e.items() if (len(value.keys()) > 0)}#---------HP
        self.tp = sum(((len(self.e[a].keys()) * 2) + 1) for a in self.e.keys())
        # if (self.mi == 0): print(f"CY: {self.po.cycle}")
        print(f"M{self.mi}: EM: {(em * 100.0):.2f}%\tZR: {(zr * 100.0):.2f}%\tMR: {(mr * 100.0):.2f}%" + 
              f"\tEL: {len(self.e.keys())}   \tTP: {self.tp}    \tEX: {len(exp)}\tREW: {self.po.rew_metric:.2f}%")
oracle = Oracle()
oracle.update()