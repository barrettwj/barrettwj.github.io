import random
import heapq
class Oracle:
    def __init__(self):
        self.H = 6#----------------------------------------------------------------------------------------------------------------HP
        self.K = 207#-should be odd!!!---------------------------------------------------------------------------------------------HP
        self.s = Sensorium(self)
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while True:
            self.s.update()
            for a in self.m: a.update()
class Sensorium:
    def __init__(self, po_in):
        self.po = po_in
        #______________________________________________________________EM INTEROCEPTION_______________________________________________
        em_int_card = 3#------------------------------------------------------------------------------------------------------------HP
        em_int_dim = 11#-should be odd!!!-------------------------------------------------------------------------------------------HP
        start_idx = -round((em_int_dim - 1) / 2)
        em_int_v = {(start_idx + a) for a in range(em_int_dim)}
        em_int_num_values = (em_int_dim - em_int_card + 1)
        em_val_interval = (1.0 / (em_int_num_values - 1))
        self.em_aff_values = {frozenset({(start_idx + a + b) for b in range(em_int_card)}):
                              (a * em_val_interval) for a in range(em_int_num_values)}
        self.unavail_idxs = em_int_v.copy()
        #______________________________________________________________RF AFFERENT___________________________________________________
        aff_dim = 67#-should be odd!!!---------------------------------------------------------------------------------------------HP
        start_idx = -round((aff_dim - 1) / 2)
        self.aff_v = {(start_idx + a) for a in range(aff_dim)}
        while (len(self.aff_v & self.unavail_idxs) > 0): self.aff_v = {(a - 1) for a in self.aff_v}
        self.unavail_idxs |= self.aff_v
        #______________________________________________________________RF EFFERENT___________________________________________________
        eff_dim = 67#-should be odd!!!---------------------------------------------------------------------------------------------HP
        start_idx = -round((eff_dim - 1) / 2)
        self.eff_v = {(start_idx + a) for a in range(eff_dim)}
        while (len(self.eff_v & self.unavail_idxs) > 0): self.eff_v = {(a + 1) for a in self.eff_v}
        self.unavail_idxs |= self.eff_v
        self.sv = set()
        ts_len = 5#---------------------------------------------------------------------------------------------------------------HP
        self.aff_card = round(aff_dim / (ts_len + 1))
        tv = self.aff_v.copy()
        self.ts = []
        for _ in range(ts_len):
            rv = set(random.sample(list(tv), self.aff_card))
            tv -= rv
            self.ts.append(rv.copy())
        self.ts_idx = self.idx_delta = 0
        beh_mag = (len(self.ts) - 1)
        self.beh_idx_set = {(beh_mag - a) for a in range((beh_mag * 2) + 1)}
        self.beh_map_max_size = ts_len#-------------------------------------------------------------------------------------------HP
        self.eff_card = round(eff_dim / (self.beh_map_max_size + 1))
        tv = self.eff_v.copy()
        self.beh_map = dict()
        for _ in range(self.beh_map_max_size):
            rv = set(random.sample(list(tv), self.eff_card))
            tv -= rv
            ri = random.choice(list(self.beh_idx_set))
            self.beh_idx_set.remove(ri)
            self.beh_map[frozenset(rv.copy())] = ri
        self.sv_card = (em_int_card + self.aff_card + self.eff_card)
        self.bv = set()
    def update(self):
        self.bv = (self.po.m[0].pv & self.eff_v)
        heap = [(len(k ^ self.bv), random.randrange(10000), k) for k in self.beh_map.keys()]
        heapq.heapify(heap)
        self.bv = heapq.heappop(heap)[2].copy()
        self.idx_delta = self.beh_map[self.bv]
        self.ts_idx = ((self.ts_idx + len(self.ts) + self.idx_delta) % len(self.ts))
        self.sv = self.ts[self.ts_idx].copy()
        heap = [(abs(self.po.m[0].em - v), random.randrange(10000), k) for k, v in self.em_aff_values.items()]
        heapq.heapify(heap)
        em_v = heapq.heappop(heap)[2].copy()
        self.sv |= em_v
        self.sv |= self.bv
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = (mi_in + 1) if (mi_in < (self.po.H - 1)) else -1
        self.pev = self.pv = self.cv = set()
        start_idx = -round((self.po.K - 1) / 2)
        self.cv_dim = 3#----------------------------------------------------------------------------------------------------------HP
        self.e = {(start_idx + a):{(start_idx + b):0 for b in range((self.po.K * self.cv_dim))} for a in range(self.po.K)}
        self.em = self.em_prev = self.em_error = 0
        self.w_max = 67#----------------------------------------------------------------------------------------------------------HP
        self.w_min = -(self.w_max - 1)
        self.em_sp = 0.10#--------------------------------------------------------------------------------------------------------HP
    def update(self):
        iv = self.po.s.sv.copy() if self.ffi == -1 else self.po.m[self.ffi].pev.copy()
        self.pev = (iv ^ self.pv)
        false_pev = (self.pv - iv)
        failed_pev = (iv - self.pv)
        self.em = (len(self.pev) / max(1, (len(iv) + len(self.pv))))
        # self.process_EPIFOR()
        wd = 1#----------------------------------------------------------------------------------------------------------------HP
        for a in self.cv:
            for b in false_pev: self.e[b][a] = max(self.w_min, (self.e[b][a] - wd))
            for b in failed_pev: self.e[b][a] = min(self.w_max, (self.e[b][a] + wd))
        fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != -1) else set()#----------------------------------------------------HP
        # fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != -1) else self.po.m[0].pv.copy()#-----------------------------------HP
        if self.cv_dim == 3: self.cv = (iv | {(self.po.K + a) for a in self.pv} | {((self.po.K * 2) + a) for a in fbv})
        if self.cv_dim == 2: self.cv = (iv | {(self.po.K + a) for a in fbv})
        self.pv = {a for a in self.e.keys() if sum(self.e[a][b] for b in self.cv) > 0}
        agent_str = f"\tAG: {self.po.s.idx_delta}" if (self.ffi == -1) else ""
        print(f"M{self.ffi + 1}  EM: {(self.em * 100.0):.2f}%\tIV: {len(iv)}\tPV: {len(self.pv)}" + agent_str)
    def process_EPIFOR(self):
        if self.ffi == -1:
            em_sp_abs_error = abs(self.em - self.em_sp)
            sc = 3.0#-------------------------------------------------------------------------------------------------------------HP
            sc_val = round(em_sp_abs_error * sc)
            tA = (self.pv & self.po.s.eff_v)
            for a in tA:
                tB = (self.cv & set(self.e[a].keys()))
                for b in tB: self.e[a][b] = max(0, (self.e[a][b] - sc_val))
oracle = Oracle()
oracle.update()