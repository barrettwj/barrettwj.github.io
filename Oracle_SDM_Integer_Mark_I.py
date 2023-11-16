import random
# import math
class Oracle:
    def __init__(self):
        self.H = 6#---------------------------------------------------------------------------------------HP
        self.d = 10#-should be a multiple of 10-----------------------------------------------------------HP
        # self.r = (round(math.log(self.d) / math.log(10)) + 1)
        self.ds_dim = 10#-should be >= self.d-------------------------------------------------------------HP
        self.ds = [random.randrange(self.d) for _ in range(self.ds_dim)]
        self.PE_ex = self.ds_index = 0
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while (True):
            beh = (self.m[0].P - ((self.m[0].P // self.d) * self.d))
            # self.ds_index = beh
            index_delta = (-(len(self.ds) - 1) + beh)
            self.ds_index = ((self.ds_index + len(self.ds) + index_delta) % len(self.ds))
            # self.ds_index = ((self.ds_index + len(self.ds) + beh) % len(self.ds))
            self.PE_ex = ((self.ds[self.ds_index] * self.d) + beh)
            for a in self.m:
                a.update()
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.mi = mi_in
        self.E = []
        self.P = self.PE = self.A = self.Z = 0
        self.M = 1000#-----------------------------------------------------------------------------------HP
        self.K = 1.05#-----------------------------------------------------------------------------------HP
        self.D_max = 10000#----------------------------------------------------------------------------------HP
        self.Q = (self.po.d ** 2)
    def update(self):
        I = self.po.PE_ex if (self.mi == 0) else self.po.m[(self.mi - 1)].PE
        self.Z = ((I * self.Q) + self.po.m[((self.mi + 1) % self.po.H)].P)
        vi = set()
        if ((len(self.E) < self.M) and (self.Z not in self.E)):
            vi.add(len(self.E))
            self.E.append(self.Z)
        while (abs(self.A - self.Z) > 0):
            Z = 0
            self.P = 0
            ct = 0
            for i, e in enumerate(self.E):
                U = (e // self.Q)
                D = abs(U - self.Z)
                if (D < self.D_max):
                    Z += (float(U) / (self.K ** float(D)))
                    self.P += (e - (U * self.Q))
                    vi.add(i)
                    ct += 1
            den = float(max(1, ct))
            self.A = self.Z
            self.Z = round(Z / den)
            self.P = round(self.P / den)
        diff = min(abs(self.Z - (e // self.Q)) for e in self.E)
        if (diff > 0): self.E.append(((self.Z * self.Q) + I))
        for a in vi: self.E[a] += (float(I - (self.E[a] - ((self.E[a] // self.Q) * self.Q))) / float(self.Q - 1))
        ###-forgetting!!!
        em = (float(abs(I - self.P)) / float(self.Q - 1))
        print(f"EM {self.mi}: {(em * 100.0):.2f}%")
oracle = Oracle()
oracle.update()