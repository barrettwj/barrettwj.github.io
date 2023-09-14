import random
import math
class Oracle:
    def __init__(self):
        self.H = 6#--------------------------------------------------------------------------------------------------------------HP
        self.K = 40#-------------------------------------------------------------------------------------------------------------HP
        self.N = (self.K * 3)#---------------------------------------------------------------------------------------------------HP
        self.PV = 37#------------------------------------------------------------------------------------------------------------HP
        self.iv_mask = set(range(self.K))
        self.m = [Matrix(self, a) for a in range(self.H)]
        #__________________________________________________________________________________________________________________________
        ts_dim = 5#--------------------------------------------------------------------------------------------------------------HP
        ts_range_set = {a for a in range(self.K)}
        ts_density = 0.58#-------------------------------------------------------------------------------------------------------HP
        ts_card = math.floor(float(len(ts_range_set)) * ts_density)
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
        self.av = dict()
        self.cv = dict()
        self.ov = self.prototype_v = self.prev_v = self.pv = set()
        self.delta_v_max = 2#------------------------------------------------------------------------------------HP
        self.r_max = 3#------------------------------------------------------------------------------------------HP
        self.num_samples = 10#-----------------------------------------------------------------------------------HP
        self.ppcL = self.ppcR = -1
        self.agency = False
    def update(self):
        # fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        fbv = self.po.m[self.fbi].pv.copy()
        ctv = (self.prototype_v | {(self.po.K + a) for a in self.pv} | {((self.po.K * 2) + a) for a in fbv})
        cands = {a for a in self.av.keys() if (len(self.av[a] ^ ctv) == min(len(self.av[a] ^ ctv) for a in self.av.keys()))}
        self.pv = self.cv[random.choice(list(cands))].copy() if (len(cands) > 0) else set()
        if (self.mi == 0):
            self.po.ts_index = ((self.po.ts_index + len(self.po.ts) + 1) % len(self.po.ts))
            iv = self.po.ts[self.po.ts_index].copy()
        else: iv = self.po.m[self.ffi].ov.copy()
        self.ov = (iv ^ self.pv)
        erm = len(self.ov)
        ###########
        self.prototype_v = iv.copy()
        num_attempts_max = 100
        num_attempts = 0
        while((len(self.prototype_v ^ self.prev_v) > self.delta_v_max) and (num_attempts < num_attempts_max)):
            si = list(self.av.keys())
            random.shuffle(si)
            skip = set()
            r = 0
            num_samples = 0
            avg_v_dict = dict()
            while ((len(si) > 0) and (r < self.r_max) and (num_samples < self.num_samples)):
                for a in si:
                    tav = (self.av[a] & self.po.iv_mask)
                    d = len(tav ^ self.prototype_v)
                    if (d == r):
                        for b in tav:
                            if (b in avg_v_dict.keys()): avg_v_dict[b] += 1
                            else: avg_v_dict[b] = 1
                        for b in avg_v_dict.keys():
                            if (b not in tav): avg_v_dict[b] -= 1
                        skip.add(a)
                        num_samples += 1
                si = list(set(si) - skip)
                r += 1
            self.prev_v = self.prototype_v.copy()
            self.prototype_v = {a for a in avg_v_dict.keys() if (avg_v_dict[a] > 0)}
            #########
            num_attempts += 1
        ##########
oracle = Oracle()
oracle.update()