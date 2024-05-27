import random
import math
class Oracle:
    def __init__(self):
        self.H = 3#-----------------------------------------------------------------------------------------HP
        self.M = 53#-53-------------------------------------------------------------------------------------HP
        self.K = 167#-97------------------------------------------------------------------------------------HP
        self.adc_max = 37#-37-------------------------------------------------------------------------------HP
        self.adc_min = round(self.adc_max * 0.70)
        ##############################################################################################################
        self.tsp_dim_pct = 0.40#-0.30-----------------------------------------------------------------------HP
        self.tsp_dim = round(self.K * self.tsp_dim_pct)
        ts_dim = 3#-----------------------------------------------------------------------------------------HP
        self.iv_mask = {a for a in range(self.K)}
        self.iv_map = {a:frozenset(random.sample(list(self.iv_mask), self.tsp_dim)) for a in range(ts_dim)}
        self.bv_mask = {(self.K + a) for a in range(self.K)}
        self.bv_map_adc_max = 200#--------------------------------------------------------------------------HP
        self.bv_map_dim_max = (ts_dim - 1)
        self.bv_map = dict()
        ##############################################################################################################
        em_start_idx = (self.K * 2)
        self.em_mask = {(em_start_idx + a) for a in range(self.K)}
        em_val_card = 13#-must be >= 2-----------------------------------------------------------------------HP
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
        self.em = self.em_prev = self.em_delta_abs = self.forget_period_ct = 0
        self.forget_period = 10#-----------------------------------------------------------------------------HP
    def update(self):
        fbv_raw = self.po.m[self.fbi].pv.copy()
        # fbv_raw = self.po.m[self.fbi].pv.copy() if self.fbi != 0 else set()
        fbv = {-(a + 1) for a in fbv_raw}
        """
        # if ((self.fbi == 0) and (random.randrange(1000000) < 900000)):
        if self.fbi == 0:
            dim = round(self.po.tsp_dim_pct * len(self.po.matrix_cl_mask))
            rs = random.sample(list(self.po.matrix_cl_mask), dim)
            fbv = {-(random.choice(range((a * self.po.M), ((a + 1) * self.po.M))) + 1) for a in rs}
        """
        ##############################################################################################################
        cv = (self.pv | fbv)
        acts = {a:(len(self.e[a].keys() ^ cv) / max(1, (len(self.e[a]) + len(cv)))) for a in self.e.keys()}
        le = len(acts)
        self.ov = set()
        vi = dict()
        # alpha = 4#-musn't be too large!!!--------------------------------------------------------------------------HP
        if le > 0:
            # mean = (sum(acts.values()) / le)
            # sigma = (sum(((v - mean) ** 2) for v in acts.values()) / le)
            # thresh = max(0, (mean - ((sigma ** 0.5) * alpha)))
            # rs = random.sample(range(le), le)
            # aks = [a[2] for a in sorted([(v, rs.pop(), k) for k, v in acts.items() if (v <= thresh)])]#--------?????
            # aks = [a[2] for a in sorted([(v, rs.pop(), k) for k, v in acts.items() if (v < thresh)])]#---------?????
            aks = [a[2] for a in self.softmax(acts)]
            for a in aks:
                cli = (a // self.po.M)
                if cli in vi:
                    vi[cli][1].add(a)
                    #########################################
                    rel_v = {-(b + 1) for b in (set(range((cli * self.po.M), ((cli + 1) * self.po.M))) & fbv_raw)}
                    if a in self.e:
                        for b in rel_v: self.e[a][b] = random.randrange(self.po.adc_min, self.po.adc_max)
                    else: self.e[a] = {b:random.randrange(self.po.adc_min, self.po.adc_max) for b in rel_v}
                    if cli not in self.ov: self.ov.add(cli)
                    #########################################
                else: vi[cli] = [a, set()]
        self.pv = {v[0] for v in vi.values()}
        self.em_prev = self.em
        self.em = sum((len(v[1]) / (self.po.M - 1)) for v in vi.values())
        em_norm = len(vi)
        mr = (self.em / max(1, em_norm))
        ##############################################################################################################
        if self.ffi == -1:
            bv = {a for a in self.pv if ((a // self.po.M) in self.po.bv_mask)}
            # bv = self.pv.copy()
            rs = random.sample(range(len(self.po.bv_map)), len(self.po.bv_map))
            bv_sorted = sorted([((len(k ^ bv) / max(1, (len(k) + len(bv)))), rs.pop(), k, v[0]) for k, v in self.po.bv_map.items()])
            if len(bv_sorted) == 0: d = 1
            else: d, r, bv_found, bv_idx = bv_sorted.pop(0)
            if d > 0:#-------------------------------------------------------------------------------------------HP
                # print(self.po.cy)
                tl = list(self.po.iv_map.keys() - {v[0] for v in self.po.bv_map.values()})
                bv_idx = random.choice(tl)
            self.po.bv_map[frozenset(bv.copy())] = [bv_idx, self.po.bv_map_adc_max]
            # print(f"D: {d:.2f}")
            while len(self.po.bv_map) > self.po.bv_map_dim_max:
                rs = random.sample(list(self.po.bv_map.keys()), len(self.po.bv_map))
                for a in rs:
                    if (self.po.bv_map[a][1] > 0): self.po.bv_map[a][1] -= 1
                    else:
                        del self.po.bv_map[a]
                        break
            iv = {a for a in self.po.iv_map[bv_idx]}
            iv |= {(a // self.po.M) for a in bv if ((a // self.po.M) in self.po.bv_mask)}
            ##########################################
            rs = random.sample(range(len(self.po.em_map)), len(self.po.em_map))
            em_sorted = sorted([(abs(k - self.em_delta_abs), rs.pop(), v) for k, v in self.po.em_map.items()])
            iv |= em_sorted.pop(0)[2]
            ##########################################
        else: iv = self.po.m[self.ffi].ov.copy()
        ###########################################################################################################
        zr = 0
        pvc = self.pv.copy()
        # cv = (pvc | fbv)
        cv = self.pv.copy()
        self.pv = set()
        pv_ack = set()
        for a in iv:
            ci = set(range((a * self.po.M), ((a + 1) * self.po.M)))
            ovl = (ci & pvc)
            if len(ovl) == 0:
                self.em += 1
                zr += 1
                cav = (ci - self.e.keys())
                if not cav:
                    tl = list(ci & self.e.keys())
                    rs = random.sample(range(len(tl)), len(tl))
                    tls = sorted([(sum(self.e[b][c] for c in self.e[b].keys()), rs.pop(), b) for b in tl])
                    del self.e[tls[0][2]]
                    cav = (ci - self.e.keys())
                wi = random.choice(list(cav))
                #########################################
                rel_v = {-(b + 1) for b in (ci & fbv_raw)}
                if wi in self.e:
                    for b in rel_v: self.e[wi][b] = random.randrange(self.po.adc_min, self.po.adc_max)
                else: self.e[wi] = {b:random.randrange(self.po.adc_min, self.po.adc_max) for b in rel_v}
                self.ov.add(a)
                #########################################
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
        ###########################################
        for a in pv_ex:
            cli = (a // self.po.M)
            rel_v = {-(b + 1) for b in (set(range((cli * self.po.M), ((cli + 1) * self.po.M))) & fbv_raw)}
            if a in self.e:
                for b in rel_v: self.e[a][b] = random.randrange(self.po.adc_min, self.po.adc_max)
            else: self.e[a] = {b:random.randrange(self.po.adc_min, self.po.adc_max) for b in rel_v}
            self.ov.add(cli)
        ###########################################
        ##############################################################################################################
        self.forget_period_ct += 1
        if self.forget_period_ct == self.forget_period:
            tl = list(self.e.keys())
            for a in tl:
                if len(self.e[a]) > 100:#---------------------------------------------------------------------HP
                    self.e[a] = {k:(v - 1) for k, v in self.e[a].items() if (v > 0)}
                    if not self.e[a]: del self.e[a]
            self.forget_period_ct = 0
        ##############################################################################################################
        for a in self.e.keys():
            if len(self.e[a]) > 105:#--------------------------------------------------------------------------HP
                rs = random.sample(range(len(self.e[a])), len(self.e[a]))
                tls = sorted([(self.e[a][b], rs.pop(), b) for b in self.e[a].keys()])
                del self.e[a][tls[0][2]]
        ##############################################################################################################
        bv_string = f"  BVID: {bv_idx:2d}" if self.ffi == -1 else ""
        print(f"M: {(self.ffi + 1)}  EM: {self.em:.2f}  EMDA: {self.em_delta_abs:.2f}" +
        f"  ES: {len(self.e):6d}  PV: {len(self.pv):4d}  ZR: {zr:.2f}  MR: {mr:.2f}  PVEX: {len(pv_ex):4d}" +
        f"  BVL: {len(self.po.bv_map):2d}" + bv_string)
    def softmax(self, x):
        sum_v = sum(math.exp(v) for v in x.values())
        rs = random.sample(range(len(x)), len(x))
        return sorted([((math.exp(v) / sum_v), rs.pop(), k) for k, v in x.items()])
oracle = Oracle()
oracle.update()
