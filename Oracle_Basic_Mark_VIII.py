import random
class Oracle:
    def __init__(self):
        ###################################################################
        self.H = 5#---------------------------------------------------------------------------------------------HP
        self.N = 8#---------------------------------------------------------------------------------------------HP
        self.K_pct = 0.60#--------------------------------------------------------------------------------------HP
        self.K = round(self.N * self.K_pct)
        ###################################################################
        self.eff_dim = 4
        self.effv_mask = set(range(self.eff_dim))
        self.effv_card = round(len(self.effv_mask) * self.K_pct)
        self.affv_mask = set(range(self.N)) - self.effv_mask
        self.affv_card = self.K - self.effv_card
        self.exv = set()
        self.bv_map_max = 2 ** len(self.effv_mask)
        self.bv_map = dict()
        ###################################################################
        self.cy = 0
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while True:
            for a in self.m: a.update()
            self.cy += 1
class Matrix:
    def __init__(self, po_in, mi_in):
        #####################################################
        self.po = po_in
        self.ffi = mi_in - 1
        self.fbi = (mi_in + 1) % self.po.H
        #####################################################
        self.pv = set()
        self.effv = set()
        self.affv = set()
        #####################################################
        self.em = 0
    def update(self):
        ###########################################################################################################################
        # fb = self.po.m[self.fbi].pv.copy() if self.fbi != 0 else {0, 2, 4}#-innate prior?
        fb = self.po.m[self.fbi].pv.copy() if self.fbi != 0 else set()#-degenerate prior?
        # fb = self.po.m[self.fbi].pv.copy() if self.fbi != 0 else self.po.exv.copy()#-resonance?
        ###########################################################################################################################
        if self.ffi == -1:
            #######################################################################################################
            self.em = (self.em / self.po.H)
            tl = [f"C: {self.po.cy:>{10}}", "".join('1' if x in self.po.exv else '0' for x in range(self.po.N))]
            tl.extend(["".join('1' if x in y.pv else '0' for x in range(self.po.N)) for y in self.po.m])
            tl.append(f"EM: {f'{self.em:.2f}'.rjust(4)}")
            tl.append(f"BL: {str(len(self.po.bv_map)).rjust(3)}")
            print(" | ".join(tl))
            self.em = 0
            #######################################################################################################
            # self.po.exv = self.po.exv ^ self.pv
            #######################################################################################################
            self.effv = self.pv & self.po.effv_mask
            effv_fs = frozenset(self.effv)
            if effv_fs in self.po.bv_map: self.po.exv = self.po.bv_map[effv_fs].copy()
            else:
                if len(self.po.bv_map) < self.po.bv_map_max:
                    na_max = 1000
                    na = 0
                    # nv = set(random.sample(list(self.po.affv_mask), self.po.affv_card))
                    if self.po.bv_map: nv = random.choice(list(self.po.bv_map.values())).copy()
                    else: nv = set(random.sample(list(self.po.affv_mask), self.po.affv_card))
                    while na < na_max and nv in self.po.bv_map.values():
                        # nv = set(random.sample(list(self.po.affv_mask), self.po.affv_card))
                        ri = random.choice(list(self.po.affv_mask))
                        if ri in nv: nv.remove(ri)
                        else: nv.add(ri)
                        na += 1
                    self.po.exv = nv.copy()
                    self.po.bv_map[effv_fs] = nv.copy()
            self.po.exv |= self.effv
            ####################################################################################################
            self.pv = (self.po.exv - self.pv) ^ fb
            ####################################################################################################
        else: self.pv = (self.po.m[self.ffi].pv - self.pv) ^ fb
        ##############################################################################################################################
        if self.pv == fb:
            self.em += 1
            ri = random.choice(list(self.po.effv_mask))
            if ri in self.pv: self.pv.remove(ri)
            else: self.pv.add(ri) 
        ###############################################################################################################################
oracle = Oracle()
oracle.update()