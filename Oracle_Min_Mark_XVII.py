import random
import math
class Oracle:
    def __init__(self):
        self.H = 6#--------------------------------------------------------------------------------------------------------------HP
        self.K = 39#-------------------------------------------------------------------------------------------------------------HP
        self.M = 49#-------------------------------------------------------------------------------------------------------------HP
        self.N = (self.K * self.M)
        self.PV = 27#------------------------------------------------------------------------------------------------------------HP
        # max_pct = 1.0#-----------------------------------------------------------------------------------------------------------HP
        # self.C = math.floor(float(self.N) * max_pct)
        self.m = [Matrix(self, a) for a in range(self.H)]
        #__________________________________________________________________________________________________________________________
        ts_dim = 5#--------------------------------------------------------------------------------------------------------------HP
        ts_range_set = {a for a in range(self.K)}
        ts_density = 0.28#-------------------------------------------------------------------------------------------------------HP
        ts_card = math.floor(float(len(ts_range_set)) * ts_density)
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
        # self.e = dict()
        self.e = {a:dict() for a in range(self.po.N)}
        self.ov = self.av = self.conf_cli = set()
        self.ppcL = self.ppcR = -1
    def update(self):
        #__________________________________________________________________________________________________________________________
        # fbv_cli = self.po.m[self.fbi].conf_cli.copy() if (self.fbi != 0) else set()
        # fbv_av = self.po.m[self.fbi].av.copy() if (self.fbi != 0) else set()
        fbv_cli = self.po.m[self.fbi].conf_cli.copy()
        fbv_av = self.po.m[self.fbi].av.copy()
        cv = (self.av | {(a + self.po.N) for a in fbv_av})
        avs = {a:(len(set(self.e[a].keys()) ^ cv) - len(self.e[a].keys())) for a in self.e.keys()}
        self.av = {a for a in avs.keys() if (avs[a] == min(avs.values()))}
        self.conf_cli = set()
        for a in self.av:
            cli = (a // self.po.M)
            if (len(self.av & set(range((self.po.M * cli), (self.po.M * (cli + 1))))) == 1): self.conf_cli.add(cli)
        if (self.mi == 0):
            bv = 0
            if (self.ppcL in self.conf_cli): bv += -1
            if (self.ppcR in self.conf_cli): bv += 1
            self.agency = (bv != 0)
            ts = self.conf_cli.copy() if (len(self.conf_cli) > 0) else set(range(self.po.K))
            if ((self.ppcL == -1) or (self.ppcR == -1) or ((self.ppcL != -1) and (self.ppcR != -1) and (bv == 0))):
                if ((self.ppcL == -1) and (self.ppcR != -1)):
                    tv = (ts - {self.ppcR})
                    self.ppcL = random.choice(list(tv)) if (len(tv) > 0) else -1
                if ((self.ppcR == -1) and (self.ppcL != -1)):
                    tv = (ts - {self.ppcL})
                    self.ppcR = random.choice(list(tv)) if (len(tv) > 0) else -1                    
            # if ((bv == 0) and (random.randrange(1000000) < 100000)):#-synapse discovery----------------------------------------HP
            if (bv == 0):#-synapse discovery----------------------------------------HP
                ri = random.choice([-1, 1])
                if (ri == -1):
                    tv = (ts - {self.ppcR})
                    self.ppcL = random.choice(list(tv)) if (len(tv) > 0) else -1
                if (ri == 1):
                    tv = (ts - {self.ppcL})
                    self.ppcR = random.choice(list(tv)) if (len(tv) > 0) else -1
            bv = 0
            if (self.ppcL in self.conf_cli): bv += -1
            if (self.ppcR in self.conf_cli): bv += 1
            self.po.ts_index = ((self.po.ts_index + len(self.po.ts) + bv) % len(self.po.ts))
            # self.po.ts_index = ((self.po.ts_index + len(self.po.ts) + bv + 1) % len(self.po.ts))
            iv = self.po.ts[self.po.ts_index].copy()
            if (self.ppcL in self.conf_cli): iv.add(self.ppcL)
            if (self.ppcR in self.conf_cli): iv.add(self.ppcR)
        else: iv = self.po.m[self.ffi].ov.copy()
        #_________________________________________________________________________________________________________________________
        self.ov = set()
        emr = len(self.conf_cli ^ iv)
        em = zr = mr = 0
        for a in iv:
            ci = set(range((self.po.M * a), (self.po.M * (a + 1))))
            pv = (self.av & ci)
            if (len(pv) == 0):
                # self.ov.add(a)
                em += 1.0
                zr += 1.0
                ci_mod = [b for b in (ci & set(self.e.keys())) if (len(self.e[b].keys()) == 0)]
                # ci_mod = []
                wi = random.choice(list(ci)) if (len(ci_mod) == 0) else random.choice(ci_mod)
            if (len(pv) > 1):
                self.ov.add(a)
                em += (float(len(pv) - 1) / float(self.po.M - 1))
                mr += 1.0
                # cands = [b for b in pv if (len(self.e[b].keys()) == min(len(self.e[b].keys()) for b in pv))]
                # cands = [b for b in pv if (len(self.e[b].keys()) == max(len(self.e[b].keys()) for b in pv))]
                cands = []
                wi = random.choice(list(pv)) if (len(cands) == 0) else random.choice(cands)
                for b in pv:
                    if (b != wi):
                        if (a in fbv_cli):
                            fbv_ci = (ci - fbv_av)
                            for d in fbv_ci: self.e[b][d] = self.po.PV
                        else:
                            ovA = (cv & set(self.e[wi].keys()) & set(self.e[b].keys()))
                            if (len(ovA) > 0): del self.e[b][random.choice(list(ovA))]
            if (len(pv) == 1): wi = random.choice(list(pv))
            if (wi in self.e.keys()):
                for b in cv: self.e[wi][b] = self.po.PV
            else: self.e[wi] = {b:self.po.PV for b in cv}
        #_____________________________________________________________________________________________________________________
        den = float(max(1, len(iv)))
        em /= den
        zr /= den
        mr /= den
        for a in self.e.keys(): self.e[a] = {key:(value - 1) for key, value in self.e[a].items() if (value > 0)}
        # if (len(self.e.keys()) > self.po.C): self.e = {key:value for key, value in self.e.items() if (len(value.keys()) > 0)}
        self.tp = sum(((len(self.e[a].keys()) * 2) + 1) for a in self.e.keys())
        agency_str = f"\tBV: {bv}\tL:{self.ppcL}  R:{self.ppcR}" if ((self.mi == 0) and (self.agency)) else ""
        # if (self.mi == 0): print(f"CY: {self.po.cycle}")
        print(f"M{self.mi}: EM: {(em * 100.0):.2f}%\tZR: {(zr * 100.0):.2f}%\tMR: {(mr * 100.0):.2f}%" + 
              f"\tEL: {len(self.e.keys())}\tER: {emr}\tTP: {self.tp}" + agency_str)
oracle = Oracle()
oracle.update()