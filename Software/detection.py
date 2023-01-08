""" 
/*
 * @Author: Andreas Bank
 * @Email: diegruppetg@gmail.com
 * @Date: 15.06.2020
 * @Last Modified by: Andy
 * @Last Modified time: 19.09.20
 * @Description: Die Suchalgorithmen für bad Pixel
 * @Version V2: Digital BPM, Schneller
 */
 """

import config as cfg
import numpy as np

global light_protection
light_protection = 0.02  # 10%

# Hot Pixel finder:
def hot_pixel_finder(d2_pic, thresh=0.99):
    counter = 0
    height, width = np.shape(d2_pic)
    BPM = np.zeros((height, width))
    for z in range(height):
        for s in range(width):
            if d2_pic[z, s] >= int(2**cfg.color_depth) * thresh:
                BPM[z, s] = 1  # Digital
                counter += 1
    # print("Hot Pixel: " , counter)
    if counter > height * width * light_protection:  # Überbelichtungsschutz
        counter = -1
        # print("Ueberbelichtet")
    return BPM, counter


# Dead Pixel finder:
def dead_pixel_finder(d2_pic, thresh=0.01):
    counter = 0
    height, width = np.shape(d2_pic)
    BPM = np.zeros((height, width))
    for z in range(height):
        for s in range(width):
            if d2_pic[z, s] <= int(2**cfg.color_depth) * thresh:
                BPM[z, s] = 1  # Digital
                counter += 1
    # print("Tote Pixel: " , counter)
    if counter > height * width * light_protection:
        counter = -1
        # print("zu viele Dead Pixel")
    return BPM, counter


def multi_picture_pixel_compare(d3_pic, thresh_hot=0.99, thresh_dead=0.01):
    pic_number, height, width = np.shape(d3_pic)
    print(pic_number, " Bilder pruefen...")
    BPM_D = np.zeros((height, width))
    BPM_H = np.zeros((height, width))
    invalid = np.zeros((height, width))
    overexposed = 0
    underexposed = 0
    for i in range(pic_number):
        # print("Bild Nr. ",i)
        cfg.lock.acquire()
        if cfg.kill_flag_threads == True:  # kill Tread
            cfg.error_code = -1
            cfg.lock.release()
            return -6
        cfg.loading_bar = cfg.loading_bar + 1
        cfg.lock.release()
        BPM_dead, num_dead = dead_pixel_finder(d3_pic[i], thresh_dead)  # Check for Black
        if num_dead < 0:
            BPM_dead = invalid
            underexposed = underexposed + 1
        BPM_D = BPM_D + BPM_dead
        BPM_hot, num_hot = hot_pixel_finder(d3_pic[i], thresh_hot)  # Check HOT
        if num_hot < 0:
            BPM_hot = invalid
            overexposed = overexposed + 1
        BPM_H = BPM_H + BPM_hot
    # Auswertung
    print(overexposed, " Bilder ueberbelichtet, ", underexposed, " Bilder zu dunkel")
    BPM_D = (BPM_D - int(0.3 * (pic_number - underexposed))) > 0  # Digit + mehr als 30%
    BPM_H = (BPM_H - int(0.3 * (pic_number - overexposed))) > 0
    BPM = np.logical_or(BPM_D, BPM_H)
    error = np.nonzero(BPM)
    error = len(error[0])
    print("Multi Picture findet ", error)
    # Tread Zeugs
    cfg.lock.acquire()
    if overexposed > pic_number / 3:  # Warning
        cfg.error_code = -3
    cfg.error_collect["MPPC"] = error
    cfg.global_BPM_multi = BPM  # Tread
    cfg.loading_bar = cfg.loading_bar + 1  # Final
    cfg.lock.release()
    return BPM, error


def top(x, max):
    if x >= max:
        return max
    else:
        return x


def bottom(x):
    if x < 0:
        return 0
    else:
        return x


