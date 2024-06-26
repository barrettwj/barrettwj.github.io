import random
"""
import sys
import os
# cookies found as "chats?bundleVersion=X.Y.Z" under "Network" tab of developer tools (right-click and Inspect in Bing chat box).
# Copy everything after "Cookie:" Request Header
with open('Copilot Cookies.txt', 'r') as file: os.environ["BING_COOKIES"] = file.read()
import asyncio
from sydney import SydneyClient
from sydney.exceptions import (ConversationLimitException,
                               NoConnectionException,
                               NoResponseException,
                               ThrottledRequestException,
                               CaptchaChallengeException,
                               )
"""
class Oracle:
    def __init__(self):
        self.H = 3#-----------------------------------------------------------------------------------------HP
        self.M = 53#-53-------------------------------------------------------------------------------------HP
        self.K = 97#-97-------------------------------------------------------------------------------------HP
        self.adc_max = 47#-37------------------------------------------------------------------------------HP
        self.adc_min = round(self.adc_max * 0.85)
        self.cy = 0
        # self.max_int = sys.maxsize# = 2^63 = 9.223372037E18
        start_idx = 0
        ##############################################################################################################
        self.tsp_dim_pct = 0.30#-0.30-----------------------------------------------------------------------HP
        self.tsp_dim = round(self.K * self.tsp_dim_pct)
        ts_dim = 3#-----------------------------------------------------------------------------------------HP
        self.iv_mask = {(start_idx + a) for a in range(self.K)}
        start_idx += len(self.iv_mask)
        self.bv_mask = {(start_idx + a) for a in range(self.K)}
        start_idx += len(self.bv_mask)
        self.iv_bv_map = {frozenset(random.sample(list(self.iv_mask), self.tsp_dim)):
                          frozenset(random.sample(list(self.bv_mask), self.tsp_dim)) for _ in range(ts_dim)}
        ##############################################################################################################
        em_start_idx = start_idx
        self.em_mask = {(em_start_idx + a) for a in range(self.K)}
        start_idx += len(self.em_mask)
        em_val_card = 7#-must be >= 2-----------------------------------------------------------------------HP
        em_num_vals = (self.K - em_val_card + 1)
        em_interval = (1.0 / (em_num_vals - 1))
        self.em_map = {(a * em_interval):frozenset((em_start_idx + a + b)
                                                   for b in range(em_val_card)) for a in range(em_num_vals)}
        """
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
        """
        ##############################################################################################################
        self.matrix_dim = start_idx
        self.matrix_dim_offset = (self.matrix_dim * self.M)
        self.m = [Matrix(self, a) for a in range(self.H)]
    def update(self):
        # asyncio.run(self.sydney_interaction("What is the tallest building?"))
        while True:
            for a in self.m: a.update()
            self.cy += 1
    """
    async def sydney_interaction(self, prompt_in = "", set_style = "precise", reset_conv = False):
        out = []
        async with SydneyClient(style=set_style) as sydney:# style= "balanced", "precise", "creative"
            if reset_conv: await sydney.reset_conversation()
            try:
                # print("Sydney: ", end="", flush=True)
                response, suggested_responses = await sydney.ask(prompt_in, suggestions=True, citations=False)
                # print(response, end="", flush=True)
                # print("\n")
                out.append(response)
                for a in suggested_responses: out.append(a)
                # if suggested_responses:
                #     print("Suggested Responses: ", end="", flush=True)
                #     print(suggested_responses, end="", flush=True)
                # print("\n")
            except ConversationLimitException:
                await sydney.reset_conversation()
                # asyncio.run(self.sydney_interaction(prompt_in))
            except CaptchaChallengeException:
                print("Captcha Exception!")
                # asyncio.run(self.sydney_interaction(prompt_in))
        print(out)
        return out
    """
