import random
class Oracle:
    def __init__(self):
        self.H = 6#---------------------------------------------------------------------------------------------HP
        self.N = 512#-------------------------------------------------------------------------------------------HP
        self.M_pct = 0.25#--------------------------------------------------------------------------------------HP
        self.M = round(self.N * self.M_pct)
        self.A = 0.02#------------------------------------------------------------------------------------------HP
        self.av = set(random.sample(range(self.N), self.M))
        self.r = [Res(self, a) for a in range(self.H)]
        self.cy = 0
    def update(self):
        while True:
            for a in self.r: self.av = a.update(self.av, self.A, self.M)
            self.cy += 1
class Res:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.mi = mi_in
        self.blank_dv = ([0] * self.po.N)
        self.num_gen_A = 0
        self.num_gen_B = 0
        self.mem = dict()
        self.acts = []
        self.adc_mult = 2#-------------------------------------------------------------------------------------HP
        self.rp_max = 10#--------------------------------------------------------------------------------------HP
        self.mem_cap = 500#------------------------------------------------------------------------------------HP
    def update(self, v_in, alpha_in, sdim_in):
        self.acts = self.generate_activations_A(v_in.copy(), alpha_in, sdim_in)
        print(f"R:{str(self.mi).rjust(2)}  GA:{str(self.num_gen_A).rjust(4)}  GB:{str(self.num_gen_B).rjust(3)}" +
              f"  MEM:{str(len(self.mem)).rjust(4)}")
        return {a[0] for a in self.acts}
    def generate_activations_A(self, v_in, alpha_in, sdim_in):
        out = []
        self.num_gen_A = self.num_gen_B = na = 0
        if (len(self.mem) > self.mem_cap):
            self.mem = {k:[v[0], v[1], v[2], (v[3] - 1)] for k, v in self.mem.items() if (v[3] > 0)}
        while ((len(out) < sdim_in) and (na < sdim_in)):
            p = dict()
            for k, v in self.mem.items():
                if (v[2] > 0): self.mem[k] = [v[0], v[1], (v[2] - 1), v[3]]
                else: p[k] = (len(k ^ v_in) / max(1, (len(k) + len(v_in))))
            p_inh = {kA:(vA + sum((1 - vB) for kB, vB in p.items() if (kB != kA))) for kA, vA in p.items()}
            inh_val = 0
            beta = (alpha_in + 1)
            while ((len(out) < sdim_in) and (len(p_inh) > 0)):
                d = [(k, (v - inh_val)) for k, v in p_inh.items()]
                rs = random.sample(range(len(d)), len(d))
                ds = sorted(d, key = lambda x: (x[1], rs.pop()))
                beta = (ds[0][1] / len(p))
                if (beta <= alpha_in):
                    wk = ds[0][0].copy()
                    diff_v = (v_in ^ ds[0][0])
                    if len(diff_v) > 0:#-----------------------------------------------------------------------HP
                        ri = random.choice(list(diff_v))
                        wkA = set(ds[0][0])
                        wkA.remove(ri) if (ri in wkA) else wkA.add(ri)
                        wk = frozenset(wkA)
                        self.mem[wk] = self.mem[ds[0][0]].copy()
                        self.num_gen_A += 1
                        del self.mem[ds[0][0]]
                    self.mem[wk][2] = self.mem[wk][1]
                    self.mem[wk][3] = (self.adc_mult * self.mem[wk][1])
                    out.append([wk.copy(), beta])
                    break
                del p_inh[ds[0][0]]
                inh_val += (1 - p[ds[0][0]])
            if ((len(out) < sdim_in) and (beta > alpha_in)):
                wk = frozenset(v_in.copy())
                if wk not in self.mem.keys():
                    rval = random.choice(range(self.rp_max))
                    self.mem[wk] = [self.blank_dv.copy(), rval, rval, (self.adc_mult * rval)]
                    self.num_gen_B += 1
                    out.append([wk.copy(), 0])
                else: break
            na += 1
        return out.copy()
oracle = Oracle()
oracle.update()