import random
class Oracle:
    def __init__(self):
        self.H = 6#-----------------------------------------------------------------------------------------------HP
        self.N = 2048#---------------------------------------------------------------------------------------------HP
        density_pct = 0.37#---------------------------------------------------------------------------------------HP
        self.density = round(self.N * density_pct)
        emdm_dim = 1000
        self.emdm_mask = {(self.N - 1 - a) for a in range(emdm_dim)}
        emdm_min_val = -1
        emdm_max_val = 1
        emdm_inc = ((emdm_max_val - emdm_min_val) / (emdm_dim - 1))
        self.emdm_vals = {(emdm_min_val + (a * emdm_inc)): frozenset({a}) for a in range(emdm_dim)}
        self.iv_mask = (set(range(self.N)) - self.emdm_mask)
        iv_card = round(len(self.iv_mask) * density_pct)
        ts_dim = 13#-----------------------------------------------------------------------------------------------HP
        self.ts = [set(random.sample(list(self.iv_mask), iv_card)) for _ in range(ts_dim)]
        self.ts_idx = 0
        self.bv_map = dict()
        self.blank_cv = ([0] * self.N)
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while True:
            for a in self.m: a.update()
            self.ts_idx = ((self.ts_idx + 1) % len(self.ts))
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.fbv = set()
        self.fbv_mod = set()
        self.iv = set()
        self.ev = set()
        self.cv = set()
        self.pv = set()
        self.pv_prev = set()
        self.cv_max = 10000#--------------------------------------------------------------------------------------HP
        self.cv_min = -(self.cv_max - 1)
        self.mem = dict()
        self.min_dist_thresh = 0.001#-----------------------------------------------------------------------------HP
        self.em = self.em_prev = self.em_delta = 0
        self.rsA = random.sample(range(len(self.po.emdm_vals)), len(self.po.emdm_vals))
    def update(self):
        self.fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        # self.fbv = self.po.m[self.fbi].pv.copy()
        self.fbv_mod = {-(a + 1) for a in self.fbv}
        self.generate_prediction()
        bv_idx = -1
        if (self.ffi == -1):
            #"""
            min_dist = (self.min_dist_thresh * 10)
            for k, v in self.po.bv_map.items():
                dist = (len(k ^ self.pv) / self.po.N)
                if (dist < min_dist):
                    bv_idx = v[0]
                    self.iv = v[1].copy()
                    min_dist = dist
            if (min_dist > self.min_dist_thresh):
                bv_idx = random.choice(range(len(self.po.ts)))
                rv = self.po.ts[bv_idx].copy()
                self.po.bv_map[frozenset(self.pv)] = [bv_idx, rv.copy()]
                self.iv = rv.copy()
            #"""
            # self.iv = self.po.ts[self.po.ts_idx]
            d = [(abs(self.em_delta - k), v) for k, v in self.po.emdm_vals.items()]
            rs = self.rsA.copy()
            ds = sorted(d, key = lambda x: (x[0], rs.pop(0)))
            self.iv |= ds[0][1]
        else: self.iv = self.po.m[self.ffi].ev.copy()
        self.ev = ((self.iv ^ self.pv) ^ self.fbv)
        self.em_prev = self.em
        self.em = (len(self.ev) / self.po.N)
        self.em_delta = (self.em - self.em_prev)
        bv_str = f"  BV: {str(bv_idx).rjust(2)}" if (bv_idx != -1) else ""
        print(f"M{(self.ffi + 1)}  EM: {str(f'{self.em:.2f}').rjust(4)}" + bv_str)
        ivl = [1 if (a in self.iv) else -1 for a in range(self.po.N)]
        dv = 0.01#---------------------------------------------------------------------------------------------------HP
        failed_ev = (self.iv - self.pv)
        for a in self.cv:
            if (a in self.mem):
                for b in failed_ev: self.mem[a][0][b] = min(self.cv_max, (self.mem[a][0][b] + dv))
            else: self.mem[a] = [ivl.copy(), 0]
            # else: self.mem[a] = [self.blank_cv.copy(), 0]
        false_ev = (self.pv - self.iv)
        for a in self.cv:
            if (a in self.mem):
                for b in false_ev: self.mem[a][0][b] = max(self.cv_min, (self.mem[a][0][b] - dv))
            else: self.mem[a] = [ivl.copy(), 0]
            # else: self.mem[a] = [self.po.blank_cv.copy(), 0]
    def generate_prediction(self):
        # self.cv = self.fbv_mod.copy()
        # self.cv = self.iv.copy()
        self.cv = (self.iv | {(a + self.po.N) for a in self.pv} | self.fbv_mod)
        # self.cv = (self.iv | self.fbv_mod)
        # self.cv = (self.iv | {(a + self.po.N) for a in self.pv_prev} | self.fbv_mod)
        sum_v = self.po.blank_cv.copy()
        for a in self.cv:
            if (a in self.mem): sum_v = [(x + y) for x, y in zip(sum_v, self.mem[a][0])]
            # else: self.mem[a] = [self.po.blank_cv.copy(), 0]
        self.pv_prev = self.pv.copy()
        self.pv = {i for i, a in enumerate(sum_v) if (a > 0)}
oracle = Oracle()
oracle.update()