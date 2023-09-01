import random
class Oracle:
    def __init__(self):
        self.H = 6#--------------------------------------------------------------------------------------------------------------HP
        self.K = 16#-------------------------------------------------------------------------------------------------------------HP
        self.M = 49#-------------------------------------------------------------------------------------------------------------HP
        self.N = (self.K * self.M)
        self.PV = 97#------------------------------------------------------------------------------------------------------------HP
        self.m = [Matrix(self, a) for a in range(self.H)]
        ts_dim = 10#-------------------------------------------------------------------------------------------------------------HP
        self.ts_idx = self.cyc = 0
        self.ts = [{random.randrange((self.M * a), (self.M * (a + 1))) for a in range(self.K)} for _ in range(ts_dim)]
    def update(self):
        while True:
            for a in self.m: a.update()
            self.cyc += 1
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.mi = mi_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.e = {a:dict() for a in range(self.po.N)}
        self.av = self.ov = set()
    def update(self):
        if (self.ffi == -1):
            iv = self.po.ts[self.po.ts_idx].copy()
            self.po.ts_idx = ((self.po.ts_idx + 1) % len(self.po.ts))
        else: iv = self.po.m[self.ffi].ov.copy()
        # rand_v = {random.randrange((self.po.M * a), (self.po.M * (a + 1))) for a in range(self.po.K)}
        # fbv = self.po.m[self.fbi].av.copy() if (self.fbi != 0) else rand_v.copy()
        # fbv = self.po.m[self.fbi].av.copy() if (self.fbi != 0) else set()
        fbv = self.po.m[self.fbi].av.copy()
        cv = (self.av | {(a + self.po.N) for a in fbv})
        avA = dict()
        prv = cv.copy()
        for a in self.e.keys():
            lov = (set(self.e[a].keys()) & cv)
            avA[a] = len(lov)
            prv &= lov
        uv = (cv - prv)
        avB = {a:(avA[a] - len(prv)) for a in avA.keys()}
        self.av = {key for key, value in avB.items() if ((value > 0) and (value == max(avB.values())))}
        if ((len(cv) == 0) and (len(self.av) == 0) and (self.po.cyc < 10)):
            self.av = {key for key, value in avB.items() if (value == max(avB.values()))}
        self.ov = (iv - self.av)
        exv = (self.av - iv)
        em = 0
        for a in iv:
            ci = set(range((self.po.M * (a // self.po.M)), (self.po.M * ((a // self.po.M) + 1))))
            pv = ((ci & self.av) - {a})
            if (len(pv) > 0):
                em += (float(len(pv)) / float(self.po.M - 1))
                for b in pv:
                    tv = (set(self.e[b].keys()) & prv)
                    if (len(tv) > 0):
                        del self.e[b][random.choice(list(tv))]
                        tv = (uv - set(self.e[b].keys()))
                        if (len(tv) > 0):
                            ri = random.choice(list(tv))
                            self.e[b][ri] = self.po.PV
                            uv.remove(ri)
            for b in cv: self.e[a][b] = self.po.PV
        de = float(max(1, len(iv)))
        em = ((em / de) * 100.0)
        erm = ((float(len(self.ov)) / de) * 100.0)
        for a in self.e.keys(): self.e[a] = {key:(value - 1) for key, value in self.e[a].items() if (value > 0)}
        tp = sum(((len(self.e[a].keys()) * 2) + 1) for a in self.e.keys())
        print(f"M{self.mi}  ERM: {erm:.1f}%\t  EM: {em:.1f}%\tTP: {tp}\tEX: {len(exv)}\tAV: {len(self.av)}")
oracle = Oracle()
oracle.update()
