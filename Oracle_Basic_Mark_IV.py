import random
H = 7#-----------------------------------------------------------------------------------------------HP
N = 2#-must be > 1 !!!-------------------------------------------------------------------------------HP
K = 3#-----------------------------------------------------------------------------------------------HP
M = ((K * 2) + 1)
i = 0
mem = [random.sample(list(range(-K, K + 1)), N) for _ in range(H)]
ext = random.sample(list(range(-K, K + 1)), N)
ext_prev = random.sample(list(range(-K, K + 1)), N)
inf = random.sample(list(range(-K, K + 1)), N)#---this influence propagates down the hierarchy-------HP
##############################################################################################################################################
ts_len = M#-must be >= M-----------------------------------------------------------------------------HP
ts = list(range(ts_len))
# ts = random.sample(list(range(-K, K + 1)), ts_len)
ts_idx = 0
while True:
    ##########################################################################################################################################
    fb = ext if i == (H - 1) else mem[i + 1]#---------Resonance???!!!----alter with added inf to add noise influence (creativity)???
    # inf needs to intermittently have a non-zero value and then return to 0 !!!
    ##########################################################################################################################################
    if i == 0:
        ##########################################################################
        ts_idx = (ts_idx + mem[i][0]) % ts_len
        # ts_idx += mem[i][0]
        # if ts_idx < 0: ts_idx = 0
        # if ts_idx > (ts_len - 1): ts_idx = (ts_len - 1)
        ##########################################################################
        ext = [mem[i][0], ts[ts_idx]]
        # single value form:  ext = ext_prev - ext + mem[i]
        # ext = [xA + yA for xA, yA in zip([xB - yB for xB, yB in zip(ext_prev, ext)], mem[i])]
        # ext = [xA + yA for xA, yA in zip([xB - yB for xB, yB in zip(ext_prev, ext)], [mem[i][0], ts[ts_idx]])]
        # # ext_prev = ext
        ff = ext
    else: ff = mem[i - 1]
    #############################################################################################################################################
    # single value form:  mem[i] = ff - mem[i] + fb
    mem[i] = [xA + yA for xA, yA in zip([xB - yB for xB, yB in zip(ff, mem[i])], fb)]
    #############################################################################################################################################
    if i == 0:
        w = 6
        pcn = 2
        tl = [ext]
        tl.extend(mem)
        f_str_list = [" ".join([f"{x:>{w}.{pcn}f}" if isinstance(x, float) else f"{x:>{w}}" for x in a]) for a in tl]
        f_str = " | ".join(f_str_list)
        print(f_str)
    #############################################################################################################################################
    i = (i + 1) % H
    #############################################################################################################################################