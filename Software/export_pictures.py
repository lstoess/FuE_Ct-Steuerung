"""
/*
 * @Author: Julian Schweizerhof
 * @Email: diegruppetg@gmail.com
 * @Date: 2020-09-18 15:07:37
 * @Last Modified by: JLS666
 * @Last Modified time: 2020-09-18 14:42:32
 * @Description: Python Programm um ein Array als Bild speichern zu können
 */
 """
import numpy as np                  
import cv2
import os
from datetime import datetime        


def export_pictures(path, image_name, image, time):          # path: Zielverzeichnis, image_name: Name des Bildes, image: Array des Bildes
                                                            # os.path.join() für Crossplatform-Funktionalität, fügt / oder \ je nach Betriebssystem
    image_name = os.path.splitext(image_name)[0]
    current_time = str(time)
    dir_name = os.path.join(path, "Korrigierte Bilder vom " + current_time)
    if os.path.exists(dir_name):
        pass
    else:
        os.mkdir(dir_name)
    file_name = image_name + "_korrigiert.png"
                                                            # print("Image beim Exportieren: ", image, "Typ ist", type(image), "Shape ist: ", np.shape(image))

    cv2.imwrite(os.path.join(dir_name, file_name), image)   # Array als PNG speichern mit verlustfreier Kompression
                                                            # cv2.imwrite(os.path.join(dir_name, "0" + file_name), image, [cv2.IMWRITE_PNG_COMPRESSION,0])     # Array als PNG speichern ohne Kompression

    print(os.path.join(path, image_name))
                                                            # print("export_pictures") # debug


def export_pictures_easy(path, image_name, image):
    cv2.imwrite(os.path.join(path, image_name), image)
    return os.path.join(path, image_name)
