import random
class Oracle:
    def __init__(self):
        self.H = 6#----------------------------------------------------------------------------------------HP
        self.m_dim_out = 4096#-----------------------------------------------------------------------------HP
        self.card_pct = 0.37#------------------------------------------------------------------------------HP
        self.m_range = set(range(self.m_dim_out))
        self.exov_dim = round(self.m_dim_out / 2)
        self.exov_mask = {(self.m_dim_out - 1 - a) for a in range(self.exov_dim)}
        self.exov_card = round(len(self.exov_mask) * self.card_pct)
        self.exov = set(random.sample(list(self.exov_mask), self.exov_card))
        self.exiv_mask = (self.m_range - self.exov_mask)
        self.exiv_card = round(len(self.exiv_mask) * self.card_pct)
        self.exiv = set(random.sample(list(self.exiv_mask), self.exiv_card))
        self.bv_map_cap_max = 100#-------------------------------------------------------------------------HP
        self.bv_map = {frozenset(self.exov):self.exiv.copy()}
        self.bv_indices = {frozenset(self.exov):0}
        self.bv_idx = -1
        self.exiv |= self.exov
        self.m = [Matrix(self, a, self.m_dim_out) for a in range(self.H)]
        self.cy = self.emg = 0 
    def update(self):
        while True:
            self.emg = 0
            for a in self.m:
                a.update()
                self.emg += a.em
            self.emg /= self.H
            self.exov = (self.m[0].pv & self.exov_mask)
            tfs = frozenset(self.exov)
            d = [(len(tfs ^ k), v, self.bv_indices[k]) for k, v in self.bv_map.items()]
            rs = random.sample(range(len(d)), len(d))
            ds = sorted(d, key = lambda x: (x[0], rs.pop()))
            self.bv_idx = -1
            thresh = 0#-----------------------------------------------------------------------------------HP
            if (ds[0][0] > thresh):
                ts = ds[0][1].copy()
                tsA = (self.exiv_mask - ts)
                rs = set(random.sample(list(ts), ds[0][0]))
                ts -= rs
                rs = set(random.sample(list(tsA), ds[0][0]))
                ts |= rs
                # ts = set(random.sample(list(self.exiv_mask), self.exiv_card))#-novel random experience invoked by novel behavior
                ts |= self.exov
                self.bv_map[tfs] = ts.copy()
                self.bv_idx = len(self.bv_indices)
                self.bv_indices[tfs] = self.bv_idx
            else:
                self.exiv = (ds[0][1] | self.exov)
                self.bv_idx = ds[0][2]
            if len(self.bv_map) > self.bv_map_cap_max:
                pass
            # print(f"EM: {self.emg:.4f}")
            self.cy += 1
