import random
import math
class Oracle:
    def __init__(self):
        self.H = 3#----------------------------------------------------------------------------------------------------------------HP
        self.K = 128#--------------------------------------------------------------------------------------------------------------HP
        self.Z = 100#-------------------------------------------------------------------------------------------------------------HP
        self.pv_min = 10#----------------------------------------------------------------------------------------------------------HP
        self.pv_range = 3.70#------------------------------------------------------------------------------------------------------HP
        self.pv_max = max((self.pv_min + 1), round(float(self.pv_min) * self.pv_range))
        self.ppcv_dim = 20#--------------------------------------------------------------------------------------------------------HP
        self.ppcv_L = set(range((self.K - (self.ppcv_dim * 2)), (self.K - self.ppcv_dim)))
        self.ppcv_R = set(range((self.K - self.ppcv_dim), self.K))
        self.m = [Matrix(self, a) for a in range(self.H)]
        #____________________________________________________________________________________________________________________________
        ts_dim = 5#----------------------------------------------------------------------------------------------------------------HP
        ts_range_set = (set(range(self.K)) - self.ppcv_L - self.ppcv_R)
        ts_density = 0.33#---------------------------------------------------------------------------------------------------------HP
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
            self.cycle += 1
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.mi = mi_in
        self.ffi = (self.mi - 1)
        self.fbi = ((self.mi + 1) % self.po.H)
        self.blank_cv = [0] * self.po.K
        self.read_v = self.blank_cv.copy()
        self.poss_indices = set(range((self.po.Z + 1)))
        self.mem = dict()
        self.last_index_A = self.last_index_B = -1
        self.iv = self.ov = self.prototype_v = self.prev_v = self.pv = set()
        self.prototype_delta_max = 0#----------------------------------------------------------------------------------------------HP
        self.sample_min = 15#-musn't be set too high!!!!----------------------------------------------------------------------------HP
        self.sample_pct = 0.04#-----------------------------------------------------------------------------------------------------HP
        self.write_delta = 50#-----------------------------------------------------------------------------------------------------HP
        num_steps_to_max = 100#-----------------------------------------------------------------------------------------------------HP
        self.cv_max = (self.write_delta * num_steps_to_max)
        self.cv_min = -(self.write_delta * (num_steps_to_max - 1))
        self.ppc_signal = 0
        self.tp = 0
        self.agency = False
    def update(self):
        if (self.mi == 0):
            self.ppc_signal = 0
            self.agency = False
            if (len(self.pv & self.po.ppcv_L) == self.po.ppcv_dim):
                self.ppc_signal += -1
                self.agency = True
            if (len(self.pv & self.po.ppcv_R) == self.po.ppcv_dim):
                self.ppc_signal += 1
                self.agency = True
            confluence = ((self.agency == True) and (self.ppc_signal == 0))
            if (((self.agency == False) and (random.randrange(1000000) < 500000)) or confluence):#-motor babble-----------------HP
                self.ppc_signal = -1 if (random.randrange(1000000) < 500000) else 1
            self.po.ts_index = ((self.po.ts_index + len(self.po.ts) + self.ppc_signal) % len(self.po.ts))
            self.iv = self.po.ts[self.po.ts_index].copy()
            if (self.ppc_signal == -1): self.iv |= self.po.ppcv_L
            if (self.ppc_signal == 1): self.iv |= self.po.ppcv_R
        else: self.iv = self.po.m[self.ffi].ov.copy()
        while ((len(self.mem.keys()) + 1) > self.po.Z):
            remove_indices = set()
            exclusion_set = {self.last_index_A, self.last_index_B}
            si = [a for a in self.mem.keys() if (a not in exclusion_set)]
            random.shuffle(si)
            for a in si:
                flag = True
                for i, b in enumerate(self.mem[a][1]):
                    if (b > 0): self.mem[a][1][i] -= 1
                    if (b < 0): self.mem[a][1][i] += 1
                    if(flag and (self.mem[a][1][i] != 0)): flag = False
                if flag:
                    # remove_indices.add(a)
                    if (self.mem[a][2] > 0): self.mem[a][2] -= 1
                    else: remove_indices.add(a)
            while (((len(self.mem.keys()) + 1) > self.po.Z) and (len(remove_indices) > 0)):
                ri = random.choice(list(remove_indices))
                del self.mem[ri]
                remove_indices.remove(ri)
        if (self.last_index_A != -1):
            for i, a in enumerate(self.mem[self.last_index_A][1]):
                if ((i in self.iv) and ((a + self.write_delta) <= self.cv_max)): self.mem[self.last_index_A][1][i] += self.write_delta
                if ((i not in self.iv) and ((a - self.write_delta) >= self.cv_min)): self.mem[self.last_index_A][1][i] -= self.write_delta
        self.tp = sum((len(self.mem[a][0]) + len(self.mem[a][1]) + 2) for a in self.mem.keys())
        # fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        fbv = self.po.m[self.fbi].pv.copy()
        # self.prototype_v = (self.pv | {(self.po.K + a) for a in fbv})
        # self.prototype_v = (self.prototype_v | {(self.po.K + a) for a in self.pv} | {((self.po.K * 2) + a) for a in fbv})
        # self.prototype_v = (self.prototype_v | {(self.po.K + a) for a in fbv})
        self.prototype_v = (self.iv | {(self.po.K + a) for a in self.pv} | {((self.po.K * 2) + a) for a in fbv})
        avail_indices = (self.poss_indices - set(self.mem.keys()) - {self.last_index_A, self.last_index_B})
        self.last_index_B = random.choice(list(avail_indices))
        write_v = self.prototype_v.copy()
        self.mem[self.last_index_B] = [write_v.copy(), self.blank_cv.copy(), random.randrange(self.po.pv_min, self.po.pv_max)]
        num_attempts_max = 10#----------------------------------------------------------------------------------------------------HP
        num_attempts = 0
        while((len(self.prototype_v ^ self.prev_v) > self.prototype_delta_max) and (num_attempts < num_attempts_max)):
            si = list(self.mem.keys())
            num_samples_min = max(self.sample_min, round(float(len(self.mem.keys())) * self.sample_pct))
            random.shuffle(si)
            skip = set()
            r = 0
            avg_vA_dict = dict()
            self.read_v = self.blank_cv.copy()
            while ((len(si) > 0) and (len(skip) < num_samples_min)):
                for a in si:
                    tav = self.mem[a][0].copy()
                    d = len(tav ^ self.prototype_v)
                    if (d == r):
                        for b in tav:
                            if (b in avg_vA_dict.keys()): avg_vA_dict[b] += 1
                            else: avg_vA_dict[b] = 1
                        for b in avg_vA_dict.keys():
                            if (b not in tav): avg_vA_dict[b] -= 1
                        for i, b in enumerate(self.mem[a][1]): self.read_v[i] += b
                        self.mem[a][2] = random.randrange(self.po.pv_min, self.po.pv_max)
                        skip.add(a)
                si = list(set(si) - skip)
                r += 1
            self.prev_v = self.prototype_v.copy()
            self.prototype_v = {a for a in avg_vA_dict.keys() if (avg_vA_dict[a] > 0)}
            self.read_v = [round(float(a) / float(max(1, len(skip)))) for a in self.read_v]
            num_attempts += 1
        dist = min(len(self.mem[a][0] ^ self.prototype_v) for a in self.mem.keys()) if (len(self.mem.keys()) > 0) else -1
        cands = {a for a in self.mem.keys() if (len(self.mem[a][0] ^ self.prototype_v) == dist)}
        avail_indices = (self.poss_indices - set(self.mem.keys()) - {self.last_index_A, self.last_index_B})
        self.last_index_A = random.choice(list(cands)) if (len(cands) > 0) else random.choice(list(avail_indices))
        if ((self.last_index_A not in self.mem.keys()) or (dist != 0)):
            self.mem[self.last_index_A] = [self.prototype_v.copy(), self.blank_cv.copy(), random.randrange(self.po.pv_min, self.po.pv_max)]
        self.pv = {i for i, a in enumerate(self.mem[self.last_index_A][1]) if (a > 0)}
        # self.pv = {i for i, a in enumerate(self.read_v) if (a > 0)}
        den = float(max(1, (len(self.iv) + len(self.pv))))
        self.ov = (self.iv ^ self.pv)
        erm = ((float(len(self.ov)) / den) * 100.0)
        agency_str = f"\tPPC: {self.ppc_signal}" if ((self.mi == 0) and (self.agency)) else ""
        print(f"M{self.mi}\tER: {erm:.2f}%\tTP: {self.tp}\tMEM: {len(self.mem.keys())}" + agency_str)
oracle = Oracle()
oracle.update()