class Matrix:
    def __init__(self, po_in, mi_in):
        self.po = po_in
        self.ffi = (mi_in - 1)
        self.fbi = ((mi_in + 1) % self.po.H)
        self.MV = self.po.M
        self.iv = self.ov = self.av = set()
        self.fbvm = dict()
        self.e = dict()
        self.em = self.em_prev = self.em_delta_abs = self.forget_period_ct = 0
        self.forget_period = 3#->=1----------------------------------------------------------------------------HP
        self.bv_list = []
    def update(self):
        fbv = self.po.m[self.fbi].av.copy()
        # fbv = self.po.m[self.fbi].av.copy() if (self.fbi != 0) else set()
        self.fbvm = {(a // self.MV):-(a + 1) for a in fbv}
        ##############################################################################################################
        cv = self.av.copy()
        cv |= {(self.po.matrix_dim_offset + (a * self.MV)) for a in self.iv}#------------------------------------------CAUSES ISSUES!!!???
        acts = dict()
        for a in self.e.keys():
            tv = cv.copy()
            cli = (a // self.MV)
            if cli in self.fbvm: tv.add(self.fbvm[cli])
            acts[a] = (len(self.e[a].keys() ^ tv) / max(1, (len(self.e[a]) + len(tv))))
        le = len(acts)
        self.ov = set()
        vi = dict()
        alpha = 1#-musn't be too large!!!--------------------------------------------------------------------------HP
        if le > 0:
            mu = (sum(acts.values()) / le)
            vari = (sum(((v - mu) ** 2) for v in acts.values()) / le)#----?????
            sigma = (vari ** (1 / 2))
            thresh = max(0, (mu - (sigma * alpha)))
            elite = [(k, v) for k, v in acts.items() if (v <= thresh)]
            rs = random.sample(range(len(elite)), len(elite))
            aks = [a[0] for a in sorted(elite, key=lambda x: (x[1], rs.pop()))]
            for a in aks:
                cli = (a // self.MV)
                if cli in vi:
                    vi[cli][1].add(a)
                    #########################################
                    if cli in self.fbvm:
                        if a in self.e: self.e[a][self.fbvm[cli]] = random.randrange(self.po.adc_min, self.po.adc_max)
                        else: self.e[a] = {self.fbvm[cli]:random.randrange(self.po.adc_min, self.po.adc_max)}
                    if cli not in self.ov: self.ov.add(cli)
                    #########################################
                else: vi[cli] = [a, set()]
        pv = {v[0] for v in vi.values()}
        self.em_prev = self.em
        self.em = sum((len(v[1]) / (self.MV - 1)) for v in vi.values())
        em_norm = len(vi)
        mr = (self.em / max(1, em_norm))
        ##############################################################################################################
        if self.ffi == -1:
            bv = {(a // self.MV) for a in pv if ((a // self.MV) in self.po.bv_mask)}
            data = [((len(v ^ bv) / max(1, (len(v) + len(bv)))), k, v) for k, v in self.po.iv_bv_map.items()]
            rs = random.sample(range(len(data)), len(data))
            bv_sorted = sorted(data, key=lambda x: (x[0], rs.pop()))
            d, iv_found, bv_found = bv_sorted.pop(0)
            bv_idx = self.bv_list.index(bv_found) if (bv_found in self.bv_list) else -1
            if bv_idx == -1:
                bv_idx = len(self.bv_list)
                self.bv_list.append(bv_found)
            self.iv = {a for a in iv_found}
            self.iv |= {a for a in bv_found}
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
            ovl = (ci & pv)
            if len(ovl) == 0:
                self.em += 1
                zr += 1
                if ((self.ffi != -1) and (a in self.po.m[self.ffi].fbvm)):
                    wi = -(self.po.m[self.ffi].fbvm[a] + 1)#----------------------helpful??????
                else:
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
                if a in self.fbvm:
                    if wi in self.e: self.e[wi][self.fbvm[a]] = random.randrange(self.po.adc_min, self.po.adc_max)
                    else: self.e[wi] = {self.fbvm[a]:random.randrange(self.po.adc_min, self.po.adc_max)}
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
        pv_ex = (pv - pv_ack)
        ###########################################
        for a in pv_ex:
            cli = (a // self.MV)
            if cli in self.fbvm:
                if a in self.e: self.e[a][self.fbvm[cli]] = random.randrange(self.po.adc_min, self.po.adc_max)
                else: self.e[a] = {self.fbvm[cli]:random.randrange(self.po.adc_min, self.po.adc_max)}
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
        bv_string = f"  BVL: {len(self.bv_list):2d}  BVID: {bv_idx:2d}" if self.ffi == -1 else ""
        print(f"M{(self.ffi + 1)}  EM: {self.em:.2f}  EMDA: {self.em_delta_abs:.2f}" +
        f"  ES: {len(self.e):6d}  PV: {len(self.av):4d}  ZR: {zr:.2f}  MR: {mr:.2f}  PVEX: {len(pv_ex):4d}" + bv_string)
oracle = Oracle()
oracle.update()
