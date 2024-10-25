import random
H = 4
N = 32
K_pct = 0.37
K = round(N * K_pct)
# eff_pct = 0.50
# eff_dim = round(N * eff_pct)
# eff_mask = set(range(eff_dim))
# eff_card = round(len(eff_mask) * K_pct)
# aff_mask = set(range(N)) - eff_mask
# aff_card = K - eff_card
sample_range_list = list(range(N))
mem = [set(random.sample(sample_range_list, K)) for _ in range(H)]
#################################################################################
ext = set(random.sample(sample_range_list, K))
ext_prev = set()
ts_dim = 37
ts = [set(random.sample(sample_range_list, K)) for _ in range(ts_dim)]
# ts = [set(random.sample(list(aff_mask), aff_card)) for _ in range(ts_dim)]
rfb = set(random.sample(sample_range_list, K))
ext_map = dict()
bvrA = ts_dim - 1
bvrB = (bvrA * 2) + 1
bv_set = {-bvrA + a for a in range(bvrB)}
rsA = random.sample(range(1000000), 1000000)
#################################################################################
i = em = ts_idx = 0
def print_network():
    tl = [ext]
    tl.extend(mem)
    fl = ["".join([f"{'*' if x in a else ' ':>{1}}" for x in range(N)]) for a in tl]
    fl.append(f"EM: {f'{em:.4f}'.rjust(6)}")
    print(" | ".join(fl))
while True:
    #############################################################################
    fb_alt = set()
    # fb_alt = rfb.copy()
    # fb_alt = ext.copy()
    fb = fb_alt.copy() if i == H - 1 else mem[i + 1].copy()
    #############################################################################
    if i == 0:
        em /= len(mem)
        print_network()
        em = 0
        #########################################################################
        #"""
        bv = mem[i].copy()
        # bv = mem[i] & eff_mask
        match = False
        if ext_map:
            d = [(len(k ^ bv), v) for k, v in ext_map.items()]
            rs = rsA.copy()
            d = sorted(d, key = lambda x: (x[0], rs.pop()))
            if d[0][0] < 1:
                ts_idx = (ts_idx + d[0][1]) % ts_dim
                match = True
        if not match:
            rd = random.choice(list(bv_set))
            ts_idx = (ts_idx + rd) % ts_dim
            ext_map[frozenset(bv)] = rd
        #"""
        #########################################################################
        # ts_idx = (ts_idx + 1) % ts_dim
        #########################################################################
        res = ts[ts_idx].copy()
        # res |= bv
        ext = (ext_prev - res)
        ext ^= mem[i]
        ext_prev = ext.copy()
        #########################################################################
        ff = ext.copy()
    else: ff = mem[i - 1].copy()
    #############################################################################
    ev = ff - mem[i]
    em += len(ev) / N
    # em += len(ev) / (N * 2)
    mem[i] = ev ^ fb
    #############################################################################
    i = (i + 1) % H