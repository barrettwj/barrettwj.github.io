import random
N = 1024#------------------------------------------------------------------------------------------------------HP
max_val = 50#--------------------------------------------------------------------------------------------------HP
# min_val = -max_val
min_val = -(max_val - 1)
mem_cap = 200#--------------------------------------------------------------------------------------------------HP
mem_potential_idxs = set(range(mem_cap))
adc_max = 1000#--------------------------------------------------------------------------------------------HP
mem = dict()
# max_delta = (max_val - min_val)
max_delta = ((max_val - min_val) * N)
ts_dim = 500#-----------------------------------------------------------------------------------------------HP
ts = [[random.randint(min_val, max_val) for _ in range(N)] for _ in range(ts_dim)]
ts_idx = cy = 0
vp = 0.01#-------------------------------------------------------------------------------------------------HP
min_act_val = (vp + 1)
while (min_act_val > vp):
# while True:
    cv = ts[ts_idx].copy()
    skip = set()
    finished = False
    rate_A = rate_B = rate_C = inc_val = min_act_k = 0
    mem_dim_def = (3 - len(mem))#--------------------------------------------------------------------------HP
    if (mem_dim_def > 0):
        for _ in range(mem_dim_def):
            avail_idxs = (mem_potential_idxs - mem.keys())
            mem[random.choice(list(avail_idxs))] = [[random.randint(min_val, max_val) for _ in range(N)], adc_max]
    # A = {k:(sum((abs(x - y) / max_delta) for x, y in zip(cv, v[0])) / N) for k, v in mem.items()}
    A = {k:sum((abs(x - y) / max_delta) for x, y in zip(cv, v[0])) for k, v in mem.items()}
    B = {kA:(vA + sum((1 - vB) for kB, vB in A.items() if (kB != kA))) for kA, vA in A.items()}
    norm_B = len(B)
    while not finished:
        C = {kA:(vA - inc_val) for kA, vA in B.items() if (kA not in skip)}
        min_act_val = min(C.values())
        for k, v in C.items():
            if (v == min_act_val): min_act_k = k
        min_act_val /= norm_B
        for k in mem.keys():
            if (mem[k][1] > 0): mem[k][1] -= 1
        if (min_act_val <= vp):
            diff_v = [((x - y) * 0.001) for x, y in zip(cv, mem[min_act_k][0])]#-------------------------------------------HP
            new_v = []
            for x, y in zip(diff_v, mem[min_act_k][0]):
                val = (x + y)
                if val < min_val: val = min_val
                if val > max_val: val = max_val
                new_v.append(val)
            mem[min_act_k] = [new_v.copy(), adc_max]
            rate_A += 1
            finished = True
        else:
            if (len(C) < 4):#----causes issues if much larger than 3 or at all less than 3!!!!--------------------------------HP
                if (len(mem) == mem_cap):
                    d = [(k, v[1]) for k, v in mem.items()]
                    rs = random.sample(range(len(d)), len(d))
                    ds = sorted(d, key = lambda x: (x[1], rs.pop()))
                    del mem[ds[0][0]]
                avail_idxs = (mem_potential_idxs - mem.keys())
                mem[random.choice(list(avail_idxs))] = [cv.copy(), adc_max]
                rate_C += 1
                finished = True
            else:
                rate_B += 1
                inc_val += (1 - A[min_act_k])
                skip.add(min_act_k)
    print(f"CY: {cy}  RA: {rate_A}  RB: {rate_B}  RC: {rate_C}  ME: {len(mem)} MA: {min_act_val:.4f}")
    cy += 1
    ts_idx = ((ts_idx + 1) % len(ts))