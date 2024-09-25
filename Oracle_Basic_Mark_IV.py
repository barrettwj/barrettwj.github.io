import random
H = 5#-must be > 1 !!!-------------------------------------------------------------------------------HP
N = 3#-must be > 1 !!!-------------------------------------------------------------------------------HP
K = 3#-----------------------------------------------------------------------------------------------HP
mem = [random.sample(range(-K, K + 1), N) for _ in range(H)]
ext = [7] * N
ext_prev = [-10] * N
inf = [-2] * N#-----------this influence propagates down the hierarchy--------------------------------HP
# stasis_ss = 23#-------------------------------------------------------------------------------------HP
# stasis_samples = []
# mem_mirror = [-100] * H
i = 0
ts_len = 7#-must be > K * 2---------------------------------------------------------------------------HP
ts = list(range(ts_len))
ts_idx = 0
while True:
    # fb = ext if i == (H - 1) else mem[i + 1]#---------Resonance???!!!----alter to add noise influence (creativity)
    fb = inf if i == (H - 1) else mem[i + 1]
    if i == 0:
        ts_idx = ((ts_idx + ts_len + mem[i][0] + mem[i][2]) % ts_len)
        ext = [mem[i][0], ts[ts_idx], mem[i][2]]
        # ext = [xA + yA for xA, yA in zip([xB - yB for xB, yB in zip(ext_prev, ext)], mem[i])]# ext = ext_prev - ext + mem[i]#-----Agency???!!!
        # ext_prev = ext
        ff = ext
    else: ff = mem[i - 1]
    mem[i] = [xA + yA for xA, yA in zip([xB - yB for xB, yB in zip(ff, mem[i])], fb)]# mem[i] = ff - mem[i] + fb
    #############################################################
    width = 4
    precision = 2
    tl = [ext.copy()]
    tl.extend(mem.copy())
    # formatted_list = [f"{x:>{width}.{precision}f}" if isinstance(x, float) else f"{x:>{width}}" for x in tl]
    formatted_list = ["  ".join([f"{x:>{width}.{precision}f}" if isinstance(x, float) else f"{x:>{width}}" for x in a]) for a in tl]
    formatted_str = "  | ".join(formatted_list)
    print(formatted_str)
    #############################################################
    i = (i + 1) % H
    """
    stasis_samples.append(sum([abs(x - y) for x, y in zip(mem, mem_mirror)]))
    mem_mirror = mem.copy()
    if len(stasis_samples) == stasis_ss:
        avg_v = sum(stasis_samples) / stasis_ss
        stasis_samples = []
        if avg_v == 0: break#--------------------------------------------------------------------------HP
    """
print(ext)