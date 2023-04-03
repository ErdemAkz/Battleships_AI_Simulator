import pygame as pg
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import random
import sys
import time

matplotlib.use('TkAgg')

pg.init()
pg.display.set_caption("Battleship")

SCREEN_WIDTH  = 600
SCREEN_HEIGHT = 600
BOARD_SIZE = 10
SQUARE_SIZE = 60
SCREEN = pg.display.set_mode((SCREEN_WIDTH+1, SCREEN_HEIGHT+1))

BEYAZ = (255, 255, 255)
SIYAH = (0, 0, 0)
KIRMIZI = (200, 0, 0)

class Oyun:

    def __init__(self):
        self.GEMI_HARITA = np.zeros([10,10])
        self.ATES_NOKTALARI = np.zeros([10,10])
        self.GEMI_KOORDINAT = dict()
        self.KOORDINATLAR = dict()
        self.BATAN_GEMI_KOORDINATLARI = []
        self.OLASILIK_HARITA = np.zeros([10,10])
        self.GEMILER = {"Amiral Gemisi":5, "Kuvazor Gemisi":4, "Muhrip":3, "Hucumbot":3, "Denizalti":2}
        self.DELAY = 300
        self.GUESS_EVENT = pg.USEREVENT
        pg.time.set_timer(self.GUESS_EVENT, self.DELAY)
        self.RUNNING = True
        self.PUAN = 0
        self.targets = []
        self.goal = sum(self.GEMILER.values())

    def Gemi_Yerlestir(self):
        for gemi, gemi_boyutu in self.GEMILER.items():
            while True:
                start_row = random.choice(range(10))
                start_col = random.choice(range(10))

                # randomly choose an axis to hold constant
                const_axis = random.choice(["row", "col"])

                # randomly choose a direction
                direction = random.choice(["up", "down"])

                # select endpoint
                if const_axis == "row":
                    if direction == "up" and start_col - gemi_boyutu >= 0:
                        end_row = start_row + 1
                        end_col = start_col - gemi_boyutu
                        start_col, end_col = end_col, start_col
                    elif direction == "down" and start_col + gemi_boyutu <= 9:
                        end_row = start_row + 1
                        end_col = start_col + gemi_boyutu
                    else:
                        continue

                elif const_axis == "col":
                    if direction == "up" and start_row - gemi_boyutu >= 0:
                        end_row = start_row - gemi_boyutu
                        start_row, end_row = end_row, start_row
                        end_col = start_col + 1
                    elif direction == "down" and start_row + gemi_boyutu <= 9:
                        end_row = start_row + gemi_boyutu
                        end_col = start_col + 1
                    else:
                        continue

                # check that all spaces that we want to insert into are clear
                if np.all(self.GEMI_HARITA[start_row:end_row, start_col:end_col] == 0):
                    self.GEMI_HARITA[start_row:end_row, start_col:end_col] = 1

                    # create a quickly-searchable dictionary of coordinates mapped to ships
                    if const_axis == "row":
                        coord_list = list(zip([start_row] * gemi_boyutu, [col for col in range(start_col, end_col)]))
                        self.GEMI_KOORDINAT[gemi] = coord_list
                        for coord in coord_list:
                            self.KOORDINATLAR[coord] = gemi
                    elif const_axis == "col":
                        coord_list = list(zip([row for row in range(start_row, end_row)], [start_col] * gemi_boyutu))
                        self.GEMI_KOORDINAT[gemi] = coord_list
                        for coord in coord_list:
                            self.KOORDINATLAR[coord] = gemi

                else:
                    continue
                break

    def ates_et(self, hedef_x, hedef_y):
        self.ATES_NOKTALARI[hedef_x][hedef_y] = 1
        gemi_batti = 0
        if self.GEMI_HARITA[hedef_x][hedef_y] == 1:
            self.PUAN += 1
            gemi_batti = 1
            vurulan_gemi = self.KOORDINATLAR.get((hedef_x, hedef_y))
            for x,y in self.GEMI_KOORDINAT.get(vurulan_gemi):
                if self.ATES_NOKTALARI[x][y] == 0:
                    gemi_batti = 0

            ship = self.KOORDINATLAR.pop((hedef_x, hedef_y))
            # if ship is sunk, add its coordinates to list of sunken ship coordinates
            if ship not in self.KOORDINATLAR.values():
                self.BATAN_GEMI_KOORDINATLARI.extend(self.GEMI_KOORDINAT[ship])
                self.GEMI_KOORDINAT.pop(ship)

            if(gemi_batti):
                self.GEMILER.pop(vurulan_gemi)

            if self.PUAN == self.goal:
                self.RUNNING = False


        return gemi_batti

    def get_en_uzun_gemi_alive(self):
        return max(self.GEMILER.values())

    def rastgele_koordinat(self):
        x = 0
        y = 0
        while True:
            x, y = random.choice(range(10)), random.choice(range(10))
            if self.ATES_NOKTALARI[x][y] == 1:
                continue;
            else:
                break

        return x,y

    def capraz_rastgele_koordinat(self, length=None):
        x = 0
        y = 0
        while True:
            x, y = random.choice(range(10)), random.choice(range(10))
            if length:
                if (x + y) % length != 0:
                    continue
            if self.ATES_NOKTALARI[x][y] == 1:
                continue
            else:
                break

        return x, y

    def olasilik_haritasi_yarat(self):
        prob_map = np.zeros([10, 10])
        for ship_name in set(self.KOORDINATLAR.values()):
            ship_size = self.GEMILER[ship_name]
            use_size = ship_size - 1
            # check where a ship will fit on the board
            for row in range(10):
                for col in range(10):
                    if self.ATES_NOKTALARI[row][col] != 1:
                        # get potential ship endpoints
                        endpoints = []
                        # add 1 to all endpoints to compensate for python indexing
                        if row - use_size >= 0:
                            endpoints.append(((row - use_size, col), (row + 1, col + 1)))
                        if row + use_size <= 9:
                            endpoints.append(((row, col), (row + use_size + 1, col + 1)))
                        if col - use_size >= 0:
                            endpoints.append(((row, col - use_size), (row + 1, col + 1)))
                        if col + use_size <= 9:
                            endpoints.append(((row, col), (row + 1, col + use_size + 1)))

                        for (start_row, start_col), (end_row, end_col) in endpoints:
                            if np.all(self.ATES_NOKTALARI[start_row:end_row, start_col:end_col] == 0):
                                prob_map[start_row:end_row, start_col:end_col] += 1

                    # increase probability of attacking squares near successful hits
                    # Bir noktayi vurduysak ve o noktada gemi varsa ve o gemi henuz batmadiysa
                    if self.ATES_NOKTALARI[row][col] == 1 and \
                            self.GEMI_HARITA[row][col] == 1 and \
                            (row, col) not in self.BATAN_GEMI_KOORDINATLARI:  # un-weight hits on sunk ships
                        #vurduğumuz noktanın sağ tarafi harita dışı değilse ve sağ noktasina ates edilmediyse
                        if (row + 1 <= 9) and (self.ATES_NOKTALARI[row + 1][col] == 0):
                            #o noktanın sol noktası harita icindeyse ve ates edildiyse ve bir gemi varsa
                            #ama o gemi batmayan bir gemiyse
                            if (row - 1 >= 0) and \
                                    (row - 1, col) not in self.BATAN_GEMI_KOORDINATLARI and \
                                    (self.ATES_NOKTALARI[row - 1][col] == self.GEMI_HARITA[row - 1][col] == 1):
                                prob_map[row + 1][col] += 15
                            else:
                                prob_map[row + 1][col] += 10

                        if (row - 1 >= 0) and (self.ATES_NOKTALARI[row - 1][col] == 0):
                            if (row + 1 <= 9) and \
                                    (row + 1, col) not in self.BATAN_GEMI_KOORDINATLARI and \
                                    (self.ATES_NOKTALARI[row + 1][col] == self.GEMI_HARITA[row + 1][col] == 1):
                                prob_map[row - 1][col] += 15
                            else:
                                prob_map[row - 1][col] += 10

                        if (col + 1 <= 9) and (self.ATES_NOKTALARI[row][col + 1] == 0):
                            if (col - 1 >= 0) and \
                                    (row, col - 1) not in self.BATAN_GEMI_KOORDINATLARI and \
                                    (self.ATES_NOKTALARI[row][col - 1] == self.GEMI_HARITA[row][col - 1] == 1):
                                prob_map[row][col + 1] += 15
                            else:
                                prob_map[row][col + 1] += 10

                        if (col - 1 >= 0) and (self.ATES_NOKTALARI[row][col - 1] == 0):
                            if (col + 1 <= 9) and \
                                    (row, col + 1) not in self.BATAN_GEMI_KOORDINATLARI and \
                                    (self.ATES_NOKTALARI[row][col + 1] == self.GEMI_HARITA[row][col + 1] == 1):
                                prob_map[row][col - 1] += 15
                            else:
                                prob_map[row][col - 1] += 10

                    # decrease probability for misses to zero
                    elif self.ATES_NOKTALARI[row][col] == 1 and self.GEMI_HARITA[row][col] != 1:
                        prob_map[row][col] = 0

        self.OLASILIK_HARITA = prob_map

    def olasilik_tahmini(self):
        self.olasilik_haritasi_yarat()
        # get the row, col numbers of the largest element in PROB_MAP
        # https://thispointer.com/find-max-value-its-index-in-numpy-array-numpy-amax/
        max_indices = np.where(self.OLASILIK_HARITA == np.amax(self.OLASILIK_HARITA))
        guess_row, guess_col = max_indices[0][0], max_indices[1][0]

        return guess_row, guess_col

    def draw_heat_map(self):
        self.olasilik_haritasi_yarat()
        board_y = 0
        for i in range(10):
            board_x = 700
            for j in range(10):
                if np.sum(self.OLASILIK_HARITA):
                    size_factor = 255 * self.OLASILIK_HARITA[i][j] / np.amax(self.OLASILIK_HARITA)
                    red, green, blue = (0, 0, 0)
                    if size_factor >= 220:
                        red = size_factor
                        green = 0
                        blue = 0
                    elif 70 <= size_factor < 220:
                        red = size_factor
                        green = size_factor // 3
                        blue = 0
                    elif 0 <= size_factor < 70:
                        red = 0
                        green = 0
                        blue = size_factor
                    pg.draw.rect(SCREEN, (red, green, blue), pg.Rect(board_x, board_y, SQUARE_SIZE, SQUARE_SIZE))

                board_x += SQUARE_SIZE
            board_y += SQUARE_SIZE

        for i in range(700, 1360, 60):
            pg.draw.line(SCREEN, BEYAZ, (i, 0), (i, 1300))
        for i in range(0, 660, 60):
            pg.draw.line(SCREEN, BEYAZ, (700, i), (1300, i))

    def draw_Board(self):
        y = 0
        for i in range(BOARD_SIZE):
            x = 0
            for j in range(BOARD_SIZE):
                if self.GEMI_HARITA[i][j] == 0:
                    pg.draw.rect(SCREEN, SIYAH, pg.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE))
                elif self.GEMI_HARITA[i][j] == 1:
                    pg.draw.rect(SCREEN, (111, 111, 111), pg.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE))
                if self.ATES_NOKTALARI[i][j] == 1:
                    pg.draw.line(SCREEN, KIRMIZI,
                                 (x, y),
                                 (x + SQUARE_SIZE, y + SQUARE_SIZE),
                                 width=5)
                    pg.draw.line(SCREEN, KIRMIZI,
                                 (x, y + SQUARE_SIZE),
                                 (x + SQUARE_SIZE, y),
                                 width=5)
                x = x + SQUARE_SIZE

            y = y + SQUARE_SIZE

        for i in range(0, 660, 60):
            pg.draw.line(SCREEN, BEYAZ, (0, i), (600, i))
            pg.draw.line(SCREEN, BEYAZ, (i, 0), (i, 600))

    def hunt_target(self):
        # enter hunt mode when no more targets left
        if not self.targets:
            guess_row, guess_col = self.rastgele_koordinat()
        else:
            guess_row, guess_col = self.targets.pop()

        if self.GEMI_HARITA[guess_row][guess_col] == 1:
            # add all adjacent squares to list of potential targets where possible
            potential_targets = [(guess_row + 1, guess_col), (guess_row, guess_col + 1),
                                 (guess_row - 1, guess_col), (guess_row, guess_col - 1)]
            for target_row, target_col in potential_targets:
                if (0 <= target_row <= 9) and \
                        (0 <= target_col <= 9) and \
                        (self.ATES_NOKTALARI[target_row][target_col] == 0) and \
                        ((target_row, target_col) not in self.targets):
                    self.targets.append((target_row, target_col))

        return guess_row, guess_col

    def hunt_target_capraz_koordinat(self):
        # enter hunt mode when no more targets left
        if not self.targets:
            len = self.get_en_uzun_gemi_alive()
            guess_row, guess_col = self.capraz_rastgele_koordinat(length=len)
        else:
            guess_row, guess_col = self.targets.pop()

        if self.GEMI_HARITA[guess_row][guess_col] == 1:
            # add all adjacent squares to list of potential targets where possible
            potential_targets = [(guess_row + 1, guess_col), (guess_row, guess_col + 1),
                                 (guess_row - 1, guess_col), (guess_row, guess_col - 1)]
            for target_row, target_col in potential_targets:
                if (0 <= target_row <= 9) and \
                        (0 <= target_col <= 9) and \
                        (self.ATES_NOKTALARI[target_row][target_col] == 0) and \
                        ((target_row, target_col) not in self.targets):
                    self.targets.append((target_row, target_col))

        return guess_row, guess_col

    def hamle_hesapla(self,mod):
        if (mod == 0):
            x, y = self.rastgele_koordinat()
        elif (mod == 1):
            x, y = self.hunt_target()
        elif (mod == 2):
            x, y = self.hunt_target_capraz_koordinat()
        elif (mod == 3):
            x, y = self.olasilik_tahmini()


        return x,y

    def Oyna(self,mod=0,statics=0):
        self.Gemi_Yerlestir()
        if(mod == 3):
            self.olasilik_haritasi_yarat()


        hamle_sayisi = 0
        if(statics):
            while self.RUNNING:
                x,y = self.hamle_hesapla(mod)
                self.ates_et(x,y)
                hamle_sayisi += 1
            return hamle_sayisi

        while self.RUNNING:

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.RUNNING = False

                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        self.RUNNING = False
                    elif event.key == pg.K_RIGHT:

                        x, y = self.hamle_hesapla(mod)
                        self.ates_et(x, y)
                        hamle_sayisi += 1

                    elif event.key == pg.K_SPACE:

                        if self.DELAY == 999999:
                            self.DELAY = 300
                        else:
                            self.DELAY = 999999
                        pg.time.set_timer(self.GUESS_EVENT, self.DELAY)

                elif event.type == self.GUESS_EVENT:
                    x, y = self.hamle_hesapla(mod)
                    self.ates_et(x, y)
                    hamle_sayisi += 1

            self.draw_Board()
            if(mod == 3):
                self.draw_heat_map()
            pg.display.update()

        return hamle_sayisi

