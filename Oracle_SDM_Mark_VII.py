import random
class Oracle:
    def __init__(self):
        self.H = 6#-----------------------------------------------------------------------------------------------------------HP
        self.mem_cap_max = 200#----------------------------------------------------------------------------------------------HP
        self.adc_max = 100#---------------------------------------------------------------------------------------------------HP
        self.cy = 0
        self.emg = 1000
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        # while True:
        while (self.emg > 0):
            self.emg = 0
            for a in self.m:
                a.update()
                self.emg += a.em
            self.emg /= len(self.m)
            self.cy += 1
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        trc_card = 5#-5--------------------------------------------------------------------------------------------------------HP
        trc_num_values = 9#-9--------------------------------------------------------------------------------------------------HP
        self.cv_dim = 0
        self.iv_trc = Transcoder(self.cv_dim, -1, 1, trc_num_values, 1, trc_card, False)
        self.iv_mask = self.iv_trc.vec_set.copy()
        self.cv_dim += len(self.iv_mask)
        self.bv_trc = Transcoder(self.cv_dim, -1, 1, trc_num_values, 1, trc_card, False)
        self.bv_mask = self.bv_trc.vec_set.copy()
        self.cv_dim += len(self.bv_mask)
        self.em_trc = Transcoder(self.cv_dim, 0, 1, trc_num_values, 1, trc_card, False)
        self.em_mask = self.em_trc.vec_set.copy()
        self.cv_dim += len(self.em_mask)
        self.blank_cv = ([0] * self.cv_dim)
        self.av_dim = (self.cv_dim * 2)
        self.blank_av = ([0] * self.av_dim)
        self.mem = dict()
        self.bv_idx_map = dict()
        self.ctv = self.iv = self.ev = self.pv = set()
        self.em = self.em_prev = self.em_delta_abs = 0
    def update(self):
        #############################################################################################################################
        # fbv = set()
        fbv = self.po.m[self.fbi].pv.copy()
        # fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        fbv = {(a + self.cv_dim) for a in fbv}
        ############################################################################################################################
        bv_idx = -1
        if (self.ffi == -1):
            bv = (self.bv_mask & self.pv)
            if frozenset(bv) not in self.bv_idx_map:
                bv_idx = len(self.bv_idx_map)
                self.bv_idx_map[frozenset(bv)] = bv_idx
            else: bv_idx = self.bv_idx_map[frozenset(bv)]
            # self.iv = (self.iv_trc.get_vector(self.bv_trc.get_value(bv)) | bv | self.em_trc.get_vector(self.em_delta_abs))
            self.iv = (self.iv_trc.get_vector(self.bv_trc.get_value(bv)) | bv)
        else: self.iv = self.po.m[self.ffi].ev.copy()
        #############################################################################################################################
        self.ev = (self.iv ^ self.pv)
        em_norm = max(1, (len(self.iv) + len(self.pv)))
        self.em_prev = self.em
        self.em = (len(self.ev) / em_norm)
        self.em_delta_abs = abs(self.em - self.em_prev)
        #############################################################################################################################
        tfs = frozenset(self.ctv)
        tcv = [1 if (a in self.iv) else -1 for a in range(self.cv_dim)]
        self.mem[tfs] = [[(x + y) for x, y in zip(self.mem[tfs][0], tcv)],
                         self.po.adc_max] if (tfs in self.mem) else [tcv.copy(), self.po.adc_max]
        #############################################################################################################################
        while (len(self.mem) > self.po.mem_cap_max):
            td = self.mem.copy()
            for k, v in td.items():
                if (v[1] > 0): self.mem[k] = [v[0], (v[1] - 1)]
                else:
                    del self.mem[k]
                    break
        #############################################################################################################################
        offset_prev_ctv = {(a + (self.cv_dim * 2)) for a in self.ctv}#-----------does this help/hurt????
        self.ctv = (self.iv | fbv | offset_prev_ctv)
        self.ctv = self.associate(self.ctv.copy())
        data = [((k ^ self.ctv), v[0]) for k, v in self.mem.items()]
        rs = random.sample(range(len(data)), len(data))
        data_sorted = sorted(data, key = lambda x: (x[0], rs.pop()))
        sasi = min(3, len(data_sorted))#-------------------------------------------------------------------------------------HP
        sum_v = self.blank_cv.copy()
        for a in range(sasi): sum_v = [(x + y) for x, y in zip(data_sorted[a][1], sum_v)]
        self.pv = {i for i, a in enumerate(sum_v) if (a > 0)}
        ############################################################################################################################
        if (self.ffi == -1): print(f"CY: {self.po.cy}")
        bv_str = f"  BVI: {bv_idx}" if (bv_idx != -1) else ""
        print(f"M{(self.ffi + 1)}  EM: {self.em:.2f}  MC: {len(self.mem)}" + bv_str)
    def associate(self, v_in):
        test_v = v_in.copy()
        delta_v = set()
        delta_v ^= test_v
        num_trials = 0
        num_trials_max = 50#------------------------------------------------------------------------------------HP
        thresh = 3#---------------------------------------------------------------------------------------------HP
        min_sasi = 10#------------------------------------------------------------------------------------------HP
        while ((len(delta_v) > thresh) and (num_trials < num_trials_max)):
            data = [((k ^ test_v), k) for k in self.mem.keys()]
            rs = random.sample(range(len(data)), len(data))
            data_sorted = sorted(data, key = lambda x: (x[0], rs.pop()))
            sasi = min(min_sasi, len(data_sorted))
            sum_av = self.blank_av.copy()
            for a in range(sasi): sum_av = [(b + 1) if (i in data_sorted[a][1]) else (b - 1) for i, b in enumerate(sum_av)]
            delta_v = test_v.copy()
            test_v = {i for i, a in enumerate(sum_av) if (a > 0)}
            delta_v ^= test_v
            num_trials += 1
        return test_v.copy()
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
        data = [((len(set(k) ^ vector_in) / max(1, (len(k) + len(vector_in)))),
                 (i / (len(self.sorted_vecs) - 1))) for i, k in enumerate(self.sorted_vecs)]
        rs = random.sample(range(len(data)), len(data))
        data_sorted = sorted(data, key = lambda x: (x[0], rs.pop()))
        split_val = ((data_sorted[0][1] + data_sorted[1][1]) / 2)
        return (self.min_val + (split_val * self.val_range))
    def get_vector(self, value_in):
        data = [(abs(v - value_in), (i / (len(self.sorted_vals) - 1))) for i, v in enumerate(self.sorted_vals)]
        rs = random.sample(range(len(data)), len(data))
        data_sorted = sorted(data, key = lambda x: (x[0], rs.pop()))
        split_val = ((data_sorted[0][1] + data_sorted[1][1]) / 2)
        tidx = self.avail_start_idcs[round(split_val * (len(self.avail_start_idcs) - 1))]#------use round()?????
        return {self.sorted_vec_set[((tidx + a) % len(self.sorted_vec_set))] for a in range(self.card_val)}
    def print_trcd(self):
        print(self.sorted_vec_set)
        print(self.avail_start_idcs)
        for i, a in enumerate(self.sorted_vecs): print(f"{a}:  {self.sorted_vals[i]:.4f}")
oracle = Oracle()
oracle.update()