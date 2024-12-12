import random
################################################################################################################################
N = 16 * 3#-----------------------------------------------------------------------------------------------------HP
M = 50#------------------------------------------------------------------------------------------------------HP
mem_max_dim = 200#-------------------------------------------------------------------------------------------HP
mem_min_dim = 3#---------------------------------------------------------------------------------------------HP
mem_potential_idcs = set(range(mem_max_dim))
max_val = 1024#-----------------------------------------------------------------------------------------------HP
min_val = -max_val#------------------------------------------------------------------------------------------HP
abs_delta_range = (max_val - min_val)
max_delta = (abs_delta_range * N)
mid_val = (min_val + (abs_delta_range / 2))
blank_v = [mid_val] * N
thresh = 0.01#-0.01-----------------------------------------------------------------------------------------HP
adc_max = 1000000#----------------------------------------------------------------------------------------HP
forget_period = 10#------------------------------------------------------------------------------------------HP
forget_period_ct = 0
rsA = random.sample(range(mem_max_dim), mem_max_dim)#----------I need a better solution????
mem = dict()
mk = mk_p = mkt = mkt_p = -1
cy = exp = 0
################################################################################################################################
ts_idx = 0
ts_dim = 10#-------------------------------------------------------------------------------------------------HP
##############################################################################
ts = [[random.randint(min_val, max_val) for _ in range(N)] for _ in range(ts_dim)]
##############################################################################
# ts[-1] = ts[random.randrange(ts_dim - 1)].copy()
##############################################################################
# rv = [random.randint(min_val, max_val) for _ in range(N)]
# ts = [rv.copy() for _ in range(ts_dim)]
##############################################################################
# step = 42
# ts = []
# rv_prev = None
# for a in range(ts_dim):
#     rv = []
#     for b in range(N):
#         val = min_val + (a * step) + b
#         if val > max_val: val = min_val + (val - max_val - 1)
#         if val < min_val: val = max_val - (min_val - val - 1)
#         rv.append(val)
#     ts.append(rv.copy())
################################################################################################################################
act_v_prev = {k:0 for k in range(ts_dim)}
act_v = dict()
avg_corr = avg_dups = 0
act_hist_depth = 7
act_hist = []
################################################################################################################################
while True:
    ############################################################################################################################
    for v in mem.values():
        if (v[1][0] < adc_max): v[1][0] += 1
    ############################################################################################################################
    mem_dim_def = (mem_min_dim - len(mem))
    if (mem_dim_def > 0):
        for _ in range(mem_dim_def):
            avail_idcs = (mem_potential_idcs - mem.keys())
            mem[random.choice(list(avail_idcs))] = [blank_v.copy(), [0, 0], dict()]
    ############################################################################################################################
    mem_dim_exc = (len(mem) - mem_max_dim + 20)#---------------------------------------------------------------HP
    if (mem_dim_exc > 0):
        for _ in range(mem_dim_exc):
            rs = rsA.copy()
            mxk, mxv = max([(k, v[1][1]) for k, v in mem.items()], key = lambda x: (x[1], rs.pop()))
            if (mxv > 1): del mem[mxk]#-------------------------------------------------------------------------HP
    ############################################################################################################################
    exiv = ts[ts_idx].copy()
    A = {k:(sum(abs(x - y) for x, y in zip(exiv, v[0])) / max_delta) for k, v in mem.items()}
    B = [(kA, (vA + sum((1 - vB) for kB, vB in A.items() if (kB != kA)))) for kA, vA in A.items()]
    norm = len(A)
    thresh_mod = thresh * norm
    rs = rsA.copy()
    mk, mv = min(B, key = lambda x: (x[1], rs.pop()))
    ############################################################################################################################
    skip = set()
    rA = rB = rC = rD = 0
    while ((len(B) > 0) and (mv > thresh_mod)):
        mem[mk][1][1] = mem[mk][1][0]
        mem[mk][1][0] = 0
        skip.add(mk)
        B = [(a[0], (a[1] - (1 - A[mk]))) for a in B if (a[0] not in skip)]
        lb = len(B)
        if (lb == 0):
            rA += 1
            avail_idcs = (mem_potential_idcs - mem.keys())
            mk, mv = random.choice(list(avail_idcs)), 0
            mem[mk] = [exiv.copy(), [0, 0], dict()]
        if (lb == 1):
            rB += 1
            mk, mv = B[0][0], B[0][1]
        if (lb > 1):
            rC += 1
            rs = rsA.copy()
            mk, mv = min(B, key = lambda x: (x[1], rs.pop()))
    #############################################################################################################################
    if (rA == 0):
        sp = 150#-----------------------------------------------------------------------------------------------HP
        mem[mk][1][1] = mem[mk][1][0]
        mem[mk][1][0] = 0
        for i, a in enumerate(exiv):
            dvA = (a - mem[mk][0][i])#------------this is the error to be represented???
            abs_dvA = abs(dvA)
            if (abs_dvA > thresh):
                mem[mk][0][i] += (dvA * 0.001)#-0.001---------------------------------------------------------HP
                dvA = (a - mem[mk][0][i])
                abs_dvA = abs(dvA)
                for b in skip:
                    dvB = (a - mem[b][0][i])
                    abs_dvB = abs(dvB)
                    diff = (sp - (abs_dvB - abs_dvA))
                    if (diff > 0):
                        signB = 1 if abs(a - (mem[b][0][i] + 1)) > abs_dvB else -1
                        val_B = (mem[b][0][i] + (signB * diff))
                        if val_B < min_val: val_B = min_val
                        if val_B > max_val: val_B = max_val
                        mem[b][0][i] = val_B
    #############################################################################################################################
    if (mkt_p not in mem[mk][2]):#------------------------------------element level prediction error
        idx_range = set(range((mk * M), ((mk + 1) * M)))
        avail_idx = (idx_range - mem[mk][2].keys())
        new_idx = random.choice(list(avail_idx)) if (avail_idx) else random.choice(list(idx_range))
        mem[mk][2][new_idx] = mkt
        mkt = new_idx
        rD += 1
    else: mkt = mkt_p
    ######################################################################
    p_dict = {kA:{kB for kB, vB in vA[2].items() if (vB == mkt)} for kA, vA in mem.items() if (mkt in vA[2].values())}
    mk_p = set(p_dict.keys()).pop() if (len(p_dict) == 1) else -1
    mkt_p = p_dict[mk_p].pop() if (mk_p != -1) else -1
    pes = "T  " if (mkt_p != -1) else " F"
    #############################################################################################################################
    if ts_idx not in act_v: act_v[ts_idx] = mk
    else:
        act_hist.append((act_v.copy(), act_v_prev.copy()))
        act_v_prev = act_v.copy()
        act_v = {ts_idx:mk}
        if (len(act_hist) == act_hist_depth):
            avg_corr = (sum((sum(1 for k, v in a[0].items() if (v == a[1][k])) / len(a[0])) for a in act_hist) / len(act_hist))
            avg_dups = 0
            for a in act_hist:
                dups_dict = dict()
                for b in a[0].values():
                    if b in dups_dict: dups_dict[b] += 1
                    else: dups_dict[b] = 1
                avg_dups += sum(v - 1 for v in dups_dict.values() if v > 1) / len(a[0]) 
            avg_dups /= len(act_hist)
            act_hist = []
    #############################################################################################################################
    avg_tcd = sum(len(v[2]) for v in mem.values()) / len(mem)
    #############################################################################################################################
    print(" | ".join([
        f"ID:{str(ts_idx).rjust(3)}", f"MK:{str(mk).rjust(4)}", f"MV:{f'{mv / norm:.4f}'.rjust(7)}", f"ML:{str(len(mem)).rjust(3)}",
        f"CO:{f'{avg_corr:.2f}'.rjust(4)}", f"SK:{str(len(skip)).rjust(3)}", f"PE:{pes.rjust(3)}", f"PV:{str(mk_p).rjust(4)}",
        f"RA:{str(rA).rjust(3)}", f"RB:{str(rB).rjust(3)}", f"RC:{str(rC).rjust(3)}", f"RD:{str(rD).rjust(3)}",
        f"ATCD:{f'{avg_tcd:.2f}'.rjust(4)}", f"EXP:{str(exp).rjust(4)}", f"DU:{f'{avg_dups:.2f}'.rjust(4)}"
    ]))
    #############################################################################################################################
    # forget_period_ct += 1
    forget_period_ct = 0
    if (forget_period_ct == forget_period):
        rs = rsA.copy()
        mxk, mxv = max([(k, v[1][1]) for k, v in mem.items()], key = lambda x: (x[1], rs.pop()))
        if (mxv > 100): del mem[mxk]#-100------------------------------------------------------------------------------HP
        forget_period_ct = 0
    #############################################################################################################################
    ts_idx = ((ts_idx + 1) % len(ts))
    if (ts_idx == 0): exp += 1
    cy += 1