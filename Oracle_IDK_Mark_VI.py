import random
class Oracle:
    def __init__(self):
        self.H = 3#-----------------------------------------------------------------------------------------HP
        self.M = 53#-53-------------------------------------------------------------------------------------HP
        self.K = 197#-97-------------------------------------------------------------------------------------HP
        self.Q = (self.H * self.M * self.K)
        self.min_conns = 3#-must be >= 1; musn't be too large!!!--------------------------------------------HP
        self.adc_max = 37#-if too large, fb seems impaired???-----------------------------------------------HP
        self.adc_min = round(self.adc_max * 0.80)
        #######################################################################################################
        tsp_dim_pct = 0.20#-0.20----------------------------------------------------------------------------HP
        tsp_dim = round(self.K * tsp_dim_pct)
        ts_dim = round(self.K / (tsp_dim + 2))
        self.iv_mask = {a for a in range(self.K)}
        # tv = self.iv_mask.copy()
        # self.iv_map = dict()
        # for a in range(ts_dim):
        #     ts = set(random.sample(list(tv), tsp_dim))
        #     tv -= ts
        #     self.iv_map[a] = frozenset(ts.copy())
        ########################################################################################################
        self.bv_mask = {(self.K + a) for a in range(self.K)}
        # tv = self.bv_mask.copy()
        # self.bv_map = dict()
        # for a in range(ts_dim):
        #     ts = set(random.sample(list(tv), tsp_dim))
        #     tv -= ts
        #     self.bv_map[frozenset(ts.copy())] = a
        ##########################################################################################################
        ts_dim = 25
        self.iv_map = {a:frozenset(set(random.sample(list(self.iv_mask), tsp_dim))) for a in range(ts_dim)}
        self.bv_map = {frozenset(set(random.sample(list(self.bv_mask), tsp_dim))):a for a in range(ts_dim)}
        ##########################################################################################################
        em_start_idx = (self.K * 2)
        # self.em_mask = {(em_start_idx + a) for a in range(self.K)}
        em_val_card = 13#-must be >= 2--------------------------------------------------------------------------HP
        em_num_vals = (self.K - em_val_card + 1)
        em_interval = (1.0 / (em_num_vals - 1))
        self.em_map = {(a * em_interval):frozenset({(em_start_idx + a + b) for b in range(em_val_card)}) for a in range(em_num_vals)}
        ##########################################################################################################
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
        max_val = (max(len(self.po.bv_map), len(self.po.em_map), self.po.Q) + 100)
        self.rsid = [a for a in range(max_val)]
    def update(self):
        # fbv_conf = {(a // self.po.M):-(a + 1) for a in self.po.m[self.fbi].pv}
        fbv_conf = {(a // self.po.M):-(a + 1) for a in self.po.m[self.fbi].pv} if self.fbi != 0 else dict()
        self.ov = set()
        ###########################################################################################################
        fb_inf_act = set()
        acts = dict()
        for a in self.e.keys():
            act = (len(self.e[a].keys() ^ self.av) / max(1, (len(self.e[a]) + len(self.av))))
            cli = (a // self.po.M)
            if ((cli in fbv_conf) and (fbv_conf[cli] in self.e[a])):
                act = max(0, (act - 0.20))#--------------------------------------------------------------------HP
            acts[a] = act
        le = len(acts)
        rs = random.sample(self.rsid, le)
        acts = {a[2]:a[0] for a in sorted([(v, rs.pop(), k) for k, v in acts.items()])}
        thresh = 0
        alpha = 3#-musn't be too large!!!----------------------------------------------------------------------HP
        if le > 0:
            mean = (sum(acts.values()) / le)
            sigma = (sum(((v - mean) ** 2) for v in acts.values()) / le)
            thresh = max(0, (mean - ((sigma ** 0.5) * alpha)))
        self.pv = set()
        vi = dict()
        for k, v in acts.items():
            # if v < thresh:#----------------------------------?????
            if v <= thresh:#---------------------------------?????
                cli = (k // self.po.M)
                if cli in vi:
                    if vi[cli][1] == -1:
                        vi[cli][1] = k
                        fb_inf_act.add(k)
                        if cli in fbv_conf: self.e[k][fbv_conf[cli]] = random.randrange(self.po.adc_min, self.po.adc_max)
                    else: vi[cli][2].add(k)
                    if cli not in self.ov:
                        self.ov.add(cli)
                else:
                    self.pv.add(k)
                    vi[cli] = [k, -1, set()]
        self.em_prev = self.em
        self.em = 0
        for v in vi.values():
            le = len(v[2])
            if le > 0:
                self.em += ((le - 1) / (self.po.M - 1))
                tv = (self.av & self.e[v[0]].keys() & self.e[v[1]].keys())
                for a in v[2]:
                    olv = (self.e[a].keys() & tv)
                    if len(olv) > 0: del self.e[a][random.choice(list(olv))]
        em_ct = len(vi)
        mr = (self.em / max(1, em_ct))
        ################################################################################################################
        bv_idx = -1
        if self.ffi == -1:
            bv = ({(a // self.po.M) for a in self.pv} & self.po.bv_mask)
            rs = random.sample(self.rsid, len(self.po.bv_map))
            bv_sorted = sorted([(len(k ^ bv), rs.pop(), k, v) for k, v in self.po.bv_map.items()])
            d, r, bv_ppcv, bv_idx = bv_sorted.pop(0)
            # print(d)
            iv = {a for a in self.po.iv_map[bv_idx]}
            iv |= bv_ppcv
            ########################################################
            # self.low_ad = False
            ##########################################################
            rs = random.sample(self.rsid, len(self.po.em_map))
            em_sorted = sorted([(abs(k - self.em_delta_abs), rs.pop(), v) for k, v in self.po.em_map.items()])
            iv |= em_sorted.pop(0)[2]
        else: iv = self.po.m[self.ffi].ov.copy()
        #################################################################################################################
        zr = 0
        avc = self.av.copy()
        self.av = set()
        pv_ack = set()
        for a in iv:
            ci = {((a * self.po.M) + b) for b in range(self.po.M)}
            ovl = (ci & self.pv)
            if len(ovl) == 0:
                self.em += 1
                zr += 1
                cav = (ci - self.e.keys())
                while not cav:
                    tl = list(ci & self.e.keys())
                    random.shuffle(tl)
                    for b in tl:
                        self.e[b] = {k:(v - 1) for k, v in self.e[b].items() if (v > 0)}
                        if len(self.e[b]) < self.po.min_conns:
                            del self.e[b]
                            cav = (ci - self.e.keys())
                            break
                wi = random.choice(list(cav))
                if a in fbv_conf:
                    fb_inf_act.add(wi)
                    if wi in self.e:
                        self.e[wi][fbv_conf[a]] = random.randrange(self.po.adc_min, self.po.adc_max)
                    else:
                        self.e[wi] = {fbv_conf[a]:random.randrange(self.po.adc_min, self.po.adc_max)}
                self.ov.add(a)
            else:
                pv_ack |= ovl
                wi = ovl.pop()
            if wi in self.e:
                for b in avc: self.e[wi][b] = random.randrange(self.po.adc_min, self.po.adc_max)
            else: self.e[wi] = {b:random.randrange(self.po.adc_min, self.po.adc_max) for b in avc}
            self.av.add(wi)
        self.em /= max(1, (em_ct + len(iv)))
        zr /= max(1, len(iv))
        self.em_delta_abs = abs(self.em - self.em_prev)
        pv_ex = (self.pv - pv_ack)
        for a in pv_ex:
            pass#----------------------should I use these to trigger feedback???
        ################################################################################################################
        tl = list(self.e)
        for a in tl:
            # pass
            # self.e[a] = {k:(v - 1) for k, v in self.e[a].items() if (v > 0)}#----------------------necessary?????
            if len(self.e[a]) < self.po.min_conns: del self.e[a]#----------------------------------necessary?????
        ################################################################################################################
        bv_string = f"  BVID: {bv_idx:2d}" if bv_idx != -1 else ""
        lad_string = "  LAD" if self.low_ad else ""
        print(f"M: {(self.ffi + 1)}  EM: {self.em:.2f}  EMDA: {self.em_delta_abs:.2f}" +
        f"  ES: {len(self.e):6d}  PV: {len(self.pv):4d}  ZR: {zr:.2f}  MR: {mr:.2f}  PVEX: {len(pv_ex):4d}" +
        f"  FBIN: {len(fb_inf_act):4d}" + bv_string + lad_string)
oracle = Oracle()
oracle.update()
