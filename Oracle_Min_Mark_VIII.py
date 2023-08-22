import random
class Oracle:
    def __init__(self):
        self.H = 6#--------------------------------------------------------------------------------------------------------------HP
        self.num_clusters = 40#--------------------------------------------------------------------------------------------------HP
        self.m = [Matrix(self, a) for a in range(self.H)]
        #_______________________________________________GENERATE TEST SEQUENCE_____________________________________________________
        ts_dim = 10#-------------------------------------------------------------------------------------------------------------HP
        ts_range_set = {a for a in range(self.num_clusters)}
        ts_density = 0.33#-------------------------------------------------------------------------------------------------------HP
        ts_card = round(float(len(ts_range_set)) * ts_density)
        self.ts = []
        self.ts_index = self.cycle = 0
        while (len(self.ts) < ts_dim):
            ts_range_set_temp = ts_range_set.copy()
            tv = set()
            while (len(tv) < ts_card):
                ri = random.choice(list(ts_range_set_temp))
                ts_range_set_temp.remove(ri)
                tv.add(ri)
            self.ts.append(tv.copy())
    def update(self):
        while (True):
            for a in self.m: a.update()
            self.cycle += 1
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.mi = mi_in
        self.ffi = (self.mi - 1)
        self.fbi = (self.mi + 1) if (self.mi < (self.po.H - 1)) else -1
        self.M = 50#-------------------------------------------------------------------------------------------------------------HP
        self.adc_val = 30#-------------------------------------------------------------------------------------------------------HP
        self.m_dim = (self.M * self.po.num_clusters)
        self.e = dict()
        self.ov = self.av = set()
        self.tp = 0
        self.ppcL = self.ppcR = -1
        self.agency = False
    def update(self):
        #___________________________STORE FEEDBACK INPUT AND GENERATE CONTEXT VECTOR______________________________________________
        # fbv = self.po.m[self.fbi].av.copy() if (self.fbi != -1) else set()
        fbv = self.po.m[self.fbi].av.copy() if (self.fbi != -1) else self.po.m[0].av.copy()
        fbv = {(a + self.m_dim) for a in fbv}
        cv = (self.av | fbv)
        #________________________________________COMPUTE PREDICTIVE ACTIVATION____________________________________________________
        vals = {a:len(set(self.e[a].keys()) & cv) for a in self.e.keys()}
        self.av = {a for a in vals.keys() if (vals[a] == max(vals.values()))}
        if (self.mi == 0):
        #_____________________________________________DETECT PREDICTED ACTION_____________________________________________________
            bv = 0
            if (self.ppcL in self.av):
                cli = (self.ppcL // self.M)
                pv = (self.av & set(range((self.M * cli), (self.M * (cli + 1)))))
                if (len(pv) == 1): bv += -1
            if (self.ppcR in self.av):
                cli = (self.ppcR // self.M)
                pv = (self.av & set(range((self.M * cli), (self.M * (cli + 1)))))
                if (len(pv) == 1): bv += 1
            self.agency = (bv != 0)
        #___________________________________________ASSIGN PROPRIOCEPTIVE ELEMENTS________________________________________________
            if ((bv == 0) and (len(self.av) > 0)):
                if ((self.ppcL == -1) and (self.ppcR != -1)): bv = -1
                if ((self.ppcR == -1) and (self.ppcL != -1)): bv = 1
                if ((self.ppcL == -1) and (self.ppcR == -1)): bv = random.choice([-1, 1])
                if (bv == 0): bv = random.choice([-1, 1])
                if (bv == -1):
                    self.ppcL = random.choice(list(self.av))
                    while (self.ppcL == self.ppcR): self.ppcL = random.choice(list(self.av))
                if (bv == 1):
                    self.ppcR = random.choice(list(self.av))
                    while (self.ppcR == self.ppcL): self.ppcR = random.choice(list(self.av))
        #_______________________________________MANIFEST ACTION AND STORE SELECTED INPUT__________________________________________
            self.po.ts_index = ((self.po.ts_index + len(self.po.ts) + bv) % len(self.po.ts))
            iv = self.po.ts[self.po.ts_index].copy()
        else: iv = self.po.m[self.ffi].ov.copy()
        #_____________________________________COMPUTE PREDICTION ERROR AND UPDATE CONNECTION PERMANENCE___________________________
        exp = set()
        self.ov = set()
        em = zr = mr = 0
        for a in iv:
            ci = set(range((self.M * a), (self.M * (a + 1))))
            pv = (self.av & ci)
            exp |= pv
            if (len(pv) == 0):
                em += 1.0
                zr += 1.0
                wi = random.choice(list(ci))
            if (len(pv) > 1):
                self.ov.add(a)
                em += (float(len(pv) - 1) / float(self.M - 1))
                mr += 1.0
                wi = random.choice(list(pv))
                pv.remove(wi)
                for b in pv:
                    tv = (cv & set(self.e[b].keys()) & self.e[wi].keys())
                    if (len(tv) > 0): self.e[b][random.choice(list(tv))] = 0
            if (len(pv) == 1): wi = pv.pop()
            if wi in self.e.keys():
                for b in cv: self.e[wi][b] = self.adc_val
            else: self.e[wi] = {b:self.adc_val for b in cv}
        #_______________________________________PRUNE NETWORK AND COMPUTE METRICS_________________________________________________
        denom = float(max(1, len(iv)))
        em /= denom
        zr /= denom
        mr /= denom
        exp = (self.av - exp)
        if (len(self.e.keys()) > 100):#-----------------------------------------------------------------------------------------HP
            for a in self.e.keys(): self.e[a] = {key:(value - 1) for key, value in self.e[a].items() if (value > 0)}
            self.e = {key:value for key, value in self.e.items() if (len(value) > 0)}
        self.tp = (len(self.e.keys()) + sum((len(self.e[a].keys()) * 2) for a in self.e.keys()))
        agency_str = f"\tBV: {bv}\tL:{self.ppcL}  R:{self.ppcR}" if (self.agency) else ""
        if (self.mi == 0): print(f"CY: {self.po.cycle}")
        print(f"M{self.mi}: EM: {(em * 100.0):.2f}%\tZR: {(zr * 100.0):.2f}%\tMR: {(mr * 100.0):.2f}%" + 
              f"\tEL: {len(self.e.keys())}\tTP: {self.tp}    \tEX: {len(exp)}" + agency_str)
oracle = Oracle()
oracle.update()