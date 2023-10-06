import random
import math
class Oracle:
    def __init__(self):
        self.H = 3#----------------------------------------------------------------------------------------------------------------HP
        self.K = 256#--------------------------------------------------------------------------------------------------------------HP
        self.pv_min = 351#---------------------------------------------------------------------------------------------------------HP
        self.pv_range = 1.11#------------------------------------------------------------------------------------------------------HP
        self.pv_max = max((self.pv_min + 1), round(float(self.pv_min) * self.pv_range))
        self.ppcv_dim = 2#-5-------------------------------------------------------------------------------------------------------HP
        self.ppcv_L = set(range((self.K - (self.ppcv_dim * 2)), (self.K - self.ppcv_dim)))
        self.ppcv_R = set(range((self.K - self.ppcv_dim), self.K))
        self.m = [Matrix(self, a) for a in range(self.H)]
        #____________________________________________________________________________________________________________________________
        ts_dim = 5#----------------------------------------------------------------------------------------------------------------HP
        ts_range_set = (set(range(self.K)) - self.ppcv_L - self.ppcv_R)
        ts_density = 0.37#---------------------------------------------------------------------------------------------------------HP
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
        self.e = {a:[dict(), dict()] for a in range(self.po.K)}
        self.sparsity = 0.04#------------------------------------------------------------------------------------------------------HP
        self.cluster_dim = round(1.0 / self.sparsity)
        self.num_clusters_min = math.floor(float(len(self.e.keys())) / float(self.cluster_dim))
        self.ai_min = (self.num_clusters_min * self.cluster_dim)
        self.iv = self.ov = self.cv = self.pv = set()
        self.ppc_signal = self.tp = 0
        self.agency = False
    def update(self):
        #_____________________________________________________________________________________________________________________________
        # fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()#-greater beneficial stochasticity???
        fbv = self.po.m[self.fbi].pv.copy()#-seems to stabilize beh/att???Idk???
        #_____________________________________________________________________________________________________________________________
        # self.cv = (self.iv | {(self.po.K + a) for a in self.pv} | {((self.po.K * 2) + a) for a in fbv})
        # self.cv = (self.iv | {(self.po.K + a) for a in fbv})
        self.cv = (self.pv | {(self.po.K + a) for a in fbv})
        #_____________________________________________________________________________________________________________________________
        r = min(len(set(self.e[a][0].keys()) ^ self.iv) for a in self.e.keys())
        si = list(self.e.keys())
        random.shuffle(si)
        ai = []
        while (len(ai) < self.ai_min):
            for a in si:
                if ((len(ai) < self.ai_min) and (a not in ai) and (len(set(self.e[a][0].keys()) ^ self.iv) == r)): ai.append(a)
            r += 1
        #_____________________________________________________________________________________________________________________________
        clusters = []
        ovs = []
        while ((len(ai) >= self.cluster_dim) and (len(clusters) < self.num_clusters_min)):
            a = ai.pop(0)
            cluster = {a}
            r = min((len((set(self.e[a][0].keys()) & self.iv) ^ (set(self.e[b][0].keys()) & self.iv)) -
                     len((set(self.e[a][1].keys()) & self.cv) ^ (set(self.e[b][1].keys()) & self.cv))) for b in ai)
            while (len(cluster) < self.cluster_dim):
                for b in ai:
                    if ((len(cluster) < self.cluster_dim) and (b not in cluster) and
                        ((len((set(self.e[a][0].keys()) & self.iv) ^ (set(self.e[b][0].keys()) & self.iv)) -
                        len((set(self.e[a][1].keys()) & self.cv) ^ (set(self.e[b][1].keys()) & self.cv))) == r)): cluster.add(b)
                r += 1
            if (len(cluster) == self.cluster_dim):
                ri = random.choice(list(cluster))
                ov = (set(self.e[ri][0].keys()) & self.iv)
                for b in cluster:
                    if (b != ri): ov &= (set(self.e[b][0].keys()) & self.iv)
                if (len(ov) == 0): ov = self.iv.copy()
                ovs.append(ov.copy())
                clusters.append(cluster.copy())
            ai = [b for b in ai if (b not in cluster)]
        #_____________________________________________________________________________________________________________________________
        em = zr = mr = 0
        for i, a in enumerate(clusters):
            for b in a:
                for c in ovs[i]: self.e[b][0][c] = random.randrange(self.po.pv_min, self.po.pv_max)
                # for c in self.iv: self.e[b][0][c] = random.randrange(self.po.pv_min, self.po.pv_max)
            pv = (a & self.pv)
            if (len(pv) == 0):
                em += 1.0
                zr += 1.0
                # cands = {b for b in a if (len(self.e[b][1].keys()) == min(len(self.e[b][1].keys()) for b in a))}
                cands = set()
                wi = random.choice(list(cands)) if (len(cands) > 0) else random.choice(list(a))
            if (len(pv) > 1):
                em += (float(len(pv) - 1) / float(self.cluster_dim - 1))
                mr += 1.0
                wi = random.choice(list(pv))
            if (len(pv) == 1): wi = random.choice(list(pv))
            for c in self.cv: self.e[wi][1][c] = random.randrange(self.po.pv_min, self.po.pv_max)
        den = float(max(1, len(clusters)))
        em /= den
        zr /= den
        mr /= den
        r = min(len(set(self.e[a][1].keys()) ^ self.cv) for a in self.e.keys())
        self.pv = {a for a in self.e.keys() if (len(set(self.e[a][1].keys()) ^ self.cv) == r)}
        self.ov = self.pv.copy()
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
            self.ppc_signal = 1
            self.iv = self.po.ts[self.po.ts_index].copy()
            if (self.ppc_signal == -1): self.iv |= self.po.ppcv_L
            if (self.ppc_signal == 1): self.iv |= self.po.ppcv_R
            self.po.ts_index = ((self.po.ts_index + len(self.po.ts) + self.ppc_signal) % len(self.po.ts))#---DEBUG
        else: self.iv = self.po.m[self.ffi].ov.copy()
        #____________________________________________________________________________________________________________________________
        # self.tp = sum((len(self.mem[a][0]) + len(self.mem[a][1]) + 2) for a in self.mem.keys())
        agency_str = f"\tPPC: {self.ppc_signal}" if ((self.mi == 0) and (self.agency)) else ""
        print(f"M{self.mi}\tEM: {(em * 100.0):.2f}%\tZR: {(zr * 100.0):.2f}%\tMR: {(mr * 100.0):.2f}%" +
              f"\tTP: {self.tp}\tEL: {len(self.e.keys())}" + agency_str)
        #___________________________________________________________________________________________________________________________
        for a in self.e.keys():
            self.e[a][0] = {key:(value - 1) for key, value in self.e[a][0].items() if (value > 0)}
            self.e[a][1] = {key:(value - 1) for key, value in self.e[a][1].items() if (value > 0)}
oracle = Oracle()
oracle.update()