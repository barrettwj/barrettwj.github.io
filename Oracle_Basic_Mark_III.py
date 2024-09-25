import random
H = 7#-must be > 1 !!!-------------------------------------------------------------------------------HP
i = 0
mem = random.sample(list(range(-3, 4)), H)
ext = 7
ext_prev = -10
# inf = -23#-----------this influence propagates down the hierarchy------------------------------------HP
###########################################################################################################################
ts_len = 3
# ts = random.sample(range(-3, 4), ts_len)
ts = list(range(ts_len))
ts_idx = 0
while True:
    #######################################################################################################################
    fb = ext if i == (H - 1) else mem[i + 1]#---------Resonance???!!!----alter to add noise influence (creativity)
    #######################################################################################################################    
    if i == 0:
        ts_idx = (ts_idx + mem[i]) % ts_len
        # ext = ts[ts_idx]
        ext = ext_prev - ext + ts[ts_idx]
        # ext = ext_prev - ext + mem[i]
        ext_prev = ext
        ff = ext
    else: ff = mem[i - 1]
    ########################################################################################################################
    mem[i] = ff - mem[i] + fb
    ########################################################################################################################
    tl = [ext]
    tl.extend(mem)
    w = 4
    pcn = 2
    f_str_list = [f"{x:>{w}.{pcn}f}" if isinstance(x, float) else f"{x:>{w}}" for x in tl]
    f_str = " | ".join(f_str_list)
    print(f_str)
    ########################################################################################################################
    i = (i + 1) % H
    ########################################################################################################################