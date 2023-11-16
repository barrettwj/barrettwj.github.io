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
            for a in self.m: a.update()
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.mi = mi_in
        self.E = []
        self.I = self.P = self.PE = self.A = self.Z = 0
        self.M = 1000#-----------------------------------------------------------------------------------HP
        self.K = 1.05#-----------------------------------------------------------------------------------HP
        self.D_max = 10000#-Is this helpful or necessary????????-----------------------------------------HP
        self.S_max = 1000#-------------------------------------------------------------------------------HP
        self.S = [self.S_max] * self.M
        self.Q = (self.po.d ** 2)
    def update(self):
        # FB = self.po.m[((self.mi + 1) % self.po.H)].P
        FB = self.po.m[((self.mi + 1) % self.po.H)].P if (self.mi < (self.po.H - 1)) else 0
        self.Z = ((self.I * self.Q) + FB)
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
                    self.S[i] = self.S_max
                    vi.add(i)
                    ct += 1
            den = float(max(1, ct))
            self.A = self.Z
            self.Z = round(Z / den)
            self.P = round(self.P / den)
        diff = min(abs(self.Z - (e // self.Q)) for e in self.E)
        if (diff > 0):
            vi.add(len(self.E))
            self.E.append(((self.Z * self.Q) + self.I))
        if (self.mi == 0):
            beh = (self.P - ((self.P // self.po.d) * self.po.d))
            # self.po.ds_index = beh
            index_delta = (-round(float(len(self.po.ds)) / 2) + beh)
            self.po.ds_index = ((self.po.ds_index + len(self.po.ds) + index_delta) % len(self.po.ds))
            # self.po.ds_index = ((self.po.ds_index + len(self.po.ds) + beh) % len(self.po.ds))
            self.I = ((self.po.ds[self.po.ds_index] * self.po.d) + beh)
        else: self.I = self.po.m[(self.mi - 1)].PE
        self.PE = abs(self.I - self.P)
        em = (float(self.PE) / float(self.Q - 1))
        for a in vi: self.E[a] += (float(self.I - (self.E[a] - ((self.E[a] // self.Q) * self.Q))) / float(self.Q - 1))
        # while ((len(self.E) + 1) > self.M):
        #     min_val = min(s for s in self.S)
        #     indices = [i for i in range(len(self.E)) if ((i not in vi) and (self.S[i] == min_val))]
        #     random.shuffle(indices)
        #     remove_indices = set()
        #     while (((len(self.E) + 1) > self.M) and (len(indices) > 0)):
        #         ind = indices.pop()
        #         remove_indices.add(ind)
        print(f"EM {self.mi}: {(em * 100.0):.2f}%")
oracle = Oracle()
oracle.update()