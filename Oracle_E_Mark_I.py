import random
import sys
class Oracle:
    def __init__(self):
        self.max_int = (sys.maxsize - 1000)
        self.min_int = -(self.max_int - 1)
        self.H = 6#--------------------------------------------------------------------------------------------------------HP
        self.input_dim = 32#-----------------------------------------------------------------------------------------------HP
        self.ppcL = (self.input_dim - 1)
        self.ppcR = (self.input_dim - 2)
        self.ds_range_set = {a for a in range(self.input_dim)}
        self.ds_range_set.remove(self.ppcL)
        self.ds_range_set.remove(self.ppcR)
        self.ds_index = 0
        self.ds_card = 16
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
        self.context_dim = 3#----------------------------------------------------------------------------------------------HP
        self.iv = self.cv = self.pv = self.pev = set()
        avec = ([0] * self.po.input_dim * self.context_dim)
        self.e = {a:avec.copy() for a in range(self.po.input_dim)}
        self.cv_max = min(1000, ((self.po.max_int - 10) // len(avec)))#-----------------------------------------------------HP
        self.cv_min = -(self.cv_max - 1)
        self.em = 0
    def update(self):
        # fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        fbv = self.po.m[self.fbi].pv.copy()
        self.cv = (self.iv | {(a + self.po.input_dim) for a in self.pv} | {(a + (self.po.input_dim * 2)) for a in fbv})
        # self.cv = (self.iv | {(a + self.po.input_dim) for a in fbv})
        self.pv = {a for a in self.e.keys() if (sum(self.e[a][b] for b in self.cv) > 0)}
        if (self.ffi == -1):
            self.po.ds_index = ((self.po.ds_index + 1) % len(self.po.ds))
            self.iv = self.po.ds[self.po.ds_index].copy()
        else: self.iv = self.po.m[self.ffi].pev.copy()
        self.pev = (self.iv ^ self.pv)
        em_den = float(max(1, (len(self.iv) + len(self.pv))))
        self.em = (float(len(self.pev)) / em_den)
        failed_pev = (self.iv - self.pv)
        false_pev = (self.pv - self.iv)
        for a in self.cv:
            for b in failed_pev:
                delta = 1
                self.e[b][a] = min((self.e[b][a] + delta), self.cv_max)
            for b in false_pev:
                delta = 1
                self.e[b][a] = max((self.e[b][a] - delta), self.cv_min)
        if (self.ffi == -1): print(f"EM: {(self.em * 100.0):.2f}%")
oracle = Oracle()
oracle.update()