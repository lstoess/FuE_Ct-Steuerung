"""
/*
 * @Author: Julian Schweizerhof
 * @Email: diegruppetg@gmail.com
 * @Date: 2020-06-15 17:48:37
 * @Last Modified by: JLS666
 * @Last Modified time: 2020-10-14 23:25:37
 * @Description: Python Programm um ein oder mehrere pictureer des Formats his zu importieren
 */
 """

#########################################################################################################
# HIS-File Aufbau:  100 Byte großer Header, danach unkomprimiertes picture im Rohformat, z.B. in uint16
#                   Der 9. uint16 im Header: numb der Pixel in der Breite
#                   Der 10. uint16 im Header: numb der Pixel in der Höhe
#                   Der 11. uint16 im Header: numb der pictureer in der pictureserie
#                   Über die Dateigröße kann die color_depth berechnet werden
#########################################################################################################

import os                          # Für die Path-Manipulation
import numpy as np                 # Für Arrays
import cv2                         # Import und Export OpenCV
from datetime import datetime      # Für das Auslesen des aktuellen Datum und Zeit


def get_number_images(pImportPath, rows, cols):             # Funktion: Die numb der pictureer in der Datei bestimmten, Rückgabewert: numb pictureer
    file = open(pImportPath, "rb")                           # File erneut öffnen, da ansonsten der "Cursor" falsch liegt
    data = np.fromfile(file, dtype=np.uint16)               # komplettes File einlesen
    numbber_images = (np.size(data) - 50) / (rows * cols)    # Die numb der pictureer bestimmen: die Größe des uint16 Arrays bestimmen, dann minus 50 Elemten (der Header der Datei) und dann geteilt durch die Pixel-numb eines picturees
    file.close()                                             # File schließen
    return numbber_images                                    # Die numb der pictureer zurückgeben


def get_color_depth(pImportPath,):                           # Funktion: color_depth einer HIS-Datei bestimmten, Rückgabewert: color_depth im Format uint16 oder uint8
    file = open(pImportPath, "rb")                           # File erneut öffnen, da ansonsten der "Cursor" falsch liegt
    data = np.fromfile(file, dtype=np.uint16)               # komplettes File einlesen
    cols = int(np.take(data, 8))                             # Breite auslesen
    rows = int(np.take(data, 9))                             # Höhe auslesen
    numbber_images = int(np.take(data, 10))                  # numb der pictureer auslesen
    color_depth = ((np.size(data) - 50) * 16 / (rows * cols * numbber_images))  # Die numb der pictureer bestimmen: die Größe des uint16 Arrays bestimmen, dann minus 50 Elemten (der Header der Datei) und dann geteilt durch die Pixel-numb eines picturees
    file.close()                                             # File schließen
    if int(color_depth) == 16:                               # 16 Bit pro Pixel?
        temp_var = np.zeros(1, dtype=np.uint16)              # Für einheitiger Rückgabetyp
        color_depth = temp_var.dtype                         # Für einheitiger Rückgabetyp
    elif int(color_depth) == 8:                              # 8 Bit pro Pixel?
        temp_var = np.zeros(1, dtype=np.uint8)               # Für einheitiger Rückgabetyp
        color_depth = temp_var.dtype                         # Für einheitiger Rückgabetyp
    else:                                                    # Keine 8 oder 16 Bit pro Pixel?
        color_depth = "FEHLER"                               # Datei gibt keinen Sinn
        print("Fehler, unbekanntes HIS Format")              # debug Ausgabe
    return color_depth                                       # color_depth


