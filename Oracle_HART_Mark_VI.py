import random
class Oracle:
    def __init__(self):
        self.H = 1#---------------------------------------------------------------------------------------HP
        self.N = 16#------------------------------------------------------------------------------------HP
        self.N_range = range(self.N)
        self.max_val = 128
        self.min_val = -128
        self.val_range = range(self.min_val, (self.max_val + 1))
        ts_dim = 7#--------------------------------------------------------------------------------------HP
        self.ts = [[random.choice(list(self.val_range)) for _ in self.N_range] for _ in range(ts_dim)]
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
        self.mem_fb = Memory(self.po.N, self.po.min_val, self.po.max_val)
        self.mem_im = Memory(self.po.N, self.po.min_val, self.po.max_val)
        self.mem_ff = Memory(self.po.N, self.po.min_val, self.po.max_val)
        self.mem_map = Memory(self.po.N, self.po.min_val, self.po.max_val)
        self.mmi = 0
        self.mmi_map = dict()
        self.ev = [0 for _ in self.po.N_range]
        self.pv = [0 for _ in self.po.N_range]
        # self.fb_alt = [random.random() for _ in self.po.N_range]
        self.fb_alt = [0 for _ in self.po.N_range]
        self.ts_idx = 0
    def update(self):
        fb = self.fb_alt.copy() if self.fbi == 0 else self.po.m[self.fbi].pv.copy()
        if self.ffi == -1:
            ff = self.po.ts[self.ts_idx].copy()
            self.ts_idx = (self.ts_idx + 1) % len(self.po.ts)
        else: ff = self.po.m[self.ffi].pv.copy()
        self.mmi_map[self.mmi] = ff.copy()
        # self.ev = [(((y - x) + 2) / 4) for x, y in zip(self.pv, ff)]
        self.ev = [abs(y - x) for x, y in zip(self.pv, ff)]
        # pe = sum(abs(a) for a in self.ev) / len(self.ev)
        pe = sum(self.ev) / len(self.ev)
        thresh_out = 0.06#-------------------------------------------------------------------------------------HP
        # fbi = self.mem_fb.generate_inference(fb, thresh_out)
        # imi = self.mem_im.generate_inference(self.pv, thresh_out)
        ffi = self.mem_ff.generate_inference(ff, thresh_out)
        # self.mmi = self.mem_map.generate_inference([fbi, imi, ffi], thresh_out)
        # self.mmi = self.mem_map.generate_inference([imi], thresh_out)
        # self.mmi = self.mem_map.generate_inference([fbi, ffi], thresh_out)
        # if self.mmi in self.mmi_map: self.pv = self.mmi_map[self.mmi].copy()
        self.pv = [0 for _ in self.po.N_range]
        # print(f"M{self.ffi + 1}  PE:{f'{pe:.2f}'.rjust(5)}")
class Memory:
    def __init__(self, N_in, min_val_in, max_val_in):
        self.mem = dict()
        self.mem_cap = 12#-------------------------------------------------------------------------------------HP
        self.adc_max = 1000#------------------------------------------------------------------------------------HP
        self.N = N_in
        self.min_val = min_val_in
        self.max_val = max_val_in
        self.abs_delta_max = self.max_val - self.min_val
        self.delta_norm = self.abs_delta_max * self.N
        self.adapt = True
    def generate_inference(self, v_in, thr_in):
        if len(self.mem) == 0: self.mem = {0:[0, [0 for _ in range(self.N)]]}
        avg_adc = 0
        for v in self.mem.values():
            if v[0] < self.adc_max: v[0] += 1
            avg_adc += v[0] / self.adc_max
        avg_adc /= len(self.mem)
        mem_exc = len(self.mem) - self.mem_cap
        for _ in range(mem_exc):
            eidx = max([(k, v[0]) for k, v in self.mem.items()], key = lambda x: (x[1], x[0]))[0]
            del self.mem[eidx]
        v_in_t = v_in.copy()
        for i, a in enumerate(v_in_t):
            if a < self.min_val: v_in[i] = self.min_val
            if a > self.max_val: v_in[i] = self.max_val
        z = {k:(sum(abs(x - y) for x, y in zip(v_in, v[1])) / self.delta_norm) for k, v in self.mem.items()}
        ziv = {k:(1 - v) for k, v in z.items()}
        norm = len(z)
        zi = {kA:(vA + sum(vB for kB, vB in ziv.items() if kB != kA)) for kA, vA in z.items()}
        mv, mk = min([((v / norm), k) for k, v in zi.items()])
        cA = cB = cC = 0
        while (len(zi) > 1) and (mv > thr_in):
            # self.mem[mk][0] = 0
            di_val = ziv[mk]
            zi = {k:(v - di_val) for k, v in zi.items() if k != mk}
            mv, mk = min([((v / norm), k) for k, v in zi.items()])
            cA += 1
        if self.adapt and (mv <= thr_in):
            self.mem[mk][0] = 0
            # err_thresh = thr_in * 0.09#----------------------------------------------------------------HP
            err_thresh = 0.001
            eta = 0.50#-------------------------------------------------------------------------------------HP
            error = 0
            abs_error = 0
            tl = []
            for x, y in zip(self.mem[mk][1], v_in):
                diff = (y - x)
                error += diff
                abs_diff = abs(diff)
                abs_error += abs_diff
                if abs_diff > err_thresh: tl.append(x + (diff * eta))
                else: tl.append(x)
                # else: tl.append(y)
            self.mem[mk][1] = tl.copy()
            # print(f"{abs_error:.5f}")
            cB += 1
        mvpr = mv
        if mv > thr_in:
            # self.mem[mk][0] = 0
            mk = self.generate_available_key()
            self.mem[mk] = [0, v_in.copy()]
            mv = thr_in
            cC += 1
        print(f"MK: {str(mk).rjust(4)}  MV: {f'{mvpr:.2f}'.rjust(4)}  ML: {str(len(self.mem)).rjust(3)}  cA: {str(cA).rjust(3)}" +
              f"  cB: {cB}  cC: {cC}  ADA: {f'{avg_adc:.2f}'.rjust(4)}")
        return mk
    def generate_available_key(self):
        out = 0
        sign = -1
        ct = 0
        while out in self.mem:
            ct += 1
            sign = -sign
            out += sign * ct
        return out
oracle = Oracle()
oracle.update()