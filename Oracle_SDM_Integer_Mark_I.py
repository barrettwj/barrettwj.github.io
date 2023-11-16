import random
class Oracle:
    def __init__(self):
        self.H = 6#----------------------------------------------------------------------------------------HP
        self.d = 10#-should be a power of 10---------------------------------------------------------------HP
        self.ds_dim = 10#-should be >= self.d--------------------------------------------------------------HP
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
        self.M = 5000#--------------------------------------------------------------------------------------HP
        self.avail_indices = {a for a in range(self.M)}
        self.s_max = 500#-----------------------------------------------------------------------------------HP
        self.Q = round(self.po.d ** 2)
        self.vi = set()
    def vector(self, n_in, dim_in):
        n = n_in
        out = []
        while (n > 0):
            n, digit = divmod(n, 10)
            out.append(digit)
        while (len(out) < dim_in): out.append(0)
        return out.copy()
    def update(self):
        FB = self.po.m[((self.mi + 1) % self.po.H)].P
        # FB = self.po.m[((self.mi + 1) % self.po.H)].P if (self.mi < (self.po.H - 1)) else 0
        self.Z = ((self.I * self.Q) + FB)
        self.vi = set()
        self.P = 0
        #______________________________________________________________________________________________________________________________
        if (self.Z > 0):
            A = self.vector(self.Z, 4)
            self.Z = sum((a * (10 ** i)) for i, a in enumerate(A))
            poss_indices = (self.avail_indices - set(self.E.keys()))
            if (len(poss_indices) > 0): self.E[random.choice(list(poss_indices))] = [(self.Z * self.Q), self.s_max]
            si = [a for a in self.E.keys()]
            random.shuffle(si)
            Z = [0] * 4
            P = [0] * 2
            D_max = 9#-------------------------------------------------------------------------------------------------------------HP
            for a in si:
                U = (self.E[a][0] // self.Q)
                C = self.vector(U, 4)
                D = sum(abs(C[i] - b) for i, b in enumerate(A))
                if (D < D_max):
                    for i, b in enumerate(A): Z[i] += (float(C[i]) * (1.0 - (float(abs(C[i] - b)) / float(self.po.d - 1))))
                    Y = self.vector((self.E[a][0] - (U * self.Q)), 2)
                    for i, b in enumerate(Y): P[i] += float(b)
                    self.E[a][1] = self.s_max
                    self.vi.add(a)
            norm = float(max(1, len(self.vi)))
            Z = [round(a / norm) for a in Z]
            self.Z = sum((a * (10 ** i)) for i, a in enumerate(Z))
            P = [round(a / norm) for a in P]
            self.P = sum((a * (10 ** i)) for i, a in enumerate(P))
            #___________________________________________________________________________________________________________________
            diffs = []
            for a in self.E.values():
                C = self.vector((a[0] // self.Q), 4)
                diffs.append(sum(abs(b - Z[i]) for i, b in enumerate(C)))
            self.innovation = min(diffs)
            if (self.innovation > 0):
                poss_indices = (self.avail_indices - set(self.E.keys()))
                if (len(poss_indices) > 0): self.E[random.choice(list(poss_indices))] = [(self.Z * self.Q), self.s_max]
        #________________________________________________________________________________________________________________________
        if (self.mi == 0):
            B = (self.P - ((self.P // self.po.d) * self.po.d))
            # B = 1
            self.po.ds_index = B
            # self.po.ds_index = (B % len(self.po.ds))
            # index_delta = B
            # index_delta = (-round(float(len(self.po.ds)) / 2.0) + B)
            # self.po.ds_index = ((self.po.ds_index + len(self.po.ds) + index_delta) % len(self.po.ds))
            self.I = ((self.po.ds[self.po.ds_index] * self.po.d) + B)
        else: self.I = self.po.m[(self.mi - 1)].PE
        #_______________________________________________________________________________________________________________________
        IV = self.vector(self.I, 2)
        PV = self.vector(self.P, 2)
        PEV = [abs(IV[i] - a) for i, a in enumerate(PV)]
        self.PE = sum((a * (10 ** i)) for i, a in enumerate(PEV))
        em = (float(sum(PEV)) / float((self.po.d - 1) * 2))
        #______________________________________________________________________________________________________________________
        for a in self.vi:
            C = self.vector((self.E[a][0] - ((self.E[a][0] // self.Q) * self.Q)), 2)
            EV = [(IV[i] - a) for i, a in enumerate(C)]
            CV = [(float(abs(a)) / float(self.po.d - 1)) for i, a in enumerate(EV)]
            DV = [(C[i] + round((1.0 - a) * float(EV[i]))) for i, a in enumerate(CV)]
            val = sum((a * (10 ** i)) for i, a in enumerate(DV))
            self.E[a][0] = ((self.E[a][0] // self.Q) + val)
        #______________________________________________________________________________________________________________________
        while ((len(self.E.keys()) + 2) > self.M):
            for a in self.E.keys():
                if (self.E[a][1] > 0): self.E[a][1] -= 1
            min_val = min(a[1] for a in self.E.values())
            indices = [key for key, value in self.E.items() if (value[1] == min_val)]
            random.shuffle(indices)
            while (((len(self.E.keys()) + 2) > self.M) and (len(indices) > 0)):
                ind = indices.pop()
                del self.E[ind]
        #_______________________________________________________________________________________________________________________
        print(f"EM {self.mi}: {(em * 100.0):.2f}%\tINN: {self.innovation}\tP: {self.P}")
        # print(self.E)
oracle = Oracle()
oracle.update()