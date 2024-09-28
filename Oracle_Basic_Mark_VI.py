import random
H = 5#------------------------------------------------------------------------------------------------HP
K = 13717#--------------------------------------------------------------------------------------------HP
nw = [random.randrange(-K, K) for _ in range(H + 1)]
nwl = len(nw)
w = len(str(K)) + 1
ts_len = 5
ts = list(range(ts_len))
i = ts_idx = 0
# def wrap_value(val, minval, maxval): return (((val - minval) % (maxval - minval + 1)) + minval)
while True:
    fb = nw[(i + 1) % nwl]
    no_pv = (nw[(i - 1) % nwl] - nw[i] + fb)
    pv = (fb - nw[(i + 2) % nwl])
    gradient_pct = 0.97#------------------------------------------------------------------------------HP
    gradient = round((pv - no_pv) * gradient_pct)
    if i == 0:
        print(" | ".join([f"{x:>{w}}" for x in nw]))
        ts_idx = (no_pv + gradient)#-------------Agency Enabled
        # ts_idx = (ts_idx + 1)#-------------------Agency Disabled
        nw[i] = ts[ts_idx % ts_len]
    else: nw[i] = (no_pv + gradient)
    i = (i + 1) % H