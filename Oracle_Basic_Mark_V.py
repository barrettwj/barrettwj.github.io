import random
import heapq
H = 5
N = 28#-24
D = N * 2
N_range = range(N)
D_range = range(D)
N_inv_list = [-N + a for a in N_range]
K_pct = 0.47#-0.12
K = round(N * K_pct)
#################################################################################
oracle = [set() for _ in range(H)]
evs = oracle.copy()
#################################################################################
ext = set()
bv_prev = set()
fb_alt = set()
# fb_alt = set(random.sample(N_range, K))
ext_map_adc_max = 11
ext_map = dict()
ts_res = set()
idx_map = dict()
#################################################################################
symchar = '\u25AA'
i = em = em_prev = em_delta = ts_idx = 0
def print_network():
    fl = [str(ts_idx).rjust(3)]
    tl = [ext.copy()]
    tl.extend(oracle)
    # tl.extend(evs)
    fl.extend(["".join([f"{symchar if x in y else ' '}" for x in N_range]) for y in tl])
    # fl.extend(["".join([f"{symchar if x in y else ' '}" for x in N_inv_list]) for y in tl])
    fl.append(f"EM: {f'{em:.3f}'.rjust(5)}")
    fl.append(f"EX: {str(len(ext_map)).rjust(3)}")
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
        #########################################################################
        # bv = oracle[i].copy()
        bv = bv_prev.copy()
        bv_prev = oracle[i].copy()
        d = [(len(k ^ bv), k) for k in ext_map.keys() if len(k ^ bv) < 1]
        if d:
            heapq.heapify(d)
            d = sorted(d, key = lambda x: x[0])
            ts_res = ext_map[d[0][1]][0].copy()
            ts_idx = idx_map[frozenset(ts_res)]
            ext_map[d[0][1]][1] = 0
        else:
            ts_res = set(random.sample(N_range, K))
            while frozenset(ts_res) in idx_map.keys(): ts_res = set(random.sample(N_range, K))
            ext_map[frozenset(bv)] = [ts_res.copy(), 0]
            ts_idx = 0
            while ts_idx in idx_map.values(): ts_idx += 1
            idx_map[frozenset(ts_res)] = ts_idx
        for v in ext_map.values():
            if v[1] < ext_map_adc_max: v[1] += 1
        ext_map = {k:v for k, v in ext_map.items() if v[1] < ext_map_adc_max}
        vs = [a[0] for a in ext_map.values()]
        idx_map = {k:v for k, v in idx_map.items() if set(k) in vs}
        #########################################################################
        ext = {-(a + 1) for a in ext if a in N_range}
        ext |= ts_res
        #########################################################################
        ff = ext.copy()
    else: ff = oracle[i - 1].copy()
    #############################################################################
    ev = ff - oracle[i]
    evs[i] = ev.copy()
    em += len(ev) / D
    oracle[i] = ev ^ fb
    #############################################################################
    i = (i + 1) % H