class Matrix:
    def __init__(self, po_in, mi_in, m_dim_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.m_dim = m_dim_in
        # self.mem_A_rho_initial = (1 / (mi_in + 2))#--------------------------------------------------------HP
        # self.mem_A_rho_initial = ((mi_in + 1) / (self.po.H * 1.005))#--------------------------------------HP
        self.mem_A_rho_initial = 0.95#-----------------------------------------------------------------------HP
        self.mem_B_rho_initial = self.mem_A_rho_initial#-----------------------------------------------------HP
        self.mem_B_dim = m_dim_in
        self.context_dim = 3#--------------------------------------------------------------------------------HP
        self.mf_mag_max = 1000#------------------------------------------------------------------------------HP
        self.mem_A_dim = (m_dim_in * self.context_dim)
        self.mem_A = Memory(self.mem_A_dim, self.mem_A_rho_initial)
        self.mem_B = Memory(self.mem_B_dim, self.mem_B_rho_initial)
        self.M = dict()#-mapping matrix
        self.iv = self.ev = self.cv = self.pv = set()
        self.em = 0
    def update(self):
        # fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        fbv = self.po.m[self.fbi].pv.copy()
        # fbv = {(self.exiv_dim + a) for a in fbv}
        if self.ffi == -1: self.iv = self.po.exiv.copy()
        else: self.iv = self.po.m[self.ffi].ev.copy()
        self.ev = (self.iv ^ self.pv)
        em_norm = max(1, (len(self.iv) + len(self.pv)))
        self.em = (len(self.ev) / em_norm)
        if self.em > 0.10: self.learn(self.cv, self.iv)
        # self.learn(self.cv, self.iv)
        self.cv = self.iv.copy()
        if self.context_dim > 1: self.cv |= {(self.m_dim + a) for a in fbv}
        if self.context_dim > 2: self.cv |= {((self.m_dim * 2) + a) for a in self.pv}
        self.pv = self.predict(self.cv)
        bv_str = f"  BV: {self.po.bv_idx}" if (self.ffi == -1) else ""
        print(f"M:{(self.ffi + 1)}  EM: {self.em:.2f}  MA: {len(self.mem_A.C)}  MB: {len(self.mem_B.C)}" + bv_str)
    def learn(self, X, Y):
        J = self.mem_A.learn(X)
        K = self.mem_B.learn(Y)
        if J not in self.M: self.M[J] = {K:1}
        else:
            if K not in self.M[J]: self.M[J][K] = 1
            else:
                self.M[J][K] += 1
                if self.M[J][K] > self.mf_mag_max:
                    for k, v in self.M[J].items(): self.M[J][k] = max(0, (v - 1))
    def predict(self, X):
        J = self.mem_A.test(X)
        K = 0
        if J not in self.M: self.M[J] = {0:1}
        else:
            d = [(self.M[J][k], k) for k in self.M[J].keys()]
            rs = random.sample(range(len(d)), len(d))
            ds = sorted(d, key = lambda x: (x[0], rs.pop()), reverse = True)
            K = ds[0][1]
        return {i for i, a in enumerate(self.mem_B.C[K][0]) if (a > 0)}
class Memory:
    def __init__(self, n_in, rho_in):
        self.rho = rho_in
        self.n = n_in
        self.cv_mag_max = 1000000#------------------------------------------------------------------------------HP
        self.cv_mag_min = -(self.cv_mag_max - 1)
        self.C_dim_min = 2#-------------------------------------------------------------------------------------HP
        self.C_dim_max = 20#------------------------------------------------------------------------------------HP
        self.C_adc_max = 1000#----------------------------------------------------------------------------------HP
        self.match_mode = 1#-0:AND, 1:XOR-----------------------------------------------------------------------HP
        self.C = {a:[([0] * n_in), self.C_adc_max] for a in range(self.C_dim_min)}
    def learn(self, vec):
        J = self.test(vec)
        self.C[J][1] = self.C_adc_max
        for k, v in self.C.items():
            if (k != J): self.C[k][1] = max(0, (v[1] - 1))
        delta = 1#---------------------------------------------------------------------------------------------HP
        for i, a in enumerate(self.C[J][0]):
            if i in vec: self.C[J][0][i] = min((a + delta), self.cv_mag_max)
            else: self.C[J][0][i] = max((a - delta), self.cv_mag_min)
        return J
    def test(self, vec):
        J = random.choice(list(self.C.keys()))
        cands = self.C.copy()
        thresh = self.C_dim_min#-maybe set higher???--------------------------------------------------------------HP
        while (len(cands) > thresh):
            ac = dict()
            for k, v in cands.items():
                ts = {i for i, a in enumerate(v[0]) if (a > 0)}
                if self.match_mode == 0:
                    norm = max(1, min(len(ts), len(vec)))
                    ac[k] = (len(ts & vec) / norm)
                if self.match_mode == 1:
                    norm = max(1, (len(ts) + len(vec)))
                    ac[k] = (1 - (len(ts ^ vec) / norm))
            ac_inh = [((vA - sum(vB for kB, vB in ac.items() if (kB != kA))), kA) for kA, vA in ac.items()]
            rs = random.sample(range(len(ac_inh)), len(ac_inh))
            ac_inh_sorted = sorted(ac_inh, key = lambda x: (x[0], rs.pop()), reverse = True)
            J = ac_inh_sorted[0][1]
            if (ac[J] < self.rho): del cands[J]
            else: break
        if (len(cands) == thresh):
            if (len(self.C) == self.C_dim_max):
                d = [(v[1], k) for k, v in self.C.items()]
                rs = random.sample(range(len(d)), len(d))
                ds = sorted(d, key = lambda x: (x[0], rs.pop()))
                J = ds[0][1]
            else: J = len(self.C)
            self.C[J] = [[1 if (i in vec) else -1 for i in range(self.n)], self.C_adc_max]
        return J
class Transcoder:
    def __init__(self, start_idx_in, min_val_in, max_val_in, num_values_in, enc_step_in, enc_card_in, cyclic_in = False):
        self.vec_set = set()
        self.sorted_vecs = []
        self.sorted_vals = []
        inc = (abs(max_val_in - min_val_in) / (num_values_in - 1))
        if enc_step_in > enc_card_in: enc_step_in = enc_card_in
        if (cyclic_in and (enc_card_in % 2 != 0)): enc_card_in += 1
        limit_idx = (num_values_in * enc_step_in)
        self.card_val = enc_card_in
        for a in range(num_values_in):
            if cyclic_in: ts = [(start_idx_in + ((b + (a * enc_step_in)) % limit_idx)) for b in range(enc_card_in)]
            else: ts = [(start_idx_in + (b + (a * enc_step_in))) for b in range(enc_card_in)]
            self.vec_set |= set(ts)
            self.sorted_vecs.append(ts.copy())
            val = (min_val_in + (a * inc))
            self.sorted_vals.append(val)
        self.sorted_vec_set = sorted(list(self.vec_set))
        self.min_val = min_val_in
        self.max_val = max_val_in
        self.val_range = abs(self.max_val - self.min_val)
        tc = enc_step_in if cyclic_in else enc_card_in
        self.avail_start_idcs = [a for a in range(len(self.sorted_vec_set) + 1 - tc)]
    def get_value(self, vector_in):
        d = [((len(set(k) ^ vector_in) / max(1, (len(k) + len(vector_in)))),
                 (i / (len(self.sorted_vecs) - 1))) for i, k in enumerate(self.sorted_vecs)]
        rs = random.sample(range(len(d)), len(d))
        ds = sorted(d, key = lambda x: (x[0], rs.pop()))
        split_val = ((ds[0][1] + ds[1][1]) / 2)
        return (self.min_val + (split_val * self.val_range))
    def get_vector(self, value_in):
        d = [(abs(v - value_in), (i / (len(self.sorted_vals) - 1))) for i, v in enumerate(self.sorted_vals)]
        rs = random.sample(range(len(d)), len(d))
        ds = sorted(d, key = lambda x: (x[0], rs.pop()))
        split_val = ((ds[0][1] + ds[1][1]) / 2)
        tidx = self.avail_start_idcs[round(split_val * (len(self.avail_start_idcs) - 1))]#------use round()?????
        return {self.sorted_vec_set[((tidx + a) % len(self.sorted_vec_set))] for a in range(self.card_val)}
    # def print_trcd(self):
    #     print(self.sorted_vec_set)
    #     print(self.avail_start_idcs)
    #     for i, a in enumerate(self.sorted_vecs): print(f"{a}:  {self.sorted_vals[i]:.4f}")
oracle = Oracle()
oracle.update()

