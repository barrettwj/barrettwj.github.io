import random
import heapq
class Oracle:
    def __init__(self):
        self.H = 6#----------------------------------------------------------------------------------------------------------------HP
        self.mval = 49#-49-----------------------------------------------------------------------------------------------------------HP
        self.s = Sensorium(self)
        self.m = [Matrix(self, a) for a in range(self.H)]
        self.em_global = 0
    def update(self):
        while True:
            self.em_global = 0
            for a in self.m:
                a.update()
                self.em_global += a.em
            self.em_global /= float(len(self.m))
class Sensorium:
    def __init__(self, po_in):
        self.po = po_in
        self.mval = self.po.mval
        #______________________________________________________________EM INTEROCEPTION_______________________________________________
        em_int_card = 3#------------------------------------------------------------------------------------------------------------HP
        em_int_dim = 17#-should be odd!!!-------------------------------------------------------------------------------------------HP
        start_idx = -round((em_int_dim - 1) / 2)
        em_int_v = {(start_idx + a) for a in range(em_int_dim)}
        em_int_num_values = (em_int_dim - em_int_card + 1)
        em_val_interval = (1.0 / float(em_int_num_values - 1))
        self.em_aff_values = {frozenset({(start_idx + a + b) for b in range(em_int_card)}):
                                (float(a) * em_val_interval) for a in range(em_int_num_values)}
        self.unavail_idxs = em_int_v.copy()
        #______________________________________________________________RF AFFERENT___________________________________________________
        aff_ch_A_dim = 107#-should be odd!!!---------------------------------------------------------------------------------------HP
        aff_ch_A_card_pct = 0.15#--------------------------------------------------------------------------------------------------HP
        self.aff_ch_A_card = round(float(aff_ch_A_dim) * aff_ch_A_card_pct)
        start_idx = -round((aff_ch_A_dim - 1) / 2)
        self.aff_ch_A_v = {(start_idx + a) for a in range(aff_ch_A_dim)}
        while (len(self.aff_ch_A_v & self.unavail_idxs) > 0): self.aff_ch_A_v = {(a + 1) for a in self.aff_ch_A_v}
        self.unavail_idxs |= self.aff_ch_A_v
        #______________________________________________________________RF EFFERENT___________________________________________________
        eff_ch_A_dim = 107#-should be odd!!!---------------------------------------------------------------------------------------HP
        eff_ch_A_card_pct = 0.15#--------------------------------------------------------------------------------------------------HP
        self.eff_ch_A_card = round(float(eff_ch_A_dim) * eff_ch_A_card_pct)
        start_idx = -round((eff_ch_A_dim - 1) / 2)
        self.eff_ch_A_v = {(start_idx + a) for a in range(eff_ch_A_dim)}
        while (len(self.eff_ch_A_v & self.unavail_idxs) > 0): self.eff_ch_A_v = {(a - 1) for a in self.eff_ch_A_v}
        self.unavail_idxs |= self.eff_ch_A_v
        self.eff_ch_A_v_exp = set()
        for a in self.eff_ch_A_v: self.eff_ch_A_v_exp |= set(range((a * self.mval), ((a + 1) * self.mval)))
        self.sv = set()
        ts_len = 5#---------------------------------------------------------------------------------------------------------------HP
        tv = self.aff_ch_A_v.copy()
        self.ts = []
        for _ in range(ts_len):
            rv = set(random.sample(list(tv), self.aff_ch_A_card))
            tv -= rv
            self.ts.append(rv.copy())
        self.ts_idx = self.idx_delta = 0
        beh_mag = (len(self.ts) - 2)#---------------------------------------------------------------------------------------------HP
        self.beh_set = {(beh_mag - a) for a in range((beh_mag * 2) + 1)}
        self.beh_map_max_size = 5#-----------------------------------------------------------------------------------------------HP
        tv = self.eff_ch_A_v.copy()
        self.beh_map = dict()
        for _ in range(self.beh_map_max_size):
            rv = set(random.sample(list(tv), self.eff_ch_A_card))
            tv -= rv
            ri = random.choice(list(self.beh_set))
            self.beh_set.remove(ri)
            self.beh_map[frozenset(rv.copy())] = ri
        self.sv_card = (em_int_card + self.aff_ch_A_card + self.eff_ch_A_card)
        self.sv_span_min = (self.mval * (min(self.unavail_idxs) - 10))
        self.sv_span_max = (self.mval * (max(self.unavail_idxs) + 10))
    def update(self):
        em_val = self.po.m[0].em
        bv = (self.po.m[0].mpv & self.eff_ch_A_v_exp)
        bv = {(a // self.mval) for a in bv if (len(bv & set(range(((a // self.mval) * self.mval), (((a // self.mval) + 1) * self.mval)))) == 1)}
        heap = [(len(k ^ bv), random.randrange(100), k) for k in self.beh_map.keys()]
        heapq.heapify(heap)
        bv = heapq.heappop(heap)[2].copy()
        self.idx_delta = self.beh_map[bv]
        # self.idx_delta = 1
        self.ts_idx = ((self.ts_idx + len(self.ts) + self.idx_delta) % len(self.ts))
        self.sv = self.ts[self.ts_idx].copy()
        diffs = {k: abs(em_val - v) for k, v in self.em_aff_values.items()}
        min_val = min(diffs.values())
        cands = [k for k, v in diffs.items() if v == min_val]
        em_v = random.choice(cands).copy()
        # self.sv |= em_v
        self.sv |= bv
        return self.sv
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = (mi_in + 1) if (mi_in < (self.po.H - 1)) else -1
        self.mval = self.po.mval
        self.ov = self.mav = self.mpv = self.fbv = self.excess_leaked_mpv = set()
        self.e = dict()
        self.adc_max = 200#-300---------------------------------------------------------------------------------------------------HP
        self.adc_min = round(float(self.adc_max - 1) * 0.95)#-0.95----------------------------------------------------------------HP
        self.em = self.em_prev = self.em_error = self.zero_rate = self.mto_rate = 0
        self.em_sp = 0.10#--------------------------------------------------------------------------------------------------------HP
    def update(self):
            self.fbv = self.po.m[self.fbi].mpv.copy() if (self.fbi != -1) else set()#---------------------------------------------HP
            # self.fbv = self.po.m[self.fbi].mpv.copy() if (self.fbi != -1) else self.po.m[0].mpv.copy()#-------------------------HP
            fbv_conf_v = {(a // self.mval):a for a in self.fbv
                          if (len(self.fbv & set(range(((a // self.mval) * self.mval), (((a // self.mval) + 1) * self.mval)))) == 1)}
            fbv_conf_v_keys = set(fbv_conf_v.keys())
            ##########################################################################################
            self.mpv = set()
            heap = []
            for a in self.e.keys():
                sum = len(set(self.e[a][0].keys()) ^ self.mav)
                cli = (a // self.mval)
                # if cli in fbv_conf_v_keys: sum += len(set(self.e[a][1].keys()) ^ {fbv_conf_v[cli]})#---------------------------HP
                if cli in fbv_conf_v_keys: sum -= len(set(self.e[a][1].keys()) ^ {fbv_conf_v[cli]})#---------------------------HP
                heap.append((sum, random.randrange(100), a))
            heapq.heapify(heap)
            num_to_set_predictive = (self.po.s.sv_card - 0)#---------------------------------------------------------------------HP
            while heap and (len(self.mpv) < num_to_set_predictive):
                k = heapq.heappop(heap)[2]
                if k not in self.mpv: self.mpv.add(k)
            iv = self.po.s.update().copy() if self.ffi == -1 else self.po.m[self.ffi].ov.copy()
            # iv = self.po.s.sv.copy() if self.ffi == -1 else self.po.m[self.ffi].ov.copy()
            self.em = self.zero_rate = self.mto_rate = 0
            self.ov = set()
            mav_update = set()
            mpv_ack = set()
            new_adc = random.randint(self.adc_min, self.adc_max)
            ci_dict = {a:set(range((a * self.mval), ((a + 1) * self.mval))) for a in iv}
            for a, ci in ci_dict.items():
                pv = (ci & self.mpv)
                mpv_ack |= pv
                pv_len = len(pv)
                if pv_len == 0:
                    # self.ov.add(a)
                    self.em += 1.0
                    self.zero_rate += 1.0
                    ci_mod = ci - set(self.e.keys())
                    while not ci_mod:
                        for b in set(self.e.keys()) & ci:
                            if not ci_mod:
                                self.e[b][0] = {k:(v - 1) for k, v in self.e[b][0].items() if (v > 0)}
                                self.e[b][1] = {k:(v - 1) for k, v in self.e[b][1].items() if (v > 0)}
                                if not self.e[b][0] or not self.e[b][1]:
                                # if not self.e[b][0]:
                                    self.e = {k:v for k, v in self.e.items() if k != b}
                                    ci_mod = ci - set(self.e.keys())
                            else: break
                    # wi = ci_mod.pop()
                    wi = random.choice(list(ci_mod))
                    self.e[wi] = {0:{b:new_adc for b in self.mav}, 1:dict()}
                else:
                    # wi = pv.pop()
                    wi = random.choice(list(pv))
                    if pv_len > 1:
                        self.ov.add(a)
                        self.em += (float(pv_len - 1) / float(self.mval - 1))
                        self.mto_rate += 1.0
                        if (a in fbv_conf_v_keys): self.e[wi][1][fbv_conf_v[a]] = new_adc
                    for b in self.mav: self.e[wi][0][b] = new_adc
                mav_update.add(wi)
            norm = float(max(1, len(ci_dict)))
            self.em /= norm
            self.zero_rate /= norm
            self.mto_rate /= norm
            ##########################################################################################
            self.excess_leaked_mpv = (self.mpv - mpv_ack)
            for a in self.excess_leaked_mpv:
                cli = (a // self.mval)
                if (cli in fbv_conf_v_keys): self.e[a][1][fbv_conf_v[cli]] = new_adc
                self.ov.add(cli)
            # self.em_error = (self.em - self.em_prev)
            # self.em_prev = self.em
            ##########################################################################################
            #---------------------------------------------------------------------------IS THIS EVEN NECESSARY??????????
            # if self.ffi == -1:
            #     em_sp_abs_error = float(abs(self.em - self.em_sp))
            #     sc = 200.0#-------------------------------------------------------------------------------------------------------HP
            #     sc_val = round(em_sp_abs_error * sc)
                # ts = (self.mpv & self.po.s.eff_ch_A_v_exp)
                # for a in ts:
                #     for b in (self.mav & set(self.e[a].keys())): self.e[a][b] = max(0, (self.e[a][b] - sc_val))
            ##########################################################################################
            # for kA in list(self.e.keys()):
            #     self.e[kA][0] = {k:(v - 1) for k, v in self.e[kA][0].items() if (v > 0)}
            #     self.e[kA][1] = {k:(v - 1) for k, v in self.e[kA][1].items() if (v > 0)}
            # self.e = {k:v for k, v in self.e.items() if v[0] or v[1]}
            self.mav = mav_update.copy()
            ##########################################################################################
            agent_str = f"\tAG: {self.po.s.idx_delta}" if (self.ffi == -1) else ""
            print(f"M{self.ffi + 1}  EM: {(self.em * 100.0):.2f}%\tZR: {self.zero_rate:.2f}" +
                  f"\tMR: {self.mto_rate:.2f}\tEX: {len(self.excess_leaked_mpv)}" +
                  f"\tBEH: {len(self.po.s.beh_map)}\tMVP: {len(self.mpv)}" + agent_str)
oracle = Oracle()
oracle.update()