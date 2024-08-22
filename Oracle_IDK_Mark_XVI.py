import random
class Oracle:
    def __init__(self):
        self.H = 4#-----------------------------------------------------------------------------------------HP
        self.N = 512#----------------------------------------------------------------------------------------HP
        self.N_range = set(range(self.N))
        self.M = 50#----------------------------------------------------------------------------------------HP
        self.K = (self.N * self.M)
        self.adc_max = 200#---------------------------------------------------------------------------------HP
        self.q_pct = 0.37#----------------------------------------------------------------------------------HP
        self.Q = round(self.N * self.q_pct)
        self.ts_dim = 7#------------------------------------------------------------------------------------HP
        self.ts_map = dict()
        while (len(self.ts_map) < self.ts_dim):
            tsA = set(random.sample(list(self.N_range), self.Q))
            tsB = set(random.sample(list(self.N_range), self.Q))
            self.ts_map[frozenset(random.choice(list(range((a * self.M), ((a + 1) * self.M))))
                                   for a in tsA)] = [len(self.ts_map), tsB.copy()]
            # self.ts_map[frozenset({(a * self.M) for a in tsA})] = [len(self.ts_map), tsB.copy()]
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
        self.fbvm = dict()
        self.em = self.em_prev = self.em_delta = self.thresh = 0
    def update(self):
        self.fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        # self.fbv = self.po.m[self.fbi].pv.copy()
        self.fbvm = dict()
        for a in self.fbv:
            cli = (a // self.po.M)
            ovlv = (self.fbv & set(range((cli * self.po.M), ((cli + 1) * self.po.M))))
            if (len(ovlv) == 1):
                idx = ovlv.pop()
                self.fbvm[cli] = -(idx + 1)
        self.generate_prediction()
        bv_idx = -1
        if (self.ffi == -1):
            d = [((len(self.pv ^ k) / max(1, (len(self.pv) + len(k)))), v) for k, v in self.po.ts_map.items()]
            rs = random.sample(range(len(d)), len(d))
            ds = sorted(d, key = lambda x: (x[0], rs.pop()))
            bv_idx = ds[0][1][0]
            self.iv = ds[0][1][1].copy()
        else: self.iv = self.po.m[self.ffi].ov.copy()
        self.em = zr = mr = of = 0
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
            else:
                pv_ack |= ovl
                wi = ovl.pop()
                if len(ovl) > 0:
                    self.em += (len(ovl) / (self.po.M - 1))
                    mr += 1
                    if a in self.fbvm:
                        for b in ovl: self.e[b][self.fbvm[a]] = self.po.adc_max
                    self.ov.add(a)
            self.av.add(wi)
            if wi in self.e:
                for b in self.cv: self.e[wi][b] = self.po.adc_max
            else: self.e[wi] = {b:self.po.adc_max for b in self.cv}
        norm = max(1, len(self.iv))
        self.em /= norm
        zr /= norm
        mr /= norm
        pv_exc = (self.pv - pv_ack)
        bv_str = "" if (bv_idx == -1) else f"  BV: {str(bv_idx).rjust(3)}"
        print(f"M:{(self.ffi + 1)}  EM: {str(f'{self.em:.2f}').rjust(4)}  MEM: {str(len(self.e)).rjust(4)}" +
              f"  ZR: {str(f'{zr:.2f}').rjust(4)}  MR: {str(f'{mr:.2f}').rjust(4)}  OF: {str(of).rjust(4)}  AV: {str(len(self.av)).rjust(6)}" + 
              f"  PV: {str(len(self.pv)).rjust(4)}  EX: {str(len(pv_exc)).rjust(4)}  TH: {str(f'{self.thresh:.2f}').rjust(4)}" + bv_str)
    def generate_prediction(self):
        self.cv = (self.iv | {(a + self.po.N) for a in self.av})
        mean = 0
        acts = []
        for k, v in self.e.items():
            act = (len(v.keys() ^ self.cv) / max(1, (len(v.keys()) + len(self.cv))))
            act = min(1, (act + (len((v.keys() & set(self.fbvm.values()))) * 0.02)))#-----------------------------------HP
            mean += act
            acts.append((k, act))
        norm = max(1, len(acts))
        mean /= norm
        sigma = ((sum(((a[1] - mean) ** 2) for a in acts) / norm) ** (1 / 2))
        alpha = 1#-shouldn't be too large!!!-If zr is high, this value may be too high!!!----------------------------HP
        self.thresh = max(0, (mean - (alpha * sigma)))
        self.pv = {a[0] for a in acts if (a[1] <= self.thresh)}
oracle = Oracle()
oracle.update()