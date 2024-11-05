import random
import heapq
class Oracle:
    def __init__(self):
        ###############################################################################################
        self.H = 6#---------------------------------------------------------------------------------------------HP
        self.N = 67#--------------------------------------------------------------------------------------------HP
        self.N_range = range(self.N)
        self.M = 47#--------------------------------------------------------------------------------------------HP
        self.Q = self.N * self.M
        self.K_pct = 0.53#--------------------------------------------------------------------------------------HP
        self.K = round(self.N * self.K_pct)
        ###############################################################################################
        ts_dim = 11#---------------------------------------------------------------------------------------------HP
        self.ts = []
        pct_diff = 1#--------------------------------------------------------------------------------------------HP
        thr = round(self.K * 2 * pct_diff)
        while len(self.ts) < ts_dim:
            rs = random.sample(self.N_range, self.K)
            rv = {random.choice(range(a * self.M, (a + 1) * self.M)) for a in rs}
            flag = True
            while flag:
                flag = False
                for b in self.ts:
                    if len(b ^ rv) < thr:
                        rs = random.sample(self.N_range, self.K)
                        rv = {random.choice(range(a * self.M, (a + 1) * self.M)) for a in rs}
                        flag = True
                        break
            self.ts.append(rv.copy())
        ###############################################################################################
        self.ext_map = dict()
        self.ext_map_adc_max = 1000#----------------------------------------------------------------------------HP
        ###############################################################################################
        self.cy = 0
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while True:
            for a in self.m: a.update()
            self.cy += 1
