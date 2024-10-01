import random
import math
H = 6#------------------------------------------------------------------------------------------------HP
K = 1737#--------------------------------------------------------------------------------------------HP
nw = [random.randrange(-K, K) for _ in range(H + 1)]
nwc = nw.copy()
nwl = len(nw)
trm = dict()
w = len(str(K)) + 1
ts_len = 17
# ts = list(range(ts_len))
ts = random.sample(range(ts_len), ts_len)
ts_idx = 1
i = em = em_prev = ts_idx_prev = 0
rs = random.sample(range(1000000), 1000000)
ps = False
while True:
    if i == 0:
        # tl = [abs(x - y) for x, y in zip(nw[1:], nwc[1:])]
        tl = [(x - y) for x, y in zip(nw[1:], nwc[1:])]
        nwc = nw.copy()
        ssum = sum(tl)
        mean = ssum / len(tl)
        var = sum((x - mean) ** 2 for x in tl) / len(tl)
        em_prev = em
        em = var
        ps_str = "  PS" if ps else ""
        ps = False
        print(" | ".join([f"{x:>{w}}" for x in nw]) + f"  EM: {f'{em:.2f}'.rjust(6)}" + ps_str)
        # print(" | ".join([f"{f'{x:.2f}'.rjust(6)}" if a > 0 else f"{x:>{w}}" for a, x in enumerate(nw)]) +
        #       f"  EM: {f'{em:.2f}'.rjust(6)}" + ps_str)
        trm[(ts_idx_prev, ts_idx)] = em_prev - em
        ts_idx_prev = ts_idx
        # d = [(k[1], v) for k, v in trm.items() if k[0] == ts_idx and v < 0]
        d = []
        if len(d) > 0:
            ps = True
            if len(d) > 1:
                rst = rs.copy()
                d = sorted(d, key = lambda x: (x[1], rst.pop()))
            ts_idx = d[0][0]#----------------policy selection
        else:
            # ts_idx = (ts_idx + nw[1]) % ts_len
            ts_idx = round(ts_idx + nw[1]) % ts_len
            # ts_idx = (ts_idx + 1) % ts_len
            # ts_idx = random.choice(list(range(ts_len)))
        # ts_idx = round(ts_idx)
        # ts_idx = math.floor(ts_idx)
        # nw[i] = ts_idx
        nw[i] = ts[ts_idx]
    else:
        fb = nw[i + 1] if i < (nwl - 1) else 0
        error = nw[i - 1] - nw[i]
        no_pv = error + fb
        dfb = nw[i + 2] if i < (nwl - 2) else 0
        pv = nw[i] - nw[i - 1] - dfb
        # pv = -(error + dfb)
        gradient_pct = 0.47#------------------------------------------------------------------------------HP
        gradient = round(pv * gradient_pct)
        # gradient = pv * gradient_pct
        nw[i] = no_pv + gradient
    i = (i + 1) % nwl