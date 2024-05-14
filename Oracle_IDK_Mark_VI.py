import random
class Oracle:
    def __init__(self):
        self.H = 3#-----------------------------------------------------------------------------------------HP
        self.M = 53#----------------------------------------------------------------------------------------HP
        self.K = 97#----------------------------------------------------------------------------------------HP
        self.Q = (self.H * self.M * self.K)
        self.min_conns = 3#-must be >= 1; musn't be too large!!!--------------------------------------------HP
        self.adc_max = 737#----------------------------------------------------------------------------------HP
        self.adc_min = round(self.adc_max * 0.80)
        #######################################################################################################
        tsp_dim_pct = 0.20#-0.20--------------------------------------------------------------------------------HP
        tsp_dim = round(self.K * tsp_dim_pct)
        # ts_dim = round(self.K / (tsp_dim + 2))
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
        #########################################################################################################
        ts_dim = 25
        self.iv_map = {a:frozenset(set(random.sample(list(self.iv_mask), tsp_dim))) for a in range(ts_dim)}
        self.bv_map = {frozenset(set(random.sample(list(self.bv_mask), tsp_dim))):a for a in range(ts_dim)}
        ###########################################################################################################
        em_start_idx = (self.K * 2)
        self.em_mask = {(em_start_idx + a) for a in range(self.K)}
        em_val_card = 2#-must be >= 2--------------------------------------------------------------------------HP
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
        fb_inf_att = set()
        acts = dict()
        shl = random.sample(list(self.e.keys()), len(self.e))
        for a in shl:
            cli = (a // self.po.M)
            temp_cv = self.av.copy()
            flag = False
            if ((cli in fbv_conf) and (fbv_conf[cli] in self.e[a])):
                fb_inf_att.add(a)
                temp_cv.add(fbv_conf[cli])
                flag = True
            act = (len(self.e[a].keys() ^ temp_cv) / max(1, (len(self.e[a]) + len(temp_cv))))
            # if flag: act = max(0, (act - 0.10))#----------necessary????-------------------------------------------HP
            acts[a] = act
        le = len(acts)
        rs = random.sample(self.rsid, le)
        acts = {a[2]:a[0] for a in sorted([(v, rs.pop(), k) for k, v in acts.items()])}
        thresh = 0
        alpha = 2#-musn't be too large!!!------------------------------------------------------------------------HP
        if le > 0:
            mean = (sum(acts.values()) / le)
            sigma = (sum(((v - mean) ** 2) for v in acts.values()) / le)
            thresh = max(0, (mean - ((sigma ** 0.5) * alpha)))
        self.pv = set()
        vi = dict()
        for k, v in acts.items():
            # if v < thresh:#----------------------------------?????
            if v <= thresh:
                cli = (k // self.po.M)
                if cli in vi:
                    self.ov.add(cli)
                    vi[cli][1].add(k)
                else:
                    self.pv.add(k)
                    vi[cli] = [k, set()]
        self.em_prev = self.em
        self.em = 0
        for v in vi.values():
            le = len(v[1])
            if le > 0:
                self.em += ((le - 1) / (self.po.M - 1))
                olv = (self.e[v[0]].keys() & self.av)
                for a in v[1]:#------------------------------------------------------WORK ON THIS!!!!!!!!!!!!!!
                    tv = (self.e[a].keys() & olv)
                    if len(tv) > 0: del self.e[a][random.choice(list(tv))]
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
        fb_inf_act = set()
        for a in iv:
            ci = set(range((a * self.po.M), ((a + 1) * self.po.M)))
            ovl = (ci & self.pv)
            if len(ovl) == 0:
                self.ov.add(a)
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
            else:
                pv_ack |= ovl
                wi = ovl.pop()
            ncv = avc.copy()
            if a in fbv_conf:
                ncv.add(fbv_conf[a])
                if wi in fb_inf_att:
                    fb_inf_act.add(wi)
                    pv_ack.add(wi)
                self.ov.add(a)#---------------------------------------------------------------------------?????
            if wi in self.e:
                # for b in ncv: self.e[wi][b] = random.randrange(self.po.adc_min, self.po.adc_max)
                for b in ncv: self.e[wi][b] = self.po.adc_max
            # else: self.e[wi] = {b:random.randrange(self.po.adc_min, self.po.adc_max) for b in ncv}
            else: self.e[wi] = {b:self.po.adc_max for b in ncv}
            self.av.add(wi)
        self.em /= max(1, (em_ct + len(iv)))
        zr /= max(1, len(iv))
        self.em_delta_abs = abs(self.em - self.em_prev)
        pv_ex = (self.pv - pv_ack)
        ################################################################################################################
        tl = list(self.e)
        for a in tl:
            # pass
            self.e[a] = {k:(v - 1) for k, v in self.e[a].items() if (v > 0)}#------------------unnecessary?????
            if len(self.e[a]) < self.po.min_conns: del self.e[a]#------------------------------unnecessary?????
        ################################################################################################################
        bv_string = f"  BVID: {bv_idx:2d}" if bv_idx != -1 else ""
        lad_string = "  LAD" if self.low_ad else ""
        print(f"M: {(self.ffi + 1)}  EM: {self.em:.4f}  EMDA: {self.em_delta_abs:.4f}" +
        f"  ES: {len(self.e):6d}  PV: {len(self.pv):4d}  ZR: {zr:.2f}  MR: {mr:.2f}  PVEX: {len(pv_ex):4d}" +
        f"  FBIN: {len(fb_inf_act):4d}" + bv_string + lad_string)
oracle = Oracle()
oracle.update()
