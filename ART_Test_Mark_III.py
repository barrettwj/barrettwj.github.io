import random
################################################################################################################################
N = 128#-----------------------------------------------------------------------------------------------------HP
M = 50#------------------------------------------------------------------------------------------------------HP
mem_max_dim = 200#-------------------------------------------------------------------------------------------HP
mem_min_dim = 3#---------------------------------------------------------------------------------------------HP
mem_potential_idcs = set(range(mem_max_dim))
max_val = 128#-----------------------------------------------------------------------------------------------HP
# min_val = -(max_val - 1)#------------------------------------------------------------------------------------HP
min_val = 0
abs_delta_range = (max_val - min_val)
delta_thresh_pct = 0.005#-must be smaller than thresh????----------------------------------------------------HP
delta_thresh = (abs_delta_range * delta_thresh_pct)
max_delta = (abs_delta_range * N)
thresh = 0.008#-0.009----------------------------------------------------------------------------------------HP
adc_max = 1000000000#----------------------------------------------------------------------------------------HP
forget_period = 10
forget_period_ct = 0
rsA = random.sample(range(mem_max_dim), mem_max_dim)
mem = dict()
mk = mk_p = mkt = mkt_p = -1
cy = exp = 0
################################################################################################################################
ts_dim = 5#-------------------------------------------------------------------------------------------------HP
ts = [[random.randint(min_val, max_val) for _ in range(N)] for _ in range(ts_dim)]
# ts = []
# min_dist = 0.30
# while (len(ts) < ts_dim):
#     rv = [random.randint(min_val, max_val) for _ in range(N)]
#     flag = False
#     for a in ts:
#         dist = sum((abs(x - y) / max_delta) for x, y in zip(a, rv))
#         if (dist < min_dist):
#             flag = True
#             break
#     if not flag: ts.append(rv.copy())
ts_idx = 0
################################################################################################################################
act_v_prev = {k:0 for k in range(ts_dim)}
act_v = dict()
avg_diff = 0
act_hist_depth = 7
act_hist = []
while True:
    exiv = ts[ts_idx].copy()
    ############################################################################################################################
    for v in mem.values():
        if (v[1][0] < adc_max): v[1][0] += 1
    ############################################################################################################################
    mem_dim_def = (mem_min_dim - len(mem))
    if (mem_dim_def > 0):
        for _ in range(mem_dim_def):
            avail_idcs = (mem_potential_idcs - mem.keys())
            mem[random.choice(list(avail_idcs))] = [([0] * N), [0, 0], dict()]
    ############################################################################################################################
    mem_dim_exc = (len(mem) - mem_max_dim + 5)#---------------------------------------------------------------HP
    if (mem_dim_exc > 0):
        for _ in range(mem_dim_exc):
            dC = [(k, v[1][1]) for k, v in mem.items()]
            rs = rsA.copy()
            dsC = sorted(dC, key = lambda x: (x[1], rs.pop(0)), reverse = True)
            if (dsC[0][1] > 1): del mem[dsC[0][0]]
    ############################################################################################################################
    mk_prev = mk
    A = {k:sum((abs(x - y) / max_delta) for x, y in zip(exiv, v[0])) for k, v in mem.items()}
    B = {kA:(vA + sum((1 - vB) for kB, vB in A.items() if (kB != kA))) for kA, vA in A.items()}
    norm = len(B)
    dA = [(k, (v / norm)) for k, v in B.items()]
    rs = rsA.copy()
    dsA = sorted(dA, key = lambda x: (x[1], rs.pop(0)))
    mk, mv = dsA[0][0], dsA[0][1]
    ############################################################################################################################
    skip = dict()
    skip_order = dict()
    novum = False
    rA = rB = rC = rD = 0
    while (mv > thresh):
        mem[mk][1][1] = mem[mk][1][0]
        mem[mk][1][0] = 0
        skip[mk] = (1 - A[mk])
        skip_order[mk] = len(skip_order)
        disinh = sum(skip.values())
        dB = [(k, ((v - disinh) / norm)) for k, v in B.items() if (k not in skip.keys())]
        ld = len(dB)
        if (ld == 0):
            rA += 1
            avail_idcs = (mem_potential_idcs - mem.keys())
            mk, mv = random.choice(list(avail_idcs)), 0
            mem[mk] = [exiv.copy(), [0, 0], dict()]
            novum = True
            break
        if (ld == 1):
            rB += 1
            mk, mv = dB[0][0], dB[0][1]
        if (ld > 1):
            rC += 1
            rs = rsA.copy()
            dsB = sorted(dB, key = lambda x: (x[1], rs.pop(0)))
            mk, mv = dsB[0][0], dsB[0][1]
    #############################################################################################################################
    if not novum:
        mem[mk][1][1] = mem[mk][1][0]
        mem[mk][1][0] = 0
        for i, a in enumerate(exiv):
            delta_vector_A = (a - mem[mk][0][i])
            abs_delta_vector_A = abs(delta_vector_A)
            delta_vector_A_pct_mag = (abs_delta_vector_A / abs_delta_range)
            if (abs_delta_vector_A > 0.0001):#----------------------------------------------------------------------HP
                mem[mk][0][i] += (delta_vector_A * 0.001)#----------------------------------------------------------HP
                delta_vector_A = (a - mem[mk][0][i])
                abs_delta_vector_A = abs(delta_vector_A)
                delta_vector_A_pct_mag = (abs_delta_vector_A / abs_delta_range)
            for b in skip.keys():
                delta_vector_B = (mem[b][0][i] - a)
                abs_delta_vector_B = abs(delta_vector_B)
                delta_vector_B_pct_mag = (abs_delta_vector_B / abs_delta_range)
                diff = ((delta_vector_A_pct_mag + 0.01) - delta_vector_B_pct_mag)#------------------------------------HP
                if (diff > 0.0001):#-----------------------------------------------------------------------------------HP
                    signum_B = (delta_vector_B / max(1, abs_delta_vector_B))
                    val_B = (mem[b][0][i] + (signum_B * diff * (skip_order[b] + 1) * 500.0))#------------------------HP
                    if val_B < min_val: val_B = min_val
                    if val_B > max_val: val_B = max_val
                    mem[b][0][i] = val_B
    #############################################################################################################################
    pes = " F"
    # if (avg_diff == 1):
    for kA, vA in mem.items():
        td = vA[2].copy()
        for kB, vB in vA[2].items():
            if ((vB == mkt) and ((kA != mk) or (kB != mkt_p))): del td[kB]#-----------necessary???-----helpful???
        mem[kA][2] = td.copy()
    if (mkt_p not in mem[mk][2]):
        idx_range = set(range((mk * M), ((mk + 1) * M)))
        avail_idx = (idx_range - mem[mk][2].keys())
        new_idx = random.choice(list(avail_idx)) if (avail_idx) else random.choice(list(idx_range))
        mem[mk][2][new_idx] = mkt
        mkt = new_idx
        rD += 1
    else:
        mkt = mkt_p
        pes = "T  "
    mkt_p = -1
    for kA, vA in mem.items():
        p_set = {kB for kB, vB in vA[2].items() if (vB == mkt)}
        if (p_set):
            mkt_p = p_set.pop()
            for a in p_set: del mem[kA][2][a]#-----------------------------necessary?????----helpful?????
    #############################################################################################################################
    if ts_idx not in act_v: act_v[ts_idx] = mk
    else:
        act_hist.append((act_v.copy(), act_v_prev.copy()))
        act_v_prev = act_v.copy()
        act_v = dict()
        if (len(act_hist) == act_hist_depth):
            avg_diff = 0
            for i, a in enumerate(act_hist):
                diff = (sum(1 for k, v in a[0].items() if (v == a[1][k])) / len(a[0]))
                avg_diff += diff
            avg_diff /= len(act_hist)
            act_hist = []
    #############################################################################################################################
    avg_tcd = sum(len(v[2]) for v in mem.values())
    avg_tcd /= len(mem)
    #############################################################################################################################
    print(f"ID: {str(ts_idx).rjust(3)}  MK: {str(mk).rjust(4)}  MV: {str(f'{mv:.4f}').rjust(5)}  ML: {str(len(mem)).rjust(4)}" + 
        f"  DF: {str(f'{avg_diff:.2f}').rjust(4)}  SK: {str(len(skip)).rjust(3)}  PE: {pes.rjust(3)}  PV: {str(mkt_p).rjust(4)}" +
        f"  RA: {str(rA).rjust(3)}  RB: {str(rB).rjust(3)}  RC: {str(rC).rjust(3)}  RD: {str(rD).rjust(3)}" +
        f"  ATCD: {str(f'{avg_tcd:.2f}').rjust(3)}  EXP: {str(exp).rjust(3)}")
    #############################################################################################################################
    forget_period_ct += 1
    if (forget_period_ct == forget_period):
        dC = [(k, v[1][1]) for k, v in mem.items()]
        rs = rsA.copy()
        dsC = sorted(dC, key = lambda x: (x[1], rs.pop(0)), reverse = True)
        if (dsC[0][1] > 1): del mem[dsC[0][0]]
        forget_period_ct = 0
    #############################################################################################################################
    ts_idx = ((ts_idx + 1) % len(ts))
    if (ts_idx == 0): exp += 1
    cy += 1