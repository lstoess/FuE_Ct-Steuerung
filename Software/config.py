import numpy as np  # Für Arrays
from enum import Enum  # Import OpenCV
from _thread import start_new_thread, allocate_lock  # oder mit therading lib.


# Global         Muss man das in Python überhaupt machen?
pic_height = 512
pic_width = 512
pic_number = 0
color_depth = 16  # in Bit
# BPM= array([Bildbreite][Bildhoehe]) #Bad Pixel Map
# ImageArr= np.array([[Bildbreite][Bildhoehe][Bilderzahl]])
pic_counter = 0

# Tread Sachen
global_BPM_moving = 0
global_BPM_multi = 0
global_BPM_dynamic = 0
loading_bar = 0  # Globaler Tread Ladebalken
loading_bar_max = 100  # auf Anz der Bilder * Detections setzen
loading_bar_exp = 0
lock = allocate_lock()  # Mutex
kill_flag_threads = False  # Kill flag für alle Treads
error_code = 0  # 0=ok -1=Fehler allgemein -2=Fehler Dynamic hat zu wenig Bilder, -3=Viele Bilder überbelichtet. -4=FCC Fehler
error_collect = {"aMW": 0, "dC": 0, "MPPC": 0}  # Die gefundenen Fehler
recall_time = 1000

"""

    B = np.array([ [[111, 112], [121, 122]],
               [[211, 212], [221, 222]],
               [[311, 312], [321, 322]] ])  # 3D Array
"""
# Methoden_Liste=['NARC', 'NMFC', 'NSRC'] #zur Korrektur
class Methods(Enum):  # zur Korrektur
    NARC = 2  # Mittelwert
    NMFC = 1  # Median
    NSRC = 3  # Replacement