import random
class Oracle:
    def __init__(self):
        self.H = 6#----------------------------------------------------------------------------------------------------------------HP
        self.K = 67#-67--------------------------------------------------------------------------------------------------------------HP
        self.Z = 257#--------------------------------------------------------------------------------------------------------------HP
        self.pv_min = 71#-41------------------------------------------------------------------------------------------------------HP
        self.pv_range = 1.73#------------------------------------------------------------------------------------------------------HP
        self.pv_max = max((self.pv_min + 1), round(float(self.pv_min) * self.pv_range))
        self.ppcv_dim = 5#-5------------------------------------------------------------------------------------------------------HP
        self.ppcv_L = set(range((self.K - (self.ppcv_dim * 2)), (self.K - self.ppcv_dim)))
        self.ppcv_R = set(range((self.K - self.ppcv_dim), self.K))
        #____________________________________________________________________________________________________________________________
        ts_dim = 5#----------------------------------------------------------------------------------------------------------------HP
        ts_range_set = (set(range(self.K)) - self.ppcv_L - self.ppcv_R)
        ts_density = 0.57#-0.37--------------------------------------------------------------------------------------------------------HP
        ts_card = round(float(len(ts_range_set)) * ts_density)
        self.ts = []
        self.ts_index = self.cycle = 0
        while (len(self.ts) < ts_dim):
            ts_range_set_temp = ts_range_set.copy()
            tv = set()
            while (len(tv) < ts_card):
                ri = random.choice(list(ts_range_set_temp))
                ts_range_set_temp.remove(ri)
                tv.add(ri)
            self.ts.append(tv.copy())
        #______________________________________________________________________________________________________________________________
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while (True):
            for a in self.m: a.update()
            print()
            self.cycle += 1
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
        self.aa_factor = 5#-10---------------------------------------------------------------------------------------------------HP
        self.write_delta_max = 9#-507-musn't be set too low???!!!---------------------------------------------------------------HP
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
        while ((len(self.Bv ^ self.Av) > 0) and (aa_ct < self.aa_factor)):
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
            self.ppc_signal = 0
            self.agency = False
            if (len(self.pv & self.po.ppcv_L) == self.po.ppcv_dim):
                self.ppc_signal += -1
                self.agency = True
            if (len(self.pv & self.po.ppcv_R) == self.po.ppcv_dim):
                self.ppc_signal += 1
                self.agency = True
            both = ((self.agency == True) and (self.ppc_signal == 0))
            if (both or ((random.randrange(1000000) < 500000) and (self.agency == False))):#-motor babble--------------------------HP
                self.ppc_signal = random.choice([-1, 1])
            #------TODO: encode reward signals and prediction confidence into input
            self.po.ts_index = ((self.po.ts_index + len(self.po.ts) + self.ppc_signal) % len(self.po.ts))
            self.iv = self.po.ts[self.po.ts_index].copy()
            if (self.ppc_signal == -1): self.iv |= self.po.ppcv_L
            if (self.ppc_signal == 1): self.iv |= self.po.ppcv_R
            # self.po.ts_index = ((self.po.ts_index + len(self.po.ts) + self.ppc_signal) % len(self.po.ts))
        else: self.iv = self.po.m[self.ffi].ov.copy()
        #____________________________________________________________________________________________________________________________
        #-------TODO: modulate write_delta proportional to prediction confidence and RL signals
        write_delta = self.write_delta_max
        for i, a in enumerate(self.mem[self.rel_idx][1]):
            # write_delta = round((1.0 - conf_v[i]) * 1.0 * float(self.write_delta_max))#--------------causes issues!!??--Is this ideal???
            # write_delta = round(conf_v[i] * float(self.write_delta_max))#--------------causes issues!!??--Is this ideal???
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