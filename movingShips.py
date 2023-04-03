import time
import matplotlib.pyplot as plt
import pygame as pg
import numpy as np
import random
from operator import itemgetter
import matplotlib

matplotlib.use('TkAgg')

pg.init()
pg.display.set_caption("Battleship")

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
BOARD_SIZE = 10
SQUARE_SIZE = 60
SCREEN = pg.display.set_mode((SCREEN_WIDTH + 1, SCREEN_HEIGHT + 1))

BEYAZ = (255, 255, 255)
SIYAH = (0, 0, 0)
KIRMIZI = (200, 0, 0)
YESIL = (0,200,0)


class Oyun:

    def __init__(self):
        self.GEMI_HARITA = np.zeros([10, 10])
        self.ATES_NOKTALARI = np.zeros([10, 10])
        self.GEMI_KOORDINAT = dict()
        self.KOORDINATLAR = dict()
        self.VURULAN_KOORDINATLAR = dict()
        self.SON_ATES_EDILEN_KOORDINATLAR = []

        self.BATAN_GEMI_KOORDINATLARI = []
        self.OLASILIK_HARITA = np.zeros([10, 10])
        self.GEMILER = {"Amiral Gemisi":5, "Kuvazor Gemisi":4, "Muhrip":3, "Hucumbot":3, "Denizalti":2}
        self.GEMILER_KAC_KERE_VURULDU = {"Amiral Gemisi": [], "Kuvazor Gemisi": [], "Muhrip": [], "Hucumbot": [], "Denizalti": []}
        self.YONLER = [0,0,0,0,0]
        self.ROTASYON = [0,0,0,0,0]
        self.DELAY = 300
        self.GUESS_EVENT = pg.USEREVENT
        pg.time.set_timer(self.GUESS_EVENT, self.DELAY)
        self.RUNNING = True
        self.PUAN = 0
        self.targets = []
        self.goal = sum(self.GEMILER.values())
        self.son_ates_koordinati = ()
        self.SON_ATES_EDILEN_KOORDINAT = (0,0)
        self.SON_ATES_EDILEN_KOORDINAT_HIT = False
        self.GEMI_BATTI = False
        self.HIT_COORDINATES = []

    def Gemi_Yerlestir(self):
        gemi_index = 0
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
                        self.VURULAN_KOORDINATLAR[gemi] = []
                        for coord in coord_list:
                            self.KOORDINATLAR[coord] = gemi
                        self.ROTASYON[gemi_index] = 0
                        gemi_index += 1
                    elif const_axis == "col":
                        coord_list = list(zip([row for row in range(start_row, end_row)], [start_col] * gemi_boyutu))
                        self.GEMI_KOORDINAT[gemi] = coord_list
                        self.VURULAN_KOORDINATLAR[gemi] = []
                        for coord in coord_list:
                            self.KOORDINATLAR[coord] = gemi
                        self.ROTASYON[gemi_index] = 1
                        gemi_index += 1

                else:
                    continue
                break

        for i in range(5):
            self.YONLER[i] = random.choice(range(0,2))

    def move_ship_collision(self, gemi, gemi_index):

        vurulan_nokta_sayisi = len(self.VURULAN_KOORDINATLAR[gemi])
        if vurulan_nokta_sayisi == self.GEMILER[gemi]:
            return False

        if self.ROTASYON[gemi_index] == 0: # x ekseni
            
            if self.YONLER[gemi_index] == 1: # sağa
                row, col = max(self.GEMI_KOORDINAT[gemi], key=itemgetter(1))
                if col < 9 and self.GEMI_HARITA[row][col + 1] == 0:
                    return True

            elif self.YONLER[gemi_index] == 0: # sola
                row, col = min(self.GEMI_KOORDINAT[gemi], key=itemgetter(1))
                if col > 0 and self.GEMI_HARITA[row][col - 1] == 0:
                    return True

        elif self.ROTASYON[gemi_index] == 1: # y ekseni

            if self.YONLER[gemi_index] == 1:  # yukari
                row, col = min(self.GEMI_KOORDINAT[gemi], key=itemgetter(0))
                if row > 0 and self.GEMI_HARITA[row - 1][col] == 0:
                    return True

            elif self.YONLER[gemi_index] == 0:  #asagi
                row, col = max(self.GEMI_KOORDINAT[gemi], key=itemgetter(0))
                if row < 9 and self.GEMI_HARITA[row + 1][col] == 0:
                    return True


        return False

    def try_moving(self, gemi, gemi_index):
        collision_yok = self.move_ship_collision(gemi, gemi_index)
        if collision_yok:

            if self.ROTASYON[gemi_index] == 1 and self.YONLER[gemi_index] == 1:  # yukari
                row_start, col_start = min(self.GEMI_KOORDINAT[gemi], key=itemgetter(0))
                row_end, col_end = max(self.GEMI_KOORDINAT[gemi], key=itemgetter(0))
                self.GEMI_HARITA[row_end][col_end] = 0
                self.GEMI_HARITA[row_start - 1][col_start] = 1
                self.KOORDINATLAR.pop((row_end, col_end))
                self.KOORDINATLAR[(row_start - 1, col_start)] = gemi
                self.GEMI_KOORDINAT[gemi].remove((row_end, col_end))
                self.GEMI_KOORDINAT[gemi].append((row_start - 1, col_start))

                for row,col in sorted(self.VURULAN_KOORDINATLAR[gemi], key=lambda k: [k[0], k[1]]):
                    self.VURULAN_KOORDINATLAR[gemi].remove((row,col))
                    self.VURULAN_KOORDINATLAR[gemi].append((row-1,col))

                return True

            elif self.ROTASYON[gemi_index] == 1 and self.YONLER[gemi_index] == 0:  # asagi
                row_start, col_start = min(self.GEMI_KOORDINAT[gemi], key=itemgetter(0))
                row_end, col_end = max(self.GEMI_KOORDINAT[gemi], key=itemgetter(0))
                self.GEMI_HARITA[row_start][col_start] = 0
                self.GEMI_HARITA[row_end + 1][col_end] = 1
                self.KOORDINATLAR.pop((row_start, col_start))
                self.KOORDINATLAR[(row_end + 1, col_end)] = gemi
                self.GEMI_KOORDINAT[gemi].remove((row_start, col_start))
                self.GEMI_KOORDINAT[gemi].append((row_end + 1, col_end))

                for row, col in reversed(sorted(self.VURULAN_KOORDINATLAR[gemi], key=lambda k: [k[0], k[1]])):
                    self.VURULAN_KOORDINATLAR[gemi].remove((row, col))
                    self.VURULAN_KOORDINATLAR[gemi].append((row + 1, col))

                return True

            elif self.ROTASYON[gemi_index] == 0 and self.YONLER[gemi_index] == 0:  # sola
                row_start, col_start = min(self.GEMI_KOORDINAT[gemi], key=itemgetter(1))
                row_end, col_end = max(self.GEMI_KOORDINAT[gemi], key=itemgetter(1))
                self.GEMI_HARITA[row_end][col_end] = 0
                self.GEMI_HARITA[row_start][col_start - 1] = 1
                self.KOORDINATLAR.pop((row_end, col_end))
                self.KOORDINATLAR[(row_start, col_start - 1)] = gemi
                self.GEMI_KOORDINAT[gemi].remove((row_end, col_end))
                self.GEMI_KOORDINAT[gemi].append((row_start, col_start - 1))

                for row, col in sorted(self.VURULAN_KOORDINATLAR[gemi], key=lambda k: [k[1], k[0]]):
                    self.VURULAN_KOORDINATLAR[gemi].remove((row, col))
                    self.VURULAN_KOORDINATLAR[gemi].append((row, col-1))

                return True

            elif self.ROTASYON[gemi_index] == 0 and self.YONLER[gemi_index] == 1:  # sağa
                row_start, col_start = min(self.GEMI_KOORDINAT[gemi], key=itemgetter(1))
                row_end, col_end = max(self.GEMI_KOORDINAT[gemi], key=itemgetter(1))
                self.GEMI_HARITA[row_start][col_start] = 0
                self.GEMI_HARITA[row_end][col_end + 1] = 1
                self.KOORDINATLAR.pop((row_start, col_start))
                self.KOORDINATLAR[(row_end, col_end + 1)] = gemi
                self.GEMI_KOORDINAT[gemi].remove((row_start, col_start))
                self.GEMI_KOORDINAT[gemi].append((row_end, col_end + 1))

                for row, col in reversed(sorted(self.VURULAN_KOORDINATLAR[gemi], key=lambda k: [k[1], k[0]])):
                    self.VURULAN_KOORDINATLAR[gemi].remove((row, col))
                    self.VURULAN_KOORDINATLAR[gemi].append((row, col + 1))

                return True
        return False

    def move_ships(self):
        """
        Move ships one unit in the direction they are currently facing
        If a ship hits a wall or another ship, it will reverse direction and move one unit in the opposite direction
        """
        gemi_index = 0
        for gemi in self.GEMILER:
            moved = self.try_moving(gemi,gemi_index)
            if moved == 0:
                if self.YONLER[gemi_index] == 0:
                    self.YONLER[gemi_index] = 1
                else:
                    self.YONLER[gemi_index] = 0
                moved = self.try_moving(gemi, gemi_index)

            gemi_index += 1

    def check_gemi_batti(self,gemi):
        if self.GEMILER.get(gemi) == len(self.VURULAN_KOORDINATLAR[gemi]):
            self.GEMI_BATTI = True
        else:
            self.GEMI_BATTI = False

    def ates_et(self, hedef_x, hedef_y):
        self.son_ates_koordinati = (hedef_x, hedef_y)
        self.ATES_NOKTALARI[hedef_x][hedef_y] = 1
        self.SON_ATES_EDILEN_KOORDINAT = ((hedef_x,hedef_y))
        if self.KOORDINATLAR.get((hedef_x, hedef_y)) is None:
            self.GEMI_BATTI = False
        gemi_batti = 0
        if self.GEMI_HARITA[hedef_x][hedef_y] == 1 \
                and ((hedef_x,hedef_y) not in self.VURULAN_KOORDINATLAR[self.KOORDINATLAR.get((hedef_x, hedef_y))]):

            self.PUAN += 1
            vurulan_gemi = self.KOORDINATLAR.get((hedef_x, hedef_y))
            self.VURULAN_KOORDINATLAR[vurulan_gemi].append((hedef_x, hedef_y))
            self.check_gemi_batti(self.KOORDINATLAR.get((hedef_x, hedef_y)))
            self.HIT_COORDINATES.append((hedef_x,hedef_y))

            self.GEMILER_KAC_KERE_VURULDU.get(vurulan_gemi).append((hedef_x,hedef_y))

            if self.PUAN == self.goal:
                self.RUNNING = False

            self.SON_ATES_EDILEN_KOORDINAT_HIT = True
            return True

        self.SON_ATES_EDILEN_KOORDINAT_HIT = False
        return False

    def get_en_uzun_gemi_alive(self):
        return max(self.GEMILER.values())

    def rastgele_koordinat(self):
        x, y = random.choice(range(10)), random.choice(range(10))
        return x, y

    def draw_Board(self):
        y = 0
        for i in range(BOARD_SIZE):
            x = 0
            for j in range(BOARD_SIZE):
                if self.GEMI_HARITA[i][j] == 0:
                    pg.draw.rect(SCREEN, SIYAH, pg.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE))
                    pg.draw.line(SCREEN, SIYAH,
                                 (x, y),
                                 (x + SQUARE_SIZE, y + SQUARE_SIZE),
                                 width=5)
                    pg.draw.line(SCREEN, SIYAH,
                                 (x, y + SQUARE_SIZE),
                                 (x + SQUARE_SIZE, y),
                                 width=5)
                elif self.GEMI_HARITA[i][j] == 1:
                    pg.draw.rect(SCREEN, (111, 111, 111), pg.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE))
                    if (i, j) in self.VURULAN_KOORDINATLAR[self.KOORDINATLAR.get((i, j))]:
                        pg.draw.line(SCREEN, KIRMIZI,
                                     (x, y),
                                     (x + SQUARE_SIZE, y + SQUARE_SIZE),
                                     width=5)
                        pg.draw.line(SCREEN, KIRMIZI,
                                     (x, y + SQUARE_SIZE),
                                     (x + SQUARE_SIZE, y),
                                     width=5)
                if (i,j) == self.son_ates_koordinati:
                    pg.draw.line(SCREEN, YESIL,
                                 (x, y),
                                 (x + SQUARE_SIZE, y + SQUARE_SIZE),
                                 width=5)
                    pg.draw.line(SCREEN, YESIL,
                                 (x, y + SQUARE_SIZE),
                                 (x + SQUARE_SIZE, y),
                                 width=5)


                x = x + SQUARE_SIZE

            y = y + SQUARE_SIZE

        for i in range(0, 660, 60):
            pg.draw.line(SCREEN, BEYAZ, (0, i), (600, i))
            pg.draw.line(SCREEN, BEYAZ, (i, 0), (i, 600))

    def hit_moving_ships(self):
        if not self.targets:
            guess_row, guess_col = self.rastgele_koordinat()
        else:
            guess_row, guess_col = self.targets.pop()

        if self.GEMI_HARITA[guess_row][guess_col] == 1:
            if guess_row <= 9:
                potential_targets = [(guess_row + 1, guess_col), ((guess_row - 2, guess_col))]
                if guess_col <= 7:
                    potential_targets.append((guess_row, guess_col + 3))
                elif guess_col >= 3:
                    potential_targets.append((guess_row, guess_col - 4))

            if guess_row >= 0:
                potential_targets = [(guess_row - 1, guess_col), ((guess_row + 2, guess_col))]
                if guess_col <= 7:
                    potential_targets.append((guess_row, guess_col + 3))
                elif guess_col >= 3:
                    potential_targets.append((guess_row, guess_col - 4))

            for target_row, target_col in potential_targets:
                if (0 <= target_row <= 9) and \
                        (0 <= target_col <= 9) and \
                            ((target_row, target_col) not in self.targets) and \
                                ((target_row, target_col) not in sum(self.VURULAN_KOORDINATLAR.values(), [])):
                    self.targets.append((target_row, target_col))

        return guess_row, guess_col

    def sabit_tarama(self):

        if self.SON_ATES_EDILEN_KOORDINAT_HIT and not self.GEMI_BATTI:
            row,col = self.SON_ATES_EDILEN_KOORDINAT

            if row < 9:
                self.targets.append((row + 1, col))
            if row > 0:
                self.targets.append((row - 1, col))
            if col < 9:
                self.targets.append((row, col + 1))
            if col > 0:
                self.targets.append((row, col - 1))

            return self.SON_ATES_EDILEN_KOORDINAT


        if not self.targets:
            guess_row, guess_col = self.rastgele_koordinat()
        else:
            guess_row, guess_col = self.targets.pop()


        return guess_row, guess_col

    def get_direction(self,gemi):
        if len(set(self.GEMILER_KAC_KERE_VURULDU.get(gemi))) > 1:

            (x1, y1) = next(iter(self.GEMILER_KAC_KERE_VURULDU.get(gemi)))
            (x2, y2) = next(iter(self.GEMILER_KAC_KERE_VURULDU.get(gemi)))

            if x1 == x2:
                return 0 #yatay
            elif y1 == y2:
                return 1 #dikey
        return 2

    def olasilik(self):

        if self.SON_ATES_EDILEN_KOORDINAT_HIT and not self.GEMI_BATTI:
            row,col = self.SON_ATES_EDILEN_KOORDINAT

            if row < 9:
                self.targets.append((row + 1, col))
            if row > 0:
                self.targets.append((row - 1, col))
            if col < 9:
                self.targets.append((row, col + 1))
            if col > 0:
                self.targets.append((row, col - 1))

            return self.SON_ATES_EDILEN_KOORDINAT

        guess_row, guess_col = self.rastgele_koordinat()

        if not self.targets:
            prob_map = np.zeros([10, 10])
            check = 0
            for gemi in self.GEMILER:

                # GEMİNİN 2 KOORDİNATİ VURULDUYSA DOĞRULTUSUNA BAK DOĞRULTUDA ATEŞ ET
                if len(self.GEMILER_KAC_KERE_VURULDU.get(gemi)) != self.GEMILER.get(gemi) and \
                        len(self.GEMILER_KAC_KERE_VURULDU.get(gemi)) > 0:

                    (x, y) = self.GEMILER_KAC_KERE_VURULDU.get(gemi)[0]
                    check = 1
                    for i in range(0, 10):
                        if i != x:
                            prob_map[i][y] = 2

                    for i in range(0, 10):
                        if i != y:
                            prob_map[x][i] = 2

                #for (x, y) in self.GEMILER_KAC_KERE_VURULDU.get(gemi):
                    #prob_map[x][y] = 0

            #(x, y) = self.SON_ATES_EDILEN_KOORDINAT
            #prob_map[x][y] = 0
            self.OLASILIK_HARITA = prob_map

            if check:
                indices = np.argwhere(self.OLASILIK_HARITA > 0)
                random_index = indices[np.random.randint(indices.shape[0])]
                #return random_index
                guess_row, guess_col = random_index
        else:
            guess_row, guess_col = self.targets.pop()

        return guess_row, guess_col

    def olasilik_haritasi_yarat(self):
        prob_map = np.zeros([10, 10])
        for ship_name in set(self.KOORDINATLAR.values()):
            ship_size = self.GEMILER[ship_name]
            use_size = ship_size - 1
            # check where a ship will fit on the board
            for row in range(10):
                for col in range(10):
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
                            prob_map[start_row:end_row, start_col:end_col]   += 1

                    for gemi in self.GEMILER:

                        #GEMİNİN 2 KOORDİNATİ VURULDUYSA DOĞRULTUSUNA BAK DOĞRULTUDA ATEŞ ET
                        if len(self.GEMILER_KAC_KERE_VURULDU.get(gemi)) != self.GEMILER.get(gemi) and \
                                len(self.GEMILER_KAC_KERE_VURULDU.get(gemi)) > 0:

                            (x,y) = self.GEMILER_KAC_KERE_VURULDU.get(gemi)[0]

                            for i in range(0,10):
                                if i != x:
                                    prob_map[i][y] += 2

                            for i in range(0,10):
                                if i != y:
                                    prob_map[x][i] += 2

                        for (x,y) in self.GEMILER_KAC_KERE_VURULDU.get(gemi):
                            prob_map[x][y] = 0

                    (x,y) = self.SON_ATES_EDILEN_KOORDINAT
                    prob_map[x][y] = 0

        self.OLASILIK_HARITA = prob_map

    def olasilik_tahmini(self):

        if self.SON_ATES_EDILEN_KOORDINAT_HIT and not self.GEMI_BATTI:
            return self.SON_ATES_EDILEN_KOORDINAT

        self.olasilik_haritasi_yarat()
        #print(self.OLASILIK_HARITA)
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

    def hamle_hesapla(self, mod):
        if (mod == 0):
            x, y = self.rastgele_koordinat()
        elif (mod == 1):
            x, y = self.sabit_tarama()
        elif (mod == 2):
            x, y = self.olasilik()

        return x, y

    def Oyna(self, mod=0, statics=0):
        self.Gemi_Yerlestir()
        if (mod == 2):
            self.olasilik_haritasi_yarat()
        for gemi in self.GEMILER:
            self.move_ship_collision(gemi,1)

        hamle_sayisi = 0
        if (statics):
            while self.RUNNING:
                x, y = self.hamle_hesapla(mod)
                self.ates_et(x, y)
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
                        self.move_ships()
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
                    self.move_ships()
                    self.ates_et(x, y)
                    hamle_sayisi += 1


            self.draw_Board()
            if (mod == 2):
                self.draw_heat_map()
            pg.display.update()

        return hamle_sayisi


