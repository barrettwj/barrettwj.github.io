import random
class Oracle:
    def __init__(self):
        self.H = 2#-----------------------------------------------------------------------------------------HP
        self.N = 256#---------------------------------------------------------------------------------------HP
        self.M = 49#----------------------------------------------------------------------------------------HP
        self.adc_max = 50#-musn't be too high!!!------------------------------------------------------------HP
        self.n_pct = 0.10#----------------------------------------------------------------------------------HP
        self.K = (self.N * self.M)
        self.total_m = set(range(self.K))
        self.exov_dim_pct = 0.25#---------------------------------------------------------------------------HP
        self.exov_dim = round(self.N * self.exov_dim_pct)
        self.exov_mask = {(self.N - 1 - a) for a in range(self.exov_dim)}
        self.exov_card = round(self.exov_dim * self.n_pct)
        self.exiv_mask = (set(range(self.N)) - self.exov_mask)
        self.exiv_card = round(len(self.exiv_mask) * self.n_pct)
        ###################################################################################################################
        self.ts_dim = 7#------------------------------------------------------------------------------------HP
        self.ts_map = dict()
        while (len(self.ts_map) < self.ts_dim):
            self.ts_map[frozenset(random.sample(
                list(self.exov_mask),
                self.exov_card))] = [len(self.ts_map), set(random.sample(list(self.exiv_mask), self.exiv_card))]
        # rv = set(random.choice(list(self.ts_map.keys())))
        # self.rexov = {((a * self.M) + 2) for a in rv}
        ###################################################################################################################
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
        self.e_cap = 5000#----------------------------------------------------------------------------------HP
        self.e = dict()
        self.pv_dim = (self.po.exiv_card + self.po.exov_card)
        self.iv = set()
        self.pv = set()
        self.av = set()
        self.cv = set()
        self.ov = set()
        self.fbv = set()
        self.fbvm = set()
        self.exov = set()
        self.em = self.em_prev = self.em_delta = 0
    def update(self):
        ########################################################################################################################
        fbv_raw = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        # self.fbv = fbv_raw.copy()
        self.fbv = {-(a + 1) for a in fbv_raw}
        # self.fbvm = {(a // self.po.M):-(a + 1) for a in self.fbv}
        self.fbvm = {-((a // self.po.M) + 1) for a in fbv_raw}
        ########################################################################################################################
        self.process_inference()
        ########################################################################################################################
        bv_idx = -1
        if (self.ffi == -1):
            self.exov = ({(a // self.po.M) for a in self.pv} & self.po.exov_mask)
            d = [((len(self.exov ^ k) / max(1, (len(self.exov) + len(k)))), set(k), v) for k, v in self.po.ts_map.items()]
            rs = random.sample(range(len(d)), len(d))
            ds = sorted(d, key = lambda x: (x[0], rs.pop()))
            bv_idx = ds[0][2][0]
            self.iv = ds[0][2][1].copy()
            self.iv |= ds[0][1]
        else: self.iv = self.po.m[self.ffi].ov.copy()
        ########################################################################################################################
        self.em = 0
        zr = 0
        mr = 0
        pv_ack = set()
        self.ov = set()
        self.av = set()
        for a in self.iv:
            ci = set(range((self.po.M * a), (self.po.M * (a + 1))))
            ovl = (ci & self.pv)
            le = len(ovl)
            if le == 0:
                self.em += 1
                zr += 1
                cav = (ci - self.e.keys())
                if not cav:
                    d = [(sum(self.e[b][c] for c in self.e[b]), b) for b in (ci & self.e.keys())]
                    rs = random.sample(range(len(d)), len(d))
                    ds = sorted(d, key = lambda x: (x[0], rs.pop()))
                    del self.e[ds[0][1]]
                    cav = (ci - self.e.keys())
                wi = random.choice(list(cav))
                self.e[wi] = {b:self.po.adc_max for b in self.cv}
                self.ov.add(a)
            else:
                pv_ack |= ovl
                wi = ovl.pop()
                if le > 1:
                    self.em += ((le - 1) / (self.po.M - 1))
                    mr += 1
                    self.ov.add(a)
                else:
                    if (wi in self.e):
                        for b in self.cv: self.e[wi][b] = self.po.adc_max
                    else:self.e[wi] = {b:self.po.adc_max for b in self.cv}   
            self.av.add(wi)
        self.em /= max(1, len(self.iv))
        pv_exc = (self.pv - pv_ack)
        #########################################################################################################################
        if (len(self.e) > self.e_cap):
            ec = self.e.copy()
            # ec = {k:v for k, v in self.e.items() if (k not in self.cv)}
            for kA in ec.keys():
                self.e[kA] = {kB:(vB - 1) for kB, vB in self.e[kA].items() if (vB > 0)}
                if not self.e[kA]: del self.e[kA]
            while (len(self.e) > self.e_cap):
                d = [(sum(self.e[k][a] for a in self.e[k].keys()), k) for k in self.e.keys()]
                rs = random.sample(range(len(d)), len(d))
                ds = sorted(d, key = lambda x: (x[0], rs.pop()))
                del self.e[ds[0][1]]
        #########################################################################################################################
        # self.process_inference()
        #########################################################################################################################
        #________________________________________________________________________________________________________________
        bv_str = "" if (bv_idx == -1) else f"  BV: {str(bv_idx).rjust(2)}"
        print(f"M:{(self.ffi + 1)}  EM: {str(f'{self.em:.2f}').rjust(4)}  MEM: {str(len(self.e)).rjust(4)}" +
              f"  PV: {str(len(self.pv)).rjust(2)}  EX: {str(len(pv_exc)).rjust(2)}" +
              f"  ZR: {str(zr).rjust(2)}  MR: {str(mr).rjust(2)}" + bv_str)
        ########################################################################################################################
    def process_inference(self):
        # self.cv = (self.iv | {(a + self.po.N) for a in self.av} | {(a + (self.po.N * 2)) for a in self.fbv})
        self.cv = (self.iv | {(a + self.po.N) for a in self.av} | {(a + self.po.N + self.po.K) for a in self.fbvm})
        # self.cv = (self.iv | {(a + self.po.N) for a in self.av} | self.fbvm)
        # self.cv = (self.av | self.fbvm)
        # self.cv = (self.iv | {(a + self.po.N) for a in self.av})
        # self.cv = self.av.copy()
        d = [((len(v.keys() ^ self.cv) / max(1, (len(v.keys()) + len(self.cv)))), k) for k, v in self.e.items()]
        rs = random.sample(range(len(d)), len(d))
        ds = sorted(d, key = lambda x: (x[0], rs.pop()))
        pv_dim = min(len(ds), self.pv_dim)
        self.pv = {ds[a][1] for a in range(pv_dim)}
        #######################################################################################################################
        if (self.ffi == -1):
            tv = ({(a // self.po.M) for a in self.pv} & self.po.exov_mask)
            # if (len(self.exov) == 0):
            # if (random.randrange(1000000) < 100000):
            if (len(tv) < self.po.exov_card):
                    self.pv |= {((a * self.po.M) + 2) for a in random.choice(list(self.po.ts_map.keys()))}
                    # self.pv |= self.po.rexov
                    # print(self.po.cy)
oracle = Oracle()
oracle.update()