if __name__ == '__main__':


    # 0 - 1 tur oyna
    # 1 - 100 tur simule et
    statics = 1
    oyun_sayisi = 30


    # 0 - rastgele
    # 1 - hunt method
    # 2 - hunt method capraz koordinat
    # 3 - olasilik
    search_mod = 3

    s_mod = ""
    if search_mod == 0:
        s_mod = "Rastgele Ateş"
    elif search_mod == 1:
        s_mod = "Hunt Metodu"
    elif search_mod == 2:
        s_mod = "Çapraz Koordinat Hunt Metodu"
    elif search_mod == 3:
        s_mod = "Olasılık Haritasi Yöntemi"

    if (search_mod == 3):
        SCREEN_WIDTH = 1300
        SCREEN = pg.display.set_mode((SCREEN_WIDTH + 1, SCREEN_HEIGHT + 1))
        
    if(statics):
        top = 0
        x = []
        y = []
        # get the start time
        st = time.time()
        for i in range(oyun_sayisi):
            hamle_sayisi = Oyun().Oyna(search_mod, statics)

            top += hamle_sayisi

            y.append(hamle_sayisi)
            x.append(i)

        print("Avarage turns: " + str(top / oyun_sayisi))
        print("Min Turns: "+ str(min(y)))
        print("Max Turns: "+ str(max(y)))

        et = time.time()
        elapsed_time = et - st
        print('Execution time:', elapsed_time, 'seconds')

        plt.plot(x,y, marker=".",linestyle="None")
        plt.axhline(y=np.nanmean(y),color="red")
        plt.xlabel("N-th game")
        plt.ylabel("Turns to finish")
        plt.title(s_mod)
        plt.ylim(ymin=0)
        plt.show()

    else:
        hamle_sayisi = Oyun().Oyna(search_mod,statics)
        print("Turns to complete: "+str(hamle_sayisi))

    pg.quit()