import random
class Oracle:
    def __init__(self):
        self.H = 3#-----------------------------------------------------------------------------------------------HP
        self.N = 1024#---------------------------------------------------------------------------------------------HP
        density_pct = 0.37#---------------------------------------------------------------------------------------HP
        self.density = round(self.N * density_pct)
        #############################################################################################################################
        self.ts_idx = 0
        ts_dim = 5#-----------------------------------------------------------------------------------------------HP
        ################################################################
        #"""
        emdm_nv = 500#--------------------------------------------------------------------------------------------HP
        emdm_card = 5#---------------------------------------------------------------------------------------------HP
        self.emdm_mask = {(self.N - 1 - a) for a in range(emdm_nv + (emdm_card - 1))}
        start_idx = min(self.emdm_mask)
        emdm_max_val = 1
        emdm_min_val = -1
        emdm_inc = ((emdm_max_val - emdm_min_val) / (emdm_nv - 1))
        self.emdm_vals = {frozenset({(start_idx + a + b) for b in range(emdm_card)}):
                          (emdm_min_val + (a * emdm_inc))  for a in range(emdm_nv)}
        self.iv_mask = (set(range(self.N)) - self.emdm_mask)
        iv_card = round(len(self.iv_mask) * density_pct)
        # self.ts = [set(random.sample(list(self.iv_mask), iv_card)) for _ in range(ts_dim)]
        #"""
        #################################################################
        self.ts = [set(random.sample(range(self.N), self.density)) for _ in range(ts_dim)]
        ##############################################################################################################################
        self.bv_map = dict()
        self.blank_cv = ([0] * self.N)
        ##############################################################################################################################
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
        self.cv_max = 10000#--------------------------------------------------------------------------------------HP
        self.cv_min = -(self.cv_max - 1)
        # self.adc_max = 1000000000#--------------------------------------------------------------------------------HP
        # self.forget_period = 1000#---------------------------------------------------------------------------------HP
        # self.forget_period_ct = 0
        self.mem = dict()
        self.bv_idx = self.bv_idx_prev = -1
        self.em = self.em_prev = self.em_delta = 0
        self.rsA = random.sample(range(len(self.po.emdm_vals)), len(self.po.emdm_vals))
        self.rsB = random.sample(range(1000000), 1000000)
        self.confusion_map_dim = 50#---------------------------------------------------------------------------------HP
        self.confusion_map = dict()
    def update(self):
        ############################################################################################################################
        """
        for k, v in self.mem.items():
            if (v[1][0] < self.adc_max): v[1][0] += 1
        #############################################################
        self.forget_period_ct += 1
        if (self.forget_period_ct == self.forget_period):
            d = [(k, v[1][1]) for k, v in self.mem.items()]
            rs = self.rsB.copy()
            ds = sorted(d, key = lambda x: (x[1], rs.pop(0)), reverse = True)
            if (ds[0][1] > 10): del self.mem[ds[0][0]]#--------------------------------------------------------------HP
            self.forget_period_ct = 0
        """
        #############################################################################################################################
        self.fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        # self.fbv = self.po.m[self.fbi].pv.copy()
        self.fbv_mod = {-(a + 1) for a in self.fbv}
        #############################################################################################################################
        self.cv = (self.iv | {(a + self.po.N) for a in self.pv} | self.fbv_mod)
        sum_v = self.po.blank_cv.copy()
        for a in self.cv:
            if (a in self.mem):
                sum_v = [(x + y) for x, y in zip(sum_v, self.mem[a][0])]
                # self.mem[a][1][1] = self.mem[a][1][0]
                # self.mem[a][1][0] = 0
            # else: self.mem[a] = [self.po.blank_cv.copy(), [0, 0]]
            else: self.mem[a] = [self.po.blank_cv.copy()]
        self.pv = {i for i, a in enumerate(sum_v) if (a > 0)}
        #############################################################################################################################
        self.bv_idx_prev = self.bv_idx
        self.bv_idx = -1
        if (self.ffi == -1):
            ##########################################################
            if (self.bv_idx_prev != -1):
                if (self.bv_idx_prev not in self.confusion_map): self.confusion_map[self.bv_idx_prev] = [0]
                else:
                    self.confusion_map[self.bv_idx_prev].append(self.em_delta)
                    if (len(self.confusion_map[self.bv_idx_prev]) > self.confusion_map_dim): self.confusion_map[self.bv_idx_prev].pop(0)
            ##########################################################
            self.iv = set()
            ##########################################################
            """
            d = [(k, abs(self.em_delta - v)) for k, v in self.po.emdm_vals.items()]
            rs = self.rsA.copy()
            ds = sorted(d, key = lambda x: (x[1], rs.pop()))
            self.iv = set(ds[0][0])
            """
            ##########################################################
            if (self.po.bv_map):
                d = [((len(k ^ self.pv) / self.po.N), k, v) for k, v in self.po.bv_map.items()]
                rs = self.rsB.copy()
                ds = sorted(d, key = lambda x: (x[0], rs.pop()))
                thresh = abs(self.em_delta)#----------------------------------------------------------------------------------HP
                if (ds[0][0] >= thresh):
                    if (random.randrange(1000000) < 900000):
                        d = [(sum(v), k) for k, v in self.confusion_map.items()]
                        rs = self.rsB.copy()
                        ds = sorted(d, key = lambda x: (x[0], rs.pop()), reverse = True)
                        self.bv_idx = ds[0][1]
                    else: self.bv_idx = random.choice(range(len(self.po.ts)))
                    rv = (self.iv | self.po.ts[self.bv_idx])
                    self.po.bv_map[frozenset(rv)] = self.bv_idx#--------------------------------------????????????
                    self.iv = rv.copy()
                else:
                    self.bv_idx = ds[0][2]
                    self.iv |= ds[0][1]
            else:
                self.bv_idx = random.choice(range(len(self.po.ts)))
                rv = (self.iv | self.po.ts[self.bv_idx])
                self.po.bv_map[frozenset(rv)] = self.bv_idx#--------------------------------------????????????
                self.iv = rv.copy()
            ##########################################################
        else: self.iv = self.po.m[self.ffi].ev.copy()
        ###############################################################################################################################
        self.ev = (self.iv ^ self.pv)
        self.em_prev = self.em
        self.em = (len(self.ev) / self.po.N)
        self.em_delta = (self.em - self.em_prev)
        self.ev ^= self.fbv
        ################################################################################################################################
        dv = 1#---------------------------------------------------------------------------------------------------HP
        et1 = (self.iv - self.pv)
        et2 = (self.pv - self.iv)
        for a in self.cv:
            for b in et1: self.mem[a][0][b] = min(self.cv_max, (self.mem[a][0][b] + dv))
            for b in et2: self.mem[a][0][b] = max(self.cv_min, (self.mem[a][0][b] - dv))
        ##################################################################################################################################
        bv_str = f"  BV: {str(self.bv_idx).rjust(2)}" if (self.bv_idx != -1) else ""
        print(f"M{(self.ffi + 1)}  EM: {str(f'{self.em:.2f}').rjust(4)}  MEM: {str(len(self.mem)).rjust(4)}" + bv_str)
        ##################################################################################################################################
oracle = Oracle()
oracle.update()