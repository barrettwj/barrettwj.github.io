import random
class Oracle:
    def __init__(self):
        self.H = 3#-----------------------------------------------------------------------------------------HP
        self.N = 64#----------------------------------------------------------------------------------------HP
        self.N_range = set(range(self.N))
        self.M = 50#----------------------------------------------------------------------------------------HP
        self.K = (self.N * self.M)
        self.K_range = set(range(self.K))
        self.adc_max = 200#----------------------------------------------------------------------------------HP
        self.q_pct = 0.20#----------------------------------------------------------------------------------HP
        self.Q = round(self.N * self.q_pct)
        self.ts_dim = 5#------------------------------------------------------------------------------------HP
        self.ts_map = dict()
        while (len(self.ts_map) < self.ts_dim):
            tsA = set(random.sample(list(self.N_range), self.Q))
            tsB = set(random.sample(list(self.N_range), self.Q))
            self.ts_map[frozenset(random.choice(list(range((a * self.M), ((a + 1) * self.M))))
                                   for a in tsA)] = [len(self.ts_map), tsB.copy()]
        self.cy = 0
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while True:
            for a in self.m: a.update()
            self.cy += 1
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.e = dict()
        self.iv = set()
        self.pv = set()
        self.av = set()
        self.cv = set()
        self.ov = set()
        self.fbv = set()
        self.fbvm = set()
        self.em = self.em_prev = self.em_delta = self.thresh = 0
    def update(self):
        self.fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        # self.fbv = self.po.m[self.fbi].pv.copy()
        self.fbvm = {-(a + 1) for a in self.fbv}
        self.process_inference()
        bv_idx = -1
        if (self.ffi == -1):
            d = [((len(self.pv ^ k) / max(1, (len(self.pv) + len(k)))), v) for k, v in self.po.ts_map.items()]
            rs = random.sample(range(len(d)), len(d))
            ds = sorted(d, key = lambda x: (x[0], rs.pop()))
            bv_idx = ds[0][1][0]
            pv_mod = {(a // self.po.M) for a in self.pv}
            self.iv = (pv_mod ^ ds[0][1][1])
        else: self.iv = self.po.m[self.ffi].ov.copy()
        self.em = 0
        zr = 0
        mr = 0
        of = 0
        pv_ack = set()
        self.av = set()
        for a in self.iv:
            ci = set(range((self.po.M * a), (self.po.M * (a + 1))))
            ovl = (ci & self.pv)
            if len(ovl) == 0:
                self.em += 1
                zr += 1
                cav = (ci - self.e.keys())
                if not cav:
                    of += 1
                    d = [(len(self.e[b]), b) for b in (ci & self.e.keys())]
                    rs = random.sample(range(len(d)), len(d))
                    ds = sorted(d, key = lambda x: (x[0], rs.pop()))
                    del self.e[ds[0][1]]
                    cav = (ci - self.e.keys())
                wi = random.choice(list(cav))
                self.av |= ci
                self.ov.add(a)
            else:
                pv_ack |= ovl
                wi = ovl.pop()
                if len(ovl) > 1:
                    self.em += ((len(ovl) - 1) / (self.po.M - 1))
                    mr += 1
                    tv = (ovl - {wi})
                    for b in tv:
                        for c in self.fbv:
                            # if c in self.e[b]: del self.e[b][c]
                            if ((c in self.e[b]) and (self.e[b][c] > 0)): self.e[b][c] -= 1
                    self.av |= ci
                    self.ov.add(a)
            if wi in self.e:
                diff_v = (self.e[wi].keys() ^ self.cv)
                if len(diff_v) > 0:
                    ri = random.choice(list(diff_v))
                    if ri in self.e[wi]: del self.e[wi][ri]
                    else: self.e[wi][ri] = self.po.adc_max
            else: self.e[wi] = {b:self.po.adc_max for b in self.cv}
            self.av.add(wi)
        norm = max(1, len(self.iv))
        self.em /= norm
        zr /= norm
        mr /= norm
        pv_exc = (self.pv - pv_ack)
        bv_str = "" if (bv_idx == -1) else f"  BV: {str(bv_idx).rjust(3)}"
        print(f"M:{(self.ffi + 1)}  EM: {str(f'{self.em:.2f}').rjust(4)}  MEM: {str(len(self.e)).rjust(4)}" +
              f"  ZR: {str(f'{zr:.2f}').rjust(4)}  MR: {str(f'{mr:.2f}').rjust(4)}  OF: {str(of).rjust(4)}" + 
              f"  PV: {str(len(self.pv)).rjust(4)}  EX: {str(len(pv_exc)).rjust(4)}  TH: {str(f'{self.thresh:.2f}').rjust(4)}" + bv_str)
    def process_inference(self):
        self.cv = (self.iv | {(a + self.po.N) for a in self.av} | self.fbvm)
        # self.cv = (self.av | self.fbvm)
        # self.cv = (self.iv | {(a + self.po.N) for a in self.av})
        # self.cv = self.av.copy()
        d = [(k, (len(v.keys() ^ self.cv) / max(1, (len(v.keys()) + len(self.cv))))) for k, v in self.e.items()]
        norm = max(1, len(d))
        mean = (sum(a[1] for a in d) / norm)
        sigma = ((sum(((a[1] - mean) ** 2) for a in d) / norm) ** (1 / 2))
        alpha = 4#----------------------------------------------------------------------------------------------HP
        self.thresh = max(0, (mean - (alpha * sigma)))
        self.pv = {a[0] for a in d if ((a[1] <= self.thresh) and (len(self.pv) < self.po.N))}
oracle = Oracle()
oracle.update()