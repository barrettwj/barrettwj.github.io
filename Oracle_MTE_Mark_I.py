import random
import heapq
class Oracle:
    def __init__(self):
        self.H = 6#-------------------------------------------------------------------------HP
        self.N = 128#-----------------------------------------------------------------------HP
        self.M = 4#-because 4**N == 2**2N
        K_pct = 0.47#-----------------------------------------------------------------------HP
        self.K = round(self.N * K_pct)
        self.N_range = range(self.N)
        self.N_range_ext = range(self.N, self.N * 2)
        ts_dim = 7
        self.ts = [set(random.sample(self.N_range, self.K)) for _ in range(ts_dim)]
        self.m = [Matrix(self, a) for a in range(self.H)]
        self.cy = 0
    def update(self):
        while True:
            for a in self.m: a.update()
            self.cy += 1
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = mi_in - 1
        self.fbi = (mi_in + 1) % self.po.H
        self.M_ril = [a for a in range(self.po.M)]
        self.adc_max = 1000000#-------------------------------------------------------------HP
        self.e = [[[set(), 0, 0] for _ in range(self.po.M)]] * self.po.N
        self.pvcl = set()
        self.cv = set()
        self.fb_alt = set()
        # self.fb_alt = set(random.sample(self.po.N_range, self.po.K))
        self.ts_idx = 0
    def update(self):
        ##################################################################################################################
        for a in self.e:
            for b in a:
                if b[1] < self.adc_max: b[1] += 1
        ##################################################################################################################
        if self.ffi == -1:
            ffcl = self.po.ts[self.ts_idx].copy()
            self.ts_idx = (self.ts_idx + 1) % len(self.po.ts)
        else: ffcl = self.po.m[self.ffi].pvcl
        ##################################################################################################################
        for a in ffcl & self.pvcl:
            for b in self.e[a]:
                if b[2] == -1:
                    b[1] = 0
                    b[2] = 0
        ##################################################################################################################
        self.pvcl = ffcl - self.pvcl
        ##################################################################################################################
        em = len(self.pvcl) / self.po.N
        avg = 0
        for a in self.e: avg += sum(b[1] / self.adc_max for b in a) / len(a)
        avg /= len(self.e)
        print(f"M{self.ffi + 1} EM: {f'{em:.3f}'.rjust(5)} ADCAVG: {f'{avg:.4f}'.rjust(6)}")
        ##################################################################################################################
        for a in self.pvcl:
            random.shuffle(self.M_ril)
            for b in self.M_ril:
                if self.e[a][b][1] > 5000:#-------------------------------------------------HP
                    self.e[a][b][0] = self.cv.copy()
                    self.e[a][b][1] = 4000#-------------------------------------------------HP
                    break
        ##################################################################################################################
        fbcl = self.fb_alt.copy() if self.fbi == 0 else self.po.m[self.fbi].pvcl.copy()
        self.pvcl ^= fbcl
        ##################################################################################################################
        self.cv = {(a - self.po.N) for a in self.cv if a in self.po.N_range_ext}
        self.cv |= {(a + self.po.N) for a in ffcl}
        ##################################################################################################################
        thresh = 0.90#-----------------------------------------------------------------------HP
        for i, a in enumerate(self.e):
            d = [((len(b[0] & self.cv) / max(1, len(b[0] | self.cv))), j) for j, b in enumerate(a)]#-Jaccard Index
            heapq.heapify(d)
            d = sorted(d, key = lambda x: x[0], reverse = True)
            if d[0][0] >= thresh:
                self.pvcl.add(i)
                a[d[0][1]][2] = -1
        ##################################################################################################################
oracle = Oracle()
oracle.update()