class Matrix:
    def __init__(self, po_in, mi_in):
        ###############################################################################################
        self.po = po_in
        self.ffi = mi_in - 1
        self.fbi = (mi_in + 1) % self.po.H
        ###############################################################################################
        self.e = dict()
        self.pv = set()
        self.cv = set()
        self.er = set()
        self.av = set()
        self.ff = set()
        self.ff_cl = set()
        self.fb = set()
        self.fb_cl = set()
        self.pv_cl = set()
        # self.fb_alt = set(random.sample(self.po.N_range, self.po.K))
        self.fb_alt = set()
        self.adc_max = 5000
        ###############################################################################################
        self.ts_idx_set = {a for a in range(len(self.po.ts))}
        self.em = self.em_prev = self.em_delta = 0
    def update(self):
        ###############################################################################################
        self.fb = self.fb_alt.copy() if self.fbi == 0 else self.po.m[self.fbi].pv.copy()
        self.fb_cl = self.convert(self.fb)
        ###############################################################################################
        self.er ^= self.fb_cl
        ###############################################################################################
        self.pv = set()
        for a in self.er:
            ci = set(range(a * self.po.M, (a + 1) * self.po.M))
            tvA = (self.ff & ci) | (self.fb & ci)
            if len(tvA) == 1: self.pv.add(tvA.pop())
        ###############################################################################################
        for vA in self.e.values():
            for vB in vA.values():
                if vB < self.adc_max: vB += 1
        ###############################################################################################
        remn = set(self.po.N_range) - self.convert(self.pv)
        thresh_A = 0.95#-------------------------------------------------------------------------------------HP
        maxval = 1
        avgd = 0
        avgd_ct = 0
        avgs = 0
        avgs_ct = 0
        for a in remn:
            b = [k for k in self.e.keys() if (k // self.po.M) == a]
            if b:
                avgd += len(b)
                avgd_ct += 1
                c = {k:(len(self.e[k].keys() & self.cv) / max(1, len(self.e[k].keys() | self.cv))) for k in b}#-Jaccard Index
                # c = {k:(1 - (len(self.e[k].keys() ^ self.cv) / max(1, len(self.e[k].keys() | self.cv)))) for k in b}#-Hamming Distance
                if len(c) > 1:
                    minval = -(len(c) - 1)
                    norm = maxval - minval
                    d = [((((vA - sum(vB for kB, vB in c.items() if (kB != kA))) - minval) / norm), kA) for kA, vA in c.items()]
                    heapq.heapify(d)
                    d = sorted(d, key = lambda x: x[0], reverse = True)
                else: d = [(v, k) for k, v in c.items()]
                avgs += sum(y[0] for y in d) / max(1, len(d))
                # avgs += sum(c.values()) / len(c)
                avgs_ct += 1
                if d[0][0] >= thresh_A: self.pv.add(d[0][1])
        ###############################################################################################
        ts_idx = -1
        if self.ffi == -1:
            for v in self.po.ext_map.values():
                if v[1] < self.po.ext_map_adc_max: v[1] += 1
            self.po.ext_map = {k:v for k, v in self.po.ext_map.items() if v[1] < 23}#----------------------HP
            bv = self.pv.copy()
            d = [(len(k ^ bv), k) for k in self.po.ext_map.keys() if (len(k ^ bv) < 1)]#------------------HP
            if d:
                if len(d) > 1:
                    heapq.heapify(d)
                    d = sorted(d, key = lambda x: x[0])
                ts_idx = self.po.ext_map[d[0][1]][0]
                self.po.ext_map[d[0][1]][1] = 0
            if ts_idx == -1:
                ts_idx = random.choice(list(self.ts_idx_set))
                self.po.ext_map[frozenset(bv)] = [ts_idx, 0]
            self.ff = self.po.ts[ts_idx].copy()
        else: self.ff = self.po.m[self.ffi].pv.copy()
        ###############################################################################################
        self.ff_cl = self.convert(self.ff)
        self.pv_cl = self.convert(self.pv)
        ###############################################################################################
        self.er = self.ff_cl - self.pv_cl
        ###############################################################################################
        self.av = set()
        zr = 0
        for a in self.er:
            ci = set(range(a * self.po.M, (a + 1) * self.po.M))
            ciav = ci - self.e.keys()
            if not ciav:
                zr += 1
                d = [((sum(self.e[kA][kB] for kB in self.e[kA].keys()) / max(1, len(self.e[kA]))), kA) for kA in ci]
                heapq.heapify(d)
                d = sorted(d, key = lambda x: x[0], reverse = True)
                # d = sorted(d, key = lambda x: x[0])#-----favors exploration???
                wi = d[0][1]
            else: wi = random.choice(list(ciav))
            self.av.add(wi)
            self.e[wi] = {b:0 for b in self.cv}
        zr /= max(1, len(self.er))
        ###############################################################################################
        for a in self.pv_cl & self.ff_cl:
            ci = set(range(a * self.po.M, (a + 1) * self.po.M))
            ov = self.pv & ci
            if len(ov) == 1:
                wi = ov.pop()
                self.av.add(wi)
                if wi in self.e.keys():
                    for b in self.cv: self.e[wi][b] = 0
                else: self.e[wi] = {b:0 for b in self.cv}
        ###############################################################################################
        self.em = len(self.er) / self.po.N
        self.em_delta = self.em - self.em_prev
        self.em_prev = self.em
        ###############################################################################################
        self.cv = self.av | {a + self.po.Q for a in self.pv}#----best???!!!
        # self.cv = self.av.copy()
        # self.cv = self.pv.copy()                    
        ###############################################################################################
        tl = [f"M{str(self.ffi + 1).rjust(1)}"]
        tl.append(f"EM: {f'{self.em:.2f}'.rjust(4)}")
        tl.append(f"PV: {str(len(self.pv)).rjust(3)}")
        tl.append(f"EL: {str(len(self.e)).rjust(6)}")
        if avgs_ct > 0: tl.append(f"AM: {f'{avgs / avgs_ct:.2f}'.rjust(4)}")
        else: tl.append(f"AM: ----")
        tl.append(f"AMN: {str(avgs_ct).rjust(3)}")
        if avgd_ct > 0: tl.append(f"ED: {str(round(avgd / avgd_ct)).rjust(3)}")
        else: tl.append(f"ED: ---")
        tl.append(f"ZR: {f'{zr:.2f}'.rjust(4)}")
        tl.append(f"EXL: {str(len(self.po.ext_map)).rjust(3)}")
        if self.ffi == -1: tl.append(f"EXI: {str(ts_idx).rjust(3)}")
        print(" | ".join(tl))     
        ###############################################################################################
    def convert(self, v_in):
        out = set()
        for a in v_in:
            b = a // self.po.M
            if len(v_in & set(range(b * self.po.M, (b + 1) * self.po.M))) == 1: out.add(b)
        return out.copy()
oracle = Oracle()
oracle.update()