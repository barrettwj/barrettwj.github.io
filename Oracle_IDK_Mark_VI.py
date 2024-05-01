import random
import heapq
class Oracle:
    def __init__(self):
        self.H = 3
        self.M = 53
        self.K = 67
        self.adc_max = 377
        #######################################################################################################
        tsp_dim_pct = 0.20
        tsp_dim = round(self.K * tsp_dim_pct)
        ts_dim = round(self.K / (tsp_dim + 2))
        self.iv_mask = {a for a in range(self.K)}
        tv = self.iv_mask.copy()
        self.iv_map = dict()
        for a in range(ts_dim):
            ts = set(random.sample(list(tv), tsp_dim))
            tv -= ts
            self.iv_map[a] = frozenset(ts.copy())
        ########################################################################################################
        self.bv_mask = {(self.K + a) for a in range(self.K)}
        tv = self.bv_mask.copy()
        self.bv_map = dict()
        for a in range(ts_dim):
            ts = set(random.sample(list(tv), tsp_dim))
            tv -= ts
            self.bv_map[frozenset(ts.copy())] = a
        #########################################################################################################
        # ts_dim = 25
        # self.iv_map = {a:frozenset(set(random.sample(list(self.iv_mask), tsp_dim))) for a in range(ts_dim)}
        # self.bv_map = {frozenset(set(random.sample(list(self.bv_mask), tsp_dim))):a for a in range(ts_dim)}
        ###########################################################################################################
        em_start_idx = (self.K * 2)
        self.em_mask = {(em_start_idx + a) for a in range(self.K)}
        em_val_card = 13
        em_num_vals = (self.K - em_val_card + 1)
        em_interval = (1.0 / (em_num_vals - 1))
        self.em_map = {(a * em_interval):frozenset({(em_start_idx + a + b) for b in range(em_val_card)}) for a in range(em_num_vals)}
        ###########################################################################################################
        ev_start_idx = (self.K * 3)
        self.ev_mask = {(ev_start_idx + a) for a in range(self.K)}
        ev_val_card = 3
        ev_num_vals = (self.K - ev_val_card + 1)
        ev_interval = (1.0 / (ev_num_vals - 1))
        self.ev_map = {(a * ev_interval):frozenset({(ev_start_idx + a + b) for b in range(ev_val_card)}) for a in range(ev_num_vals)}
        ##########################################################################################################
        self.C = (self.iv_mask | self.bv_mask | self.em_mask | self.ev_mask)
        self.fbv_offset = -((len(self.C) * self.M) + 1)
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
        self.ov = self.av = self.pv = self.cv = self.cv_prev = set()
        self.e = dict()
        self.em = self.em_prev = self.em_delta_abs = self.ev = 0
        self.low_ad = False
        self.min_conns = 10
        self.em_el_mask = set()
        for a in self.po.em_mask: self.em_el_mask |= set(range((a * self.po.M), ((a + 1) * self.po.M)))
    def update(self):
        # fbv = {(a + self.po.fbv_offset) for a in self.po.m[self.fbi].pv}
        fbv = {(a + self.po.fbv_offset) for a in self.po.m[self.fbi].pv} if self.fbi != 0 else set()
        self.cv_prev = self.cv.copy()
        self.cv = (self.av | fbv)
        self.ov = set()
        ################################################################################################################
        self.pv = set()
        vi = dict()
        heap = [((len(set(self.e[a]) ^ self.cv) / (len(self.e[a]) + len(self.cv))), random.randrange(10000), a) for a in self.e]
        # heap = [(len(set(self.e[a]) ^ self.cv), random.randrange(10000), a) for a in self.e]
        li = [a[0] for a in heap]
        le = len(li)
        mean = (sum(li) / max(1, le))
        variance = (sum(((a[0] - mean) ** 2) for a in heap) / max(1, le))
        stdv = (variance ** 0.5)
        # thresh = (mean - (variance * 200))#--------------------------------------------------------------------------------HP
        thresh = (mean - (stdv * 4))#-----------------------------------------------------------------------------------------HP
        # thresh = mean
        # median = 0
        # if le > 0: median = sorted(li)[le//2] if (le % 2) != 0 else ((sorted(li)[le//2] + sorted(li)[((le//2) - 1)]) / 2)
        # thresh = median
        heapq.heapify(heap)
        while heap:
            d, r, a = heapq.heappop(heap)
            cli = (a // self.po.M)
            if cli in vi:
                self.ov.add(cli)
                vi[cli] += 1
            else:
                if d <= thresh: self.pv.add(a)
                vi[cli] = 1                
        self.em_prev = self.em
        vals = [((a - 1) / (self.po.M - 1)) for a in vi.values()]
        self.em = sum(vals)
        em_ct = len(vals)
        ################################################################################################################
        if self.ffi == -1:
            bv = ({(a // self.po.M) for a in self.pv} & self.po.bv_mask)
            heap = [(len(k ^ bv), random.randrange(10000), v, k) for k, v in self.po.bv_map.items()]
            heapq.heapify(heap)
            d, r, bv_idx, bv_vec = heapq.heappop(heap)
            iv = {a for a in self.po.iv_map[bv_idx]}
            iv |= bv_vec
            ########################################################
            delta = 50#--------------------------------------------------------------------------------------------------HP
            if not self.low_ad:
                inc_val = (-delta + round(self.em_delta_abs * delta * 2.0))
                for a in self.pv:
                    if (a // self.po.M) in bv_vec:
                        tv = (set(self.e[a]) & self.cv_prev & self.em_el_mask)
                        for b in tv: self.e[a][b] = max(0, (self.e[a][b] + inc_val))
            ########################################################
            self.low_ad = False
            if (round(self.em_delta_abs * 1000000.0) <= random.randrange(50000)):#---------------------------------------------HP
            # if False:
                num = round(len(iv) * 0.05)#------------------------------------------------------------------------------------HP
                if num > 0:
                    self.low_ad = True
                    tv = iv.copy()
                    while len(iv ^ tv) < num:
                        ri = random.choice(list(self.po.iv_mask))
                        if ri in tv: tv.remove(ri)
                        else: tv.add(ri)
                    iv = tv.copy()
            ########################################################
            # ev_bv = ({(a // self.po.M) for a in self.pv} & self.po.ev_mask)
            # heap = [(len(v ^ ev_bv), random.randrange(10000), k) for k, v in self.po.ev_map.items()]
            # heapq.heapify(heap)
            # self.ev = heapq.heappop(heap)[2]
            # if (round(self.ev * 1000000.0) > random.randrange(1000000)):#----------------------------------------HP
            if False:
                num = round(len(iv) * 0.70)
                if num > 0:
                    rs = set(random.sample(list(self.po.iv_mask), num))
                    for a in rs:
                        if a in iv: iv.remove(a)
                        else: iv.add(a)
            ##########################################################
            heap = [(abs(k - self.em_delta_abs), random.randrange(10000), v) for k, v in self.po.em_map.items()]
            heapq.heapify(heap)
            iv |= heapq.heappop(heap)[2]
            ##########################################################
            # heap = [(abs(k - self.ev), random.randrange(10000), v) for k, v in self.po.ev_map.items()]
            # heapq.heapify(heap)
            # iv |= heapq.heappop(heap)[2]
        else: iv = self.po.m[self.ffi].ov.copy()
        #################################################################################################################
        self.av = set()
        for a in iv:
            ci = set(range((a * self.po.M), ((a + 1) * self.po.M)))
            ovl = (ci & self.pv)
            if len(ovl) == 0:
                self.ov.add(a)
                self.em += 1
                em_ct += 1
                cav = (ci - set(self.e))
                while not cav:
                    cnav = (ci & set(self.e))
                    for b in cnav:
                        self.e[b] = {k:(v - 1) for k, v in self.e[b].items() if (v > 0)}
                        if len(self.e[b]) < self.min_conns:
                            del self.e[b]
                            break
                    cav = (ci - set(self.e))
                wi = random.choice(list(cav))
            else: wi = ovl.pop()
            if wi in self.e:
                for b in self.cv: self.e[wi][b] = self.po.adc_max
            else: self.e[wi] = {b:self.po.adc_max for b in self.cv}
            self.av.add(wi)
        self.em /= max(1, em_ct)
        self.em_delta_abs = abs(self.em - self.em_prev)
        ################################################################################################################
        # tl = list(self.e)
        # for a in tl:
        #     self.e[a] = {k:(v - 1) for k, v in self.e[a].items() if (v > 0)}
        #     if len(self.e[a]) < self.min_conns: del self.e[a]
        print(f"M: {(self.ffi + 1)}  EM: {self.em:.4f}  EMA: {round(self.em_delta_abs * 1000000.0):7d}" +
        f"  ES: {len(self.e):6d}  PV: {len(self.pv):4d}")
oracle = Oracle()
oracle.update()
