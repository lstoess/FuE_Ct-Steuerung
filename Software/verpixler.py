import random as r
import config as cfg
import numpy as np


def pixelate(d2_pic, num_pixels=100, line_enable=False, cluster=False, min_deviation=20):
    height, width = np.shape(d2_pic)  # Bild Dimensionen
    r.seed(d2_pic[1, 1] + num_pixels)  # Zufallsgenerator
    BPM = np.zeros((height, width))  # Leer Bild erstellen
    for i in range(num_pixels):
        x = r.randint(0, width - 1)
        y = r.randint(0, height - 1)  # Zufall Position
        gray = r.randint(0, 2**cfg.color_depth)  # Zufall Grauwert
        if abs(d2_pic[x, y] - gray) > 2**cfg.color_depth * min_deviation / 100:
            d2_pic[x, y] = gray  # Pixel einfügen
            BPM[x, y] = 100  # error in perfekter BPM vermerken
        else:
            i -= 1

    if line_enable:
        print("Es werden Linienfehler erzeugt")
        for v in range(line_enable):
            length = r.randint(10, int(width / 3))  # Zufällige Länge der Linie
            dir = r.choice(["X", "Y"])  # Zufällige Richtung
            x = r.randint(0, width - 1)  # Zufällige Startposition
            y = r.randint(0, height - 1)
            if dir == "X":
                x = r.randint(0, width - length)  # Linie vollständig im Bild enthalten
            else:
                y = r.randint(0, width - length)

            gray = r.randint(0, 2**cfg.color_depth)  # Zufall Grauwert
            if abs(d2_pic[x, y] - gray) > 2**cfg.color_depth * min_deviation / 100:
                if dir == "X":
                    d2_pic[x : x + length, y] = gray
                    BPM[x : x + length, y] = 100  # BPM schreiben
                else:
                    d2_pic[x, y : y + length] = gray
                    BPM[x, y : y + length] = 100
            else:
                v -= 1
    if cluster:
        a, b, c = cluster(d2_pic, number=cluster)
        BPM = BPM + b
        d2_pic = a
    print("Bad-Pixel wurden erzeugt")
    return d2_pic, BPM


def cluster(d2_pic, diameter=8, number=1, density=1 / 3):
    print("cluster wird erzeugt Anzahl ist verfaelscht")
    height, width = np.shape(d2_pic)
    r.seed(d2_pic[1, 1] + number + diameter)
    BPM = np.zeros((height, width))
    counter = 0
    for i in range(number):
        x = r.randint(int(diameter / 2), width - int(diameter / 2) - 1)
        y = r.randint(int(diameter / 2), height - int(diameter / 2) - 1)
        gray = r.randint(d2_pic[x, y], 2**cfg.color_depth)
        gray = r.randint(gray, 2**cfg.color_depth)
        gray = r.randint(gray, 2**cfg.color_depth)
        for v in range(int((diameter**2) * density)):
            x2 = int(r.gauss(0, diameter / 3))
            y2 = int(r.gauss(0, diameter / 3))
            d2_pic[x + x2, y + y2] = gray
            BPM[x + x2, y + y2] = 100
            counter += 1

    return d2_pic, BPM, counter


def auswertung(BPM_2test, BPM_original, name_addition="0"):
    if np.shape(BPM_2test) != np.shape(BPM_original):
        print("Digga Dimensionen!")
        return -1
    height, width = np.shape(BPM_2test)
    counter = [0, 0, 0, 0, 0, 0]  # True Pos, True Neg, False Pos, False Neg, TPR, FPR
    num_bad_pixel = 0
    detected_num = 0
    for s in range(height):
        for z in range(width):
            if BPM_original[s, z] > 0 and BPM_2test[s, z] > 0:
                counter[0] += 1
            elif BPM_original[s, z] == 0 and BPM_2test[s, z] == 0:
                counter[1] += 1
            elif BPM_original[s, z] > 0 and BPM_2test[s, z] == 0:
                counter[2] += 1
            elif BPM_original[s, z] == 0 and BPM_2test[s, z] > 0:
                counter[3] += 1
            if BPM_original[s, z]:
                num_bad_pixel += 1
            if BPM_2test[s, z]:
                detected_num += 1

    not_detected = (1 - detected_num / num_bad_pixel) * 100  # Prozent
    wrongly_detected = detected_num / (height * width - num_bad_pixel) * 100

    # Plot
    if counter[0] == 0:
        counter[4] = 1.1
    else:
        counter[4] = counter[0] / (counter[0] + counter[3])  # TPR
    if counter[2] == 0:
        counter[5] = 0
    else:
        counter[5] = counter[2] / (counter[2] + counter[1])  # FPR

    print("Auswertung: True Pos, True Neg, False Pos, False Neg")
    print(counter)
    print("Nicht Erkannt = ", not_detected, " Falsch Erkannt = ", wrongly_detected)

    return counter, not_detected, wrongly_detected, counter[4:6]

def julian(bright, dark, one_more):
    height, width = np.shape(bright)
    black_pic = np.zeros((height, width))
    counter = 0
    error, BPM = pixelate(black_pic, line_enable=3, cluster=3, min_deviation=1)
    for s in range(height):
        for z in range(width):
            if BPM[s, z] > 0:
                bright[s, z] = error[s, z]
                dark[s, z] = error[s, z]
                one_more[s, z] = error[s, z]
                counter += 1
    return bright, dark, one_more, BPM, counter