def advanced_moving_window(d3_pic, window_width=6, factor=3):  # factor aus Literatur= 3  (BildSerie2 70µA ist factor 2,5-3,5)
    num, height, width = np.shape(d3_pic)
    # print(height,width)
    BPM = np.zeros((height, width))
    for i in range(num):
        d2_pic = d3_pic[i]
        square = int(window_width / 2)  # +1
        for y in range(width):
            if (cfg.kill_flag_threads == True):  # kill Tread / aMW zu langsam für Abbruch nach Bild.
                cfg.error_code = -1
                return
            for x in range(height):
                sup_BPM = d2_pic[
                    bottom(x - square) : top(x + square, width),
                    bottom(y - square) : top(y + square, height),
                ]

                std = np.sqrt(np.var(sup_BPM))

                if float(std) * factor < abs(np.mean(sup_BPM) - d2_pic[x, y]):  # TypeError: can't multiply sequence by non-int of type 'numpy.float64'
                    BPM[x, y] = 1  # Digital

        cfg.lock.acquire()
        cfg.loading_bar = cfg.loading_bar + 1
        cfg.lock.release()
    counter = np.count_nonzero(BPM)
    print("advWindow erkennt ", counter, " Fehler. Festerbreite= ", window_width
)
    # Tread Zeugs
    cfg.lock.acquire()
    cfg.error_collect["aMW"] = counter
    cfg.global_BPM_moving = BPM  # Tread
    cfg.loading_bar = cfg.loading_bar + 1  # Final
    cfg.lock.release()
    return BPM, counter

def dynamic_check(d3_pic, factor=1.5):  # Bilder müssen verschiene sein (Helle und Dunkle!) , factor ist Schwellwert für Erkennung. 1.03-1.2
    num, height, width = np.shape(d3_pic)
    if num < 2:
        print("zu wenig Bilder")
        cfg.lock.acquire()
        cfg.loading_bar = cfg.loading_bar + num  # Damit ist es abgearbeitet.
        cfg.lock.release()
        cfg.error_code = -2
        return -1  # Hoffentlich wird das Ausgewertet.
    BPM = np.zeros((height, width))
    counter = 0
    # Hell Dunkel erstellen
    brightest = np.ones((height, width))
    darkest = np.ones((height, width)) * 2**cfg.color_depth
    for Nr in range(num):
        cfg.lock.acquire()
        if cfg.kill_flag_threads == True:  # kill Tread
            cfg.error_code = -1
            cfg.lock.release()
            return -6
        cfg.loading_bar = cfg.loading_bar + 1
        cfg.lock.release()
        for s in range(height):
            for z in range(width):
                if brightest[s, z] < d3_pic[Nr, s, z]:
                    brightest[s, z] = d3_pic[Nr, s, z]
                if darkest[s, z] > d3_pic[Nr, s, z]:
                    darkest[s, z] = d3_pic[Nr, s, z]
    # Mittlere dynamic
    dynamic = (brightest - darkest) / brightest
    dynamic_std = np.mean(dynamic)
    print("dynamic Norm = ", dynamic_std)
    for s in range(height):
        for z in range(width):
            if dynamic[s, z] < dynamic_std / factor:
                BPM[s, z] = int((dynamic_std - dynamic[s, z]) / dynamic_std * 100)
                BPM[s, z] = 1  # Digital
                counter += 1
    print(counter, " Fehler gefunden (DynamikCheck).")
    # Tread Zeugs
    cfg.lock.acquire()
    cfg.error_collect["dC"] = counter
    cfg.global_BPM_dynamic = BPM  # Tread
    cfg.loading_bar = cfg.loading_bar + 1  # Final
    cfg.lock.release()
    return BPM, counter


def mapping(BPM_A, BPM_B, BPM_C=0, BPM_D=0, BPM_E=0):
    BPM = np.logical_or(BPM_A, BPM_B)
    BPM = np.logical_or(BPM, BPM_C)
    BPM = np.logical_or(BPM, BPM_D)
    BPM = np.logical_or(BPM, BPM_E)
    return BPM
