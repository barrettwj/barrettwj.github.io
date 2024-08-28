import random
N = 24#------------------------------------------------------------------------------------------------------HP
max_val = 200#-----------------------------------------------------------------------------------------------HP
min_val = 0
span = (max_val - min_val)
mem_cap = 200#-----------------------------------------------------------------------------------------------HP
mem_potential_idcs = set(range(mem_cap))
adc_max = 100000#--------------------------------------------------------------------------------------------HP
mem = dict()
max_delta = (span * N)
ts_dim = 3#--------------------------------------------------------------------------------------------------HP
ts = [[random.randint(min_val, max_val) for _ in range(N)] for _ in range(ts_dim)]
ts_idx = cy = avg_diff = diff = emv = rA = rB = rC = 0
thresh = 0.010#----------------------------------------------------------------------------------------------HP
delta_thresh = 10#-------------------------------------------------------------------------------------------HP
skip = dict()
act_v_prev = {k:0 for k in range(ts_dim)}
act_v = dict()
rsA = random.sample(range(mem_cap), mem_cap)
act_hist_depth = 100
act_hist = []
while True:
    exiv = ts[ts_idx].copy()
    mem_min_dim = 3#-----------------------------------------------------------------------------------------HP
    mem_dim_def = (mem_min_dim - len(mem))
    if (mem_dim_def > 0):
        for _ in range(mem_dim_def):
            avail_idcs = (mem_potential_idcs - mem.keys())
            mem[random.choice(list(avail_idcs))] = [([0] * N), adc_max]
    ###################################################################
    A = {k:sum((abs(x - y) / max_delta) for x, y in zip(exiv, v[0])) for k, v in mem.items()}
    B = {kA:(vA + sum((1 - vB) for kB, vB in A.items() if (kB != kA))) for kA, vA in A.items()}
    norm = len(B)
    dA = [(k, v) for k, v in B.items()]
    rs = rsA.copy()
    dsA = sorted(dA, key = lambda x: (x[1], rs.pop()))
    mk, mv = dsA[0][0], (dsA[0][1] / norm)
    ###################################################################
    skip = dict()
    novum = False
    rA = rB = rC = 0
    while (mv > thresh):
        mem[mk][1] = adc_max
        skip[mk] = (1 - A[mk])
        disinh = sum(skip.values())
        dB = [(k, (v - disinh)) for k, v in B.items() if (k not in skip.keys())]
        ld = len(dB)
        if (ld == 0):
            rA += 1
            avail_idcs = (mem_potential_idcs - mem.keys())
            mk, mv = random.choice(list(avail_idcs)), 0
            mem[mk] = [exiv.copy(), adc_max]
            novum = True
            break
        if (ld == 1):
            rB += 1
            mk, mv = dB[0][0], (dB[0][1] / norm)
        if (ld > 1):
            rC += 1
            rs = rsA.copy()
            dsB = sorted(dB, key = lambda x: (x[1], rs.pop()))
            mk, mv = dsB[0][0], (dsB[0][1] / norm)
    ################################################################
    if not novum:
        mem[mk][1] = adc_max
        for i, a in enumerate(exiv):
            delta = (a - mem[mk][0][i])
            if (abs(delta) > delta_thresh): mem[mk][0][i] = (mem[mk][0][i] + (delta * 0.10))#----------------------HP
            # if (abs(delta) < delta_thresh): mem[mk][0][i] = a
            # else: mem[mk][0][i] = (mem[mk][0][i] + (delta * 0.80))#------------------------------------------------HP
    ################################################################
    period_set = set()
    act_v[ts_idx] = mk
    if (len(act_v) == len(ts)):
        act_hist.append((act_v.copy(), act_v_prev.copy()))
        act_v_prev = act_v.copy()
        act_v = dict()
        if (len(act_hist) == act_hist_depth):
            avg_diff = 0
            for i, a in enumerate(act_hist):
                diff = (sum(1 for k, v in a[0].items() if (v == a[1][k])) / len(ts))
                if (diff > 0.90): period_set.add(i)
                avg_diff += diff
            avg_diff /= act_hist_depth
            act_hist = []
    # if (len(period_set) > 0): print(len(period_set))
    ################################################################
    print(f"ID: {str(ts_idx).rjust(3)}  MK: {str(mk).rjust(4)}  MV: {str(f'{mv:.4f}').rjust(5)}  ML: {str(len(mem)).rjust(4)}" + 
          f"  DF: {str(f'{avg_diff:.4f}').rjust(5)}  SK: {str(len(skip)).rjust(3)}" +
          f"  RA: {str(rA).rjust(3)}  RB: {str(rB).rjust(3)}  RC: {str(rC).rjust(3)}")
    ################################################################
    # if (len(mem) > -1):#---------------------------------------------------------------------------------------------HP
    #     for k, v in mem.items():
    #         if (v[1] > 0): mem[k][1] -= 1
    #     dC = [(k, v[1]) for k, v in mem.items()]
    #     rs = rsA.copy()
    #     dsC = sorted(dC, key = lambda x: (x[1], rs.pop()))
    #     del mem[dsC[0][0]]
    ts_idx = ((ts_idx + 1) % len(ts))
    cy += 1