import random
import heapq
H = 6
N = 24
D = N * 2
N_range = range(N)
N_inv_list = [-N + a for a in N_range]
K_pct = 0.12
K = round(N * K_pct)
#################################################################################
oracle = [set(random.sample(N_range, K)) for _ in range(H)]
evs = [set(random.sample(N_range, K)) for _ in range(H)]
#################################################################################
ext = set()
ts_dim = 67
ts = [set(random.sample(N_range, K)) for _ in range(ts_dim)]
# fb_alt = set(random.sample(N_range, K))
fb_alt = set()
ext_map_adc_max = 200
ext_map = dict()
bv_set = {a for a in range(ts_dim)}
trn_map_max_dim = 500
trn_map = dict()
#################################################################################
symchar = '\u25AA'
i = em = ts_idx = ts_idx_inc = em_prev = em_delta = 0
def print_network():
    fl = [str(ts_idx_inc).rjust(2)]
    tl = [ext.copy()]
    tl.extend(oracle)
    # tl.extend(evs)
    fl.extend(["".join([f"{symchar if x in y else ' '}" for x in N_range]) for y in tl])
    # fl.extend(["".join([f"{symchar if x in y else ' '}" for x in N_inv_list]) for y in tl])
    fl.append(f"EM: {f'{em:.3f}'.rjust(5)}")
    # fl.append(f"ED: {f'{em_delta:.3f}'.rjust(6)}")
    fl.append(f"EX: {str(len(ext_map)).rjust(4)}")
    print("|".join(fl))
#################################################################################
while True:
    #############################################################################
    # fb_alt = ext.copy()
    fb = fb_alt.copy() if i == H - 1 else oracle[i + 1].copy()
    #############################################################################
    if i == 0:
        em /= H
        em_delta = em - em_prev
        print_network()
        em_prev = em
        em = 0
        ts_idx_inc = -1000000
        #########################################################################
        bv = oracle[i].copy()
        if ext_map:
            d = [(len(k ^ bv), k) for k in ext_map.keys()]
            heapq.heapify(d)
            d = sorted(d, key = lambda x: x[0])
            if d[0][0] < 1:
                ts_idx_inc = ext_map[d[0][1]][0]
                ext_map[d[0][1]][1] = 0
        if ts_idx_inc == -1000000:
            ts_idx_inc = random.choice(list(bv_set))
            ext_map[frozenset(bv)] = [ts_idx_inc, 0]
        for v in ext_map.values():
            if v[1] < ext_map_adc_max: v[1] += 1
        ext_map = {k:v for k, v in ext_map.items() if v[1] < ext_map_adc_max - 10}
        #########################################################################
        ext = {-(a + 1) for a in ts[ts_idx]}
        ts_idx = (ts_idx + ts_idx_inc) % ts_dim
        ext |= ts[ts_idx]
        #########################################################################
        ff = ext.copy()
    else: ff = oracle[i - 1].copy()
    #############################################################################
    ev = ff - oracle[i]
    evs[i] = ev.copy()
    oracle[i] = ev ^ fb
    em += len(ev) / D
    #############################################################################
    i = (i + 1) % H