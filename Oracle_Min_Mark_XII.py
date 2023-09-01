import random
class Oracle:
    def __init__(self):
        self.H = 6#--------------------------------------------------------------------------------------------------------------HP
        self.K = 20#-------------------------------------------------------------------------------------------------------------HP
        self.M = 49#-------------------------------------------------------------------------------------------------------------HP
        self.N = (self.K * self.M)
        self.PV = 17#------------------------------------------------------------------------------------------------------------HP
        self.m = [Matrix(self, a) for a in range(self.H)]
        ts_dim = 5#--------------------------------------------------------------------------------------------------------------HP
        self.ts_index = self.cycle = 0
        self.ts = [{random.randrange((self.M * a), (self.M * (a + 1))) for a in range(self.K)} for _ in range(ts_dim)]
    def update(self):
        while True:
            for a in self.m: a.update()
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
            iv = self.po.ts[self.po.ts_index].copy()
            self.po.ts_index = ((self.po.ts_index + 1) % len(self.po.ts))
        else: iv = self.po.m[self.ffi].ov.copy()
        # rand_v = {random.randrange((self.po.M * a), (self.po.M * (a + 1))) for a in range(self.po.K)}
        # fbv = self.po.m[self.fbi].av.copy() if (self.fbi != 0) else rand_v.copy()
        fbv = self.po.m[self.fbi].av.copy() if (self.fbi != 0) else set()
        # fbv = self.po.m[self.fbi].av.copy()
        cv = (self.av | {(a + self.po.N) for a in fbv})
        avA = dict()
        prv = cv.copy()
        for a in self.e.keys():
            lov = (set(self.e[a].keys()) & cv)
            avA[a] = len(lov)
            prv &= lov
        # uv = (cv - prv)
        avB = {a:(avA[a] - len(prv)) for a in avA.keys()}
        self.av = {key for key, value in avB.items() if (value == max(avB.values()))}
        self.ov = (iv - self.av)
        pm = 0
        for a in iv:
            ci = set(range((self.po.M * (a // self.po.M)), (self.po.M * ((a // self.po.M) + 1))))
            pv = ((ci & self.av) - {a})
            if (len(pv) > 0):
                pm += (float(len(pv) - 1) / float(self.po.M - 1))
                for b in pv:
                    tv = (set(self.e[b].keys()) & prv)
                    if (len(tv) > 0): del self.e[b][random.choice(list(tv))]
            for b in cv: self.e[a][b] = self.po.PV
        denom = float(max(1, len(iv)))
        em = ((float(len(self.ov)) / denom) * 100.0)
        pm = ((pm / denom) * 100.0)
        for a in self.e.keys(): self.e[a] = {key:(value - 1) for key, value in self.e[a].items() if (value > 0)}
        tp = (len(self.e.keys()) + sum((len(self.e[a].keys()) * 2) for a in self.e.keys()))
        print(f"M{self.mi}  EM: {em:.2f}%\t  PM: {pm:.2f}%\tTP: {tp}")
oracle = Oracle()
oracle.update()
