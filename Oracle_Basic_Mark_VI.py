import random
H = 5#------------------------------------------------------------------------------------------------HP
K = 1737#--------------------------------------------------------------------------------------------HP
nw = [random.randrange(-K, K) for _ in range(H + 1)]
nwc = nw.copy()
nwl = len(nw)
trm = dict()
w = len(str(K)) + 1
ts_len = 4
ts = list(range(ts_len))
ts_idx = -10
ts_idx_prev = -20
var = var_prev = 0
i = 0
rs = random.sample(range(1000000), 1000000)
# def wrap_value(val, minval, maxval): return (((val - minval) % (maxval - minval + 1)) + minval)
while True:
    fb = nw[(i + 1) % nwl]
    no_pv = (nw[(i - 1) % nwl] - nw[i] + fb)
    pv = (fb - nw[(i + 2) % nwl])
    gradient_pct = 0.99#------------------------------------------------------------------------------HP
    gradient = round((pv - no_pv) * gradient_pct)
    if i == 0:
        tl = [abs(x - y) for x, y in zip(nw[1:], nwc[1:])]
        nwc = nw.copy()
        mean = sum(tl) / len(tl)
        var_prev = var
        var = sum((x - mean) ** 2 for x in tl) / len(tl)
        print(" | ".join([f"{x:>{w}}" for x in nw]) + f"  IS: {f'{var:.2f}'.rjust(6)}")
        trm[(ts_idx_prev, ts_idx)] = var_prev - var
        ts_idx_prev = ts_idx
        d = [(k[1], v) for k, v in trm.items() if (k[0] == ts_idx and v < 0)]
        # d = []
        if d:
            rst = rs.copy()
            ds = sorted(d, key = lambda x: (x[1], rst.pop()))
            ts_idx = ds[0][0]#-------policy selection
        else:
            ts_idx = no_pv + gradient#-------------Agency Enabled
            # ts_idx += 1#-------------------Agency Disabled
        nw[i] = ts[ts_idx % ts_len]
    else: nw[i] = no_pv + gradient
    i = (i + 1) % H