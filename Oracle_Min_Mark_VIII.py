import random
class Oracle:
    def __init__(self):
        self.H = 4#--------------------------------------------------------------------------------------------------------------HP
        self.K = 40#-------------------------------------------------------------------------------------------------------------HP
        self.m = [Matrix(self, a) for a in range(self.H)]
        #_______________________________________________GENERATE TEST SET__________________________________________________________
        ts_dim = 5#--------------------------------------------------------------------------------------------------------------HP
        ts_range_set = {a for a in range(self.K)}
        ts_density = 0.48#-------------------------------------------------------------------------------------------------------HP
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
        self.fbi = ((self.mi + 1) % self.po.H)
        self.M = 50#-------------------------------------------------------------------------------------------------------------HP
        self.adc_val = 67#-------------------------------------------------------------------------------------------------------HP
        self.m_dim = (self.M * self.po.K)
        self.e = dict()
        self.ov = self.av = set()
        self.tp = 0
        self.ppcL = self.ppcR = -1
        self.agency = False
    def update(self):
        #___________________________GENERATE CONTEXT VECTOR AND COMPUTE PREDICTIVE ACTIVATION____________________________________
        # fbv = self.po.m[self.fbi].av.copy() if (self.fbi != 0) else set()
        fbv = self.po.m[self.fbi].av.copy()
        fbtv = set()
        for a in fbv:
            cli = (a // self.M)
            if (len(fbv & set(range((self.M * cli), (self.M * (cli + 1))))) == 1): fbtv.add(cli)
        fbv = {(a + self.m_dim) for a in fbtv}
        avs = {a:(len(set(self.e[a].keys()) & self.av) - len(set(self.e[a].keys()) & fbv)) for a in self.e.keys()}
        self.av = {a for a in avs.keys() if (avs[a] == max(avs.values()))}
        if (self.mi == 0):
            bv = 0
            if (self.ppcL in self.av):
                if (len(self.av & set(range((self.M * (self.ppcL // self.M)),
                                            (self.M * ((self.ppcL // self.M) + 1))))) == 1): bv += -1
            if (self.ppcR in self.av):
                if (len(self.av & set(range((self.M * (self.ppcR // self.M)),
                                            (self.M * ((self.ppcR // self.M) + 1))))) == 1): bv += 1
            self.agency = (bv != 0)
            if ((bv == 0) and (len(self.av) > 0)):
                if ((self.ppcL == -1) and (self.ppcR != -1)): bv = -1
                if ((self.ppcR == -1) and (self.ppcL != -1)): bv = 1
                if ((self.ppcL == -1) and (self.ppcR == -1)): bv = random.choice([-1, 1])
                if (bv == 0): bv = random.choice([-1, 1])
                if (bv == -1):
                    tv = (self.av - {self.ppcR})
                    self.ppcL = random.choice(list(tv)) if (len(tv) > 0) else -1
                if (bv == 1):
                    tv = (self.av - {self.ppcL})
                    self.ppcR = random.choice(list(tv)) if (len(tv) > 0) else -1
        #_______________________________________MANIFEST ACTION AND STORE SELECTED INPUT__________________________________________
            self.po.ts_index = ((self.po.ts_index + len(self.po.ts) + bv) % len(self.po.ts))
            iv = self.po.ts[self.po.ts_index].copy()
        else: iv = self.po.m[self.ffi].ov.copy()
        #_____________________________________COMPUTE PREDICTION ERROR AND OPTIMIZE CONNECTIONS___________________________________
        exp = set()
        self.ov = set()
        em = zr = mr = 0
        for a in iv:
            ci = set(range((self.M * a), (self.M * (a + 1))))
            c = (a + self.m_dim)
            pv = (self.av & ci)
            exp |= pv
            if (len(pv) == 0):
                # if ((len(self.av) > 0) and (len(self.e.keys()) > 0) and (c in fbv)): self.ov.add(a)
                em += 1.0
                zr += 1.0
                ci_mod = [b for b in (ci & set(self.e.keys())) if (len(self.e[b].keys()) == 0)]
                # ci_mod = []
                wi = random.choice(list(ci)) if (len(ci_mod) == 0) else random.choice(ci_mod)
            if (len(pv) > 1):
                self.ov.add(a)
                em += (float(len(pv) - 1) / float(self.M - 1))
                mr += 1.0
                cands = [b for b in pv if (len(self.e[b].keys()) == min(len(self.e[b].keys()) for b in pv))]
                wi = random.choice(list(pv)) if (len(cands) == 0) else random.choice(cands)
            if (len(pv) == 1): wi = random.choice(list(pv))
            if wi in self.e.keys():
                for b in self.av: self.e[wi][b] = self.adc_val
            else: self.e[wi] = {b:self.adc_val for b in self.av}
            if (c in fbv): self.e[wi][c] = self.adc_val
        #_______________________________________PRUNE NETWORK AND COMPUTE METRICS_________________________________________________
        den = float(max(1, len(iv)))
        em /= den
        zr /= den
        mr /= den
        exp = (self.av - exp)
        for a in self.e.keys(): self.e[a] = {key:(value - 1) for key, value in self.e[a].items() if (value > 0)}
        if (len(self.e.keys()) > 5000): self.e = {key:value for key, value in self.e.items() if (len(value.keys()) > 0)}#---------HP
        self.tp = sum(((len(self.e[a].keys()) * 2) + 1) for a in self.e.keys())
        agency_str = f"\tBV: {bv}\tL:{self.ppcL}  R:{self.ppcR}" if (self.agency) else ""
        if (self.mi == 0): print(f"CY: {self.po.cycle}")
        print(f"M{self.mi}: EM: {(em * 100.0):.2f}%\tZR: {(zr * 100.0):.2f}%\tMR: {(mr * 100.0):.2f}%" + 
              f"\tEL: {len(self.e.keys())}   \tTP: {self.tp}    \tEX: {len(exp)}" + agency_str)
oracle = Oracle()
oracle.update()