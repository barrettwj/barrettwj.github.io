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
            print(f"EM: {(self.em_global * 100.0):.2f}%\tIDX: {self.s.ts_idx}\tZR: {self.m[0].zero_rate}" +
                  f"\tMR: {self.m[0].mto_rate}\tEX: {len(self.m[0].excess_leaked_mpv)}")
class Sensorium:
    def __init__(self, po_in):
        self.po = po_in
        #______________________________________________________________EM INTEROCEPTION_______________________________________________
        self.em_int_card = 3#-------------------------------------------------------------------------------------------------------HP
        self.em_int_dim = 37#-should be odd!!!--------------------------------------------------------------------------------------HP
        start_idx = -round((self.em_int_dim - 1) / 2)
        self.em_int_v = {(start_idx + a) for a in range(self.em_int_dim)}
        self.em_int_num_values = (self.em_int_dim - self.em_int_card + 1)
        em_val_interval = (1.0 / float(self.em_int_num_values - 1))
        self.em_aff_values = {frozenset({(start_idx + a + b) for b in range(self.em_int_card)}):
                                (float(a) * em_val_interval) for a in range(self.em_int_num_values)}
        self.unavail_idxs = self.em_int_v.copy()
        #______________________________________________________________RF AFFERENT___________________________________________________
        self.aff_ch_A_dim = 37#-should be odd!!!-----------------------------------------------------------------------------------HP
        start_idx = -round((self.aff_ch_A_dim - 1) / 2)
        self.aff_ch_A_v = {(start_idx + a) for a in range(self.aff_ch_A_dim)}
        while (len(self.aff_ch_A_v & self.unavail_idxs) > 0): self.aff_ch_A_v = {(a + 1) for a in self.aff_ch_A_v}
        self.unavail_idxs |= self.aff_ch_A_v
        #______________________________________________________________RF EFFERENT___________________________________________________
        self.eff_ch_A_dim = 37#-should be odd!!!-----------------------------------------------------------------------------------HP
        start_idx = -round((self.eff_ch_A_dim - 1) / 2)
        self.eff_ch_A_v = {(start_idx + a) for a in range(self.eff_ch_A_dim)}
        # while (len(self.eff_ch_A_v & self.unavail_idxs) > 0): self.eff_ch_A_v = {(a - 1) for a in self.eff_ch_A_v}
        while (len(self.eff_ch_A_v & self.unavail_idxs) > 0): self.eff_ch_A_v = {(a + 1) for a in self.eff_ch_A_v}
        self.unavail_idxs |= self.eff_ch_A_v
        self.sv = self.fbv = set()
        ts_dim = (self.aff_ch_A_dim - 20)#-----------------------------------------------------------------------------------------HP
        ts_len = 9#----------------------------------------------------------------------------------------------------------------HP
        self.ts = [set(random.sample(list(self.aff_ch_A_v), ts_dim)) for _ in range(ts_len)]
        self.ts_idx = self.mval = 0
        self.beh_mag = (ts_len - 1 - 3)#---------------------------------------------------------------------------------------------HP
        self.beh_set = {(self.beh_mag - a) for a in range((self.beh_mag * 2) + 1)}
        self.beh_map = {frozenset({0}):random.choice(list(self.beh_set))}
    def update(self):
        em_val = self.po.m[0].em
        self.fbv = (self.po.m[0].mpv & self.eff_ch_A_v)
        conf_v = set()
        for a in self.fbv:
            b = (a // self.mval)
            if (len(self.fbv & set(range((b * self.mval), ((b + 1) * self.mval)))) == 1): conf_v.add(a)
        self.fbv = conf_v.copy()
        heap = [(len(k ^ self.fbv), random.randrange(100), k.copy()) for k in self.beh_map.keys()]
        heapq.heapify(heap)
        idx_delta = self.beh_map[heapq.heappop(heap)[2]]
        # self.ts_idx = ((self.ts_idx + len(self.ts) + idx_delta) % len(self.ts))
        self.ts_idx = ((self.ts_idx + len(self.ts) + 1) % len(self.ts))
        self.sv = self.ts[self.ts_idx].copy()
        min_val = min(abs(em_val - v) for v in self.em_aff_values.values())
        cands = [k for k, v in self.em_aff_values.items() if abs(em_val - v) == min_val]
        em_v = random.choice(cands).copy()
        if frozenset(self.fbv) not in self.beh_map.keys(): self.beh_map[frozenset(self.fbv.copy())] = idx_delta
        # self.sv |= em_v
        self.sv |= self.fbv
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = (mi_in + 1) if (mi_in < (self.po.H - 1)) else -1
        self.M = 49#-------------------------------------------------------------------------------------------------------------HP
        self.ov = self.mav = self.mav_prev = self.mpv = self.mpv_prev = self.excess_leaked_mpv = set()
        self.e = dict()
        self.adc_max = 500#-300------------------------------------------------------------------------------------------------------HP
        self.adc_min = round(float(self.adc_max - 1) * 0.95)#-0.95------------------------------------------------------------------HP
        self.em = self.em_prev = self.em_delta = self.zero_rate = self.mto_rate = 0
        self.em_sp = 0.10#---------------------------------------------------------------------------------------------------------HP
    def update(self):
            # self.em_delta = (self.em - self.em_prev)
            # self.em_prev = self.em
            ###################################################################
            sc = 100.0#------------------------------------------------------------------------------------------------------------HP
            conn_delta = round(abs((self.em - self.em_sp) * sc))
            # print(conn_delta)
            """
            if conn_delta > 0:
                rel_set = self.mpv_prev.copy()
                if self.ffi == -1: rel_set &= self.po.s.eff_ch_A_v
                for a in rel_set:
                    rel_conns = (set(self.e[a].keys()) & self.mav_prev)
                    for b in rel_conns: self.e[a][b] = max((self.e[a][b] - conn_delta), 0)
            """
            ###################################################################
            fbv = self.po.m[self.fbi].mpv.copy() if (self.fbi != -1) else set()
            # fbv = self.po.m[self.fbi].mpv.copy() if (self.fbi != -1) else self.po.m[0].mpv.copy()
            for a in fbv:
                b = (a // self.M)
                if (len(fbv & set(range((b * self.M), ((b + 1) * self.M)))) == 1): self.mav.add(a)
            self.mav_prev = self.mav.copy()
            self.mpv = set()
            heap = [(len(set(self.e[a].keys()) ^ self.mav), random.randrange(100), a) for a in self.e.keys()]
            heapq.heapify(heap)
            # num_set_pred = len(self.po.s.unavail_idxs)
            num_set_pred = 20
            while heap and len(self.mpv) < num_set_pred:
                k = heapq.heappop(heap)[2]
                if k not in self.mpv: self.mpv.add(k)
            # while heap:
            #     k = heapq.heappop(heap)[2]
            #     if k not in self.mpv: self.mpv.add(k)
            self.mpv_prev = self.mpv.copy()
            self.em = self.zero_rate = self.mto_rate = 0
            self.ov = set()
            mav_update = set()
            mpv_ack = set()
            new_adc = random.randint(self.adc_min, self.adc_max)
            iv = self.po.s.sv.copy() if self.ffi == -1 else self.po.m[self.ffi].ov.copy()
            ci_dict = {a:set(range((a * self.M), ((a + 1) * self.M))) for a in iv}
            for a, ci in ci_dict.items():
                pv = (ci & self.mpv)
                mpv_ack |= pv
                if len(pv) == 0:
                    self.ov.add(a)
                    self.em += 1.0
                    self.zero_rate += 1.0
                    e_keys = set(self.e.keys())
                    ci_mod = ci - e_keys
                    while not ci_mod:
                        common_keys = e_keys & ci
                        for b in common_keys:
                            for k, v in list(self.e[b].items()):
                                if v > 0: self.e[b][k] -= 1
                                else:
                                    del self.e[b][k]
                                    e_keys.discard(b) 
                            if not self.e[b]:
                                del self.e[b]
                                e_keys.discard(b)
                                ci_mod = ci - e_keys
                                if ci_mod: break
                    wi = random.choice(list(ci_mod))
                else:
                    wi = random.choice(list(pv))
                    if len(pv) > 1:
                        self.ov.add(a)
                        self.em += (float(len(pv) - 1) / float(self.M - 1))
                        self.mto_rate += 1.0
                if wi in self.e.keys():
                    for b in self.mav: self.e[wi][b] = new_adc
                else: self.e[wi] = {b:new_adc for b in self.mav}
                mav_update.add(wi)
            norm = float(max(1, len(ci_dict)))
            self.em /= norm
            self.zero_rate /= norm
            self.mto_rate /= norm
            self.excess_leaked_mpv = (self.mpv - mpv_ack)
            for a in self.excess_leaked_mpv: self.ov.add((a // self.M))
            self.mav = mav_update.copy()
oracle = Oracle()
oracle.update()