if __name__ == '__main__':


    # 0 - 1 tur oyna
    # 1 - 1000 tur simule et
    statics = 1
    oyun_sayisi = 10

    # 0 - rastgele
    # 1 - sabit tarama
    # 2 - olasilik
    search_mod = 2

    s_mod = ""
    if search_mod == 0:
        s_mod = "Rastgele Ateş"
    elif search_mod == 1:
        s_mod = "Sabit Tarama Metodu"
    elif search_mod == 2:
        s_mod = "Olasilik"


    if (search_mod == 2):
        SCREEN_WIDTH = 1300
        SCREEN = pg.display.set_mode((SCREEN_WIDTH + 1, SCREEN_HEIGHT + 1))

    if (statics):
        top = 0
        x = []
        y = []
        st = time.time()
        for i in range(oyun_sayisi):
            hamle_sayisi = Oyun().Oyna(search_mod, statics)
            top += hamle_sayisi
            y.append(hamle_sayisi)
            x.append(i)


        print("Avarage turns: " + str(top / oyun_sayisi))
        print("Min Turns: " + str(min(y)))
        print("Max Turns: " + str(max(y)))

        et = time.time()
        elapsed_time = et - st
        print('Execution time:', elapsed_time, 'seconds')

        plt.plot(x, y, marker=".", linestyle="None")
        plt.axhline(y=np.nanmean(y), color="red")
        plt.xlabel("N-th game")
        plt.ylabel("Turns to finish")
        plt.title(s_mod)
        plt.ylim(ymin=0)
        plt.show()

    else:
        hamle_sayisi = Oyun().Oyna(search_mod, statics)
        print("Turns to complete: " + str(hamle_sayisi))

    pg.quit()