import random
import heapq
class Oracle:
    def __init__(self):
        ###############################################################################################
        self.H = 6#---------------------------------------------------------------------------------------------HP
        self.N = 64#--------------------------------------------------------------------------------------------HP
        self.N_range = range(self.N)
        self.sparsity = 0.02#-----------------------------------------------------------------------------------HP
        self.M = round(1 / self.sparsity)
        self.Q = self.N * self.M
        self.K_pct = 0.51#--------------------------------------------------------------------------------------HP
        self.K = round(self.N * self.K_pct)
        ###############################################################################################
        self.ts_dim = 3#----------------------------------------------------------------------------------------HP
        self.ts_idx = 0
        self.ts = [{random.choice(range(a * self.M, (a + 1) * self.M))
                    for a in random.sample(self.N_range, self.K)} for _ in range(self.ts_dim)]
        self.ts_idx_inc_set = {a for a in range(self.ts_dim)}
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
        # self.fb_alt = set(random.sample(self.po.N_range, self.po.K))
        self.fb_alt = set()
        ###############################################################################################
        self.adc_max = 10000000#-------------------------------------------------------------------------------HP
        self.ts_idx_inc = -1
        self.em = self.em_prev = self.em_delta = 0
    def update(self):
        ###############################################################################################
        if self.ffi == -1:
            self.ts_idx_inc = -1
            bv = self.pv.copy()
            if self.po.ext_map:
                d = [(len(k ^ bv), k) for k in self.po.ext_map.keys() if (len(k ^ bv) < 1)]#-------------------HP
                if d:
                    if len(d) > 1:
                        heapq.heapify(d)
                        d = sorted(d, key = lambda x: x[0])
                    self.ts_idx_inc = self.po.ext_map[d[0][1]][0]
                    self.po.ext_map[d[0][1]][1] = 0
            if self.ts_idx_inc == -1:
                self.ts_idx_inc = random.choice(list(self.po.ts_idx_inc_set))
                self.po.ext_map[frozenset(bv)] = [self.ts_idx_inc, 0]
            if len(self.po.ext_map) > 300:#----------------------------------------------------------------------------HP
                for v in self.po.ext_map.values():
                    if v[1] < self.po.ext_map_adc_max: v[1] += 1
                self.po.ext_map = {k:v for k, v in self.po.ext_map.items() if v[1] < self.po.ext_map_adc_max - 10}#----HP
            self.po.ts_idx = (self.po.ts_idx + self.ts_idx_inc) % self.po.ts_dim
            # ff_prev_cl = self.convert(ff)
            # ff = ext_prev_cl - self.po.ts[self.po.ts_idx]
            ff = self.po.ts[self.po.ts_idx].copy()
        else: ff = self.po.m[self.ffi].pv.copy()
        ###############################################################################################
        ff_cl = self.convert(ff)
        pv_cl = self.convert(self.pv)
        er = ff_cl - pv_cl
        ###############################################################################################
        zr = 0
        for a in er:
            ci = set(range(a * self.po.M, (a + 1) * self.po.M))
            ciav = ci - self.e.keys()
            if not ciav:
                zr += 1
                cinv = ci & self.e.keys()
                d = [(sum(self.e[kA][kB] for kB in self.e[kA].keys()), kA) for kA in cinv]
                heapq.heapify(d)
                d = sorted(d, key = lambda x: x[0], reverse = True)
                # d = sorted(d, key = lambda x: x[0])#-------????
                wi = d[0][1]
            else: wi = random.choice(list(ciav))
            self.e[wi] = {b:0 for b in self.cv}
        ###############################################################################################
        self.em = len(er) / self.po.N
        self.em_delta = self.em - self.em_prev
        self.em_prev = self.em
        ###############################################################################################
        av = set()
        for a in ff_cl & pv_cl:
            ci = set(range(a * self.po.M, (a + 1) * self.po.M))
            ov = self.pv & ci
            if len(ov) == 1:
                wi = ov.pop()
                av.add(wi)
                if wi in self.e.keys():
                    for b in self.cv: self.e[wi][b] = 0
                else: self.e[wi] = {b:0 for b in self.cv}
        ###############################################################################################
        fb = self.fb_alt.copy() if self.fbi == 0 else self.po.m[self.fbi].pv.copy()
        fb_cl = self.convert(fb)
        er ^= fb_cl
        er_el = set()
        for a in er:
            ci = set(range(a * self.po.M, (a + 1) * self.po.M))
            if a in ff_cl: tv = ff & ci
            if a in fb_cl: tv = fb & ci
            if len(tv) == 1: er_el.add(tv.pop())
        ###############################################################################################
        self.cv = self.pv.copy()#----------???
        ###############################################################################################
        self.pv = er_el.copy()
        remn = set(self.po.N_range) - self.convert(er_el)
        thresh_B = 0.90#-----------------------------------------------------------------------------------------------HP
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
                minval = -(len(b) - 1)
                norm = maxval - minval
                c = {k:(len(self.e[k].keys() & self.cv) / max(1, len(self.e[k].keys() | self.cv))) for k in b}#-Jaccard similarity
                d = [((((vA - sum(vB for kB, vB in c.items() if (kB != kA))) - minval) / norm), kA) for kA, vA in c.items()]
                heapq.heapify(d)
                d = sorted(d, key = lambda x: x[0], reverse = True)
                avgs += d[0][0]
                avgs_ct += 1
                if d[0][0] >= thresh_B: self.pv.add(d[0][1])
        avgd /= max(1, avgd_ct)
        avgs /= max(1, avgs_ct)
        ###############################################################################################
        # if self.em < 0.0001 and self.em_delta < 0.0001 and len(self.po.bv_map) < self.po.bv_map_max:#---------------------------HP
        ###############################################################################################
        tl = [f"M{str(self.ffi + 1).rjust(1)}"]
        tl.append(f"EM: {f'{self.em:.2f}'.rjust(4)}")
        tl.append(f"PV: {str(len(self.pv)).rjust(3)}")
        tl.append(f"EL: {str(len(self.e)).rjust(8)}")
        # tl.append(f"EMDA: {f'{self.em_delta_avg:.3f}'.rjust(6)}")
        tl.append(f"AM: {f'{avgs:.2f}'.rjust(4)}")
        tl.append(f"ED: {str(round(avgd)).rjust(3)}")
        tl.append(f"ZR: {str(zr).rjust(4)}")
        tl.append(f"EXL: {str(len(self.po.ext_map)).rjust(3)}")
        if self.ffi == -1: tl.append(f"EXI: {str(self.ts_idx_inc).rjust(3)}")
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