def his_import_function(pImportPath, export=False, average=False, pExportPath="", time=""):     # Funktion: pictureer im HIS-Format importieren, Übergabewert: Path zum picture
    current_time = time                                                                         # aktuelles Datum und Zeit
    path_without_extensions = os.path.splitext(pImportPath)[0]                                  # Pfad ohne data_ending erzeugen, .his wird entfernt
    # print("\n\n*************************************************************")
    # print("Funktion zum Einlesen von HIS-Dateien aufgerufen")
    # print("*************************************************************\n")
    file_name, file_extensions = os.path.splitext(os.path.basename(pImportPath))                # Dateinamen und data_ending extrahieren
   
    print("Die Datei", file_name, "wird jetzt eingelesen.")
    
    fd = open(pImportPath, "rb")                                                                # Das picture öffnen im "rb"-Modus: read binary
    data = np.fromfile(fd, dtype=np.uint16, count=50)                                          # Den Header 50 mal mit unsinged int 16 Bit einlesen (erste 100 Bytes)
    rows = int(np.take(data, 8))                                                                # Reihen bestimmen, in int konvertieren, ansonsten overflow Error bei der Funktion fromfile()
    cols = int(np.take(data, 9))                                                                # Spalten bestimmen
    numbber_images = int(get_number_images(pImportPath, rows, cols))                           # numb der pictureer in der Datei bestimmen
    
    print("Ihre Datei hat", rows, "Reihen und", cols, "Spalten und besteht aus", numbber_images, "picture(ern)",)
    picure_data = np.zeros((numbber_images, rows, cols), dtype=np.uint16)                       # leeres 3D-Array der picure_data: 1. Nr. des picturees, 2. picturehöhe, 3. picturebreite
    
    for index in range(numbber_images):                                                         # Alle pictureer anzeigen und speichern
        f = np.fromfile(fd, dtype=np.uint16, count=rows * cols)                                # Pixel lesen und in einem ein dimensionales Array speichern
        im = f.reshape((rows, cols))                                                            # Array in zwei dimensionales Array mit rows x cols erstellen
        picure_data[index] = im                                                                 # Aktuelles picture speichern

        if export == True:
            """
            cv2.imshow('image', im)                                             # Array als picture anzeigen
            cv2.imwrite(path_without_extensions+"_"+str(index)+'_beta.png',im, [cv2.IMWRITE_PNG_COMPRESSION,0])     # Array als PNG speichern ohne Kompression
            print("Ihre Datei wurden unter", path_without_extensions+"_"+str(index)+".png gespeichert")
            cv2.waitKey()                                                       # Warten bis eine Taste gedrückt wird
            """
            dir_name = os.path.join(pExportPath, "Originalpicture vom " + current_time)
            if os.path.exists(dir_name):
                pass
            else:
                os.mkdir(dir_name)
            file_name = (os.path.splitext(os.path.basename(pImportPath))[0] + "_original_" + str(index) + ".png")
            cv2.imwrite(os.path.join(dir_name, file_name), im)                                  # Array als PNG speichern ohne Kompression

    if average == True:
        mean_image = np.zeros([rows, cols], dtype=np.uint32)
        for index in range(np.shape(picure_data)[0]):                                           # numb der picturedateien
            mean_image = mean_image + picure_data[index]
        mean_image = mean_image / numbber_images
        mean_image = np.rint(mean_image)                                                        # Werte auf Ganzzahlen runden
        ergmean_image = np.zeros((1, rows, cols), dtype=np.uint16)                              # 3D-Array erzeugen, ansonsten nicht kompatibel
        ergmean_image[0] = np.array(mean_image, dtype=np.uint16)

        if export == True:
            dir_name = os.path.join(pExportPath, "Originalpicture vom " + current_time)
            if os.path.exists(dir_name):
                pass
            else:
                os.mkdir(dir_name)
            file_name = (os.path.splitext(os.path.basename(pImportPath))[0] + "_original_mittelwert.png")
            cv2.imwrite(os.path.join(dir_name, file_name), ergmean_image[0])                    # Array als PNG speichern ohne Kompression

    fd.close()  # File schließen
    if average == True:
        return ergmean_image
    else:
        return picure_data


def import_function(pImportPath, export=False, pExportPath="", time=""):                        # vill noch ne fehlermeldung Wenn der Path kein Link enthält!?
    current_time = time                                                                         # aktuelles Datum und Zeit
    picture = cv2.imread(pImportPath, flags=-1)
    if np.shape(picture) == ():                                                                 # wenn das Lesen nicht erfoglreich war
        return np.zeros((1, 512, 512), dtype=np.uint16)
    picure_data = np.zeros((1, np.shape(picture)[0], np.shape(picture)[1]), dtype=picture.dtype)
    if np.shape(picure_data[0]) == np.shape(picture):                                           # Wenn die Array eine andere Größe besitzen, d.h. wenn es kein Farbpicture ist
        picure_data[0] = picture
    else:
        print("Farbpicture")

    if export == True:
        dir_name = os.path.join(pExportPath, "Originalpictureer vom " + current_time)
        if os.path.exists(dir_name):
            pass
        else:
            os.mkdir(dir_name)
        file_name = os.path.splitext(os.path.basename(pImportPath))[0] + "_original.png"
       
        cv2.imwrite(os.path.join(dir_name, file_name), picture)                                 # Array als PNG speichern ohne Kompression
    return picure_data


