import random
import heapq
class Oracle:
    def __init__(self):
        self.H = 6#----------------------------------------------------------------------------------------------------------------HP
        self.s = Sensorium(self)
        self.m = [Matrix(self, a) for a in range(self.H)]
        self.s.mval = self.m[0].M
        self.em_global = 0
    def update(self):
        while True:
            self.s.update()
            self.em_global = 0
            for a in self.m:
                a.update()
                self.em_global += a.em
            self.em_global /= float(len(self.m))
class Sensorium:
    def __init__(self, po_in):
        self.po = po_in
        #______________________________________________________________EM INTEROCEPTION_______________________________________________
        em_int_card = 3#------------------------------------------------------------------------------------------------------------HP
        em_int_dim = 97#-should be odd!!!-------------------------------------------------------------------------------------------HP
        start_idx = -round((em_int_dim - 1) / 2)
        em_int_v = {(start_idx + a) for a in range(em_int_dim)}
        em_int_num_values = (em_int_dim - em_int_card + 1)
        em_val_interval = (1.0 / float(em_int_num_values - 1))
        self.em_aff_values = {frozenset({(start_idx + a + b) for b in range(em_int_card)}):
                                (float(a) * em_val_interval) for a in range(em_int_num_values)}
        self.unavail_idxs = em_int_v.copy()
        #______________________________________________________________RF AFFERENT___________________________________________________
        aff_ch_A_dim = 97#-should be odd!!!----------------------------------------------------------------------------------------HP
        start_idx = -round((aff_ch_A_dim - 1) / 2)
        self.aff_ch_A_v = {(start_idx + a) for a in range(aff_ch_A_dim)}
        while (len(self.aff_ch_A_v & self.unavail_idxs) > 0): self.aff_ch_A_v = {(a + 1) for a in self.aff_ch_A_v}
        self.unavail_idxs |= self.aff_ch_A_v
        #______________________________________________________________RF EFFERENT___________________________________________________
        eff_ch_A_dim = 97#-should be odd!!!----------------------------------------------------------------------------------------HP
        start_idx = -round((eff_ch_A_dim - 1) / 2)
        self.eff_ch_A_v = {(start_idx + a) for a in range(eff_ch_A_dim)}
        while (len(self.eff_ch_A_v & self.unavail_idxs) > 0): self.eff_ch_A_v = {(a - 1) for a in self.eff_ch_A_v}
        self.unavail_idxs |= self.eff_ch_A_v
        self.sv = set()
        ts_dim_pct = 0.50#---------------------------------------------------------------------------------------------------------HP
        ts_dim = round(float(aff_ch_A_dim) * ts_dim_pct)
        ts_len = 19#---------------------------------------------------------------------------------------------------------------HP
        self.ts = [set(random.sample(list(self.aff_ch_A_v), ts_dim)) for _ in range(ts_len)]
        self.ts_idx = self.mval = 0
        beh_mag = (len(self.ts) - 2)#----------------------------------------------------------------------------------------------HP
        beh_set = {(beh_mag - a) for a in range((beh_mag * 2) + 1)}
        self.beh_map = {frozenset({0}):random.choice(list(beh_set))}
        self.sv_card = (em_int_card + ts_dim)
    def update(self):
        em_val = self.po.m[0].em
        fbv = (self.po.m[0].mpv & self.eff_ch_A_v)
        fbv = {a for a in fbv if (len(fbv & set(range(((a // self.mval) * self.mval), (((a // self.mval) + 1) * self.mval)))) == 1)}
        heap = [(len(k ^ fbv), random.randrange(100), k.copy()) for k in self.beh_map.keys()]
        heapq.heapify(heap)
        idx_delta = self.beh_map[heapq.heappop(heap)[2]]
        self.ts_idx = ((self.ts_idx + len(self.ts) + idx_delta) % len(self.ts))
        # self.ts_idx = ((self.ts_idx + len(self.ts) + 1) % len(self.ts))
        self.sv = self.ts[self.ts_idx].copy()
        diffs = {k: abs(em_val - v) for k, v in self.em_aff_values.items()}
        min_val = min(diffs.values())
        cands = [k for k, v in diffs.items() if v == min_val]
        em_v = random.choice(cands).copy()
        # if frozenset(fbv) not in self.beh_map.keys(): self.beh_map[frozenset(fbv.copy())] = idx_delta
        self.sv |= em_v
        self.sv |= fbv
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = (mi_in + 1) if (mi_in < (self.po.H - 1)) else -1
        self.M = 49#---------------------------------------------------------------------------------------------------------HP
        self.ov = self.mav = self.mpv = self.fbv = self.excess_leaked_mpv = set()
        self.e = dict()
        self.adc_max = 1000#-300----------------------------------------------------------------------------------------------HP
        self.adc_min = round(float(self.adc_max - 1) * 0.95)#-0.95-----------------------------------------------------------HP
        self.em = self.em_prev = self.em_error = self.zero_rate = self.mto_rate = 0
        self.em_sp = 0.10#---------------------------------------------------------------------------------------------------HP
    def update(self):
            iv = self.po.s.sv.copy() if self.ffi == -1 else self.po.m[self.ffi].ov.copy()
            self.em = self.zero_rate = self.mto_rate = 0
            self.ov = set()
            mav_update = set()
            mpv_ack = set()
            new_adc = random.randint(self.adc_min, self.adc_max)
            ci_dict = {a:set(range((a * self.M), ((a + 1) * self.M))) for a in iv}
            e_keys = set(self.e.keys())
            for a, ci in ci_dict.items():
                pv = (ci & self.mpv)
                mpv_ack |= pv
                pv_len = len(pv)
                if pv_len == 0:
                    self.ov.add(a)
                    self.em += 1.0
                    self.zero_rate += 1.0
                    ci_mod = ci - e_keys
                    while not ci_mod:
                        common_keys = e_keys & ci
                        for b in common_keys.copy():
                            if b in self.e:
                                for k, v in list(self.e[b].items()):
                                    if v > 0: self.e[b][k] -= 1
                                    else:
                                        del self.e[b][k]
                                        if not self.e[b]:
                                            del self.e[b]
                                            e_keys.discard(b)
                                            ci_mod = ci - e_keys
                                            if ci_mod: break
                    wi = random.choice(list(ci_mod))
                else:
                    wi = random.choice(list(pv))
                    if pv_len > 1:
                        self.ov.add(a)
                        self.em += (float(pv_len - 1) / float(self.M - 1))
                        self.mto_rate += 1.0
                if wi in e_keys:
                    for b in self.mav: self.e[wi][b] = new_adc
                else: self.e[wi] = {b:new_adc for b in self.mav}
                mav_update.add(wi)
            norm = float(max(1, len(ci_dict)))
            self.em /= norm
            self.zero_rate /= norm
            self.mto_rate /= norm
            ##########################################################################################
            self.excess_leaked_mpv = (self.mpv - self.fbv - mpv_ack)
            # for a in self.excess_leaked_mpv: self.ov.add(a // self.M)#-is this a good idea???
            # self.em_error = (self.em - self.em_prev)
            # self.em_prev = self.em
            ##########################################################################################
            """
            if self.ffi == -1:
                em_sp_abs_error = float(abs(self.em - self.em_sp))
                sc = 2000.0#----------------------------------------------------------------------------------------------HP
                # sc_val = round(em_sp_abs_error * sc)
                sc_val = (em_sp_abs_error * sc)
                ts = (self.mpv & self.po.s.eff_ch_A_v)
                print(len(self.mpv))
                for a in ts:
                    for b in (self.mav & set(self.e[a].keys())): self.e[a][b] = max(0, round(float(self.e[a][b]) / sc_val))
            """
            ##########################################################################################
            new_dict = {}
            for a, inner_dict in self.e.items():
                temp = {k:(v - 1) for k, v in inner_dict.items() if (v > 0)}
                if temp: new_dict[a] = temp
            self.e = new_dict
            ##########################################################################################
            self.mav = mav_update.copy()
            self.fbv = self.po.m[self.fbi].mpv.copy() if (self.fbi != -1) else set()
            # self.fbv = self.po.m[self.fbi].mpv.copy() if (self.fbi != -1) else self.po.m[0].mpv.copy()
            self.mav |= {a for a in self.fbv if (len(self.fbv & set(range(((a // self.M) * self.M), (((a // self.M) + 1) * self.M)))) == 1)}
            self.mpv = set()
            heap = [(len(set(self.e[a].keys()) ^ self.mav), random.randrange(100), a) for a in self.e.keys()]
            heapq.heapify(heap)
            while heap:
                k = heapq.heappop(heap)[2]
                if k not in self.mpv: self.mpv.add(k)
            ##########################################################################################
            # print(f"M{self.ffi + 1}  EM: {(self.em * 100.0):.2f}%\tIDX: {self.po.s.ts_idx}\tZR: {self.zero_rate:.2f}" +
            #       f"\tMR: {self.mto_rate:.2f}\tEX: {len(self.excess_leaked_mpv)}\tINC: {len(iv)}")
oracle = Oracle()
oracle.update()