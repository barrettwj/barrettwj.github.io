import random
from math import exp
# from random import choice
#______________________________________________PARAMETERS_____________________________________
val_dim = 10
set_values = [(a + 1) for a in range(val_dim)]
score_dim = 3000
score_values = [(a + 1) for a in range(score_dim)]
set_dim = 10
num_test_sets = 100000
temp = 2.0
#____________________________________________ARBITRARY TEST DATA________________________________
archetype_set = [random.choice(set_values) for _ in range(set_dim)]
max_diff = float(abs(max(set_values) - min(set_values)) * set_dim)
test_data = []
val_A = (score_dim - 1)
norm_A = float(val_A)
for i in range(num_test_sets):
    rs = [random.choice(set_values) for _ in range(set_dim)]
    idx = val_A - round((float(sum([abs(a - b) for a, b in zip(archetype_set, rs)])) / max_diff) * norm_A)
    test_data.append([score_values[idx], rs.copy()])
#________________________________________________EXPOSURE________________________________________
learning_array = [0] * (set_dim * val_dim)
for v in test_data:
    score = ((float(v[0] - 1) / norm_A) / 1000.0)
    encoded_set = [((val_dim * i) + (a - 1)) for i, a in enumerate(v[1])]
    learning_array = [(b + score) if i in encoded_set else (b - score) for i, b in enumerate(learning_array)]
hm = (max(learning_array) / temp)
e_x = [exp((float(i) / temp) - hm) for i in learning_array]
su = sum(e_x)
learning_array = [(i / su) for i in e_x]
#_________________________________________________RESULTS______________________________________
#"""
print(f"\n{archetype_set}  Archetype Set\n")
for a in range(set_dim):
    td = {(b + 1):learning_array[((a * val_dim) + b)] for b in range(val_dim)}
    print(f"Digit at position {a} (Archetype {archetype_set[a]}) {('-' * 150)}\n")
    for k, v in td.items(): print(f"{k}: {v:.5f}\t{('|' * round(v * 10000.0))}")
    print()
print(f"{archetype_set}  Archetype Set\n")
num_rep_patterns = 5
for a in range(num_rep_patterns):
    pattern = []
    for b in range(set_dim):
        tl = learning_array[(b * val_dim):((b + 1) * val_dim)]
        min_val = min(tl)
        diff = (max(tl) - min_val)
        if (diff > 0):
            wheel = []
            for i, c in enumerate(tl): wheel.extend([(i + 1) for _ in range(round(((c - min_val) / diff) * 1000.0))])
            pattern.append(random.choice(wheel))
        else: pattern.append(0)
    idx = val_A - round((float(sum([abs(a - b) for a, b in zip(archetype_set, pattern)])) / max_diff) * norm_A)
    score_val = score_values[idx]
    print(f"{pattern}\t\tScore: {score_val}")
#"""