def import_ui_function(pImportPath, pMittelwert=True, pExport=False, pExportPath="", pMittelwertGesamt=False,):          # Rückgabe picture-Array und Auflösung Breite und Höhe get_picture_data
    rows, cols, numb, color_depth = get_picture_data(pImportPath[0])
    picure_data = np.empty((0, rows, cols), dtype=color_depth)
    current_time = str(datetime.now())[:-7].replace(":", "-")                                                   # aktuelles Datum und Zeit
    for current_path in pImportPath:
        data_ending = (os.path.splitext(os.path.basename(current_path))[1]).lower()                             # data_ending aus dem Pfad seperarieren, kleinschreiben, weil manche OS (Windows) Dateieindungen Groß schreiben
        if data_ending == ".his":                                                                               # Eine his-Datei
            current_arr = his_import_function(current_path, pExport, pMittelwert, pExportPath, current_time)
            picure_data = np.append(picure_data, current_arr, axis=0)

        elif ( data_ending == ".png"
            or data_ending == ".jpg"
            or data_ending == ".jpeg"
            or data_ending == ".tif"
            or data_ending == ".tiff"):
            picure_data = np.append(picure_data, import_function(current_path, pExport, pExportPath=pExportPath, time=current_time), axis=0,)
    
    if pMittelwertGesamt:
        mean_image = np.zeros([rows, cols], dtype=np.uint32)
        for index in range(np.shape(picure_data)[0]):                               # numb der picturedateien
            mean_image = mean_image + picure_data[index]
        mean_image = mean_image / np.shape(picure_data)[0]
        mean_image = np.rint(mean_image)                                            # Werte auf Ganzzahlen runden
        ergmean_image = np.zeros((rows, cols), dtype=color_depth)                   # 3D-Array erzeugen, ansonsten nicht kompatibel
        ergmean_image = np.array(mean_image, dtype=color_depth)
        return ergmean_image
    else:
        return picure_data


def get_picture_data(pImportPath):
    data_ending = (os.path.splitext(os.path.basename(pImportPath))[1]).lower()      # kleinschreiben, weil manche OS (Windows) Dateieindungen Groß schreiben
    if data_ending == ".his":                                                       # Eine his-Datei
        fd = open(pImportPath, "rb")                                                # Das picture öffnen im "rb"-Modus: read binary
        data = np.fromfile(fd, dtype=np.uint16, count=50)                          # Den Header 50 mal mit unsinged int 16 Bit einlesen (erste 100 Bytes)
        rows = int(np.take(data, 8))                                                # Reihen bestimmen, in int konvertieren, ansonsten overflow Error bei der Funktion fromfile()
        cols = int(np.take(data, 9))                                                # Spalten bestimmen
        numb = int(np.take(data, 10))                                               # Nu der picture aus der HIS Datei auslesen.
        fd.close()  # File schließen
        color_depth = get_color_depth(pImportPath)

    elif ( data_ending == ".png"
        or data_ending == ".jpg"
        or data_ending == ".jpeg"
        or data_ending == ".tif"
        or data_ending == ".tiff"):
        picture = cv2.imread(pImportPath, flags=-1)                                 # picture mit OpenCV einlesen
        if picture is None:
            print("Fehler beim imread")
            rows = 0
            cols = 0
            numb = 0
            temp_var = np.zeros(1, dtype=np.int64)                                  # Für einheitiger Rückgabetyp
            color_depth = temp_var.dtype                                            # Datei gibt keinen Sinn
        else:
            rows = np.shape(picture)[0]                                             # Reihennumb bestimmen
            cols = np.shape(picture)[1]                                             # Spaltennumb bestimmen
            numb = 1
            color_depth = picture.dtype
    return rows, cols, numb, color_depth


def check_grey_image(pImportPath):
    picture = cv2.imread(pImportPath, flags=-1)
    picure_data = np.zeros((1, np.shape(picture)[0], np.shape(picture)[1]), dtype=picture.dtype)
    if np.shape(picure_data) == np.shape(picture):                                  # Wenn die Array eine andere Größe besitzen, d.h. wenn es kein Farbpicture ist
        return True
    else:
        return False


"""
import os
import platform
import subprocess

def open_file(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

open_file("/Users/julian/Documents")
"""


"""
meineListe = 0

meineListe = np.zeros((2,3,3),dtype=np.uint16)
#print("\n-----------------\n", meineListe)
#meineListe[0,0,0]  = 1
#print("\n-----------------\n", meineListe)

meineListe = np.append(meineListe,[[[3, 3, 3 ],[3, 3, 3],[3, 3, 3]]], axis= 0 )


meineListe = np.empty((0,3,3), dtype=np.uint16)
print("\n-----------------\n", meineListe)
meineListe = np.append(meineListe,[[[3, 3, 3 ],[3, 3, 3],[3, 3, 3]]], axis= 0 )
print("\n-----------------\n", meineListe)
meineListe = np.append(meineListe,[[[43,43, 43 ],[43, 43, 43],[43, 43, 43]]], axis= 0 )
print("\n-----------------\n", meineListe)

pass

"""

