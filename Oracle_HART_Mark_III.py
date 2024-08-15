import random
class Oracle:
    def __init__(self):
        self.H = 2#-----------------------------------------------------------------------------------------HP
        self.N = 128#---------------------------------------------------------------------------------------HP
        self.M = 49#----------------------------------------------------------------------------------------HP
        self.K = (self.N * self.M)
        self.total_m = set(range(self.K))
        self.adc_max = 20#----------------------------------------------------------------------------------HP
        self.n_pct = 0.10#----------------------------------------------------------------------------------HP
        self.n = round(self.N * self.n_pct)
        self.exiv_card = self.n
        self.exiv_mask = set(range(self.N))
        self.ts_dim = 2#------------------------------------------------------------------------------------HP
        self.ts_map = dict()
        while (len(self.ts_map) < self.ts_dim):
            self.ts_map[frozenset(random.sample(
                list(self.exiv_mask),
                self.exiv_card))] = [len(self.ts_map), set(random.sample(list(self.exiv_mask), self.exiv_card))]
        self.cy = 0
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while True:
            for a in self.m: a.update()
            self.cy += 1
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.e_cap = 100#----------------------------------------------------------------------------------HP
        self.e = dict()
        self.pv_dim = self.po.exiv_card
        self.iv = set()
        self.iv_prev = set()
        self.pv = set()
        self.pv_c = set()
        self.av = set()
        self.cv = set()
        self.ov = set()
        self.fbv = set()
        self.fbvm = set()
        self.exov = set()
        self.em = self.em_prev = self.em_delta = self.m_dim = self.num_gen_A = self.num_gen_B = 0
    def update(self):
        fbv_raw = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        # self.fbv = fbv_raw.copy()
        self.fbv = {-(a + 1) for a in fbv_raw}
        # self.fbvm = {(a // self.po.M):-(a + 1) for a in self.fbv}
        self.fbvm = {(a // self.po.M) for a in fbv_raw}
        self.process_inference()
        self.iv_prev = self.iv.copy()
        bv_idx = -1
        if (self.ffi == -1):
            d = [((len(self.pv_c ^ k) / max(1, (len(self.pv_c) + len(k)))), k, v)
                 for k, v in self.po.ts_map.items()]
            rs = random.sample(range(len(d)), len(d))
            ds = sorted(d, key = lambda x: (x[0], rs.pop()))
            bv_idx = ds[0][2][0]
            self.iv = ds[0][2][1].copy()
            # self.iv |= ds[0][1]#-no efference copy because copy IS the last self.cv!!!???
        else: self.iv = self.po.m[self.ffi].ov.copy()
        self.em = 0
        # self.iv = (self.iv ^ self.pv_c)
        zr = 0
        mr = 0
        pv_ack = set()
        self.av = set()
        for a in self.iv:
            ci = set(range((self.po.M * a), (self.po.M * (a + 1))))
            ovl = (ci & self.pv)
            if len(ovl) == 0:
                self.em += 1
                zr += 1
                cav = (ci - self.e.keys())
                if not cav:
                    d = [(self.e[b][1], b) for b in (ci & self.e.keys())]
                    rs = random.sample(range(len(d)), len(d))
                    ds = sorted(d, key = lambda x: (x[0], rs.pop()))
                    del self.e[ds[0][1]]
                    cav = (ci - self.e.keys())
                wi = random.choice(list(cav))
                self.ov.add(a)
            else:
                pv_ack |= ovl
                wi = ovl.pop()
                if len(ovl) > 1:
                    self.em += ((len(ovl) - 1) / (self.po.M - 1))
                    mr += 1
                    self.ov.add(a)
                else:
                    diff_v = (self.e[wi][0] ^ self.cv)
                    if len(diff_v) > 0:
                        ri = random.choice(list(diff_v))
                        self.e[wi][0].remove(ri) if (ri in self.e[wi][0]) else self.e[wi][0].add(ri)
                    # self.e[wi] = [self.cv.copy(), self.po.adc_max]
                    self.e[wi][1] = self.po.adc_max
            # if wi not in self.e: self.e[wi] = [self.cv.copy(), self.po.adc_max]
            # else: self.e[wi][1] = self.po.adc_max
            self.av.add(wi)
        for a in self.av:
            if a not in self.e: self.e[a] = [self.cv.copy(), self.po.adc_max]
            else: self.e[a][1] = self.po.adc_max
        self.em /= max(1, len(self.iv))
        pv_exc = (self.pv - pv_ack)
        if (len(self.e) > self.e_cap):
            self.e = {k:[v[0], max(0, (v[1] - 1))] for k, v in self.e.items()}
            # for k, v in self.e.items(): self.e[k] = [v[0], max(0, (v[1] - 1))]
            while (len(self.e) > self.e_cap):
                d = [(v[1], k) for k, v in self.e.items()]
                rs = random.sample(range(len(d)), len(d))
                ds = sorted(d, key = lambda x: (x[0], rs.pop()))
                del self.e[ds[0][1]]
        bv_str = "" if (bv_idx == -1) else f"  BV: {str(bv_idx).rjust(3)}"
        print(f"M:{(self.ffi + 1)}  EM: {str(f'{self.em:.2f}').rjust(4)}  MEM: {str(len(self.e)).rjust(3)}" +
              f"  NGA: {str(self.num_gen_A).rjust(3)}  NGB: {str(self.num_gen_B).rjust(3)}" +
              f"  PV: {str(len(self.pv)).rjust(4)}  EX: {str(len(pv_exc)).rjust(4)}" +
              f"  ZR: {str(zr).rjust(3)}  MR: {str(mr).rjust(3)}" + bv_str)
    def process_inference(self):
        #---------------------------NOTE: make sure to use either self.iv or self.iv_prev where appropriate!!!!
        # self.cv = (self.iv_prev | {(a + self.po.N) for a in self.av} | {(a + (self.po.N * 2)) for a in self.fbv})
        # self.cv = (self.iv_prev | {(a + self.po.N) for a in self.av} | {(a + self.po.N + self.po.K) for a in self.fbvm})
        self.cv = (self.iv_prev | {(a + self.po.N) for a in self.av})
        # self.cv = self.av.copy()
        acts = self.generate_activations_A(self.cv, 0.10, self.pv_dim)#------------------------------------HP
        self.pv = {a[0] for a in acts}
        self.pv_c = {(a // self.po.M) for a in self.pv}
    def generate_activations_A(self, v_in, alpha_in, sdim_in):
        out = []
        self.num_gen_A = self.num_gen_B = na = 0
        while ((len(out) < sdim_in) and (na < sdim_in)):
            elig_ks = (set(self.e.keys()) - {a[0] for a in out})
            p = {k:(len(v[0] ^ v_in) / max(1, (len(v[0]) + len(v_in)))) for k, v in self.e.items() if (k in elig_ks)}
            p_inh = {kA:(vA + sum((1 - vB) for kB, vB in p.items() if (kB != kA))) for kA, vA in p.items()}
            inh_val = 0
            beta = (alpha_in + 1)
            while ((len(out) < sdim_in) and (len(p_inh) > 0)):
                d = [(k, (v - inh_val)) for k, v in p_inh.items()]
                rs = random.sample(range(len(d)), len(d))
                ds = sorted(d, key = lambda x: (x[1], rs.pop()))
                beta = (ds[0][1] / len(p))
                if (beta <= alpha_in):
                    wk = ds[0][0]
                    diff_v = (v_in ^ self.e[wk][0])
                    if len(diff_v) > 0:#-----------------------------------------------------------------------HP
                        ri = random.choice(list(diff_v))
                        self.e[wk][0].remove(ri) if (ri in self.e[wk][0]) else self.e[wk][0].add(ri)
                        self.num_gen_A += 1
                    self.e[wk][1] = self.po.adc_max
                    out.append([wk, beta])
                    break
                del p_inh[ds[0][0]]
                inh_val += (1 - p[ds[0][0]])
            if ((len(out) < sdim_in) and (beta > alpha_in)):
                avail_idxs = (self.po.total_m - self.e.keys())
                ri = random.choice(list(avail_idxs))
                self.e[ri] = [v_in.copy(), self.po.adc_max]
                out.append([ri, 0])
            na += 1
        return out.copy()
    def generate_activations_B(self, v_in, alpha_in, sdim_in):
        out = []
        self.num_gen_A = self.num_gen_B = na = 0
        while ((len(out) < sdim_in) and (na < sdim_in)):
            elig_ks = (set(self.e.keys()) - {a[0] for a in out})
            p = {k:(len(v[0] ^ v_in) / max(1, (len(v[0]) + len(v_in)))) for k, v in self.e.items() if (k in elig_ks)}
            p_inh = {kA:(vA + sum((1 - vB) for kB, vB in p.items() if (kB != kA))) for kA, vA in p.items()}
            inh_val = 0
            beta = (alpha_in + 1)
            while ((len(out) < sdim_in) and (len(p_inh) > 0)):
                d = [(k, (v - inh_val)) for k, v in p_inh.items()]
                rs = random.sample(range(len(d)), len(d))
                ds = sorted(d, key = lambda x: (x[1], rs.pop()))
                beta = (ds[0][1] / len(p))
                if (beta <= alpha_in):
                    wk = ds[0][0]
                    diff_v = (v_in ^ self.e[wk][0])
                    if len(diff_v) > 0:#-----------------------------------------------------------------------HP
                        ri = random.choice(list(diff_v))
                        self.e[wk][0].remove(ri) if (ri in self.e[wk][0]) else self.e[wk][0].add(ri)
                        self.num_gen_A += 1
                    self.e[wk][1] = self.po.adc_max
                    out.append([wk, beta])
                    break
                del p_inh[ds[0][0]]
                inh_val += (1 - p[ds[0][0]])
            if ((len(out) < sdim_in) and (beta > alpha_in)):
                avail_idxs = (self.po.total_m - self.e.keys())
                ri = random.choice(list(avail_idxs))
                self.e[ri] = [v_in.copy(), self.po.adc_max]
                out.append([ri, 0])
            na += 1
        return out.copy()
oracle = Oracle()
oracle.update()