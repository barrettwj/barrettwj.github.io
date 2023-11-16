import random
# import math
class Oracle:
    def __init__(self):
        self.H = 6#---------------------------------------------------------------------------------------HP
        self.d = 10#-should be a multiple of 10-----------------------------------------------------------HP
        # self.r = (round(math.log(self.d) / math.log(10)) + 1)
        self.ds_dim = 10#-should be >= self.d-------------------------------------------------------------HP
        self.ds = [random.randrange(self.d) for _ in range(self.ds_dim)]
        self.ds_index = 0
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while (True):
            for a in self.m: a.update()
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.mi = mi_in
        self.E = dict()
        self.I = self.P = self.PE = self.Z = self.innovation = 0
        self.M = 5000#-----------------------------------------------------------------------------------HP
        self.avail_indices = {a for a in range(self.M)}
        self.K = 1.20#-----------------------------------------------------------------------------------HP
        self.r_max = 30#-Is this helpful or necessary????????-----------------------------------------HP
        self.s_max = 500#-------------------------------------------------------------------------------HP
        self.Q = round(self.po.d ** 2)
        self.vi = set()
    def update(self):
        # FB = self.po.m[((self.mi + 1) % self.po.H)].P
        FB = self.po.m[((self.mi + 1) % self.po.H)].P if (self.mi < (self.po.H - 1)) else 0
        self.Z = ((self.I * self.Q) + FB)
        self.vi = set()
        self.P = 0
        if (self.Z > 0):
            poss_indices = (self.avail_indices - set(self.E.keys()))
            if (len(poss_indices) > 0): self.E[random.choice(list(poss_indices))] = [(self.Z * self.Q), self.s_max]
            si = [a for a in self.E.keys()]
            random.shuffle(si)
            Z = ct = 0
            for a in si:
                U = (self.E[a][0] // self.Q)
                D = abs(U - self.Z)
                if (D < self.r_max):
                    Z += (float(U) / (self.K ** float(D)))
                    # Z += (float(U) / float(D + 1))
                    self.P += (self.E[a][0] - (U * self.Q))
                    self.E[a][1] = self.s_max
                    self.vi.add(a)
                    ct += 1
            # Z = r = ct = 0
            # si = [a for a in range(len(self.E))]
            # random.shuffle(si)
            # while ((len(si) > 0) and (r < self.r_max)):
            #     for b in si:
            #         U = (self.E[b] // self.Q)
            #         D = abs(U - self.Z)
            #         if (D == r):
            #             Z += (float(U) / (self.K ** float(D)))
            #             # Z += (float(U) / float(D + 1))
            #             self.P += (self.E[b] - (U * self.Q))
            #             self.S[b] = self.S_max
            #             self.vi.add(b)
            #             ct += 1
            #     si = [c for c in si if (c not in self.vi)]
            #     r += 1
            norm = float(max(1, ct))
            self.Z = round(Z / norm)
            self.P = round(float(self.P) / norm)
            self.innovation = round(min(abs(self.Z - (a[0] // self.Q)) for a in self.E.values()))
            if (self.innovation > 0):
                poss_indices = (self.avail_indices - set(self.E.keys()))
                if (len(poss_indices) > 0): self.E[random.choice(list(poss_indices))] = [(self.Z * self.Q), self.s_max]
        if (self.mi == 0):
            B = (self.P - ((self.P // self.po.d) * self.po.d))
            # B = 1
            # self.po.ds_index = ((self.po.ds_index + 1) % len(self.po.ds))
            self.po.ds_index = B
            # self.po.ds_index = (B % len(self.po.ds))
            # index_delta = B
            # index_delta = (-round(float(len(self.po.ds)) / 2.0) + B)
            # self.po.ds_index = ((self.po.ds_index + len(self.po.ds) + index_delta) % len(self.po.ds))
            self.I = ((self.po.ds[self.po.ds_index] * self.po.d) + B)
        else: self.I = self.po.m[(self.mi - 1)].PE
        self.PE = abs(self.I - self.P)
        em = (float(self.PE) / float(self.Q - 1))
        # for a in self.vi: self.E[a][0] += round((float(self.I - (self.E[a][0] - ((self.E[a][0] // self.Q) * self.Q))) / float(self.Q - 1)) * 5.0)#---------HP
        for a in self.vi:
            error = (self.I - (self.E[a][0] - ((self.E[a][0] // self.Q) * self.Q)))
            conf = (float(abs(error)) / float(self.Q - 1))
            delta = round((1.0 - conf) * float(error))
            self.E[a][0] += delta
        while ((len(self.E.keys()) + 2) > self.M):
            for a in self.E.keys():
                if (self.E[a][1] > 0): self.E[a][1] -= 1
            min_val = min(a[1] for a in self.E.values())
            indices = [key for key, value in self.E.items() if (value[1] == min_val)]
            random.shuffle(indices)
            while (((len(self.E.keys()) + 2) > self.M) and (len(indices) > 0)):
                ind = indices.pop()
                del self.E[ind]
        print(f"EM {self.mi}: {(em * 100.0):.2f}%\tINN: {self.innovation}\tP: {self.P}")
        # print(self.E)
oracle = Oracle()
oracle.update()