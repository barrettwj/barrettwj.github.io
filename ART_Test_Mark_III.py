import random
################################################################################################################################
N = 128#-----------------------------------------------------------------------------------------------------HP
M = 50#------------------------------------------------------------------------------------------------------HP
mem_max_dim = 200#-------------------------------------------------------------------------------------------HP
mem_min_dim = 3#---------------------------------------------------------------------------------------------HP
mem_potential_idcs = set(range(mem_max_dim))
max_val = 7#-----------------------------------------------------------------------------------------------HP
min_val = -(max_val - 1)#------------------------------------------------------------------------------------HP
# min_val = 0
abs_delta_range = (max_val - min_val)
max_delta = (abs_delta_range * N)
blank_v = ([(min_val + (abs_delta_range / 2))] * N)
thresh = 0.01#-0.008-----------------------------------------------------------------------------------------HP
adc_max = 1000000000#----------------------------------------------------------------------------------------HP
forget_period = 10
forget_period_ct = 0
rsA = random.sample(range(mem_max_dim), mem_max_dim)
mem = dict()
mk = mk_p = mkt = mkt_p = -1
cy = exp = 0
################################################################################################################################
ts_idx = 0
ts_dim = 5#-------------------------------------------------------------------------------------------------HP
##############################################################################
ts = [[random.randint(min_val, max_val) for _ in range(N)] for _ in range(ts_dim)]
##############################################################################
# rv = [random.randint(min_val, max_val) for _ in range(N)]
# ts = [rv.copy() for _ in range(ts_dim)]
##############################################################################
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
################################################################################################################################
act_v_prev = {k:0 for k in range(ts_dim)}
act_v = dict()
avg_dist = 0
act_hist_depth = 13
act_hist = []
################################################################################################################################
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
            mem[random.choice(list(avail_idcs))] = [blank_v.copy(), [0, 0], dict()]
    ############################################################################################################################
    mem_dim_exc = (len(mem) - mem_max_dim + 5)#---------------------------------------------------------------HP
    if (mem_dim_exc > 0):
        for _ in range(mem_dim_exc):
            dC = [(k, v[1][1]) for k, v in mem.items()]
            rs = rsA.copy()
            dsC = sorted(dC, key = lambda x: (x[1], rs.pop()), reverse = True)
            if (dsC[0][1] > 1): del mem[dsC[0][0]]#----------------------------------------------------------------HP
    ############################################################################################################################
    mk_prev = mk
    A = {k:sum((abs(x - y) / max_delta) for x, y in zip(exiv, v[0])) for k, v in mem.items()}
    B = {kA:(vA + sum((1 - vB) for kB, vB in A.items() if (kB != kA))) for kA, vA in A.items()}
    norm = len(B)
    dA = [(k, (v / norm)) for k, v in B.items()]
    rs = rsA.copy()
    dsA = sorted(dA, key = lambda x: (x[1], rs.pop()))
    mk, mv = dsA[0][0], dsA[0][1]
    ############################################################################################################################
    skip = dict()
    rA = rB = rC = rD = 0
    while ((len(dA) > 0) and (mv > thresh)):
        mem[mk][1][1] = mem[mk][1][0]
        mem[mk][1][0] = 0
        skip[mk] = (1 - A[mk])
        disinh = sum(skip.values())
        dA = [(k, ((v - disinh) / norm)) for k, v in B.items() if (k not in skip.keys())]
        ld = len(dA)
        if (ld == 0):
            rA += 1
            avail_idcs = (mem_potential_idcs - mem.keys())
            mk, mv = random.choice(list(avail_idcs)), 0
            mem[mk] = [exiv.copy(), [0, 0], dict()]
        if (ld == 1):
            rB += 1
            mk, mv = dA[0][0], dA[0][1]
        if (ld > 1):
            rC += 1
            rs = rsA.copy()
            dsA = sorted(dA, key = lambda x: (x[1], rs.pop()))
            mk, mv = dsA[0][0], dsA[0][1]
    #############################################################################################################################
    if (rA == 0):
        mem[mk][1][1] = mem[mk][1][0]
        mem[mk][1][0] = 0
        for i, a in enumerate(exiv):
            delta_vector_A = (a - mem[mk][0][i])
            abs_delta_vector_A = abs(delta_vector_A)
            if (abs_delta_vector_A > 0.00001):#-0.01---------------------------------------------------------------------HP
                mem[mk][0][i] += (delta_vector_A * 0.001)#-0.001---------------------------------------------------------HP
                delta_vector_A = (a - mem[mk][0][i])
                abs_delta_vector_A = abs(delta_vector_A)
            for b in skip.keys():
                delta_vector_B = (mem[b][0][i] - a)
                abs_delta_vector_B = abs(delta_vector_B)
                if (abs_delta_vector_B > 0):
                    diff = ((abs_delta_vector_A + 1) - abs_delta_vector_B)#-10----------------------------------------------HP
                    if (diff > 0):
                        signum_B = (delta_vector_B / max(1, abs_delta_vector_B))
                        val_B = (mem[b][0][i] + (signum_B * diff))
                        if val_B < min_val: val_B = min_val
                        if val_B > max_val: val_B = max_val
                        mem[b][0][i] = val_B
    #############################################################################################################################
    pes = " F"
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
    mk_p_set = set()
    for kA, vA in mem.items():
        mkt_p_set = {kB for kB, vB in vA[2].items() if (vB == mkt)}
        if (mkt_p_set):
            mk_p_set.add(kA)
            mkt_p = mkt_p_set.pop()
            if (mkt_p_set):
                #----------confidence/precision should be lowered proportional to the residual size of this set???!!!
                for a in mkt_p_set: del mem[kA][2][a]#-----------------------------necessary?????----helpful?????
    mk_p = mk_p_set.pop() if (mk_p_set) else -1
    #############################################################################################################################
    if ts_idx not in act_v: act_v[ts_idx] = mk
    else:
        act_hist.append((act_v.copy(), act_v_prev.copy()))
        act_v_prev = act_v.copy()
        act_v = {ts_idx:mk}
        if (len(act_hist) == act_hist_depth):
            avg_dist = (sum((sum(1 for k, v in a[0].items() if (v == a[1][k])) / len(a[0])) for a in act_hist) / len(act_hist))
            act_hist = []
    #############################################################################################################################
    avg_tcd = sum(len(v[2]) for v in mem.values())
    avg_tcd /= len(mem)
    #############################################################################################################################
    print(f"ID: {str(ts_idx).rjust(3)}  MK: {str(mk).rjust(4)}  MV: {str(f'{mv:.4f}').rjust(5)}  ML: {str(len(mem)).rjust(4)}" + 
        f"  DF: {str(f'{avg_dist:.2f}').rjust(4)}  SK: {str(len(skip)).rjust(3)}  PE: {pes.rjust(3)}  PV: {str(mk_p).rjust(4)}" +
        f"  RA: {str(rA).rjust(3)}  RB: {str(rB).rjust(3)}  RC: {str(rC).rjust(3)}  RD: {str(rD).rjust(3)}" +
        f"  ATCD: {str(f'{avg_tcd:.2f}').rjust(3)}  EXP: {str(exp).rjust(3)}")
    #############################################################################################################################
    forget_period_ct += 1
    if (forget_period_ct == forget_period):
        dC = [(k, v[1][1]) for k, v in mem.items()]
        rs = rsA.copy()
        dsC = sorted(dC, key = lambda x: (x[1], rs.pop()), reverse = True)
        if (dsC[0][1] > 100): del mem[dsC[0][0]]#-------------------------------------------------------------------------HP
        forget_period_ct = 0
    #############################################################################################################################
    ts_idx = ((ts_idx + 1) % len(ts))
    if (ts_idx == 0): exp += 1
    cy += 1