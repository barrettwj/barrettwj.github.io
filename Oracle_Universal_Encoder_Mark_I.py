import math
class Encoder:
    def __init__(self):
        self.enc_vec = set()
        self.nves = []
    def generate_complete_enc_vec(self):
        pass
    def encode_string(self, str_in):
        out = set()
        ###
        return out.copy()
    def decode_string(self, vec_in):
        out = ""
        ###
        return out
    def create_numerical_value_encoder(self, radix_in, l_pcs_max_in, r_pcs_max_in):
        self.nves.append(self.Numerical_Value_Encoder(radix_in, l_pcs_max_in, r_pcs_max_in))
    class Numerical_Value_Encoder:
        def __init__(self, radix_in, l_pcs_max_in, r_pcs_max_in):
            self.radix = radix_in
            self.radix_red = (self.radix - 1)
            self.l_pcs_max = l_pcs_max_in
            self.r_pcs_max = r_pcs_max_in
            self.pcs_dim = (self.l_pcs_max + self.r_pcs_max)
            self.num_enc_bound_neg = -((2 * int(self.radix ** self.pcs_dim)) - 2)
            self.num_enc_bound_pos = (-self.num_enc_bound_neg - 1)
            enc_vec_A = self.encode_numerical_value(30.729)
            # enc_vec_B = self.encode_numerical_value(23.35)
            # print(int(len(enc_vec_A ^ enc_vec_B) / 2))
            dec_val = self.decode_numerical_value(enc_vec_A)
            print(dec_val)
        def encode_numerical_value(self, val_in):
            out = set()
            digits = [(int(float(abs(val_in)) * float(self.radix ** (-(self.l_pcs_max - 1) + a))) % self.radix) for a in range(self.pcs_dim)]
            digits.reverse()
            offset = 0
            for i, a in enumerate(digits):
                step = (self.radix ** i)
                card = (step * self.radix_red)
                out |= {((step * a) + offset + b) for b in range(card)}
                offset += (self.radix_red * 2 * step)
            if (val_in < 0): out = {-(a + 1) for a in out}
            return out.copy()
        def decode_numerical_value(self, vec_in):
            idx_A = self.num_enc_bound_neg
            digits = dict()
            sign = 0
            while (idx_A < self.num_enc_bound_pos):
                if (idx_A in vec_in):
                    ts = set()
                    while (idx_A in vec_in):
                        ts.add(idx_A)
                        idx_A += 1
                    sign = 1
                    if (min(ts) < 0):
                        sign = -1
                        ts = {-(a + 1) for a in ts}
                    step = int(len(ts) / self.radix_red)
                    exp = round(math.log(float(step)) / math.log(float(self.radix)))
                    offset = sum((self.radix_red * 2 * (self.radix ** a)) for a in range(exp))
                    digits[exp] = int((min(ts) - offset) / step)
                idx_A += 1
            divisor = (float(self.radix) ** float(self.r_pcs_max))
            return (float(sign * sum((v * (self.radix ** k)) for k, v in digits.items())) / divisor)
enc = Encoder()
enc.create_numerical_value_encoder(10, 2, 2)#-should probably stay <= 3, 3 for base 10