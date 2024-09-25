import random
H = 7#-must be > 1 !!!-------------------------------------------------------------------------------HP
sample_range = list(range(-12, 13))
mem = random.sample(sample_range, H)
# mem = [2] * H
mem_mirror = [-1000000] * H
ext = 7
ext_prev = -10
inf = -23#-----------this influence propagates down the hierarchy------------------------------------HP
stasis_ss = 3#---------------------------------------------------------------------------------------HP
stasis_samples = []
i = 0
while True:
    fb = ext if i == (H - 1) else mem[i + 1]#---------Resonance???!!!----alter to add noise influence (creativity)
    if i == 0:
        ext = ext_prev - ext + mem[i]#-------------Agency???!!!---------this is much more stable!!!???
        ext_prev = ext
        ff = ext
    else: ff = mem[i - 1]
    # fb = inf if i == (H - 1) else mem[i + 1]
    # fb = ext if i == (H - 1) else mem[i + 1]#---------Resonance???!!!
    mem[i] = ff - mem[i] + fb
    #############################################################
    width = 6
    precision = 2
    formatted_list = [f"{x:>{width}.{precision}f}" if isinstance(x, float) else f"{x:>{width}}" for x in mem]
    formatted_str = " | ".join(formatted_list)
    print(formatted_str)
    #############################################################
    i = (i + 1) % H
    stasis_samples.append(sum([abs(x - y) for x, y in zip(mem, mem_mirror)]))
    mem_mirror = mem.copy()
    if len(stasis_samples) == stasis_ss:
        avg_v = sum(stasis_samples) / stasis_ss
        stasis_samples = []
        if avg_v == 0: break#--------------------------------------------------------------------------HP
# print(mem)
print(ext)