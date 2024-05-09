import random
import heapq
class Oracle:
    def __init__(self):
        self.H = 3
        self.M = 53#-53
        self.K = 67
        self.adc_max = 367
        self.adc_min = round(self.adc_max * 0.80)
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
        em_val_card = 7#-musn't be too small!!!!--------------------------------------------------------------------------HP
        em_num_vals = (self.K - em_val_card + 1)
        em_interval = (1.0 / (em_num_vals - 1))
        self.em_map = {(a * em_interval):frozenset({(em_start_idx + a + b) for b in range(em_val_card)}) for a in range(em_num_vals)}
        ##########################################################################################################
        self.C = (self.iv_mask | self.bv_mask | self.em_mask)
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
        self.ov = self.av = self.pv = set()
        self.e = dict()
        self.em = self.em_prev = self.em_delta_abs = self.ev = 0
        self.low_ad = False
        self.min_conns = 3#---------------------------------------------------------------------------------------------HP
        self.em_el_mask = set()
        for a in self.po.em_mask: self.em_el_mask |= set(range((a * self.po.M), ((a + 1) * self.po.M)))
    def update(self):
        """
        if self.ffi == -1:
            delta = 10#--------------------------------------------------------------------------------------------------HP
            if not self.low_ad:
                inc_val = round(-delta + (self.em_delta_abs * delta * 2.0))
                for a in self.pv:
                    if (a // self.po.M) in self.bv_vec:
                        # tv = (set(self.e[a]) & self.cv & self.em_el_mask)
                        tv = (set(self.e[a]) & self.cv)
                        for b in tv: self.e[a][b] = max(0, (self.e[a][b] + inc_val))
        ################################################################################################################
        """
        # fbv_conf = {(a // self.po.M):(a + self.po.fbv_offset) for a in self.po.m[self.fbi].pv}
        fbv_conf = {(a // self.po.M):(a + self.po.fbv_offset) for a in self.po.m[self.fbi].pv} if self.fbi != 0 else dict()
        self.ov = set()
        ################################################################################################################
        fb_val = 0.10#---------------------------------------------------------------------------------------------------HP
        acts = dict()
        for a in self.e:
            act = (len(set(self.e[a]) ^ self.av) / max(1, (len(self.e[a]) + len(self.av))))
            if (a // self.po.M) in fbv_conf: act = min(1, (act + fb_val))
            # if (a // self.po.M) in fbv_conf: act = (act + fb_val)
            acts[a] = act
        mean = variance = sigma = thresh = 0
        le = len(acts)
        if le > 0:
            mean = (sum(acts.values()) / le)
            variance = (sum(((v - mean) ** 2) for v in acts.values()) / le)
            sigma = (variance ** 0.5)
            mult = 1.50#-musn't be too large!!!-----------------------------------------------------------------------------HP
            thresh = (mean - (sigma * mult))
        self.pv = set()
        vi = dict()
        while acts:
            a = random.choice(list(acts.keys()))
            cli = (a // self.po.M)
            if cli in vi:
                self.ov.add(cli)
                vi[cli] += 1
            else:
                if acts[a] <= thresh: self.pv.add(a)
                vi[cli] = 1
            del acts[a]              
        self.em_prev = self.em
        vals = [((a - 1) / (self.po.M - 1)) for a in vi.values()]
        self.em = sum(vals)
        em_ct = len(vals)
        mr = (sum(vals) / max(1, len(vals)))
        ################################################################################################################
        bv_idx = -1
        if self.ffi == -1:
            bv = ({(a // self.po.M) for a in self.pv} & self.po.bv_mask)
            heap = [(len(k ^ bv), random.randrange(100000), v, k) for k, v in self.po.bv_map.items()]
            heapq.heapify(heap)
            d, r, bv_idx, bv_vec = heapq.heappop(heap)
            # print(d)
            iv = {a for a in self.po.iv_map[bv_idx]}
            iv |= bv_vec
            ########################################################
            self.low_ad = False
            # if (round(self.em_delta_abs * 1000000.0) <= random.randrange(500000)):#---------------------------------------------HP
            if False:
                num = round(len(self.po.iv_mask) * 0.10)#----------------------------------------------------------------------HP
                if num > 0:
                    self.low_ad = True
                    rv = random.sample(list(self.po.iv_mask), num)
                    for a in rv:
                        if a in iv: iv.remove(a)
                        else: iv.add(a)
            ##########################################################
            heap = [(abs(k - self.em_delta_abs), random.randrange(100000), v) for k, v in self.po.em_map.items()]
            heapq.heapify(heap)
            iv |= heapq.heappop(heap)[2]
        else: iv = self.po.m[self.ffi].ov.copy()
        #################################################################################################################
        zr = 0
        cv = self.av.copy()
        self.av = set()
        for a in iv:
            ci = set(range((a * self.po.M), ((a + 1) * self.po.M)))
            ovl = (ci & self.pv)
            if len(ovl) == 0:
                self.ov.add(a)
                self.em += 1
                zr += 1
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
            ncv = cv.copy()
            if a in fbv_conf: ncv.add(fbv_conf[a])
            if wi in self.e:
                for b in ncv: self.e[wi][b] = random.randrange(self.po.adc_min, self.po.adc_max)
            else: self.e[wi] = {b:random.randrange(self.po.adc_min, self.po.adc_max) for b in ncv}
            self.av.add(wi)
        self.em /= max(1, (em_ct + len(iv)))
        zr /= max(1, len(iv))
        em_delta = (self.em - self.em_prev)
        self.em_delta_abs = abs(self.em - self.em_prev)
        ################################################################################################################
        tl = list(self.e)
        for a in tl:
            self.e[a] = {k:(v - 1) for k, v in self.e[a].items() if (v > 0)}
            if len(self.e[a]) < self.min_conns: del self.e[a]
        bv_string = f"  BV: {bv_idx:2d}" if bv_idx != -1 else ""
        lad_string = "  LAD" if self.low_ad else ""
        print(f"M: {(self.ffi + 1)}  EM: {self.em:.2f}  EMD: {round(em_delta * 1000000.0):8d}" +
        f"  ES: {len(self.e):6d}  PV: {len(self.pv):4d}  ZR: {zr:.2f}  MR: {mr:.2f}" + bv_string + lad_string)
oracle = Oracle()
oracle.update()
