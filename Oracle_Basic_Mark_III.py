import random
H = 7#-----------------------------------------------------------------------------------------------HP
i = 0
mem = [random.randrange(-10, 10) for _ in range(H)]
ed_avg_len = 3#--------------------------------------------------------------------------------------HP
mem_eds = [[0] * ed_avg_len] * H
mem_es = [0] * H
ext = -1
ts_len = 2
ts = list(range(ts_len))
ts_idx = 0
def wrap_value(val, minval, maxval): return (((val - minval) % (maxval - minval + 1)) + minval)
def print_network():
    tl = [ext]
    tl.extend(mem)
    w = 5
    pcn = 2
    f_str_list = [f"{x:>{w}.{pcn}f}" if isinstance(x, float) else f"{x:>{w}}" for x in tl]
    f_str = " | ".join(f_str_list)
    print(f_str)
while True:
    # fb = ext if i == (H - 1) else mem[i + 1]#------alter to add noise (creativity) influence
    fb = 0 if i == (H - 1) else mem[i + 1]#------alter to add noise (creativity) influence
    if i == 0:
        print_network()
        ts_idx = (ts_idx + mem[i]) % ts_len
        ext = ts[ts_idx]
        ff = ext
    else: ff = mem[i - 1]
    # mem[i] = ff - mem[i] + fb#----------------------------essence
    conf = 0.70#-0.20------------------------------------------------------------------------------------------HP
    delta_error = mem_es[i]
    error_term = (ff - mem[i])
    mem_es[i] = error_term
    delta_error = ((delta_error - error_term) * conf)
    mem_eds[i].append(delta_error)
    mem_eds[i].pop(0)
    norm = len(mem_eds[i])
    error_delta = round(sum(((a / norm) / (1.5 ** (norm - 1 - j))) for j, a in enumerate(mem_eds[i])))
    # mem[i] = wrap_value((error_term + error_delta + fb), -K, K)
    # mem[i] = wrap_value((error_term - fb), 0, 7)
    mem[i] = (error_term + error_delta + fb)
    # mem[i] = (error_term + fb)
    i = (i + 1) % H