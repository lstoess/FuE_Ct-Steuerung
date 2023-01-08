"""
/*
 * @Author: Julian Schweizerhof und Andreas Bank
 * @Email: diegruppetg@gmail.com
 * @Date: 2020-05-26 20:13:55
 * @Last Modified by: JLS666
 * @Last Modified time: 2020-06-21 01:32:30
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
import save

""" Pfad der Bilddateien:______________________________________________________________________________________ """
import_path = ".vscode\Serie 4 original.png"
import_path_flat = "FFC_Bilder\Bildserie2_160kV_70uA_mittelwert.png"
import_path_bright = "FFC_Bilder\Bildserie1_160kV_70uA_mittelwert.png"  # MW Bild
import_path_dark = "FFC_Bilder\Bildserie1_160kV_0uA_mittelwert.png"
# import_path = "MethodentestBearbeitet.png"


""" Import der Bilddateien:______________________________________________________________________________________ """
img_data = imp.import_function(import_path)
img_data_flat = imp.import_function(import_path_flat)
img_data_bright = imp.import_function(import_path_bright)
img_data_dark = imp.import_function(import_path_dark)
img_data = np.concatenate((img_data, img_data_bright, img_data_dark, img_data_flat))
img_data[0, 0, 0] = 12  # Unfug
""" Aufruf der Detection Funktion:______________________________________________________________________________________ """
if True:
    BAD1 = detection.advanced_moving_window(img_data[0], factor=2.0, window_width=10)[0]  # F=4
    BAD1_2 = detection.advanced_moving_window(img_data[0], factor=2.5, window_width=5)[0]
    BAD1_3 = detection.advanced_moving_window(img_data_bright[0], factor=4, window_width=10)[0]
    BAD2 = detection.multi_picture_pixel_compare(img_data, thresh_hot=0.995, thresh_dead=0.1)[0]
    BAD3 = detection.dynamic_check(img_data, factor=1.03)[0]
    BAD = detection.mapping(BAD1, BAD2, BAD3, BAD1_2, BAD1_3) * 100
    
    # Anzeigen
    telemetry.mark_pixels(BAD1, img_data[0], bgr=0, algorithm="advWindow", thresh=1)
    telemetry.mark_pixels(BAD1_2, img_data[0], bgr=0, algorithm="advWindow_2", thresh=1)
    telemetry.mark_pixels(BAD1_3, img_data[0], bgr=0, algorithm="advWindow_3", thresh=1)
    telemetry.mark_pixels(BAD2, img_data[0], bgr=1, algorithm="Schwelle", thresh=1)
    telemetry.mark_pixels(BAD3, img_data[0], bgr=2, algorithm="Dynamik", thresh=1)
    
    # save
    save.BPM_Save(BAD, "Quelle1")
else:
    BAD = save.BPM_Read("Quelle1")  # Aus Speicher laden.

""" Aufruf der Correction Funktion:______________________________________________________________________________________ """
if True:
    data_save = img_data[0] + 1
    GOOD_NB2_NARC = np.uint16(correction.neighbor_2(img_data[0], BAD, 2))
    GOOD_NB2_NMFC = np.uint16(correction.neighbor_2(img_data[0], BAD, 1))
    GOOD_NB2_NSRC = np.uint16(correction.neighbor_2(img_data[0], BAD, 3))
    GOOD_NB = np.uint16(correction.neighbor(img_data[0], BAD))
    GOOD_grad_NARC = np.uint16(correction.gradient(img_data[0], BAD, 2))
    GOOD_grad_NMFC = np.uint16(correction.gradient(img_data[0], BAD, 1))
    GOOD_grad_NSRC = np.uint16(correction.gradient(img_data[0], BAD, 3))
    GOOD_hybrid = np.uint16(correction.hybrid(img_data[0], BAD, 1))
    FGOOD_hybrid = np.uint16(correction.hybrid(img_data_flat[0], BAD, 1))
    HGOOD_hybrid = np.uint16(correction.hybrid(img_data_bright[0], BAD, 1))
    DGOOD_hybrid = np.uint16(correction.hybrid(img_data_dark[0], BAD, 1))
    GOOD_flatfield = np.uint16(correction.flatfield(FGOOD_hybrid, HGOOD_hybrid, DGOOD_hybrid)[0])

""" Ausgabe der Bilder Plots und Ergebnisse:______________________________________________________________________________________ """
telemetry.markPixels(BAD, img_data[0], bgr=0, algorithm="hybrid", thresh=1)
cv2.imwrite("_korrigiert GOOD_NB2_NARC.png", GOOD_NB2_NARC)
cv2.imwrite("_korrigiert GOOD_NB2_NMFC.png", GOOD_NB2_NMFC)
cv2.imwrite("_korrigiert GOOD_NB2_NSRC.png", GOOD_NB2_NSRC)
cv2.imwrite("_korrigiert GOOD_NB.png", GOOD_NB)
cv2.imwrite("_korrigiert GOOD_Grad_NARC.png", GOOD_grad_NARC)
cv2.imwrite("_korrigiert GOOD_Grad_NMFC.png", GOOD_grad_NMFC)
cv2.imwrite("_korrigiert GOOD_Grad_NSRC.png", GOOD_grad_NSRC)
cv2.imwrite("_korrigiert GOOD_hybrid.png", GOOD_hybrid)
cv2.imwrite("_korrigiert Flatfield.png", GOOD_flatfield)
