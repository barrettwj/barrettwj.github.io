import random
H = 7#-----------------------------------------------------------------------------------------------HP
K = 3#-----------------------------------------------------------------------------------------------HP
i = 0
mem = random.sample(list(range(-K, K + 1)), H)
ext = 1
ext_prev = -1
# inf = -1#-----------this influence propagates down the hierarchy------------------------------------HP
ts_len = ((K * 2) + 1)#-must be > (K * 2)
ts = list(range(ts_len))
ts_idx = 0
def wrap_value(val, minval, maxval): return (((val - minval) % (maxval - minval + 1)) + minval)
while True:
    fb = ext if i == (H - 1) else mem[i + 1]#------alter to add noise (creativity) influence
    if i == 0:
        ##########################################################
        tl = [ext]
        tl.extend(mem)
        w = 3
        pcn = 2
        f_str_list = [f"{x:>{w}.{pcn}f}" if isinstance(x, float) else f"{x:>{w}}" for x in tl]
        f_str = " | ".join(f_str_list)
        print(f_str)
        ###########################################################
        ts_idx = (ts_idx + mem[i]) % ts_len
        # ext = ts[ts_idx]
        ext = ext_prev - ext + ts[ts_idx]#---this makes more sense than other strategies!!!!
        # ext = ext_prev - ext + mem[i]#--------------------essence
        ext_prev = ext
        ff = ext
    else: ff = mem[i - 1]
    # mem[i] = ff - mem[i] + fb#----------------------------essence
    mem[i] = wrap_value((ff - mem[i] + fb), -K, K)
    i = (i + 1) % H