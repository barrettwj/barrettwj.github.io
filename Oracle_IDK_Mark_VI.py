import random
class Oracle:
    def __init__(self):
        self.H = 10#-----------------------------------------------------------------------------------------HP
        self.M = 23#-53-------------------------------------------------------------------------------------HP
        self.K = 137#-97-------------------------------------------------------------------------------------HP
        self.adc_max = 37#-if too large, fb seems impaired???----------------------------------------------HP
        self.adc_min = round(self.adc_max * 0.90)
        ##############################################################################################################
        self.tsp_dim_pct = 0.50#-0.30----------------------------------------------------------------------------HP
        self.tsp_dim = round(self.K * self.tsp_dim_pct)
        ts_dim = 10#---------------------------------------------------------------------------------------------HP
        self.iv_mask = {a for a in range(self.K)}
        self.iv_map = {a:frozenset(random.sample(list(self.iv_mask), self.tsp_dim)) for a in range(ts_dim)}
        self.bv_mask = {(self.K + a) for a in range(self.K)}
        self.bv_map = {frozenset(random.sample(list(self.bv_mask), self.tsp_dim)):a for a in range(ts_dim)}
        ##############################################################################################################
        em_start_idx = (self.K * 2)
        self.em_mask = {(em_start_idx + a) for a in range(self.K)}
        em_val_card = 27#-must be >= 2----------------------------------------------------------------------HP
        em_num_vals = (self.K - em_val_card + 1)
        em_interval = (1.0 / (em_num_vals - 1))
        self.em_map = {(a * em_interval):frozenset((em_start_idx + a + b)
                                                   for b in range(em_val_card)) for a in range(em_num_vals)}
        ###############################################################################################################
        self.matrix_cl_mask = (self.iv_mask | self.bv_mask | self.em_mask)
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
        self.ov = self.pv = set()
        self.e = dict()
        self.em = self.em_prev = self.em_delta_abs = 0
    def update(self):
        fbv = {-(a + 1) for a in self.po.m[self.fbi].pv}
        # fbv = {-(a + 1) for a in self.po.m[self.fbi].pv} if self.fbi != 0 else dict()
        """
        # if ((self.fbi == 0) and (random.randrange(1000000) < 900000)):
        if self.fbi == 0:
            dim = round(self.po.tsp_dim_pct * len(self.po.matrix_cl_mask))
            rs = random.sample(list(self.po.matrix_cl_mask), dim)
            fbvl = [random.choice([((a * self.po.M) + b) for b in range(self.po.M)]) for a in rs]
            fbv = {-(a + 1) for a in fbvl}
        """
        ##############################################################################################################
        cv = (self.pv | fbv)
        acts = {a:(len(self.e[a].keys() ^ cv) / max(1, (len(self.e[a]) + len(cv)))) for a in self.e.keys()}
        le = len(acts)
        self.ov = set()
        vi = dict()
        alpha = 2#-musn't be too large!!!-------------------------------------------------------------------HP
        if le > 0:
            mean = (sum(acts.values()) / le)
            sigma = (sum(((v - mean) ** 2) for v in acts.values()) / le)
            thresh = max(0, (mean - ((sigma ** 0.5) * alpha)))
            rs = random.sample(range(le), le)
            # aks = [a[2] for a in sorted([(v, rs.pop(), k) for k, v in acts.items() if (v <= thresh)])]
            aks = [a[2] for a in sorted([(v, rs.pop(), k) for k, v in acts.items() if (v < thresh)])]#---------?????
            for a in aks:
                cli = (a // self.po.M)
                if cli in vi:
                    vi[cli][1].add(a)
                    if cli not in self.ov: self.ov.add(cli)
                else: vi[cli] = [a, set()]
        self.pv = {v[0] for v in vi.values()}
        self.em_prev = self.em
        self.em = sum((len(v[1]) / (self.po.M - 1)) for v in vi.values())
        em_norm = len(vi)
        mr = (self.em / max(1, em_norm))
        ##############################################################################################################
        if self.ffi == -1:
            bv = {(a // self.po.M) for a in self.pv if ((a // self.po.M) in self.po.bv_mask)}
            rs = random.sample(range(len(self.po.bv_map)), len(self.po.bv_map))
            bv_sorted = sorted([((len(k ^ bv) / max(1, (len(k) + len(bv)))), rs.pop(), k, v) for k, v in self.po.bv_map.items()])
            d, r, bv_ppcv, bv_idx = bv_sorted.pop(0)
            # print(f"D: {d:.2f}")
            iv = {a for a in self.po.iv_map[bv_idx]}
            iv |= bv_ppcv
            ##########################################
            rs = random.sample(range(len(self.po.em_map)), len(self.po.em_map))
            em_sorted = sorted([(abs(k - self.em_delta_abs), rs.pop(), v) for k, v in self.po.em_map.items()])
            iv |= em_sorted.pop(0)[2]
        else: iv = self.po.m[self.ffi].ov.copy()
        ##############################################################################################################
        zr = 0
        pvc = self.pv.copy()
        cv = (pvc | fbv)
        self.pv = set()
        pv_ack = set()
        for a in iv:
            ci = {((a * self.po.M) + b) for b in range(self.po.M)}
            ovl = (ci & pvc)
            if len(ovl) == 0:
                self.em += 1
                zr += 1
                cav = (ci - self.e.keys())
                while not cav:
                    tl = list(ci & self.e.keys())
                    random.shuffle(tl)
                    for b in tl:
                        self.e[b] = {k:(v - 1) for k, v in self.e[b].items() if (v > 0)}
                        if not self.e[b]:
                            del self.e[b]
                            cav = (ci - self.e.keys())
                            break
                wi = random.choice(list(cav))
                self.ov.add(a)
            else:
                pv_ack |= ovl
                wi = ovl.pop()
            if wi in self.e:
                for b in cv: self.e[wi][b] = random.randrange(self.po.adc_min, self.po.adc_max)
            else: self.e[wi] = {b:random.randrange(self.po.adc_min, self.po.adc_max) for b in cv}
            self.pv.add(wi)
        self.em /= max(1, (em_norm + len(iv)))
        zr /= max(1, len(iv))
        self.em_delta_abs = abs(self.em - self.em_prev)
        pv_ex = (pvc - pv_ack)
        ##############################################################################################################
        tl = list(self.e)
        for a in tl:
            self.e[a] = {k:(v - 1) for k, v in self.e[a].items() if (v > 0)}#-----------------------necessary?????
            if not self.e[a]: del self.e[a]#--------------------------------------------------------necessary?????
        ##############################################################################################################
        bv_string = f"  BVID: {bv_idx:2d}" if self.ffi == -1 else ""
        print(f"M: {(self.ffi + 1)}  EM: {self.em:.2f}  EMDA: {self.em_delta_abs:.2f}" +
        f"  ES: {len(self.e):6d}  PV: {len(self.pv):4d}  ZR: {zr:.2f}  MR: {mr:.2f}  PVEX: {len(pv_ex):4d}" + bv_string)
oracle = Oracle()
oracle.update()
