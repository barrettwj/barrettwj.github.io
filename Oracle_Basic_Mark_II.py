import random
class Oracle:
    def __init__(self):
        self.H = 3#-----------------------------------------------------------------------------------------------HP
        self.N = 1024#---------------------------------------------------------------------------------------------HP
        density_pct = 0.37#---------------------------------------------------------------------------------------HP
        # self.trc = Transcoder()
        # self.trc.add_new_data("TSC1", 1, 3, 3)
        """
        for k, v in self.trc.tcs["TSC1"].items():
            print(f"K:{k}  V:{v}")
        print()
        self.trc.add_new_data("TSC2", 1, 5, 5)
        for k, v in self.trc.tcs["TSC2"].items():
            print(f"K:{k}  V:{v}")
        print()
        self.trc.add_new_data("TSC3", 1, 3, 3)
        for k, v in self.trc.tcs["TSC3"].items():
            print(f"K:{k}  V:{v}")
        print()
        self.trc.add_new_data("TSC4", 1, 3, 3)
        for k, v in self.trc.tcs["TSC4"].items():
            print(f"K:{k}  V:{v}")
        print()
        self.trc.add_new_data("TSC5", 1, 3, 3)
        for k, v in self.trc.tcs["TSC5"].items():
            print(f"K:{k}  V:{v}")
        """
        #############################################################################################################################
        self.ts_idx = 0
        ts_dim = 2#-----------------------------------------------------------------------------------------------HP
        ################################################################
        #"""
        emdm_nv = 500#--------------------------------------------------------------------------------------------HP
        emdm_card = 2#---------------------------------------------------------------------------------------------HP
        self.emdm_mask = {(self.N - 1 - a) for a in range(emdm_nv + (emdm_card - 1))}
        start_idx = min(self.emdm_mask)
        emdm_max_val = 1
        emdm_min_val = -1
        emdm_inc = ((emdm_max_val - emdm_min_val) / (emdm_nv - 1))
        self.emdm_vals = {frozenset({(start_idx + a + b) for b in range(emdm_card)}):
                          (emdm_min_val + (a * emdm_inc))  for a in range(emdm_nv)}
        self.iv_mask = (set(range(self.N)) - self.emdm_mask)
        iv_card = round(len(self.iv_mask) * density_pct)
        self.ts = [set(random.sample(list(self.iv_mask), iv_card)) for _ in range(ts_dim)]
        #"""
        #################################################################
        # self.ts = [set(random.sample(range(self.N), self.density)) for _ in range(ts_dim)]
        #############################################################################################################################
        self.bv_map = dict()
        #############################################################################################################################
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while True:
            for a in self.m: a.update()
            self.ts_idx = ((self.ts_idx + 1) % len(self.ts))
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.M = 50#-----------------------------------------------------------------------------------------------HP
        self.K = (self.po.N * self.M)
        self.fbv = set()
        self.fbv_mod = set()
        self.fbv_cl = dict()
        self.iv = set()
        self.ev = set()
        self.cv = set()
        self.pv = set()
        self.av = set()
        self.adc_max = 1000#---------------------------------------------------------------------------------------------HP
        # self.forget_period = 1000#---------------------------------------------------------------------------------HP
        # self.forget_period_ct = 0
        self.mem = dict()
        self.bv_idx = self.bv_idx_prev = -1
        self.em = self.em_prev = self.em_delta = 0
        self.rsA = random.sample(range(len(self.po.emdm_vals)), len(self.po.emdm_vals))
        self.rsB = random.sample(range(1000000), 1000000)
        self.confusion_map_dim = 10#---------------------------------------------------------------------------------HP
        self.confusion_map = dict()#-maybe pre-populate this with high values for newly available bvs????
    def update(self):
        #############################################################################################################################
        """
        for k, v in self.mem.items():
            if (v[1][0] < self.adc_max): v[1][0] += 1
        #############################################################
        self.forget_period_ct += 1
        if (self.forget_period_ct == self.forget_period):
            d = [(k, v[1][1]) for k, v in self.mem.items()]
            rs = self.rsB.copy()
            ds = sorted(d, key = lambda x: (x[1], rs.pop(0)), reverse = True)
            if (ds[0][1] > 10): del self.mem[ds[0][0]]#--------------------------------------------------------------HP
            self.forget_period_ct = 0
        """
        #############################################################################################################################
        # self.fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        self.fbv = self.po.m[self.fbi].pv.copy()
        # self.fbv_mod = {-(a + 1) for a in self.fbv}
        self.fbv_cl = dict()
        for a in self.fbv:
            cli = (a // self.M)
            if (len(self.fbv & set(range((cli * self.M), ((cli + 1) * self.M)))) == 1): self.fbv_cl[cli] = a
        #############################################################################################################################
        self.cv = (self.iv | {(a + self.po.N) for a in self.av} | {(a + self.po.N + self.K) for a in self.fbv})
        self.pv = set()
        acts = [(k, len(v.keys() ^ self.cv)) for k, v in self.mem.items()]
        if (len(acts) > 0):
            acts_mean = (sum(a[1] for a in acts) / len(acts))
            acts_var = (sum(((a[1] - acts_mean) ** 2) for a in acts) / len(acts))
            acts_stdev = (acts_var ** (1 / 2))
            alpha = 1#--------------------------------------------------------------------------------------------------HP
            thresh_A = max(0, (acts_mean - (alpha * acts_stdev)))
            self.pv = {a[0] for a in acts if (a[1] <= thresh_A)}
        # rs = self.rsB.copy()
        # acts_sorted = sorted(acts, key = lambda x: (x[1], rs.pop()))
        #############################################################################################################################
        self.bv_idx_prev = self.bv_idx
        self.bv_idx = -1
        if (self.ffi == -1):
            ##########################################################
            if (self.bv_idx_prev != -1):
                if (self.bv_idx_prev not in self.confusion_map): self.confusion_map[self.bv_idx_prev] = [1]#---------HP
                else:
                    self.confusion_map[self.bv_idx_prev].append(self.em_delta)
                    if (len(self.confusion_map[self.bv_idx_prev]) > self.confusion_map_dim): self.confusion_map[self.bv_idx_prev].pop(0)
            ##########################################################
            self.iv = set()
            ##########################################################
            """
            d = [(k, abs(self.em_delta - v)) for k, v in self.po.emdm_vals.items()]
            rs = self.rsA.copy()
            ds = sorted(d, key = lambda x: (x[1], rs.pop()))
            self.iv |= set(ds[0][0])
            """
            ##########################################################
            if (self.po.bv_map):
                pv_mod = set()
                for a in self.pv:
                    cli = (a // self.M)
                    if (len(self.pv & set(range((cli * self.M), ((cli + 1) * self.M)))) == 1): pv_mod.add(cli)
                d = [((len(k ^ pv_mod) / self.po.N), k, v) for k, v in self.po.bv_map.items()]
                rs = self.rsB.copy()
                ds = sorted(d, key = lambda x: (x[0], rs.pop()))
                thresh_B = abs(self.em_delta)#----------------------------------------------------------------------------------HP
                # thresh_B = 1000000#-debug
                if (ds[0][0] >= thresh_B):
                    if (random.randrange(1000000) < 980000):#-----modulate explore/exploit using this value???
                        d = [(sum(v), k) for k, v in self.confusion_map.items()]
                        rs = self.rsB.copy()
                        ds = sorted(d, key = lambda x: (x[0], rs.pop()), reverse = True)
                        self.bv_idx = ds[0][1]
                    else: self.bv_idx = random.choice(range(len(self.po.ts)))
                    self.iv |= self.po.ts[self.bv_idx]
                    self.po.bv_map[frozenset(self.iv)] = self.bv_idx#--------------------------------------????????????
                else:
                    self.bv_idx = ds[0][2]
                    self.iv |= ds[0][1]
            else:
                self.bv_idx = random.choice(range(len(self.po.ts)))
                self.iv |= self.po.ts[self.bv_idx]
                self.po.bv_map[frozenset(self.iv)] = self.bv_idx#--------------------------------------????????????
            ##########################################################
        else: self.iv = self.po.m[self.ffi].ev.copy()
        #############################################################################################################################
        self.em_prev = self.em
        self.em = 0
        zr = 0
        mr = 0
        self.av = set()
        self.ev = set()
        pv_ack = set()
        c_dict = {a:set(range((self.M * a), (self.M * (a + 1)))) for a in self.iv}
        for a, ci in c_dict.items():
            pv = (self.pv & ci)
            lpv = len(pv)
            if lpv == 0:
                zr += 1
                if (a not in self.fbv_cl): self.ev.add(a)
                ciav = (ci - self.mem.keys())
                if not ciav:
                    d = [(len(v), k) for k, v in self.mem.items()]#--------------------------is this ideal???????
                    rs = self.rsB.copy()
                    ds = sorted(d, key = lambda x: (x[0], rs.pop()))
                    del self.mem[ds[0][1]]
                    ciav = (ci - self.mem.keys())
                wi = random.choice(list(ciav))
            if lpv > 1:#------------------------------------should fix to where this does not occur????
                mr += 1
                if (a not in self.fbv_cl): self.ev.add(a)
                pv_ack |= pv
                self.em += ((lpv - 1) / (self.M - 1))
                wi = random.choice(list(pv))
                #-------------------------------what to do with competitors???
            if lpv == 1:
                pv_ack |= pv
                wi = pv.pop()
            if wi not in self.mem: self.mem[wi] = {b:self.adc_max for b in self.cv}
            else:
                for b in self.cv: self.mem[wi][b] = self.adc_max
            self.av.add(wi)
        pv_exc = (self.pv - pv_ack)
        #--------------------------------------------deal with minimizing pv_exc for M0 only???
        self.em /= max(1, len(c_dict))
        self.em_delta = (self.em - self.em_prev)
        #############################################################################################################################
        bv_str = f"  BV: {str(self.bv_idx).rjust(2)}" if (self.bv_idx != -1) else ""
        print(f"M{(self.ffi + 1)}  EM: {str(f'{self.em:.2f}').rjust(4)}  MEM: {str(len(self.mem)).rjust(4)}" +
              f"  PV: {str(len(self.pv)).rjust(4)}  PVEXC: {str(len(pv_exc)).rjust(4)}  ZR: {str(zr).rjust(3)}" +
              f"  MR: {str(mr).rjust(3)}" + bv_str)
        #############################################################################################################################
class Transcoder:
    def __init__(self):
        self.tcs = dict()
        self.rsA = random.sample(range(1000000), 1000000)
    def add_new_data(self, label_in, min_val_in, max_val_in, num_vals_in):
        if label_in not in self.tcs:
            all_idcs = set()
            for v in self.tcs.values(): all_idcs |= v.keys()
            start_idx = 0
            oscA = 1
            oscB = 1
            while start_idx in all_idcs:
                start_idx += (oscA * oscB)
                oscA += 1
                oscB = -oscB
            offset = (start_idx - num_vals_in + 1) if start_idx < 0 else start_idx
            inc = ((max_val_in - min_val_in) / (num_vals_in - 1))
            self.tcs[label_in] = {(offset + a):(min_val_in + (inc * a)) for a in range(num_vals_in)}
        else:
            pass
    def get_idx(self, label_in, val_in):
        d = [(abs(v - val_in), k) for k, v in self.tcs[label_in].items()]
        rs = self.rsA.copy()
        ds = sorted(d, key = lambda x: (x[0], rs.pop()))
        return ds[0][1]
    def get_val(self, label_in, idx_in):
        return self.tcs[label_in][idx_in] if idx_in in self.tcs[label_in] else None
oracle = Oracle()
oracle.update()