import random
#______________________________________________PARAMETERS_____________________________________
val_dim = 50
set_values = [(a + 1) for a in range(val_dim)]
score_dim = 3000
score_values = [(a + 1) for a in range(score_dim)]
set_dim = 10
#____________________________________________ARBITRARY TEST DATA________________________________
archetype_set = [random.choice(set_values) for _ in range(set_dim)]
encoded_archetype_set = [((val_dim * i) + (a - 1)) for i, a in enumerate(archetype_set)]
max_diff = ((max(set_values) - min(set_values)) * set_dim)
enc_range = (set_dim * val_dim)
num_test_sets = 10000
test_data = dict()
for i in range(num_test_sets):
    rs = [random.choice(set_values) for _ in range(set_dim)]
    idx = score_dim - 1 - round((float(sum([abs(a - b) for a, b in zip(archetype_set, rs)])) / float(max_diff)) * float(score_dim - 1))
    score = score_values[idx]
    test_data[i] = [score, rs.copy()]
#________________________________________________EXPOSURE________________________________________
learning_array = [0] * enc_range
norm = float(num_test_sets * 2)
for v in test_data.values():
    score = (float(v[0] - 1) / float(score_dim - 1))
    encoded_set = [((val_dim * i) + (a - 1)) for i, a in enumerate(v[1])]
    learning_array = [(a + score) if i in encoded_set else (a - score) for i, a in enumerate(learning_array)]
learning_array = [(float(a + num_test_sets) / norm) for a in learning_array]
#_________________________________________________RESULTS______________________________________
print(archetype_set)
for a in range(set_dim):
    td = {(b + 1):learning_array[((a * val_dim) + b)] for b in range(val_dim)}
    print(f"Digit at position {a} {('-' * 150)}\n")
    for k, v in td.items(): print(f"{k}: {v:.5f}\t{('|' * round(v * 500.0))}")
    print()


