import random
import sys
class Oracle:
    def __init__(self):
        self.max_int = (sys.maxsize - 1000)
        self.min_int = -(self.max_int - 1)
        self.H = 3#---------------------------------------------------------------------------------------------------------------HP
        self.m_dim = 128#---------------------------------------------------------------------------------------------------------HP
        self.emp_target_min = 0.05#-----------------------------------------------------------------------------------------------HP
        self.emp_target_max = 0.95#-----------------------------------------------------------------------------------------------HP
        self.ppcL = (self.m_dim - 1)
        self.ppcR = (self.m_dim - 2)
        self.ds_range_set = {a for a in range(self.m_dim)}
        self.ds_range_set.remove(self.ppcL)
        self.ds_range_set.remove(self.ppcR)
        self.ds_index = 0
        ds_card_pct = 0.20#-------------------------------------------------------------------------------------------------------HP
        self.ds_card = round(float(len(self.ds_range_set)) * ds_card_pct)
        self.ds_dim = 10#---------------------------------------------------------------------------------------------------------HP
        self.ds = [set(random.sample(list(self.ds_range_set), self.ds_card)) for _ in range(self.ds_dim)]
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        while (True):
            for a in self.m: a.update()
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.mi = mi_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.fb_mode = 1#---------------------------------------------------------------------------------------------------------HP
        self.context_dim = 3#-----------------------------------------------------------------------------------------------------HP
        self.iv = self.pv = self.pev = self.Av = self.Bv = self.ppc_v = set()
        self.avec = ([0] * self.po.m_dim * self.context_dim)
        self.e = {a:self.avec.copy() for a in range(self.po.m_dim)}
        max_cv = (self.po.max_int // len(self.avec))
        self.cv_delta_mag = 1000.0#-100000.0--------------------------------------------------------------------------------------HP
        max_cv_range = (max_cv // round(self.cv_delta_mag))
        self.cv_max = min(10000, max_cv_range)#-1000000---------------------------------------------------------------------------HP
        self.cv_min = -(self.cv_max - 1)
        self.conf_norm = float(self.cv_max - 1)
        self.agency = False
        self.beh = self.em = self.em_prev = self.em_delta = 0
        self.emp_target = self.po.emp_target_min
        self.beh_data = dict()
        self.beh_data_history = 100#----------------------------------------------------------------------------------------------HP
        self.beh_data_pv = 100#---------------------------------------------------------------------------------------------------HP
    def update(self):
        #____________________________________________________________________________________________________________________________________________
        if (self.fb_mode == 0): fbv = self.po.m[self.fbi].pv.copy() if (self.fbi != 0) else set()
        if (self.fb_mode == 1): fbv = self.po.m[self.fbi].pv.copy()
        if (self.context_dim == 3): cv = (self.iv | {(a + self.po.m_dim) for a in self.pv} | {(a + (self.po.m_dim * 2)) for a in fbv})
        if (self.context_dim == 2): cv = (self.iv | {(a + self.po.m_dim) for a in fbv})
        #____________________________________________________________________________________________________________________________________________
        self.Bv = cv.copy()
        while (len(self.Av ^ self.Bv) > 0):
            avg_v = self.avec.copy()
            r_init = max([sum(self.e[a][b] for b in self.Bv) for a in self.e.keys()])
            r = r_init
            vi = set()
            num_samples = 3#---------------------------------------------------------------------------------------------------------HP
            num_attempts = 0
            num_attempts_max = 100#-if this is too low, it will struggle to converge-------------------------------------------------HP
            while ((r > 0) and (len(vi) < num_samples) and (num_attempts < num_attempts_max)):
                for a in self.e.keys():
                    if ((len(vi) < num_samples) and (a not in vi) and (sum(self.e[a][b] for b in self.Bv) == r)):
                        # for b in self.Bv: avg_v[b] += (float(self.e[a][b]) / (2.0 ** float(r_init - r)))
                        for b in self.Bv: avg_v[b] += self.e[a][b]
                        vi.add(a)
                r -= 1
                num_attempts += 1
            self.Av = self.Bv.copy()
            if (len(vi) > 0): self.Bv = {a for a in self.Bv if (round(float(avg_v[a]) / float(len(vi))) > 0)}
        diff = len(cv ^ self.Bv)
        cv = self.Bv.copy()
        #____________________________________________________________________________________________________________________________________________
        self.pv = {a for a in self.e.keys() if (sum(self.e[a][b] for b in cv) > 0)}
        if (self.ffi == -1):
            self.beh = 0
            if ((self.po.ppcL in self.pv) and (self.po.ppcR not in self.pv)): self.beh += -1
            if ((self.po.ppcR in self.pv) and (self.po.ppcL not in self.pv)): self.beh += 1
            self.agency = (self.beh != 0)
            if ((not self.agency) and (self.em_delta == 0) and (random.randrange(1000000) < 100000)): self.beh = random.choice([-1, 1])
            self.ppc_v = set()
            if (self.beh == -1): self.ppc_v.add(self.po.ppcL)
            if (self.beh == 1): self.ppc_v.add(self.po.ppcR)
            self.po.ds_index = ((self.po.ds_index + len(self.po.ds) + self.beh) % len(self.po.ds))
            self.iv = self.po.ds[self.po.ds_index].copy()
            self.iv |= self.ppc_v
        else: self.iv = self.po.m[self.ffi].pev.copy()
        #____________________________________________________________________________________________________________________________________________
        self.pev = (self.iv ^ self.pv)
        if ((self.emp_target == self.po.emp_target_min) and (self.em <= self.po.emp_target_min)): self.emp_target = self.po.emp_target_max
        if ((self.emp_target == self.po.emp_target_max) and (self.em >= self.po.emp_target_max)): self.emp_target = self.po.emp_target_min
        self.em_prev = self.em
        self.em = (float(len(self.pev)) / float(max(1, (len(self.iv) + len(self.pv)))))
        self.em_delta = (self.em - self.em_prev)
        #____________________________________________________________________________________________________________________________________________
        failed_pev = (self.iv - self.pv)
        for a in failed_pev:
            for b in cv:
                delta = round((1.0 - self.comp_conf(self.e[a][b])) * self.cv_delta_mag)
                if (delta > 0): self.e[a][b] = min((self.e[a][b] + delta), self.cv_max)
        false_pev = (self.pv - self.iv)
        for a in false_pev:
            for b in cv:
                delta = round((1.0 - self.comp_conf(self.e[a][b])) * self.cv_delta_mag)
                if (delta > 0): self.e[a][b] = max((self.e[a][b] - delta), self.cv_min)
        #___________________________________________________________________________________________________________________________________________
        if (self.agency and (len(self.ppc_v) > 0)):
        # if (len(self.ppc_v) > 0):
            if (((self.em_delta > 0) and (self.em < self.emp_target)) or ((self.em_delta < 0) and (self.em > self.emp_target))):
                if (self.po.ppcL in self.ppc_v):
                    for b in cv:
                        delta = round((1.0 - self.comp_conf(self.e[self.po.ppcL][b])) * self.cv_delta_mag)
                        if (delta > 0): self.e[self.po.ppcL][b] = min((self.e[self.po.ppcL][b] + delta), self.cv_max)
                if (self.po.ppcR in self.ppc_v):
                    for b in cv:
                        delta = round((1.0 - self.comp_conf(self.e[self.po.ppcR][b])) * self.cv_delta_mag)
                        if (delta > 0): self.e[self.po.ppcR][b] = min((self.e[self.po.ppcR][b] + delta), self.cv_max)
            if (((self.em_delta <= 0) and (self.em < self.emp_target)) or ((self.em_delta >= 0) and (self.em > self.emp_target))):
                if (self.po.ppcL in self.ppc_v):
                    for b in cv:
                        delta = round((1.0 - self.comp_conf(self.e[self.po.ppcL][b])) * self.cv_delta_mag)
                        if (delta > 0): self.e[self.po.ppcL][b] = max((self.e[self.po.ppcL][b] - delta), self.cv_min)
                if (self.po.ppcR in self.ppc_v):
                    for b in cv:
                        delta = round((1.0 - self.comp_conf(self.e[self.po.ppcR][b])) * self.cv_delta_mag)
                        if (delta > 0): self.e[self.po.ppcR][b] = max((self.e[self.po.ppcR][b] - delta), self.cv_min)
        #____________________________________________________________________________________________________________________________________________
        agency_str = f"\tAG: {self.beh}" if (self.agency) else ""
        mb_str = f"\tMB: {self.beh}" if ((self.beh != 0) and (not self.agency)) else ""
        print(f"M{self.mi}:\tEM: {(self.em * 100.0):.2f}%\tDF: {diff}" + agency_str + mb_str)
    def comp_conf(self, val_in):
        if (val_in > 0): return (float(val_in - 1) / self.conf_norm)
        else: return (float(abs(val_in)) / self.conf_norm)
oracle = Oracle()
oracle.update()