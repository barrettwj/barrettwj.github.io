import random
import sys
# import Bing_Chat_Interface_Trial_1
class Oracle:
    def __init__(self):
        self.H = 3#-----------------------------------------------------------------------------------------HP
        self.M = 103#-53-------------------------------------------------------------------------------------HP
        self.K = 67#-97-------------------------------------------------------------------------------------HP
        self.adc_max = 67#-37------------------------------------------------------------------------------HP
        self.adc_min = round(self.adc_max * 0.85)
        self.cy = 0
        self.max_int = sys.maxsize
        start_idx = 0
        ##############################################################################################################
        self.tsp_dim_pct = 0.40#-0.30-----------------------------------------------------------------------HP
        self.tsp_dim = round(self.K * self.tsp_dim_pct)
        ts_dim = 5#-----------------------------------------------------------------------------------------HP
        self.iv_mask = {(start_idx + a) for a in range(self.K)}
        start_idx += len(self.iv_mask)
        self.iv_map = {a:frozenset(random.sample(list(self.iv_mask), self.tsp_dim)) for a in range(ts_dim)}
        self.bv_mask = {(start_idx + a) for a in range(self.K)}
        start_idx += len(self.bv_mask)
        self.bv_map_adc_max = 200#--------------------------------------------------------------------------HP
        self.bv_map_dim_max = (ts_dim - 1)
        self.bv_map = dict()
        ##############################################################################################################
        em_start_idx = start_idx
        self.em_mask = {(em_start_idx + a) for a in range(self.K)}
        start_idx += len(self.em_mask)
        em_val_card = 13#-must be >= 2-----------------------------------------------------------------------HP
        em_num_vals = (self.K - em_val_card + 1)
        em_interval = (1.0 / (em_num_vals - 1))
        self.em_map = {(a * em_interval):frozenset((em_start_idx + a + b)
                                                   for b in range(em_val_card)) for a in range(em_num_vals)}
        ##############################################################################################################
        self.novel_chars_max = 500#-------------------------------------------------------------------------------HP
        self.novel_chars = dict()
        self.aff_response_start_idx = start_idx
        self.aff_response_char_dim_max = (2 ** 14)#---------------------------------------------------------------HP
        start_idx += (self.novel_chars_max * self.aff_response_char_dim_max)
        ##############################################################################################################
        self.aff_sugg_prompt_start_idx = start_idx
        self.aff_sugg_prompt_char_dim_max = (2 ** 9)#-------------------------------------------------------------HP
        start_idx += (self.novel_chars_max * self.aff_sugg_prompt_char_dim_max)
        ##############################################################################################################
        self.eff_prompt_start_idx = start_idx
        self.eff_prompt_char_dim_max = (2 ** 11)#-----------------------------------------------------------------HP
        start_idx += (self.novel_chars_max * self.eff_prompt_char_dim_max)
        ##############################################################################################################
        self.matrix_dim = start_idx
        self.matrix_dim_offset = (self.matrix_dim * self.M)
        # print(self.max_int)
        # print(self.matrix_dim_offset)
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while True:
            for a in self.m: a.update()
            self.cy += 1
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.MV = self.po.M
        self.iv = self.ov = self.av = set()
        self.e = dict()
        self.em = self.em_prev = self.em_delta_abs = self.forget_period_ct = 0
        self.forget_period = 3#->=1----------------------------------------------------------------------------HP
    def update(self):
        fbv = self.po.m[self.fbi].av.copy()
        fbvm = {(a // self.MV):{-(b + 1) for b in (set(range(((a // self.MV) * self.MV),
                                                               (((a // self.MV) + 1) * self.MV))) & fbv)} for a in fbv}
        ##############################################################################################################
        cv = self.av.copy()
        cv |= {(self.po.matrix_dim_offset + a) for a in self.iv}#------------------------------------------CAUSES ISSUES!!!???
        acts = dict()
        for a in self.e.keys():
            tv = cv.copy()
            cli = (a // self.MV)
            if cli in fbvm: tv |= fbvm[cli]
            acts[a] = (len(self.e[a].keys() ^ tv) / max(1, (len(self.e[a]) + len(tv))))
        le = len(acts)
        self.ov = set()
        vi = dict()
        alpha = 3#-musn't be too large!!!--------------------------------------------------------------------------HP
        if le > 0:
            mu = (sum(acts.values()) / le)
            # vari = (sum(((v - mu) ** 2) for v in acts.values()) / le)#----?????
            vari = (sum(((v - mu) ** 2) for v in acts.values()) / (le - 1))#----?????
            sigma = (vari ** (1 / 2))
            # thresh = max(0, (mu - (sigma * alpha)))#----?????
            thresh = (mu - (sigma * alpha))#----?????
            elite = [(k, v) for k, v in acts.items() if (v <= thresh)]
            rs = random.sample(range(len(elite)), len(elite))
            aks = [a[0] for a in sorted(elite, key=lambda x: (x[1], rs.pop()))]
            for a in aks:
                cli = (a // self.MV)
                if cli in vi:
                    vi[cli][1].add(a)
                    #########################################
                    if cli in fbvm:
                        rel_v = fbvm[cli]
                        if a in self.e:
                            for b in rel_v: self.e[a][b] = random.randrange(self.po.adc_min, self.po.adc_max)
                        else: self.e[a] = {b:random.randrange(self.po.adc_min, self.po.adc_max) for b in rel_v}
                    if cli not in self.ov: self.ov.add(cli)
                    #########################################
                else: vi[cli] = [a, set()]
        nav = {v[0] for v in vi.values()}
        self.em_prev = self.em
        self.em = sum((len(v[1]) / (self.MV - 1)) for v in vi.values())
        em_norm = len(vi)
        mr = (self.em / max(1, em_norm))
        ##############################################################################################################
        if self.ffi == -1:
            bv = {a for a in nav if ((a // self.MV) in self.po.bv_mask)}
            data = [((len(k ^ bv) / max(1, (len(k) + len(bv)))), k, v[0]) for k, v in self.po.bv_map.items()]
            rs = random.sample(range(len(data)), len(data))
            bv_sorted = sorted(data, key=lambda x: (x[0], rs.pop()))
            d = 1
            bv_found = set()
            bv_idx = 0
            if bv_sorted: d, bv_found, bv_idx = bv_sorted.pop(0)
            if d > 0.0001: bv = bv_found.copy()#-----------------------------------------------------------------HP
            fs = frozenset(bv.copy())
            if fs not in self.po.bv_map: self.po.bv_map[fs] = [bv_idx, self.po.bv_map_adc_max]
            # print(f"D: {d:.2f}")
            while len(self.po.bv_map) > self.po.bv_map_dim_max:
                rs = random.sample(list(self.po.bv_map.keys()), len(self.po.bv_map))
                for a in rs:
                    if (self.po.bv_map[a][1] > 0): self.po.bv_map[a][1] -= 1
                    else:
                        del self.po.bv_map[a]
                        break
            self.iv = {a for a in self.po.iv_map[bv_idx]}
            self.iv |= {a for a in fs}
            ##########################################
            data = [(abs(k - self.em_delta_abs), v) for k, v in self.po.em_map.items()]
            rs = random.sample(range(len(data)), len(data))
            em_sorted = sorted(data, key=lambda x: (x[0], rs.pop()))
            self.iv |= em_sorted[0][1]
            ##########################################
        else: self.iv = self.po.m[self.ffi].ov.copy()
        ###########################################################################################################
        zr = 0
        self.av = set()
        pv_ack = set()
        for a in self.iv:
            ci = set(range((a * self.MV), ((a + 1) * self.MV)))
            ovl = (ci & nav)
            if len(ovl) == 0:
                self.em += 1
                zr += 1
                cav = (ci - self.e.keys())
                if not cav:
                    tl = (ci & self.e.keys())
                    data = [(sum(self.e[b][c] for c in self.e[b].keys()), b) for b in tl]
                    rs = random.sample(range(len(data)), len(data))
                    tls = sorted(data, key=lambda x: (x[0], rs.pop()))
                    del self.e[tls[0][1]]
                    cav = (ci - self.e.keys())
                wi = random.choice(list(cav))
                #########################################
                if a in fbvm:
                    rel_v = fbvm[a]
                    if wi in self.e:
                        for b in rel_v: self.e[wi][b] = random.randrange(self.po.adc_min, self.po.adc_max)
                    else: self.e[wi] = {b:random.randrange(self.po.adc_min, self.po.adc_max) for b in rel_v}
                self.ov.add(a)
                #########################################
            else:
                pv_ack |= ovl
                wi = ovl.pop()
            if wi in self.e:
                for b in cv: self.e[wi][b] = random.randrange(self.po.adc_min, self.po.adc_max)
            else: self.e[wi] = {b:random.randrange(self.po.adc_min, self.po.adc_max) for b in cv}
            self.av.add(wi)
        self.em /= max(1, (em_norm + len(self.iv)))
        zr /= max(1, len(self.iv))
        self.em_delta_abs = abs(self.em - self.em_prev)
        pv_ex = (nav - pv_ack)
        ###########################################
        for a in pv_ex:
            cli = (a // self.MV)
            if cli in fbvm:
                rel_v = fbvm[cli]
                if a in self.e:
                    for b in rel_v: self.e[a][b] = random.randrange(self.po.adc_min, self.po.adc_max)
                else: self.e[a] = {b:random.randrange(self.po.adc_min, self.po.adc_max) for b in rel_v}
            self.ov.add(cli)
        ###########################################
        ##############################################################################################################
        self.forget_period_ct += 1
        if self.forget_period_ct == self.forget_period:
            #"""
            tl = list(self.e.keys())
            for a in tl:
                # if len(self.e[a]) > 20:#---------------------------------------------------------------------HP
                self.e[a] = {k:(v - 1) for k, v in self.e[a].items() if (v > 0)}
                if not self.e[a]: del self.e[a]
            #"""
            self.forget_period_ct = 0
        ##############################################################################################################
        bv_string = f"  BVID: {bv_idx:2d}" if self.ffi == -1 else ""
        print(f"M{(self.ffi + 1)}  EM: {self.em:.2f}  EMDA: {self.em_delta_abs:.2f}" +
        f"  ES: {len(self.e):6d}  PV: {len(self.av):4d}  ZR: {zr:.2f}  MR: {mr:.2f}  PVEX: {len(pv_ex):4d}" +
        f"  BVL: {len(self.po.bv_map):2d}" + bv_string)
oracle = Oracle()
oracle.update()
