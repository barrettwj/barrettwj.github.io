import random
import heapq
class Oracle:
    def __init__(self):
        self.H = 7
        self.M = 37
        self.K = 507
        self.adc_max = 17
        self.iv_mask = {a for a in range(self.K)}
        self.bv_mask = {(self.K + a) for a in range(self.K)}
        self.C = (self.iv_mask | self.bv_mask)
        self.fbv_offset = (len(self.C) * self.M)
        tsp_dim_pct = 0.30
        tsp_dim = round(self.K * tsp_dim_pct)
        ts_dim = 43
        self.iv_map = {a:frozenset(random.sample(list(self.iv_mask), tsp_dim)) for a in range(ts_dim)}
        self.bv_map = {frozenset(random.sample(list(self.bv_mask), tsp_dim)):a for a in range(ts_dim)}
        self.m = [Matrix(self, a) for a in range(self.H)]
        self.cy = 0
    def update(self):
        while True:
            for a in self.m: a.update()
            self.cy += 1
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.ov = self.av = self.cv = self.pv = set()
        self.e = dict()
        self.em = 0
    def update(self):
        # fbv = {(a + self.po.fbv_offset) for a in self.po.m[self.fbi].pv}
        fbv = {(a + self.po.fbv_offset) for a in self.po.m[self.fbi].pv} if self.fbi != 0 else set()
        self.cv = (self.av | fbv)
        self.infer()
        self.eval()
        for a in self.e.keys(): self.e[a] = {k:(v - 1) for k, v in self.e[a].items() if (v > 0)}
        self.e = {k:v for k, v in self.e.items() if v}
        print(f"M: {self.ffi + 1}\tEM: {self.em:.4f}\tES: {len(self.e.keys())}")
    def eval(self):
        if self.ffi == -1:
            bv = ({(a // self.po.M) for a in self.pv} & self.po.bv_mask)
            heap = [(len(k ^ bv), random.randrange(10000), v) for k, v in self.po.bv_map.items()]
            heapq.heapify(heap)
            bv_idx = heapq.heappop(heap)[2]
            iv = self.po.iv_map[bv_idx].copy()
            for k, v in self.po.bv_map.items():
                if v == bv_idx: iv |= k
        else: iv = self.po.m[self.ffi].ov.copy()
        self.av = set()
        for a in iv:
            ci = set(range((a * self.po.M), ((a + 1) * self.po.M)))
            ovl = (ci & self.pv)
            wi = random.choice(list(ci)) if len(ovl) == 0 else random.choice(list(ovl))
            if wi in self.e.keys():
                for b in self.cv: self.e[wi][b] = self.po.adc_max
            else: self.e[wi] = {b:self.po.adc_max for b in self.cv}
            self.av.add(wi)
    def infer(self):
        self.pv = set()
        self.ov = set()
        self.em = 0
        em_ct = 0
        ks = set(self.e.keys())
        for a in self.po.C:
            ciu = (ks & set(range((a * self.po.M), ((a + 1) * self.po.M))))
            if len(ciu) > 0:
                td = {b:len(set(self.e[b].keys()) ^ self.cv) for b in ciu}
                min_val = min(td.values())
                rv = [k for k, v in td.items() if v == min_val]
                le = len(rv)
                if le > 1:
                    self.em += ((le - 1) / (self.po.M - 1))
                    em_ct += 1
                    self.ov.add(a)
                    ni = random.choice(rv)
                else: ni = rv[0]
                self.pv.add(ni)
        self.em /= max(1, em_ct)
oracle = Oracle()
oracle.update()
