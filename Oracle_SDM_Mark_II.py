import random
class Oracle:
    def __init__(self):
        self.H = 6#----------------------------------------------------------------------------------------------------------------HP
        self.K = 67#---------------------------------------------------------------------------------------------------------------HP
        self.Z = 201#--------------------------------------------------------------------------------------------------------------HP
        self.pv_min = 41#-41---------------------------------------------------------------------------------------------------------HP
        self.pv_range = 1.73#------------------------------------------------------------------------------------------------------HP
        self.pv_max = max((self.pv_min + 1), round(float(self.pv_min) * self.pv_range))
        self.ppcv_dim = 5#-5-------------------------------------------------------------------------------------------------------HP
        self.ppcv_L = set(range((self.K - (self.ppcv_dim * 2)), (self.K - self.ppcv_dim)))
        self.ppcv_R = set(range((self.K - self.ppcv_dim), self.K))
        self.m = [Matrix(self, a) for a in range(self.H)]
        #____________________________________________________________________________________________________________________________
        ts_dim = 5#----------------------------------------------------------------------------------------------------------------HP
        ts_range_set = (set(range(self.K)) - self.ppcv_L - self.ppcv_R)
        ts_density = 0.47#---------------------------------------------------------------------------------------------------------HP
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
        self.read_v = self.blank_cv.copy()
        self.read_comp_v = self.blank_cv.copy()
        self.poss_indices = set(range(self.po.Z))
        self.mem = dict()
        self.iv = self.ov = self.prototype_v = self.prev_v = self.pv = set()
        self.sample_min = 17#-15-musn't be set too high????!!!!-----------------------------------------------------------------------HP
        self.sample_pct = 0.04#-0.04---------------------------------------------------------------------------------------------------HP
        self.write_delta = 1001#-1001--------------------------------------------------------------------------------------------------HP
        num_steps_to_max = 41#-41---------------------------------------------------------------------------------------------------HP
        self.cv_max = (self.write_delta * num_steps_to_max)
        self.cv_min = -(self.write_delta * (num_steps_to_max - 1))
        self.ppc_signal = self.tp = 0
        self.agency = False
    def update(self):
        fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()#-greater beneficial stochasticity???
        # fbv = self.po.m[self.fbi].pv.copy()
        #_____________________________________________________________________________________________________________________________
        self.prototype_v = (self.iv | {(self.po.K + a) for a in self.pv} | {((self.po.K * 2) + a) for a in fbv})
        # self.prototype_v = (self.pv | {(self.po.K + a) for a in fbv})#----------why doesn't this work????
        #____________________________________________________________________________________________________________________________
        avail_indices = (self.poss_indices - set(self.mem.keys()))
        self.mem[random.choice(list(avail_indices))] = [self.prototype_v.copy(), self.blank_cv.copy(),
                                                        random.randrange(self.po.pv_min, self.po.pv_max)]
        #______________________________________________________________________________________________________________________________
        num_attempts_max = 3#------------------------------------------------------------------------------------------------------HP
        num_attempts = 0
        self.read_comp_v = self.blank_cv.copy()
        read_comp_v_den = 0
        while((len(self.prototype_v ^ self.prev_v) > 0) and (num_attempts < num_attempts_max)):
            si = list(self.mem.keys())
            random.shuffle(si)
            num_samples_min = max(self.sample_min, round(float(len(self.mem.keys())) * self.sample_pct))
            skip = set()
            r = 0
            avg_vA_dict = dict()
            self.read_v = self.blank_cv.copy()
            while ((len(si) > 0) and (len(skip) < num_samples_min)):
                for a in si:
                    tav = self.mem[a][0]
                    d = len(tav ^ self.prototype_v)
                    if (d == r):
                        for b in tav:
                            if (b in avg_vA_dict.keys()): avg_vA_dict[b] += 1
                            else: avg_vA_dict[b] = 1
                        for b in avg_vA_dict.keys():
                            if (b not in tav): avg_vA_dict[b] -= 1
                        for i, b in enumerate(self.mem[a][1]): self.read_v[i] += b
                        for i, b in enumerate(self.mem[a][1]): self.read_comp_v[i] += b
                        read_comp_v_den += 1
                        self.mem[a][2] = random.randrange(self.po.pv_min, self.po.pv_max)
                        skip.add(a)
                si = list(set(si) - skip)
                r += 1
            self.prev_v = self.prototype_v.copy()
            self.prototype_v = {key for key, value in avg_vA_dict.items() if (value > 0)}
            self.read_v = [round(float(a) / float(max(1, len(skip)))) for a in self.read_v]
            self.read_comp_v = [round(float(a) / float(max(1, read_comp_v_den))) for a in self.read_comp_v]
            num_attempts += 1
        dist = min(len(self.mem[a][0] ^ self.prototype_v) for a in self.mem.keys()) if (len(self.mem.keys()) > 0) else -1
        cands = {a for a in self.mem.keys() if (len(self.mem[a][0] ^ self.prototype_v) == dist)}
        avail_indices = (self.poss_indices - set(self.mem.keys()))
        wi = random.choice(list(cands)) if (len(cands) > 0) else random.choice(list(avail_indices))
        if ((wi not in self.mem.keys()) or (dist != 0)):
            self.mem[wi] = [self.prototype_v.copy(), self.blank_cv.copy(), random.randrange(self.po.pv_min, self.po.pv_max)]
        # self.pv = {i for i, a in enumerate(self.read_v) if (a > 0)}#-----------------which one is better and why???
        self.pv = {i for i, a in enumerate(self.read_comp_v) if (a > 0)}#----------which one is better and why???
        #_____________________________________________________________________________________________________________________
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
            if (both or ((random.randrange(1000000) < 500000) and (self.agency == False))):#-motor babble-------------------------HP
                self.ppc_signal = random.choice([-1, 1])
            self.po.ts_index = ((self.po.ts_index + len(self.po.ts) + self.ppc_signal) % len(self.po.ts))
            self.iv = self.po.ts[self.po.ts_index].copy()
            if (self.ppc_signal == -1): self.iv |= self.po.ppcv_L
            if (self.ppc_signal == 1): self.iv |= self.po.ppcv_R
        else: self.iv = self.po.m[self.ffi].ov.copy()
        #___________________________________________________________________________________________________________________
        #-------TODO: modulate self.write_delta proportional to prediction confidence
        for i, a in enumerate(self.mem[wi][1]):
            if ((i in self.iv) and ((a + self.write_delta) <= self.cv_max)): self.mem[wi][1][i] += self.write_delta
            if ((i not in self.iv) and ((a - self.write_delta) >= self.cv_min)): self.mem[wi][1][i] -= self.write_delta
        #__________________________________________________________________________________________________________________
        self.ov = (self.iv ^ self.pv)
        den = float(max(1, (len(self.iv) + len(self.pv))))
        erm = ((float(len(self.ov)) / den) * 100.0)
        self.tp = sum((len(self.mem[a][0]) + len(self.mem[a][1]) + 2) for a in self.mem.keys())
        agency_str = f"\tPPC: {self.ppc_signal}\t{wi}" if ((self.mi == 0) and (self.agency)) else ""
        print(f"M{self.mi}\tER: {erm:.2f}%\tTP: {self.tp}\tMEM: {len(self.mem.keys())}" + agency_str)
        #__________________________________________________________________________________________________________________
        while ((len(self.mem.keys()) + 1) > self.po.Z):
            remove_indices = set()
            si = [a for a in self.mem.keys()]
            random.shuffle(si)
            for a in si:
                flag = True
                for i, b in enumerate(self.mem[a][1]):
                    if (b > 0): self.mem[a][1][i] -= 1
                    if (b < 0): self.mem[a][1][i] += 1
                    if(flag and (b != 0)): flag = False
                if flag:
                    # remove_indices.add(a)
                    if (self.mem[a][2] > 0): self.mem[a][2] -= 1
                    else: remove_indices.add(a)
            while (((len(self.mem.keys()) + 1) > self.po.Z) and (len(remove_indices) > 0)):
                ri = random.choice(list(remove_indices))
                del self.mem[ri]
                remove_indices.remove(ri)
oracle = Oracle()
oracle.update()