# deprecated/veraltete Funktionen
"""
def get_picture_data2(pImportPath):
    data_ending = (os.path.splitext(os.path.basename(pImportPath)) [1]).lower() # kleinschreiben, weil manche OS (Windows) Dateieindungen Groß schreiben
    if data_ending == ".his": # Eine his-Datei
        fd = open(pImportPath,'rb')                                             # Das picture öffnen im "rb"-Modus: read binary
        data = np.fromfile(fd,dtype=np.uint16, count=50)                        # Den Header 50 mal mit unsinged int 16 Bit einlesen (erste 100 Bytes)
        rows = int(np.take(data, 8))                                            # Reihen bestimmen, in int konvertieren, ansonsten overflow Error bei der Funktion fromfile()
        cols = int(np.take(data, 9))                                            # Spalten bestimmen
        fd.close()        
        numb = get_numbber_images(pImportPath, rows, cols)                                                     # File schließen
        #color_depth = data.dtype.name
        color_depth = data.dtype
    elif data_ending == ".png" or data_ending == ".jpg" or data_ending == ".jpeg" or data_ending == ".tif" or data_ending == ".tiff":
        picture = cv2.imread(pImportPath, flags= -1)
        rows = np.shape(picture)[0]
        cols = np.shape(picture)[1]
        numb = 1
        #color_depth = picture.dtype.name
        color_depth = picture.dtype
    return rows, cols, numb, color_depth


def import_ui_functionAlt(pImportPath, export = False): # Rückgabe picture-Array und Auflösung Breite und Höhe
    data_ending = (os.path.splitext(os.path.basename(pImportPath)) [1]).lower()
    if data_ending == ".his": # Eine his-Datei
        picure_data = his_import_function(pImportPath, export)
    elif data_ending == ".png" or data_ending == ".jpg" or data_ending == ".jpeg" or data_ending == ".tif" or data_ending == ".tiff":
        picure_data = import_function(pImportPath, export)
    return picure_data


def his_import_function2(pImportPath, export = False):                       # Funktion: pictureer im HIS-Format importieren, Übergabewert: Path zum picture
    path_without_extensions = os.path.splitext(pImportPath) [0]                # Pfad ohne data_ending erzeugen, .his wird entfernt
    print("\n\n*************************************************************")
    print("Funktion zum Einlesen von HIS-Dateien aufgerufen")
    print("*************************************************************\n")
    file_name, file_extensions = os.path.splitext(os.path.basename(pImportPath))# Dateinamen und data_ending extrahieren    
    print("Die Datei", file_name, "wird jetzt eingelesen.")
    fd = open(pImportPath,'rb')                                             # Das picture öffnen im "rb"-Modus: read binary
    data = np.fromfile(fd,dtype=np.uint16, count=50)                        # Den Header 50 mal mit unsinged int 16 Bit einlesen (erste 100 Bytes)
    rows = int(np.take(data, 8))                                            # Reihen bestimmen, in int konvertieren, ansonsten overflow Error bei der Funktion fromfile()
    cols = int(np.take(data, 9))                                            # Spalten bestimmen
    numbber_images = int(get_numbber_images(pImportPath, rows, cols))            # numb der pictureer in der Datei bestimmen
    print("Ihre Datei hat", rows, "Reihen und", cols, "Spalten und besteht aus", numbber_images, "picture(ern)")

    for index in range(numbber_images):                                       # Alle pictureer anzeigen und speichern
        f = np.fromfile(fd, dtype=np.uint16, count=rows*cols)               # Pixel lesen und in einem ein dimensionales Array speichern
        im = f.reshape((rows, cols)) 
                                              # Array in zwei dimensionales Array mit rows x cols erstellen
        #np.savetxt("foo.csv", im, delimiter=";")

        #for testValue in np.nditer(f):
        #    if testValue >= 60000:
        #        print("Sehr schwarz hier!")
        #plt.plot(im)
        #plt.show()
        if export == True:
            cv2.imshow('image', im)                                             # Array als picture anzeigen
            cv2.imwrite(path_without_extensions+"_"+str(index)+'_beta.png',im)     # Array als PNG speichern ohne Kompression
            print("Ihre Datei wurden unter", path_without_extensions+"_"+str(index)+".png gespeichert")
            cv2.waitKey()                                                       # Warten bis eine Taste gedrückt wird      
    if export == True:
        cv2.destroyAllWindows()                                                 # Alle Fenster schließen    
    fd.close()                                                              # File schließen
    return im


"""
