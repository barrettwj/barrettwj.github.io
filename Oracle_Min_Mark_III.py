import random
import math
import time
import pickle
import sys
import os
import pygame
import threading
from datetime import datetime
def main():
    class Oracle:
        def __init__(self):
            #______________________________________________________________________ARCHIVING___________________________________________
            self.auto_archiving_enabled = False
            self.auto_load_model = False
            self.archive_directory = 'Oracle_Min_Mark_III_Archive'
            self.archive_load = self.load_model() if self.auto_load_model else []
            self.archive_capacity = 10#------------------------------------------------------------------------------------HyperParameter
            self.save_thread = threading.Thread(target = self.save_model)
            self.save_period = 1000#----------------------------------------------------------------------------------------HyperParameter
            self.save_counter = 0
            #____________________________________________________________________ORACLE__________________________________________________
            self.model_hps = []
            if len(self.archive_load) == 0:
                self.H = 3#----------------------------------------------------------------------------------------------HyperParameter
            else:
                self.model_hps = self.archive_load.copy()
                self.H = len(self.model_hps)
            self.s = Sensorium(self)
            if len(self.archive_load) == 0:
                self.m = [Matrix(self, i, dict()) for i in range(self.H)]
            else:
                self.m = [Matrix(self, i, a.copy()) for i, a in enumerate(self.model_hps)]
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
            ar = (16.0 / 9.0)
            self.display_w = 300
            self.display_h = round(float(self.display_w) / ar)
            os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % ((1500 - self.display_w), 100)
            pygame.init()
            self.display = pygame.display.set_mode((self.display_w, self.display_h))
            pygame.display.set_caption('Oracle Min Mark III')
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
                # self.show_text("RE: " + f"{(self.re_rate_avg * 100.0):.2f}" + "%", (200, 200, 200), 10, (self.screen.get_height() - 42))
                self.show_text(f"Excess A Predictions M0: {len(self.m[0].excess_actual_mpv)}", (200, 200, 200), 10, (self.display.get_height() - 126))
                self.show_text(f"MTO RATE: {(self.m[0].mto_rate * 100.0):.2f}%", (200, 200, 200), 10, (self.display.get_height() - 114))
                # self.show_text(f"ZERO RATE: {(self.m[0].zero_rate * 100.0):.2f}%", (200, 200, 200), 10, (self.display.get_height() - 114))
                self.show_text("Max Poss. Params: " + str(self.m[0].max_possible_parameters), (200, 200, 200), 10, (self.display.get_height() - 102))
                valA = (len(self.m[0].e) * self.m[0].params_per_e)
                valB = ((float(valA) / float(self.m[0].max_possible_parameters)) * 100.0)
                valC = ((float(valA) / float(175E9)) * 100.0)
                stri = f"{valA}\t{valB:.2f}%\t{valC:.6f}%"
                self.show_text("Total Params: " + stri, (200, 200, 200), 10, (self.display.get_height() - 90))
                self.show_text(f"Oracle Dim: {len(self.m[0].e)}", (200, 200, 200), 10, (self.display.get_height() - 78))
                self.show_text(f"Excess L Predictions M0: {len(self.m[0].excess_leaked_mpv)}", (200, 200, 200), 10, (self.display.get_height() - 66))
                self.show_text(f"Exposures M0: {self.s.num_exposures:.2f}", (200, 200, 200), 10, (self.display.get_height() - 54))
                self.show_text(f"EM M0: {(self.m[0].em * 100.0):.2f}%", (200, 200, 200), 10, (self.display.get_height() - 42))
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
    class Sensorium:
        def __init__(self, po_in):
            #_____________________________________________________________SENSORIUM__________________________________________________
            self.po = po_in
            self.permitted_chars = [chr(a) for a in range(32, 127)]
            # self.permitted_chars.extend(['\t', '\n', '\r', '\b', '\f'])
            self.permitted_chars.extend(['\t', '\n'])
            self.num_auxiliary_context_symbols = 0#--------------------------------------------------------------HyperParameter
            self.auxiliary_context_symbols = [a for a in range(len(self.permitted_chars),
                                                               (len(self.permitted_chars) + self.num_auxiliary_context_symbols))]
            self.num_char_channels = 5#---------------------------------------------------------------------------------HyperParameter
            self.char_channel_dim = (len(self.permitted_chars) + len(self.auxiliary_context_symbols))
            self.char_channel_set = {a for a in range(self.num_char_channels)}
            self.channels = {a:self.char_channel_dim for a in self.char_channel_set}
            self.num_ppc_channels = 2
            # self.ppc_channel_dim = 10
            self.ppc_channel_dim = self.char_channel_dim
            self.ppc_channel_set = {(self.num_char_channels + a) for a in range(self.num_ppc_channels)}
            # for a in self.ppc_channel_set: self.channels[a] = self.ppc_channel_dim
            self.sv = set()
            #_________________________________________________________DATA__________________________________________________________
            file_path = "Conversational Dataset Bing Compose/Conversational_Dataset_Bing_Compose_V1.txt"
            self.lines = self.load_lines_from_file(file_path)
            rand_val = random.randint(0, 2)
            # rand_val = random.randint(3, 5)
            # rand_val = 3
            self.lines = self.lines[rand_val:(rand_val + 1)]#-------------------------------------------------------HyperParameter
            self.lines[0] = self.lines[0][:600]#--------------------------------------------------------------------HyperParameter
            # random.shuffle(self.lines)
            num_chars = sum(len(a) for a in self.lines)
            print("Line Index: " + str(rand_val) + "  Num Chars Total: " + str(num_chars))
            self.line_index = self.char_index = 0
            self.curr_line = self.lines[self.line_index]
            self.char_step = (self.num_char_channels - 1)#----------------------------------------------------------HyperParameter
            self.char_step_min = 1
            self.char_step_max = self.num_char_channels
            self.string_segment = ""
            #________________________________________________________EVALUATION_____________________________________________________
            self.mpv_decoded_cli_set = set()
            self.decoded_string_full = ""
            self.num_exposures = self.exposure_ct = 0
            self.enable_interoception = False
            self.interoception_ind_str = "INT " + ('-' * 150)
            self.exteroception_ind_str = "EXT " + ('*' * 150)
            self.ind_str = self.interoception_ind_str if self.enable_interoception else self.exteroception_ind_str
            self.sv_mpv_match = False
        def update(self):
            # sv_decoded_char_list = ['_'] * len(self.channels)
            # for a in self.sv:
            #     chi, chv = divmod(a, self.channel_dim)#-(channel index, channel value)
            #     sv_decoded_char_list[chi] = self.permitted_chars[chv]
            mpv_decoded_char_list = ['_'] * len(self.char_channel_set)
            mpv_decoded_ppc_list = [0] * len(self.ppc_channel_set)
            self.mpv_decoded_cli_set = set()
            for a in self.po.m[0].mpv:
                cli = (a // self.po.m[0].M)#-----------------cluster index
                chi = (cli // self.char_channel_dim)#--------------channel index---------------GENERALIZE THIS!!!!
                chv = (cli % self.char_channel_dim)#----------------channel value--------------GENERALIZE THIS!!!!
                if chi in self.char_channel_set: mpv_decoded_char_list[chi] = self.permitted_chars[chv]
                if chi in self.ppc_channel_set: mpv_decoded_ppc_list[(chi - len(self.char_channel_set))] = chv
                self.mpv_decoded_cli_set.add(cli)
            t_str = ''.join(mpv_decoded_char_list[-self.char_step:])
            # t_str = "[" + ''.join(sv_decoded_char_list) + " || " + ''.join(mpv_decoded_char_list[-self.char_step:]) + "]"
            # t_str = "[" + ''.join(sv_decoded_char_list) + " || " + ''.join(mpv_decoded_char_list) + "]"
            self.decoded_string_full += t_str
            self.ind_str = self.interoception_ind_str if self.enable_interoception else self.exteroception_ind_str
            if len(self.decoded_string_full) >= 500:
                print(self.ind_str + "\n" + self.decoded_string_full)
                self.decoded_string_full = ""
            end = (len(self.curr_line) - len(self.char_channel_set))
            self.num_exposures = ((float(self.exposure_ct) + (float(self.char_index) / float(end))) / float(len(self.lines)))
            self.string_segment = self.curr_line[self.char_index:(self.char_index + len(self.char_channel_set))]
            # self.char_index += self.char_step
            # lr_val = (mpv_decoded_ppc_list[0] - mpv_decoded_ppc_list[1])
            lr_val = 0
            self.char_index += (self.char_step + lr_val)
            if (self.char_index > (len(self.curr_line) - 1)):
                self.char_index = (self.char_index - len(self.curr_line))
                self.line_index = ((self.line_index + 1) % len(self.lines))
                self.curr_line = self.lines[self.line_index]
                self.exposure_ct += 1
            if self.char_index < 0:
                self.line_index = ((self.line_index + len(self.lines) - 1) % len(self.lines))
                self.curr_line = self.lines[self.line_index]
                self.char_index = (len(self.curr_line) + self.char_index)
            ct = 0
            while (len(self.string_segment) < len(self.char_channel_set)):
                self.string_segment += self.curr_line[ct]
                ct += 1
            temp_sv = set()
            ct = 0
            for key, value in self.channels.items():
                if key in self.char_channel_set:
                    # temp_sv.add(((key * value) + self.permitted_chars.index(self.string_segment[ct])))
                    if ct < len(self.channels):
                        temp_sv.add(((key * value) + self.permitted_chars.index(self.string_segment[ct])))
                    else:
                        val = 1
                        temp_sv.add(((key * value) + val))
                        # temp_sv.add(((key * value) + self.permitted_chars.index(self.string_segment[ct])))
                    ct += 1
                if key in self.ppc_channel_set:
                    pass
                    # val = (self.permitted_chars.index(self.string_segment[ct]) - 2)
                    # temp_sv.add(((key * value) + val))
            self.sv_mpv_match = (len(temp_sv ^ self.mpv_decoded_cli_set) == 0)
            self.enable_interoception = (self.sv_mpv_match and (self.exposure_ct > 3))
            # self.enable_interoception = False
            # sv_prev = self.sv.copy()
            if (self.enable_interoception):
                # tst = " th"
                # tsv = [((key * value) + self.permitted_chars.index(tst[key])) for key, value in self.channels.items()]
                # if sv_prev == tsv: print(mpv_decoded_char_list)
                self.sv = self.mpv_decoded_cli_set.copy()
            else: self.sv = temp_sv.copy()
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
            self.M = 100#-200 - 300------------------------------------------------------------------------------------------HyperParameter
            self.rfv_dim = len(self.po.s.channels)#--------------------------------------------------------------------------HyperParameter
            self.iv = self.ov = self.mav = self.mpv = self.excess_leaked_mpv = self.excess_actual_mpv = set()
            self.e = e_in.copy()
            self.adc_max = 1000#-2000 - 5000-----MUST BE GREATER THAN 0!!!!---MUSN'T BE SET TOO LOW!!!!----------------------HyperParameter
            self.adc_min = math.floor(float(self.adc_max) * 0.95)#-0.95------------------------------------------------------HyperParameter
            self.adc_enabled = (self.adc_min > 0)
            self.params_per_e = (self.rfv_dim * 2)
            self.max_possible_parameters = (self.params_per_e * self.M * sum(self.po.s.channels.values()))
            self.em = self.zero_rate = self.mto_rate = 0
        def update(self):
            self.iv = self.po.s.sv if self.ffi == -1 else self.po.m[self.ffi].ov
            if self.fbi != -1:
                cli = {(a // self.M) for a in self.po.m[self.fbi].mpv}
                self.iv -= cli#----------------------------------------THIS POTENTIALLY DECREASES len(self.mav)
            else:
                cli = {(a // self.M) for a in self.po.m[0].mpv}
                self.iv -= cli
            self.em = self.zero_rate = self.mto_rate = 0
            mav_update = set()
            mpv_ack = set()
            self.ov = set()
            for a in self.iv:
                ci = set(range((a * self.M), ((a + 1) * self.M)))
                new_adc = random.randint(self.adc_min, self.adc_max)
                pv = (ci & self.mpv & set(self.e.keys()))
                mpv_ack |= pv
                if len(pv) == 0:
                    self.em += 1.0
                    self.ov.add(a)
                    self.zero_rate += 1.0
                    ci_mod = (ci - set(self.e.keys()))
                    while len(ci_mod) < 1:#-------------------------------------------------------------------------------HyperParameter
                        keys_copy = list(set(self.e.keys()) & ci)
                        random.shuffle(keys_copy)
                        for b in keys_copy:
                            self.e[b] = {key:(value - 1) for key, value in self.e[b].items() if (value > 0)}
                            if len(self.e[b]) == 0:
                                del self.e[b]
                                break
                        ci_mod = (ci - set(self.e.keys()))
                    wi = random.choice(list(ci_mod))
                    self.e[wi] = {b:new_adc for b in self.mav}
                else:
                    wi = random.choice(list(pv))
                    if len(pv) > 1:#---------I'M HOPING THIS CAN ALWAYS BE IMPOSSIBLE HERE AND DEALT WITH DURING GENERATION OF self.mpv !!!
                        ##############--------I think I should ideally create a 3rd context which wins out if 2 tie in activation?????
                        print("MTO @ " + str(self.po.cycle))
                        self.em += (float(len(pv) - 1) / float(self.M - 1))
                        self.ov.add(a)
                        self.mto_rate += 1.0
                        if wi in self.e: new_adc = max(self.e[wi].values())
                    for b in self.mav: self.e[wi][b] = new_adc                    
                    # if ((len(self.e[wi]) > 7) and (self.mi == 0)): print(len(self.e[wi]))
                mav_update.add(wi)
            denom = float(max(1, len(self.iv)))
            self.em /= denom
            self.zero_rate /= denom
            self.mto_rate /= denom
            self.mav = mav_update.copy()
            self.excess_leaked_mpv = (self.mpv - mpv_ack)###----I need to use this to drive beh/att shifts?; should perhaps be the encoding for that??
            excess_cli = {(a // self.M) for a in self.excess_leaked_mpv}
            self.ov |= excess_cli
            # if ((self.adc_enabled and (self.em > 0)) or (len(self.e) > 8000)):#-----------------------------------------------HyperParameter
            # self.adc_enabled = False
            if self.adc_enabled:
            # if (self.adc_enabled and (self.em > 0)):
                for b in self.e.keys(): self.e[b] = {key:(value - 1) for key, value in self.e[b].items() if (value > 0)}
                self.e = {key:value for key, value in self.e.items() if (len(value) > 0)}
            if len(self.e) > 0:
                rv = min(len(set(value.keys()) ^ self.mav) for value in self.e.values())
                # rv_max = (len(self.mav) * 5)#----------------------------------------------------------------------------------------HyperParameter
                rv_max = (len(self.mav) * 3)#----------------------------------------------------------------------------------------HyperParameter
                self.mpv = set()
                skip_indices = set()
                if self.fbi != -1: skip_indices = self.po.m[self.fbi].mpv.copy()
                cli_filled = set()
                chi_filled = set()
                self.excess_actual_mpv = set()
                num_to_set_predictive = self.rfv_dim#---------------------------------------------------------------------------------HyperParameter
                # while ((len(self.mpv) < num_to_set_predictive) and (len(skip_indices) < len(self.e)) and (rv < rv_max)):
                while ((len(skip_indices) < len(self.e)) and (rv < rv_max)):
                # while (len(skip_indices) < len(self.e)):
                    new_set = {key for key, value in self.e.items()
                            if ((len(set(value.keys()) ^ self.mav) == rv) and (key not in skip_indices))}
                    # while ((len(self.mpv) < num_to_set_predictive) and (len(new_set) > 0)):
                    while (len(new_set) > 0):
                        ri = random.choice(list(new_set))
                        new_set.remove(ri)
                        cli = (ri // self.M)
                        chi = (cli // self.po.s.char_channel_dim)#-----------------------------------------GENERALIZE THIS!!!!
                        if ((cli in cli_filled) or (chi in chi_filled)): self.excess_actual_mpv.add(ri)
                        if ((cli not in cli_filled) and (chi not in chi_filled)):
                            self.mpv.add(ri)
                            cli_filled.add(cli)
                            chi_filled.add(chi)
                        skip_indices.add(ri)
                    rv += 1
            # excess_cli = {(a // self.M) for a in self.excess_actual_mpv}
            # self.ov |= excess_cli
        def register_data_channel(self, label_in, dict_in):
            if label_in not in self.data_channels:
                collision = False
                for value in self.data_channels.values():
                    for a in value.values():
                        for keyB, valueB in dict_in.items():
                            if a == valueB: collision = True
            else: print("LABEL ALREADY EXISTS!!!")
        def deregister_data_channel(self, label_in):
            if label_in in self.data_channels: del self.data_channels[label_in]
    oracle = Oracle()
    oracle.update()
main()
