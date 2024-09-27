import random
H = 7#------------------------------------------------------------------------------------------------HP
K = 137#----------------------------------------------------------------------------------------------HP
nw = [random.randrange(-K, K) for _ in range(H + 1)]
nwl = len(nw)
ts_len = 5
ts = list(range(ts_len))
i = ts_idx = 0
# def wrap_value(val, minval, maxval): return (((val - minval) % (maxval - minval + 1)) + minval)
while True:
    fb = nw[(i + 1) % nwl]
    if i == 0:
        print(" | ".join([f"{x:>{5}}" for x in nw]))
        ts_idx = (ts_idx + fb) % ts_len
        nw[i] = ts[ts_idx]
    no_p_val = (nw[(i - 1) % nwl] - nw[i] + fb)
    p_val = (fb - nw[(i + 2) % nwl])
    gradient_pct = 0.07#------------------------------------------------------------------------------HP
    gradient = round((p_val - no_p_val) * gradient_pct)
    nw[i] = (no_p_val + gradient)
    i = (i + 1) % H