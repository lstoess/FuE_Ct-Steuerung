""" 
/*
 * @Author: Andreas Bank
 * @Email: diegruppetg@gmail.com
 * @Date: 15.06.2020
 * @Last Modified by: Andy
 * @Last Modified time: 
 * @Description: Die Suchalgorithmen für bad Pixel
 */
 """

import config as cfg
import numpy as np
import math
import copy


# Direkte Nachbarn:


def neighbor(picture, BPM):                                             # Mittelwert der beiden Nachbarn
    if np.shape(picture) != np.shape(BPM):
        print("Dimensionen passen nicht!")
        return -1
    height, width = np.shape(picture)
    flat_image = np.uint(picture.reshape(-1))
    flat_BPM = BPM.reshape(-1)
    for i in range(height * width - 1):
        if i % width and flat_BPM[i]:
            flat_image[i] = (flat_image[i - 1] + flat_image[i + 1]) / 2  # Mittelwert einsetzen
            # print(i)
        else:
            # print("Hi")
            pass                                                # Ränder machen wir net
    beautiful = np.uint(flat_image.reshape(height, width))
    return beautiful


# Nachbar
def neighbor_2(picture, BPM, method=cfg.Methods.NMFC, window=4):     # window um BadPixel
    if np.shape(picture) != np.shape(BPM):                           # Bildgröße Prüfen
        print("Dimensionen passen nicht!")
        return -1
    height, width = np.shape(picture)                                # Bildgröße Speichern
    Q_halbe = int(window / 2)
    beautiful = copy.copy(picture)
    for z in range(height):                                          # Schleife durch alle Bildpunkte
        for s in range(width):
            if BPM[z, s] != 0:
                top = z - Q_halbe                                    # window aufspannen.
                if top < 0:
                    top = 0
                bottom = z + Q_halbe
                if bottom > height:
                    bottom = height
                left = s
                left -= Q_halbe if (s > Q_halbe) else 0
                right = s + Q_halbe
                if right > width:
                    right = width
                window = picture[top:bottom, left:right]           # window herrauskopieren
                beautiful[z, s] = Methods(window, method)          # An gewünschte Korrekturmethode übergeben.
    return beautiful


""" #NARC=0 NMFC=1 NSRC=2
SR=Simpel Replacement
MF=Median Filter
AR=Average Relacement

def neigborhood(picture, BPM, method=0):
    if(np.shape(picture
) != np.shape(BPM)):
        print("Dimensionen passen nicht!")
        return -1
    height, width = np.shape(picture
)
        
    return beautiful """

# gradient


def gradient(picture, BPM, method=cfg.Methods.NMFC, length=10):
    if np.shape(picture) != np.shape(BPM):
        print("Dimensionen passen nicht!")
        return -1
    height, width = np.shape(picture)
    direction = -1
    beautiful = copy.copy(picture)
    length_half = int(length / 2)
    for z in range(height):  # picture Iterationsschleife
        for s in range(width):
            if BPM[z, s] != 0:  # Fehlstellen erkennen
                # Gradienten legen
                vertical = beautiful[bottom(z - length_half) : top(z + length_half, height), s]
                horizontal = beautiful[z, bottom(s - length_half) : top(s + length_half, width)]
                sub = beautiful[
                    bottom(z - length_half) : top(z + length_half + 1, height),
                    bottom(s - length_half) : top(s + length_half + 1, width),
                ]
                if sub.size < (length_half * 2 + 1) ** 2:
                    north_east = [-(2**16), +(2**16)]
                    north_west = north_east
                else:
                    north_east = np.diagonal(sub)  # Falsch benannt
                    north_west = np.fliplr(sub).diagonal()  # trifft nicht Pixel
                # low gradient
                # berechnen
                gradient = [
                    max(np.gradient(vertical)),
                    max(np.gradient(horizontal)),
                    max(np.gradient(north_east)),
                    max(np.gradient(north_west)),
                ]
                Low = 2**16
                for i in range(len(gradient)):
                    if Low > gradient[i]:
                        Low = gradient[i]
                        direction = i
                # Grauwert berechnen
                if direction == 0:  # gradient[0]=vertical
                    gray = Methods(vertical, method)
                elif direction == 1:
                    gray = Methods(horizontal, method)
                elif direction == 2:
                    gray = Methods(north_east, method)
                elif direction == 3:
                    gray = Methods(north_west, method)
                else:
                    print("Error")
                beautiful[z, s] = gray  # Oder mit dem Korrigierten Teil weiterarbeiten.
    return beautiful


