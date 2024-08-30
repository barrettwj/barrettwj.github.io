import random
################################################################################################################################
N = 64#------------------------------------------------------------------------------------------------------HP
M = 50#------------------------------------------------------------------------------------------------------HP
mem_max_dim = 100#-------------------------------------------------------------------------------------------HP
mem_min_dim = 3#---------------------------------------------------------------------------------------------HP
mem_potential_idcs = set(range(mem_max_dim))
max_val = mem_max_dim#---------------------------------------------------------------------------------------HP
min_val = 0
abs_delta_range = (max_val - min_val)
delta_thresh_pct = 0.005#------------------------------------------------------------------------------------HP
delta_thresh = (abs_delta_range * delta_thresh_pct)
max_delta = (abs_delta_range * N)
thresh = 0.008#-0.009----------------------------------------------------------------------------------------HP
adc_max = 1000#----------------------------------------------------------------------------------------------HP
forget_period = 1000
forget_period_ct = 0
rsA = random.sample(range(mem_max_dim), mem_max_dim)
mem = dict()
mk = mk_p = mkt = mkt_p = -1
cy = 0
################################################################################################################################
ts_dim = 29#-------------------------------------------------------------------------------------------------HP
ts = [[random.randint(min_val, max_val) for _ in range(N)] for _ in range(ts_dim)]
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
    mem_dim_def = (mem_min_dim - len(mem))
    if (mem_dim_def > 0):
        for _ in range(mem_dim_def):
            avail_idcs = (mem_potential_idcs - mem.keys())
            mem[random.choice(list(avail_idcs))] = [([0] * N), adc_max, dict()]
    ############################################################################################################################
    mem_dim_exc = (len(mem) - mem_max_dim + 5)#---------------------------------------------------------------HP
    if (mem_dim_exc > 0):
        for _ in range(mem_dim_exc):
            for k, v in mem.items():
                if (v[1] > 0): v[1] -= 1
            dC = [(k, v[1]) for k, v in mem.items()]
            rs = rsA.copy()
            dsC = sorted(dC, key = lambda x: (x[1], rs.pop(0)))
            if (dsC[0][1] < (adc_max - 1)): del mem[dsC[0][0]]
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
    novum = False
    rA = rB = rC = 0
    while (mv > thresh):
        mem[mk][1] = adc_max#-----------------necessary???----helpful???
        skip[mk] = (1 - A[mk])
        disinh = sum(skip.values())
        dB = [(k, ((v - disinh) / norm)) for k, v in B.items() if (k not in skip.keys())]
        ld = len(dB)
        if (ld == 0):
            rA += 1
            avail_idcs = (mem_potential_idcs - mem.keys())
            mk, mv = random.choice(list(avail_idcs)), 0
            mem[mk] = [exiv.copy(), adc_max, dict()]
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
        mem[mk][1] = adc_max
        multA = 0.01#--------------------------------------------------------------------------------------------HP
        # if (mk == pv): multA *= 10.0
        multB = (multA * 5.0)#-----------------------------------------------------------------------------------HP
        for i, a in enumerate(exiv):
            delta = (a - mem[mk][0][i])
            if (abs(delta) > delta_thresh):
                mem[mk][0][i] += (delta * multA)
                for b in skip:
                    val = (mem[b][0][i] + ((mem[b][0][i] - a) * multB))
                    if val < min_val: val = min_val
                    if val > max_val: val = max_val
                    mem[b][0][i] = val
    #############################################################################################################################
    # for kA, vA in mem.items():
    #     td = vA[2].copy()
    #     for kB, vB in vA[2].items():
    #         if ((vB == mkt) and ((kA != mk) or (kB != mkt_p))): del td[kB]#-----------necessary???-----helpful???
    #     mem[kA][2] = td.copy()
    pes = " F"        
    if (mkt_p not in mem[mk][2].keys()):
        idx_range = set(range((mk * M), ((mk + 1) * M)))
        avail_idx = (idx_range - mem[mk][2].keys())
        new_idx = random.choice(list(avail_idx)) if (avail_idx) else random.choice(list(idx_range))
        mem[mk][2][new_idx] = mkt
        mem[mk][1] = adc_max
        mkt = new_idx
    else:
        mkt = mkt_p
        pes = "T  "
    mkt_p = -1
    for kA, vA in mem.items():
        p_set = {kB for kB, vB in vA[2].items() if (vB == mkt)}
        if (p_set):
            mkt_p = p_set.pop()
            # for a in p_set: del mem[kA][2][a]#-----------------------------necessary?????----helpful?????
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
    # avg_size = sum(len(v[2]) for v in mem.values())
    # avg_size /= len(mem)
    # print(f"{avg_size:.2f}")
    print(f"ID: {str(ts_idx).rjust(3)}  MK: {str(mk).rjust(4)}  MV: {str(f'{mv:.4f}').rjust(5)}  ML: {str(len(mem)).rjust(4)}" + 
        f"  DF: {str(f'{avg_diff:.2f}').rjust(4)}  SK: {str(len(skip)).rjust(3)}  PE: {pes.rjust(3)}  PV: {str(mkt_p).rjust(4)}" +
        f"  RA: {str(rA).rjust(3)}  RB: {str(rB).rjust(3)}  RC: {str(rC).rjust(3)}")
    #############################################################################################################################
    # forget_period_ct += 1
    # if (forget_period_ct == forget_period):
    #     for k, v in mem.items():
    #         if (v[1] > 0): v[1] -= 1
    #     dC = [(k, v[1]) for k, v in mem.items()]
    #     rs = rsA.copy()
    #     dsC = sorted(dC, key = lambda x: (x[1], rs.pop(0)))
    #     if (dsC[0][1] < (adc_max - 1)): del mem[dsC[0][0]]
    #     forget_period_ct = 0
    #############################################################################################################################
    ts_idx = ((ts_idx + 1) % len(ts))
    cy += 1