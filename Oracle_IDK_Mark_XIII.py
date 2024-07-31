import random
class Oracle:
    def __init__(self):
        self.H = 3#-----------------------------------------------------------------------------------------HP
        self.N = 512#-512-----------------------------------------------------------------------------------HP
        self.n_pct = 0.37#----------------------------------------------------------------------------------HP
        self.n = round(self.N * self.n_pct)
        self.exov_dim_pct = 0.25#---------------------------------------------------------------------------HP
        self.exov_dim = round(self.N * self.exov_dim_pct)
        self.exov_mask = {(self.N - 1 - i) for i in range(self.exov_dim)}
        self.exov_card = round(self.exov_dim * self.n_pct)
        self.exiv_mask = (set(range(self.N)) - self.exov_mask)
        self.exiv_dim = len(self.exiv_mask)
        self.exiv_card = (self.n - self.exov_card)
        self.ts_dim = 17#-----------------------------------------------------------------------------------HP
        self.ts_map = dict()
        while (len(self.ts_map) < self.ts_dim):
            self.ts_map[frozenset(random.sample(list(self.exov_mask),
                                                self.exov_card))] = set(random.sample(list(self.exiv_mask), self.exiv_card))
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while True:
            for a in self.m: a.update()
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.iv = self.cv = self.ev = self.pv = self.fbv = set()
        self.sel_v = []
        self.blank_dv = ([0] * self.po.N)
        self.dv_mag_max = 1000#-----------------------------------------------------------------------------HP
        self.dv_mag_min = -(self.dv_mag_max - 1)
        self.mem = dict()
        self.em = self.num_gen = self.max_dist_found = 0
    def update(self):
        ####################################################################################################
        # self.fbv = self.po.m[self.fbi].pv.copy()
        self.fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        self.process_inference()
        ####################################################################################################
        if (self.ffi == -1):
            exov = (self.pv & self.po.exov_mask)
            d = [(len(k ^ exov), k, v) for k, v in self.po.ts_map.items()]
            rs = random.sample(range(len(d)), len(d))
            ds = sorted(d, key = lambda x: (x[0], rs.pop()))
            self.iv = ds[0][2].copy()
            self.iv |= ds[0][1]
        else: self.iv = self.po.m[self.ffi].ev.copy()
        ####################################################################################################
        self.ev = (self.iv ^ self.pv)
        em_norm = max(1, (len(self.iv) + len(self.pv)))
        self.em = (len(self.ev) / em_norm)
        ####################################################################################################
        wd = 1#------------------------------------------------------------------------------------------HP
        for a in self.sel_v:
            # mult = a[1]#--------------------------------------------------------------------??????
            # mult = (1 - a[1])#--------------------------------------------------------------------??????
            mult = 1
            wd_mod = (wd * mult)
            for j, b in enumerate(self.mem[a[0]]):
                if (j in self.iv): self.mem[a[0]][j] = min(self.dv_mag_max, round(b + wd_mod))
                else: self.mem[a[0]][j] = max(self.dv_mag_min, round(b - wd_mod))
        ####################################################################################################
        # self.process_inference()
        print(f"M:{(self.ffi + 1)}  EM: {self.em:.2f}  MEM: {len(self.mem)}  NG: {self.num_gen}")
    def process_inference(self):
        fbv_mod = {-(a + 1) for a in self.fbv}
        # pv_offset = {(self.po.N + a) for a in self.pv}
        ev_offset = {(self.po.N + a) for a in self.ev}
        # self.cv = (self.iv | fbv_mod | pv_offset)
        self.cv = (self.iv | fbv_mod | ev_offset)
        # self.cv = (self.iv | {-(a + 1) for a in (self.ev ^ self.fbv)})#--------------------------------?????
        # self.cv = self.pv.copy()
        # self.cv = (self.pv | fbv_mod)
        self.sel_v = self.generate_sel_v(self.cv)
        sum_v = self.blank_dv.copy()
        for a in self.sel_v: sum_v = [(x + y) for x, y in zip(sum_v, self.mem[a[0]])]
        self.pv = {i for i, a in enumerate(sum_v) if (a > 0)}
    def generate_sel_v(self, av_in):
        vp = 0.17#------------------------------------------------------------------------------------HP
        out = []
        sample_dim = 49#-------------------------------------------------------------------------------HP
        num_attempts = 0
        num_attempts_max = 100#-----------------------------------------------------------------------HP
        self.num_gen = 0
        while ((len(out) < sample_dim) and (num_attempts < num_attempts_max)):
            exc_ks = set()
            elig_ks = (set(self.mem.keys()) - {a[0] for a in out})
            sel_prime = {k:(len(k ^ av_in) / max(1, (len(k) + len(av_in)))) for k in elig_ks}
            sel_prime_inh = {kA:(vA + sum((1 - vB) for kB, vB in sel_prime.items() if (kB != kA))) for kA, vA in sel_prime.items()}
            val = 0
            vp_met = False
            while ((len(exc_ks) < len(sel_prime)) and (len(out) < sample_dim)):
                d = [(k, (v - val)) for k, v in sel_prime_inh.items() if (k not in exc_ks)]
                ld = len(d)
                rs = random.sample(range(ld), ld)
                ds = sorted(d, key = lambda x: (x[1], rs.pop()))
                valA = (ds[0][1] / len(sel_prime))#-------------------------------------------------Is this correct?????
                # valA = (ds[0][1] / ld)#-------------------------------------------------------------Is this correct?????
                # print(f"{valA:.2f}")
                if (valA <= vp):
                    vp_met = True
                    wk = ds[0][0].copy()
                    diff_v = (av_in ^ ds[0][0])
                    if len(diff_v) > 0:
                        ri = random.choice(list(diff_v))
                        wkA = set(ds[0][0])
                        wkA.remove(ri) if (ri in wkA) else wkA.add(ri)
                        wk = frozenset(wkA)
                        self.mem[wk] = self.mem[ds[0][0]].copy()
                        self.num_gen += 1
                        del self.mem[ds[0][0]]
                    # out.append([wk.copy(), ds[0][1]])
                    out.append([wk.copy(), valA])
                    break
                exc_ks.add(ds[0][0])
                val += (1 - sel_prime[ds[0][0]])
            if not vp_met:
                wk = frozenset(av_in)
                if wk not in self.mem.keys():
                    self.mem[wk] = self.blank_dv.copy()
                    self.num_gen += 1
                out.append([wk.copy(), 1])#-------------------------------------------------------Is this correct?????
                # out.append([wk.copy(), 0])#-------------------------------------------------------Is this correct?????
            num_attempts += 1
        return out.copy()
oracle = Oracle()
oracle.update()