import random
import sys
class Oracle:
    def __init__(self):
        self.max_int = (sys.maxsize - 1000)
        self.min_int = -(self.max_int - 1)
        self.H = 6#--------------------------------------------------------------------------------------------------------HP
        self.input_dim = 64#-----------------------------------------------------------------------------------------------HP
        self.ppcL = (self.input_dim - 1)
        self.ppcR = (self.input_dim - 2)
        self.ds_range_set = {a for a in range(self.input_dim)}
        self.ds_range_set.remove(self.ppcL)
        self.ds_range_set.remove(self.ppcR)
        self.ds_index = 0
        self.ds_card = 16#-------------------------------------------------------------------------------------------------HP
        self.ds_dim = 20#--------------------------------------------------------------------------------------------------HP
        self.ds = [{random.choice(list(self.ds_range_set)) for _ in range(self.ds_card)} for _ in range(self.ds_dim)]
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while (True):
            for a in self.m: a.update()
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.context_dim = 3#-----------------------------------------------------------------------------------------------------HP
        self.iv = self.cv = self.pv = self.pev = set()
        avec = ([0] * self.po.input_dim * self.context_dim)
        self.e = {a:avec.copy() for a in range(self.po.input_dim)}
        max_cv = ((self.po.max_int - 10) // len(avec))
        self.cv_delta_mag = 100000.0#---------------------------------------------------------------------------------------------HP
        max_cv_range = (max_cv // round(self.cv_delta_mag))
        self.cv_max = min(1000000, max_cv_range)#---------------------------------------------------------------------------------HP
        self.cv_min = -(self.cv_max - 1)
        self.agency = False
        self.beh = 0
        self.em = 0
    def update(self):
        # fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        fbv = self.po.m[self.fbi].pv.copy()
        self.cv = (self.iv | {(a + self.po.input_dim) for a in self.pv} | {(a + (self.po.input_dim * 2)) for a in fbv})
        # self.cv = (self.iv | {(a + self.po.input_dim) for a in fbv})
        #--TODO: probabilistic activation based on conf levels
        if (self.ffi == -1):
            self.pv = {a for a in self.e.keys() if (sum(self.e[a][b] for b in self.cv) > 0)}
            ppc_v = set()
            self.beh = 0
            if (self.po.ppcL in self.pv):
                self.beh += -1
                ppc_v.add(self.po.ppcL)
            if (self.po.ppcR in self.pv):
                self.beh += 1
                ppc_v.add(self.po.ppcR)
            self.agency = (len(ppc_v) > 0)
            if ((not self.agency) and (random.randrange(1000000) < 100000)):
                self.beh = random.choice([-1, 1])
                if (self.beh == -1): ppc_v.add(self.po.ppcL)
                if (self.beh == 1): ppc_v.add(self.po.ppcR)
            self.po.ds_index = ((self.po.ds_index + len(self.po.ds) + self.beh) % len(self.po.ds))
            self.iv = self.po.ds[self.po.ds_index].copy()
            self.iv |= ppc_v
            self.pev = (self.iv ^ self.pv)
        else:
            self.iv = self.po.m[self.ffi].pev.copy()
            self.pev = (self.iv ^ self.pv)
            self.pv = {a for a in self.e.keys() if (sum(self.e[a][b] for b in self.cv) > 0)}
        em_den = float(max(1, (len(self.iv) + len(self.pv))))
        self.em = (float(len(self.pev)) / em_den)
        failed_pev = (self.iv - self.pv)
        false_pev = (self.pv - self.iv)
        for a in self.cv:
            #--TODO: probabilistic favoring of close matches to enable innovation / creativity
            for b in failed_pev:
                conf = self.comp_conf(self.e[b][a])
                delta = round((1.0 - conf) * self.cv_delta_mag)
                self.e[b][a] = min((self.e[b][a] + delta), self.cv_max)
            for b in false_pev:
                conf = self.comp_conf(self.e[b][a])
                delta = round((1.0 - conf) * self.cv_delta_mag)
                self.e[b][a] = max((self.e[b][a] - delta), self.cv_min)
        if (self.ffi == -1):
            agency_str = f"\tAG: {self.beh}" if (self.agency) else ""
            print(f"EM: {(self.em * 100.0):.2f}%" + agency_str)
    def comp_conf(self, val_in):
        norm = float(self.cv_max - 1)
        if (val_in > 0): return (float(val_in - 1) / norm)
        else: return (float(abs(val_in)) / norm)
oracle = Oracle()
oracle.update()