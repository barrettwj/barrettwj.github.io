import random
import heapq
H = 5
N = 28#-24
D = N * 2
# D = N
N_range = range(N)
D_range = range(D)
N_inv_list = [-N + a for a in N_range]
K_pct = 0.11#-0.12
K = round(N * K_pct)
#################################################################################
oracle = [set(random.sample(D_range, K * 2)) for _ in range(H)]
evs = oracle.copy()
#################################################################################
ev = set()
ext = set()
# fb_alt = set(random.sample(N_range, K))
fb_alt = set()
ext_map_adc_max = 200
ext_map = dict()
trn_map_max_dim = 500
trn_map = dict()
#################################################################################
symchar = '\u25AA'
i = i_prev = em = em_prev = em_delta = ts_idx = 0
ts_res = set()
def print_network():
    fl = [str(ts_idx).rjust(2)]
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
    fb_alt = ext.copy()
    fb = fb_alt.copy() if i == H - 1 else oracle[i + 1].copy()
    #############################################################################
    oracle[i_prev] = ev ^ fb
    if i == 0:
        em /= H
        em_delta = em - em_prev
        print_network()
        em_prev = em
        em = 0
        #########################################################################
        pre = ts_res.copy()
        bv = oracle[i].copy()
        d = [(len(k ^ bv), k) for k in ext_map.keys() if len(k ^ bv) < 1]
        if d:
            heapq.heapify(d)
            d = sorted(d, key = lambda x: x[0])
            ts_res = ext_map[d[0][1]][0].copy()
            ext_map[d[0][1]][1] = 0
        else:
            ts_res = set(random.sample(N_range, K))
            ext_map[frozenset(bv)] = [ts_res.copy(), 0]
        for v in ext_map.values():
            if v[1] < ext_map_adc_max: v[1] += 1
        ext_map = {k:v for k, v in ext_map.items() if v[1] < 10}
        #########################################################################
        ext = ts_res.copy()
        ext |= {-(a + 1) for a in pre}
        #########################################################################
        ff = ext.copy()
    else: ff = oracle[i - 1].copy()
    #############################################################################
    ev = ff - oracle[i]
    evs[i] = ev.copy()
    em += len(ev) / D
    #############################################################################
    i_prev = i
    i = (i + 1) % H