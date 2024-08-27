import random
N = 64#------------------------------------------------------------------------------------------------------HP
max_val = 128#--------------------------------------------------------------------------------------------------HP
# min_val = -max_val
min_val = -(max_val - 1)
span = (max_val - min_val)
mem_cap = 200#--------------------------------------------------------------------------------------------------HP
mem_potential_idcs = set(range(mem_cap))
adc_max = 50#--------------------------------------------------------------------------------------------HP
mem = dict()
max_delta = (span * N)
ts_dim = 3#-----------------------------------------------------------------------------------------------HP
ts = [{k:random.randint(min_val, max_val) for k in range(N)} for _ in range(ts_dim)]
ts_idx = cy = 0
thresh_initial = 0.01#----------------------------------------------------------------------------------------HP
thresh = thresh_initial
distr_dim = 4#-------------------------------------------------------------------------------------------------HP
distr = []
pv = set()
iv = set()
blank_dv = ([0] * mem_cap)
em = 0
mem_dim_def = (3 - len(mem))#----------------------------------------------------------------------------------HP
if (mem_dim_def > 0):
    for _ in range(mem_dim_def):
        avail_idcs = (mem_potential_idcs - mem.keys())
        mem[random.choice(list(avail_idcs))] = [dict(), adc_max, blank_dv.copy()]
while True:
    cv = ts[ts_idx].copy()
    skip = dict()
    finished = False
    rate_A = rate_B = rate_C = 0
    # mem_dim_def = (10 - len(mem))#--------------------------------------------------------------------------HP
    # if (mem_dim_def > 0):
    #     for _ in range(mem_dim_def):
    #         avail_idcs = (mem_potential_idcs - mem.keys())
    #         mem[random.choice(list(avail_idcs))] = [dict(), adc_max, blank_dv.copy()]
    A = {k:sum((abs(cv[a] - v[0][a]) / max_delta) for a in (cv.keys() & v[0].keys())) for k, v in mem.items()}
    B = {kA:(vA + sum((1 - vB) for kB, vB in A.items() if (kB != kA))) for kA, vA in A.items()}
    norm_B = len(B)
    while not finished:
        disinh = sum(skip.values())
        C = {kA:(vA - disinh) for kA, vA in B.items() if (kA not in skip.keys())}
        if (len(C) == 1):
            min_act_k = list(C.keys())[0]
            min_act_val = (C[min_act_k] / norm_B)
        else:
            d = [(k, v) for k, v in C.items()]
            rs = random.sample(range(len(d)), len(d))
            ds = sorted(d, key = lambda x: (x[1], rs.pop()))
            min_act_k, min_act_val = ds[0][0], (ds[0][1] / norm_B)
        if (min_act_val <= thresh):
            union_v = (cv.keys() & mem[min_act_k][0].keys())
            diff_v = {k:((cv[k] - mem[min_act_k][0][k]) * 0.01) for k in union_v}
            new_v = dict()
            for k in union_v:
                val = (diff_v[k] + mem[min_act_k][0][k])
                if val < min_val: val = min_val
                if val > max_val: val = max_val
                new_v[k] = val
            mem[min_act_k][0] = new_v.copy()
            mem[min_act_k][1] = adc_max
            rate_A += 1
            if (sum(1 for a in distr if (a[0] == min_act_k)) == 0): distr.append((min_act_k, min_act_val))
            else: thresh += 0.001#------------------------------------------------------------------------------------------HP
            finished = True
        else:
            if (len(C) < 3):#-musn't be too low!!!!------------------------------------------------------------------------HP
                mem_excess = (len(mem) - mem_cap)
                if (mem_excess > 0):
                    for k in mem.keys():
                        if (mem[k][1] > 0): mem[k][1] -= 1
                    d = [(k, v[1]) for k, v in mem.items()]
                    rs = random.sample(range(len(d)), len(d))
                    ds = sorted(d, key = lambda x: (x[1], rs.pop()))
                    for a in range(mem_excess): del mem[ds[a][0]]
                noise_pct = 0.01#----------------------------------------------------------------------------------------------HP
                noise_val = (span * noise_pct)
                crc = {k:(v + (random.choice([-noise_val, noise_val]) * random.random())) for k, v in cv.items()}
                avail_idcs = (mem_potential_idcs - mem.keys())
                mem[random.choice(list(avail_idcs))] = [crc.copy(), adc_max, blank_dv.copy()]
                avail_idcs = (mem_potential_idcs - mem.keys())
                mem[random.choice(list(avail_idcs))] = [cv.copy(), adc_max, blank_dv.copy()]
                rate_C += 1
                finished = True
            else:
                if (len(skip) < (len(B) - 1)):
                    rate_B += 1
                    mem[min_act_k][1] = adc_max
                    skip[min_act_k] = (1 - A[min_act_k])
                else: finished = True
    cy += 1
    if (len(distr) >= distr_dim):
        tv = {a[0] for a in distr}
        iv_l = [1 if (a in tv) else -1 for a in range(len(blank_dv))]
        for a in iv:
            new_v = []
            for x, y in zip(iv_l, mem[a][2]):
                val = (x + y)
                if val < -1000: val = -1000
                if val > 1000: val = 1000
                new_v.append(val)
            mem[a][2] = new_v.copy()
        iv = {a[0] for a in distr}
        pev = (pv ^ iv)
        em_norm = max(1, (len(pv) + len(iv)))
        em = (len(pev) / em_norm)
        sum_v = blank_dv.copy()
        for a in distr: sum_v = [(x + y) for x, y in zip(sum_v, mem[a[0]][2])]
        pv = {i for i, a in enumerate(sum_v) if (a > 0)}
        # for a in distr: print(f"K: {str(a[0]).rjust(4)}  V: {a[1]:.4f}")
        distr = []
        thresh = thresh_initial
    print(f"RA: {rate_A}  RB: {rate_B}  RC: {rate_C}  ME: {len(mem)}" +
          f"  MA: {min_act_val:.4f}  EM: {em:.2f}  TH: {thresh:.4f}")
    ts_idx = ((ts_idx + 1) % len(ts))