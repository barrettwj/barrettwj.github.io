import random
import heapq
class Oracle:
    def __init__(self):
        self.H = 3
        self.M = 47
        self.K = 507
        self.adc_max = 77
        self.sparsity = (1.0 / self.M)
        self.iv_mask = {a for a in range(self.K)}
        self.bv_mask = {(self.K + a) for a in range(self.K)}
        self.em_mask = {((self.K * 2) + a) for a in range(self.K)}
        em_val_card = 13
        em_num_vals = (self.K - em_val_card + 1)
        em_interval = (1.0 / (em_num_vals - 1))
        em_start_idx = (self.K * 2)
        self.em_map = {(a * em_interval):frozenset({(em_start_idx + a + b) for b in range(em_val_card)}) for a in range(em_num_vals)}
        self.C = (self.iv_mask | self.bv_mask | self.em_mask)
        self.fbv_offset = (len(self.C) * self.M)
        tsp_dim_pct = 0.15
        tsp_dim = round(self.K * tsp_dim_pct)
        # ts_dim = round(self.K / (tsp_dim + 1))
        ts_dim = 25
        # self.iv_map = dict()
        # tv = self.iv_mask.copy()
        # for a in range(ts_dim):
        #     ts = set(random.sample(list(tv), tsp_dim))
        #     tv -= ts
        #     self.iv_map[a] = frozenset(ts.copy())
        # self.bv_map = dict()
        # tv = self.bv_mask.copy()
        # for a in range(ts_dim):
        #     ts = set(random.sample(list(tv), tsp_dim))
        #     tv -= ts
        #     self.bv_map[frozenset(ts.copy())] = a
        self.iv_map = {a:frozenset(set(random.sample(list(self.iv_mask), tsp_dim))) for a in range(ts_dim)}
        self.bv_map = {frozenset(set(random.sample(list(self.bv_mask), tsp_dim))):a for a in range(ts_dim)}
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
        self.ov = self.av = self.pv = set()
        self.e = dict()
        self.em = self.em_prev = self.em_delta_abs = 0
    def update(self):
        # fbv = {(a + self.po.fbv_offset) for a in self.po.m[self.fbi].pv}
        fbv = {(a + self.po.fbv_offset) for a in self.po.m[self.fbi].pv} if self.fbi != 0 else set()
        cv = (self.av | fbv)
        ################################################################################################################
        self.pv = set()
        self.ov = set()
        vi = dict()
        heap = [(len(set(self.e[a].keys()) ^ cv), random.randrange(10000), a) for a in self.e.keys()]
        heapq.heapify(heap)
        num_set_pred = max(3, round(len(self.e.keys()) * self.po.sparsity))#-------------------------------------------------HP
        while (heap and (len(self.pv) < num_set_pred)):
            a = heapq.heappop(heap)[2]
            cli = (a // self.po.M)
            if cli in vi.keys():
                self.ov.add(cli)
                vi[cli] += 1
            else:
                self.pv.add(a)
                vi[cli] = 1
        self.em_prev = self.em
        vals = [((v - 1) / (self.po.M - 1)) for v in vi.values()]
        self.em = sum(vals)
        em_ct = len(vals)
        ################################################################################################################
        if self.ffi == -1:
            bv = ({(a // self.po.M) for a in self.pv} & self.po.bv_mask)
            if (round(self.em_delta_abs * 1000000.0) <= random.randrange(10)):#----------------------------------------HP
                bv_idx = random.choice(list(self.po.bv_map.values()))
            else:
                heap = [(len(k ^ bv), random.randrange(10000), v) for k, v in self.po.bv_map.items()]
                heapq.heapify(heap)
                bv_idx = heapq.heappop(heap)[2]
            iv = self.po.iv_map[bv_idx].copy()
            for k, v in self.po.bv_map.items():
                if v == bv_idx: iv |= k
            # iv |= bv
            heap = [(abs(k - self.em_delta_abs), random.randrange(10000), v) for k, v in self.po.em_map.items()]
            heapq.heapify(heap)
            iv |= heapq.heappop(heap)[2].copy()
        else: iv = self.po.m[self.ffi].ov.copy()
        #################################################################################################################
        self.av = set()
        for a in iv:
            ci = set(range((a * self.po.M), ((a + 1) * self.po.M)))
            ovl = (ci & self.pv)
            wi = random.choice(list(ci)) if len(ovl) == 0 else random.choice(list(ovl))
            if len(ovl) == 0:
                # pass
                self.ov.add(a)
                self.em += 1.0
                em_ct += 1
            if wi in self.e.keys():
                for b in cv: self.e[wi][b] = self.po.adc_max
            else: self.e[wi] = {b:self.po.adc_max for b in cv}
            self.av.add(wi)
        self.em /= max(1, em_ct)
        self.em_delta_abs = abs(self.em - self.em_prev)
        ################################################################################################################
        for a in self.e.keys(): self.e[a] = {k:(v - 1) for k, v in self.e[a].items() if (v > 0)}
        self.e = {k:v for k, v in self.e.items() if v}
        print(f"M: {self.ffi + 1}\tEM: {self.em:.4f}\tEMA: {self.em_delta_abs:.4f}\tES: {len(self.e.keys())}\tPV: {len(self.pv)}")
oracle = Oracle()
oracle.update()
