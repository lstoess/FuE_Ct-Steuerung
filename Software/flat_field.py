"""
/*
 * @Author: Julian Schweizerhof und Andreas Bank
 * @Email: diegruppetg@gmail.com
 * @Date: 2020-09
 * @Last Modified by: 
 * @Last Modified time: 
 * @Description: 
 */
 """

# import matplotlib.pyplot as plt
import numpy as np

# how to import numpy und ov2.  Python updaten, pip install, pip3 install numpy, pip3 install opencv-python.
import detection
import correction
import config
import import_pictures as imp
import cv2
import telemetry
import cProfile
import verpixler

""" Pfad der Bilddateien:______________________________________________________________________________________ """
import_path = "FFC_Bilder\Bildserie2_160kV_70uA_mittelwert.png"
import_path_bright = "FFC_Bilder\Bildserie1_160kV_70uA_mittelwert.png"        # MW Bild
import_path_dark = "FFC_Bilder\Bildserie1_160kV_0uA_mittelwert.png"


""" import der Bilddateien:______________________________________________________________________________________ """
pictures_data = imp.import_function(import_path)
pictures_data_bright = imp.import_function(import_path_bright)
pictures_data_dark = imp.import_function(import_path_dark)


""" Aufruf der Detection Funktion:______________________________________________________________________________________ """
if False:
    BAD = detection.advanced_moving_window(pictures_data[0], factor=3)[0]     # F=4

""" Aufruf der Correction Funktion:______________________________________________________________________________________ """
if True:
    GOOD = np.uint16(correction.flat_field(pictures_data[0], pictures_data_bright[0], pictures_data_dark[0])[0])

""" Audgabe der Bilder Plots und Ergebnisse:______________________________________________________________________________________ """

cv2.imwrite("_korrigiert flat_field.png", GOOD)