def Methods(pixels, method):
    if method == cfg.Methods.NMFC.value:  # NMFC
        return np.median(pixels)
    elif method == cfg.Methods.NARC.value:  # NARC
        return np.mean(pixels)  # ohne den Bad-Pixel ist es Schwer
    elif method == cfg.Methods.NSRC.value:  # NSRC
        flat_pixels = np.reshape(pixels, -1)
        length_half = len(flat_pixels)
        m = int(length_half / 2 - 1)  # Rand Probleme
        return flat_pixels[m]
    else:
        return -1


def top(x, max):
    if x >= max:
        return max
    else:
        return x


def bottom(x, min=0):
    if x < min:
        return min
    else:
        return x


# Nagao

""" def Nagao(picture, BPM):
    if(np.shape(picture) != np.shape(BPM)):
        print("Dimensionen passen nicht!")
        return -1
    height, width = np.shape(picture)
    Q_Fenster=2
    NagaoSub_a=([1,1,1,1,1]
                [0,1,1,1,0]
                [0,0,0,0,0]
                [0,0,0,0,0]
                [0,0,0,0,0])
    NagaoSub_a2=np.rot(NagaoSub_a)
    NagaoSub_b=([0,0,0,0,0]
                [0,0,0,0,0]
                [0,0,0,1,1]
                [0,0,1,1,1]
                [0,0,1,1,1])
    NagaoSub_c=([0,0,0,0,0]
                [0,1,1,1,0]
                [0,1,0,1,0]
                [0,1,1,1,0]
                [0,0,0,0,0])
    
    großBild=picture

    v_rand=np.ones([:(Q_Fenster*width)]).reshape(Q_Fenster,width)
    h_rand=np.ones([:(Q_Fenster*(heohe+Q_Fenster))]).reshape((heohe+Q_Fenster),Q_Fenster)
    np.vstack([großBild,v_rand])
    np.hstack([großBild,h_rand])
    beautiful=picture

    for z in range(height):
        for s in range(width):
            if BPM[z,s] !=0:
                #window aufspannen
                #...
                
                window*a """


def flatfield(picture, Hell_Mittel_Bild, Dunkel_Mittel_Bild):
    # Rechenvorschrift. Dunkel/(Hell-Dunkel)
    # Wiki: New=(Input-Dark)/(Flat_Field-Dark) Dark=ohne X-Ray; Flat_Field=ohne Bauteil
    # Gain und Dunkelstrom
    if np.shape(picture) != np.shape(Hell_Mittel_Bild) or np.shape(picture) != np.shape(Dunkel_Mittel_Bild):
        print("Dimensionen passen nicht!")
        return -1
    height, width = np.shape(picture)
    a = picture - Dunkel_Mittel_Bild
    b = Hell_Mittel_Bild - Dunkel_Mittel_Bild
    # a=np.array([1,3,4,5,5,6,7,0,1,4,4,1])
    # b=np.array([1,2,3,4,5,6,7,0,0,8,9,0])
    b = np.where(b != 0, b, 1)
    c = np.divide(a, b)
    c = c.reshape(-1)
    error = 0
    i = 0
    for i in range(len(c)):
        if c[i] > 1.2:  # passiet nur im Fehlerfall 2 falsche bilder
            #print(i, c[i], " Falsches Bild gewaehlt")
            cfg.error_code = -4
            error = error + 1
            c[i] = 0.2
            i= i+1      
    m = np.amax(c)
    if m == 0:
        print("Alle Bilder gleich! So kann man kein FCC machen.")
        m = 1
        cfg.error_code = -4
    c = np.divide(c, m)
    beautiful = c * 2**16 - 1
    beautiful = np.uint16(beautiful.reshape(height, width))  # int 16 geht das???
    return beautiful, error


def hybrid(picture, BPM, method=1):  # zusätzlich Einstellungen?
    beautiful = gradient(picture, BPM, method)
    beautiful = neighbor_2(beautiful, BPM, method)
    return beautiful
