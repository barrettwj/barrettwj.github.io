import random
import math
import time
import pickle
import sys
import os
import pygame
import threading
from datetime import datetime
from collections import deque
import heapq
def main():
    class Oracle:
        def __init__(self):
            #______________________________________________________________________ARCHIVING___________________________________________
            self.auto_archiving_enabled = False
            self.auto_load_model = False
            self.archive_directory = 'Oracle_Synthesis_Mark_IV_Archive'
            self.archive_load = self.load_model() if self.auto_load_model else []
            self.archive_capacity = 10#------------------------------------------------------------------------------------------------HP
            self.save_thread = threading.Thread(target = self.save_model)
            self.save_period = 1000#----------------------------------------------------------------------------------------------------HP
            self.save_counter = 0
            #____________________________________________________________________ORACLE__________________________________________________
            self.model_hps = []
            if len(self.archive_load) == 0:
                self.H = 3#----------------------------------------------------------------------------------------------------------HP
            else:
                self.model_hps = self.archive_load.copy()
                self.H = len(self.model_hps)
            self.s = Sensorium(self)
            if len(self.archive_load) == 0: self.m = [Matrix(self, i, dict()) for i in range(self.H)]
            else: self.m = [Matrix(self, i, a.copy()) for i, a in enumerate(self.model_hps)]
            self.running = True
            #____________________________________________________________________METRICS________________________________________________
            self.em = 1.0
            self.em_prev = self.em
            self.em_delta = self.frequency_avg = self.cycle = 0
            self.em_avg = 1.0
            self.em_avg_samples = []
            self.em_avg_num_samples = 31
            self.frequency_avg_samples = []
            self.frequency_avg_num_samples = 31
            self.compute_metrics = True
            #______________________________________________________________________GRAPHICS______________________________________________
            # ar = (16.0 / 9.0)
            # self.display_w = 300
            # self.display_h = round(float(self.display_w) / ar)
            # os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % ((1500 - self.display_w), 10)
            self.display_w = 1400
            self.display_h = 780
            os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % ((1500 - self.display_w), 30)
            pygame.init()
            self.display = pygame.display.set_mode((self.display_w, self.display_h))
            pygame.display.set_caption('Oracle Synthesis Mark IV')
            self.font = pygame.font.SysFont("arialblack", 12)
            pygame_icon = pygame.image.load('Input Images/Letter Images White/letter_O_img.jpg')
            pygame.display.set_icon(pygame_icon)
        def update(self):
            while self.running:
                start_time = time.time()
                self.display.fill((0, 0, 0))
                self.s.update()
                self.em = 0
                for a in self.m:
                    a.update()
                    self.em += a.em
                self.em /= float(len(self.m))
                self.em_avg_samples.append(self.em)
                if len(self.em_avg_samples) == self.em_avg_num_samples:
                    self.em_avg = (sum(self.em_avg_samples) / float(len(self.em_avg_samples)))
                    self.em_avg_samples = []
                #################################################
                if((self.save_thread.is_alive() == False) & self.auto_archiving_enabled): self.save_counter += 1
                if self.save_counter == self.save_period:
                    self.save_thread = threading.Thread(target = self.save_model)
                    self.save_thread.start()
                    self.save_counter = 0
                #############################################
                self.manage_text()
                frequency = round(min([(1.0 / max([sys.float_info.min, (time.time() - start_time)])), 10000.0]))
                self.frequency_avg_samples.append(frequency)
                if(len(self.frequency_avg_samples) == self.frequency_avg_num_samples):
                    self.frequency_avg = (sum(self.frequency_avg_samples) / float(len(self.frequency_avg_samples)))
                    self.frequency_avg_samples = []
                self.manage_pygame_events()
                self.cycle += 1
            pygame.display.quit()
            pygame.quit()
        def show_text(self, msg, color, x, y):
            text = self.font.render(msg, True, color)
            text_rect = text.get_rect()
            text_rect.topleft = (x, y)
            self.display.blit(text, text_rect)
        def manage_text(self):
            freq_avg_rounded = round(self.frequency_avg)
            freq_string = ">10000" if(freq_avg_rounded > 10000) else str(freq_avg_rounded)
            if self.compute_metrics:
                #"""
                for i, a in enumerate(self.m[0].knowledge_map.keys()):
                    if (i < 70):
                        self.show_text(a, (200, 200, 200), 10, (self.display.get_height() - 150 - (i * 12)))
                        for j, b in enumerate(self.m[0].knowledge_map[a]):
                            if (j < 32):
                                tstr = ""
                                for c in b:
                                    # cli = (c // self.m[0].M)#--------------------------cluster index
                                    # chv = (cli % self.s.char_channel_dim)#---------------channel value
                                    # char = self.s.permitted_chars_list[chv]
                                    # tstr += char
                                    tstr += c
                                self.show_text(tstr, (200, 200, 200), (50 + (j * 40)), (self.display.get_height() - 150 - (i * 12)))
                #"""
                m_ind = 0
                # self.show_text("RE: " + f"{(self.re_rate_avg * 100.0):.2f}" + "%", (200, 200, 200), 10, (self.screen.get_height() - 42))
                self.show_text(f"String Mismatch: {self.s.sv_mpv_match_val}", (200, 200, 200), 10, (self.display.get_height() - 126))
                self.show_text(f"MTO RATE: {(self.m[m_ind].mto_rate * 100.0):.2f}%", (200, 200, 200), 10, (self.display.get_height() - 114))
                # self.show_text(f"ZERO RATE: {(self.m[m_ind].zero_rate * 100.0):.2f}%", (200, 200, 200), 10, (self.display.get_height() - 114))
                self.show_text("Max Poss. Params: " + str(self.m[m_ind].max_possible_parameters), (200, 200, 200), 10, (self.display.get_height() - 102))
                # valA = (len(self.m[m_ind].e) * self.m[m_ind].params_per_e)
                valA = sum(((len(self.m[m_ind].e[a][0].keys()) * 2) + (len(self.m[m_ind].e[a][1].keys()) * 2) + 3) for a in self.m[m_ind].e.keys())
                valB = ((float(valA) / float(self.m[m_ind].max_possible_parameters)) * 100.0)
                # valC = ((float(valA) / float(175E9)) * 100.0)
                # stri = f"{valA}\t{valB:.2f}%\t{valC:.6f}%"
                stri = f"{valA}\t{valB:.2f}%"
                self.show_text("Total Params: " + stri, (200, 200, 200), 10, (self.display.get_height() - 90))
                self.show_text(f"Oracle Dim: {len(self.m[m_ind].e.keys())}", (200, 200, 200), 10, (self.display.get_height() - 78))
                self.show_text(f"Excess L Predictions M{m_ind}: {len(self.m[m_ind].excess_leaked_mpv)}", (200, 200, 200), 10, (self.display.get_height() - 66))
                self.show_text(f"Exposures: {self.s.num_exposures:.2f}", (200, 200, 200), 10, (self.display.get_height() - 54))
                self.show_text(f"EM M{m_ind}: {(self.m[m_ind].em * 100.0):.2f}%", (200, 200, 200), 10, (self.display.get_height() - 42))
                self.show_text(f"EM: {(self.em_avg * 100.0):.2f}%", (200, 200, 200), 10, (self.display.get_height() - 30))
            self.show_text(f"Frequency: {freq_string} Hz", (200, 200, 200), 10, (self.display.get_height() - 18))
        def manage_pygame_events(self):
            pygame.display.flip()
            for event in pygame.event.get():
                """ if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        manage_user_input()#---------------------------------INCLUDE THIS MAYBE???? """
                # if event.type == pygame.MOUSEBUTTONDOWN:
                    # pass
                    # mouse = pygame.mouse.get_pos()
                    # print([mouse[0],mouse[1]])
                    # pixel = pygame.Color(pygame.PixelArray(screensurf)[mouse[0],mouse[1]])
                    # print(pixel)
                    # print(screensurf.get_at(mouse))
                if event.type == pygame.QUIT:
                    self.save_thread = threading.Thread(target = self.save_model)
                    self.save_thread.start()
                    pygame.display.quit()
                    pygame.quit()
                    self.running = False
        def save_model(self):
            archive_save_list = [a.e.copy() for a in self.m]
            now = datetime.now()
            timestamp = now.strftime('%Y_%m_%d_%H_%M_%S')
            archive_filename = self.archive_directory + '/' + self.archive_directory + '_' + f'{timestamp}.pkl'
            with open(archive_filename, 'wb') as f:
                pickle.dump(archive_save_list, f)
            files = os.listdir(self.archive_directory)
            while len(files) > self.archive_capacity:
                file_paths = [os.path.join(self.archive_directory, filename) for filename in files]
                creation_times = [os.stat(file_path).st_ctime for file_path in file_paths]
                sorted_files = [file for _, file in sorted(zip(creation_times, files))]
                file_path = os.path.join(self.archive_directory, sorted_files[0])
                os.remove(file_path)
                files = os.listdir(self.archive_directory)
        def load_model(self):
            files = os.listdir(self.archive_directory)
            if files:
                file_paths = [os.path.join(self.archive_directory, filename) for filename in files]
                creation_times = [os.stat(file_path).st_ctime for file_path in file_paths]
                sorted_files = [file for _, file in sorted(zip(creation_times, files), reverse = True)]
                file_path = os.path.join(self.archive_directory, sorted_files[0])
                with open(file_path, 'rb') as f:
                    la = pickle.load(f)
                return la.copy()
            else: return []
    class Channel:
        def __init__(self):
            self.index = 0
            self.instances = dict()
        def add_instance(self, label_in, value_in):
            pass
    class Sensorium:
        def __init__(self, po_in):
            self.po = po_in
            #_____________________________________________________________SENSORIUM__________________________________________________
            self.exp_dict = dict()#----------------------------------------------------implement this!!!!!!!!!!!!
            self.permitted_chars_list = [chr(a) for a in range(32, 127)]
            # self.permitted_chars_list.extend(['\t', '\n', '\r', '\b', '\f'])
            self.permitted_chars_list.extend(['\t', '\n'])
            self.permitted_chars_dict = {char: i for i, char in enumerate(self.permitted_chars_list)}
            self.num_auxiliary_context_symbols = 0#-------------------------------------------------------------------------------HP
            self.auxiliary_context_symbols = [a for a in range(len(self.permitted_chars_list),
                                                               (len(self.permitted_chars_list) + self.num_auxiliary_context_symbols))]
            self.num_char_channels = 3#-5-------------------------------------------------------------------------------------------HP
            self.char_channel_dim = (len(self.permitted_chars_list) + len(self.auxiliary_context_symbols))
            self.char_channel_set = {a for a in range(self.num_char_channels)}
            self.channels = {a:self.char_channel_dim for a in self.char_channel_set}
            self.sv = self.temp_sv = set()
            #_________________________________________________________EXTERNAL DATA__________________________________________________
            file_path = "Conversational Dataset Bing Compose/Conversational_Dataset_Bing_Compose_V1.txt"
            self.lines = self.load_lines_from_file(file_path)
            # rand_val = random.randint(0, 2)
            # rand_val = random.randint(3, 5)
            rand_val = 2
            self.lines = self.lines[rand_val:(rand_val + 1)]#-------------------------------------------------------------------HP
            # self.lines[0] = self.lines[0][:400]#--------------------------------------------------------------------------------HP
            # random.shuffle(self.lines)
            print("Line Index: " + str(rand_val) + "  Num Chars Total: " + str(sum(len(a) for a in self.lines)))
            self.line_index = self.char_index = 0
            self.curr_line = self.lines[self.line_index]
            self.char_step = (self.num_char_channels - 1)#-1---------------------------------------------------------------------HP
            # self.char_step_min = (self.num_char_channels - 2)
            # self.char_step_max = self.num_char_channels
            #________________________________________________________DECODING & EVALUATION___________________________________________
            self.decoded_string_full = ""
            self.num_exposures = self.exposure_ct = 0
            self.enable_interoception = False
            self.interoception_ind_str = "INT " + ('-' * 150)
            self.exteroception_ind_str = "EXT " + ('*' * 150)
            self.sv_mpv_match_val = 0
            self.sv_mpv_match = False
        def update(self):
            mpv_decoded_char_list = [' ' for _ in range(len(self.char_channel_set))]
            # mpv_decoded_ppc_list = [0 for _ in range(len(self.ppc_channel_set))]
            mpv_decoded_cli_set = set()
            for a in self.po.m[0].mpv:
                cli = (a // self.po.m[0].M)#-----------------------cluster index
                chi = (cli // self.char_channel_dim)#--------------channel index---------------GENERALIZE THIS!!!!
                chv = (cli % self.char_channel_dim)#---------------channel value---------------GENERALIZE THIS!!!!
                if chi in self.char_channel_set: mpv_decoded_char_list[chi] = self.permitted_chars_list[chv]
                # if chi in self.ppc_channel_set: mpv_decoded_ppc_list[(chi - len(self.char_channel_set))] = chv
                mpv_decoded_cli_set.add(cli)
            t_str = ''.join(mpv_decoded_char_list[-self.char_step:])
            # t_str = "[" + ''.join(sv_decoded_char_list) + " || " + ''.join(mpv_decoded_char_list[-self.char_step:]) + "]"
            # t_str = "[" + ''.join(sv_decoded_char_list) + " || " + ''.join(mpv_decoded_char_list) + "]"
            self.decoded_string_full += t_str
            ind_str = self.interoception_ind_str if self.enable_interoception else self.exteroception_ind_str
            if (len(self.decoded_string_full) >= 500):
                print(ind_str + '\n' + "..." + self.decoded_string_full + "...")
                self.decoded_string_full = ""
            end = (len(self.curr_line) - len(self.char_channel_set))
            self.num_exposures = ((float(self.exposure_ct) + (float(self.char_index) / float(end))) / float(len(self.lines)))
            string_segment = self.curr_line[self.char_index:(self.char_index + len(self.char_channel_set))]
            # self.char_index += self.char_step
            # lr_val = (mpv_decoded_ppc_list[0] - mpv_decoded_ppc_list[1])
            lr_val = 0
            self.char_index += (self.char_step + lr_val)
            if (self.char_index > (len(self.curr_line) - 1)):
                self.char_index = (self.char_index - len(self.curr_line))
                self.line_index = ((self.line_index + 1) % len(self.lines))
                self.curr_line = self.lines[self.line_index]
                self.exposure_ct += 1
            if (self.char_index < 0):
                self.line_index = ((self.line_index + len(self.lines) - 1) % len(self.lines))
                self.curr_line = self.lines[self.line_index]
                self.char_index = (len(self.curr_line) + self.char_index)
            string_segment += self.curr_line[:len(self.char_channel_set)]
            self.temp_sv = set()
            ct = 0
            for key, value in self.channels.items():
                if (key in self.char_channel_set):
                    # char_index = self.permitted_chars_dict.get(string_segment[ct], 1)
                    char_index = self.permitted_chars_dict.get(string_segment[ct])
                    self.temp_sv.add((key * value) + char_index)
                    ct += 1
            self.sv_mpv_match_val = len(self.temp_sv ^ mpv_decoded_cli_set)
            # self.enable_interoception = ((self.sv_mpv_match_val == 0) and (self.exposure_ct > 2))
            # self.enable_interoception = False
            self.enable_interoception = (self.exposure_ct > 5)
            self.sv = mpv_decoded_cli_set.copy() if self.enable_interoception else self.temp_sv.copy()
        def load_lines_from_file(self, file_loc_in):
            s = ""
            out = []
            with open(file_loc_in,"r") as f:
                for line in f:
                    if(":::$" not in line): s += line
                    else:
                        if(len(s) > 0): out.append(s)
                        s = ""
                out.append(s)
            return out.copy()
    class Matrix:
        def __init__(self, po_in, mi_in, e_in):
            self.po = po_in
            self.ffi = (mi_in - 1)
            self.fbi = (mi_in + 1) if (mi_in < (self.po.H - 1)) else -1
            self.data_channels = dict()
            self.M = 200#-200 - 300------------------------------------------------------------------------------------------------------HP
            self.rfv_dim = len(self.po.s.channels)#-------------------------------------------------------------------------------------HP
            self.mem_max = 2000#--------------------------------------------------------------------------------------------------------HP
            self.iv = self.ov = self.mav = self.mpv = self.excess_leaked_mpv = set()
            self.e = e_in.copy()
            self.adc_max = 300#-2000 - 5000---------------------------------------------------------------------------------------------HP
            self.adc_min = math.floor(float(self.adc_max) * 0.95)#-0.95-----------------------------------------------------------------HP
            self.params_per_e = ((self.rfv_dim * 4) + 3)
            self.max_possible_parameters = (self.params_per_e * self.M * sum(self.po.s.channels.values()))
            self.em = self.zero_rate = self.mto_rate = 0
            self.knowledge_map = dict()
            self.aasc_mem_capacity = 1000#----------------------------------------------------------------------------------------------HP
            self.aasc_mem_avail_indices = {a for a in range(self.aasc_mem_capacity)}
            self.aasc_mem_pv = 1000#----------------------------------------------------------------------------------------------------HP
            self.aasc_mem = dict()
        def update(self):
            self.iv = self.po.s.sv.copy() if self.ffi == -1 else self.po.m[self.ffi].ov.copy()
            # self.iv = self.generate_abstraction(self.iv)
            fbv = self.po.m[self.fbi].mpv.copy() if (self.fbi != -1) else set()
            # fbv = self.po.m[self.fbi].mpv.copy() if (self.fbi != -1) else self.po.m[0].mpv.copy()
            fbv_conf_v = {(a // self.M):a for a in fbv
                          if (len(fbv & set(range(((a // self.M) * self.M), (((a // self.M) + 1) * self.M)))) == 1)}
            fbv_conf_v_keys = set(fbv_conf_v.keys())
            self.em = self.zero_rate = self.mto_rate = 0
            self.ov = set()
            mav_update = set()
            mpv_ack = set()
            new_adc = random.randint(self.adc_min, self.adc_max)
            ci_dict = {a:set(range((a * self.M), ((a + 1) * self.M))) for a in self.iv}
            for a, ci in ci_dict.items():
                pv = (ci & self.mpv)
                mpv_ack |= pv
                if len(pv) == 0:
                    self.ov.add(a)
                    self.em += 1.0
                    self.zero_rate += 1.0
                    ci_mod = (ci - set(self.e.keys()))
                    while (len(ci_mod) < 1):
                        for b in (set(self.e.keys()) & ci):
                            if (len(ci_mod) < 1):
                                self.e[b][0] = {key:(value - 1) for key, value in self.e[b][0].items() if (value > 0)}
                                if (not self.e[b][0]):
                                    self.e = {key:value for key, value in self.e.items() if (key != b)}
                                    ci_mod = (ci - set(self.e.keys()))
                            else: break
                    wi = ci_mod.pop()
                    tv = set()
                    if (a in fbv_conf_v_keys): tv.add(fbv_conf_v[a])
                    self.e[wi] = {0:{b:new_adc for b in self.mav}, 1:{b:new_adc for b in tv}}
                else:
                    wi = pv.pop()
                    tv = set()
                    if len(pv) > 1:
                        self.ov.add(a)
                        self.em += (float(len(pv) - 1) / float(self.M - 1))
                        self.mto_rate += 1.0
                        if (a in fbv_conf_v_keys): tv.add(fbv_conf_v[a])
                    for b in self.mav: self.e[wi][0][b] = new_adc
                    for b in tv: self.e[wi][1][b] = new_adc
                mav_update.add(wi)
            norm = float(max(1, len(self.iv)))
            self.em /= norm
            self.zero_rate /= norm
            self.mto_rate /= norm
            self.mav = mav_update.copy()
            self.excess_leaked_mpv = (self.mpv - mpv_ack)
            for a in self.excess_leaked_mpv:
                cli = (a // self.M)
                if (cli in fbv_conf_v_keys):
                    self.e[a][1][fbv_conf_v[cli]] = new_adc
                self.ov.add(cli)
            while (len(self.e.keys()) > self.mem_max):
                tl = list(self.e.keys())
                random.shuffle(tl)
                for a in tl:
                    self.e[a][0] = {key:(value - 1) for key, value in self.e[a][0].items() if (value > 0)}
                    self.e[a][1] = {key:(value - 1) for key, value in self.e[a][1].items() if (value > 0)}
                    if ((not self.e[a][0]) and (not self.e[a][1])):
                        self.e = {key:value for key, value in self.e.items() if (key != a)}
                        break
            if (len(self.e.keys()) > 0):
                #"""
                if (self.ffi == -1):
                    self.knowledge_map = dict()
                    for a in self.e.keys():
                        cli = (a // self.M)#------------------------------------cluster index
                        chi = (cli // self.po.s.char_channel_dim)#--------------channel index
                        chv = (cli % self.po.s.char_channel_dim)#---------------channel value
                        charA = self.po.s.permitted_chars_list[chv]
                        ts = [' ' for _ in range(len(self.po.s.char_channel_set))]
                        for b in self.e[a][0].keys():
                            cli = (b // self.M)#------------------------------------cluster index
                            chi = (cli // self.po.s.char_channel_dim)#--------------channel index
                            chv = (cli % self.po.s.char_channel_dim)#---------------channel value
                            charB = self.po.s.permitted_chars_list[chv]
                            # ts[chi] = chv
                            ts[chi] = charB
                        if charA not in self.knowledge_map.keys(): self.knowledge_map[charA] = [ts.copy()]
                        else:
                            if ts not in self.knowledge_map[charA]: self.knowledge_map[charA].append(ts.copy())
                #"""
                self.mpv = set()
                xor_heap = [((len(set(self.e[a][0].keys()) ^ self.mav) + len(set(self.e[a][1].keys()) ^ fbv)),
                             random.randrange(100), a) for a in self.e.keys()]
                heapq.heapify(xor_heap)
                num_set_pred = len(self.po.s.channels)
                while (xor_heap and (len(self.mpv) < num_set_pred)):
                    dv, rand_val, key = heapq.heappop(xor_heap)
                    if key not in self.mpv: self.mpv.add(key)
        def generate_abstraction(self, v_in):
            out = v_in.copy()
            if (len(self.aasc_mem_avail_indices) < 2):
                si = list(self.aasc_mem.keys())
                random.shuffle(si)
                heap = []
                for a in si:
                    if (self.aasc_mem[a][1] > 0): self.aasc_mem[a][1] -= 1
                    heap.append((self.aasc_mem[a][1], a))
                # heap = [(self.mem[a][1], a) for a in si]
                heapq.heapify(heap)
                while(heap and (len(self.aasc_mem_avail_indices) < 2)):
                    d, key = heapq.heappop(heap)
                    self.aasc_mem_avail_indices.add(key)
                    del self.aasc_mem[key]
            if (len(self.aasc_mem.keys()) > 0):
                avg_v = dict()
                si = list(self.aasc_mem.keys())
                random.shuffle(si)
                d_max = 10#---------------------------------------------------------------------------------------------------------------HP
                ns = 10#------------------------------------------------------------------------------------------------------------------HP
                vp = 15#-------------------------------------------------------------------------------------------------------------------HP
                heap = [((self.aasc_mem[a][0] ^ v_in), a) for a in si]
                heapq.heapify(heap)
                vi = set()
                while (heap and (len(vi) < ns)):
                    d, key = heapq.heappop(heap)
                    for a in self.aasc_mem[key][0]:
                        if (a in avg_v.keys()): avg_v[a] += 1
                        else: avg_v[a] = 1
                        for b in (avg_v.keys()):
                            if (b != a): avg_v[b] -= 1
                    self.aasc_mem[key][1] = self.aasc_mem_pv
                    vi.add(key)
                avg_vec = {a for a, b in avg_v.items() if (b > 0)}
                if (len(self.aasc_mem.keys()) > 995): out = avg_vec.copy()
                variance = (avg_vec ^ v_in)
                if (len(variance) > vp):
                    # out = avg_vec.copy()
                    ri = random.choice(list(self.aasc_mem_avail_indices))
                    self.aasc_mem_avail_indices.remove(ri)
                    self.aasc_mem[ri] = [avg_vec.copy(), self.aasc_mem_pv]
                # else: out = avg_vec.copy()
            # else:
            ri = random.choice(list(self.aasc_mem_avail_indices))
            self.aasc_mem_avail_indices.remove(ri)
            self.aasc_mem[ri] = [v_in.copy(), self.aasc_mem_pv]
            return out.copy()
    oracle = Oracle()
    oracle.update()
main()
