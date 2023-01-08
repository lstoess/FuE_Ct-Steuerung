import os
import cv2
import import_pictures as imp
from pathlib import Path
import PyQt5.QtCore as core
import json
from datetime import date
import config as cfg
from natsort import os_sorted  # für das Sortieren der BPM nach dem Alphabet
import datetime
import numpy as np


def BPM_save(BPM, Sensor_Name):
    # Rücklesen wie viele BPMs es gibt Aus Dateiname
    x = os.listdir(dir_path)
    print(len(x), " Dateien im Ordner")
    # Davon sensor
    number = 0
    for i in range(len(x)):
        file_name = str(x[i])
        if file_name.find(Sensor_Name) != -1:
            start = file_name.find("V", len(Sensor_Name))
            end = file_name.find(".", len(Sensor_Name))
            if (start < 0) or (end < 0):  # Wenn die Datei kein V oder . im Namen hat
                pass
            else:
                s_number = file_name[start + 1 : end]
                # print(s_number)
                number = int(s_number)
                if number > number:
                    number = number
                    # y=x[i]
    if len(x) > 300:
        print("Speicher voll")
        return -1
    else:
        # Schreiben
        number = number + 1
        file_path = os.sep.join([dir_path, Sensor_Name + "_V" + str(number) + ".png"])
        cv2.imwrite(file_path, BPM)
        return 0


def BPM_read(Sensor_Name):
    # Rücklesen wie viele BPMs es gibt Aus Dateiname
    x = os.listdir(dir_path)
    # Davon sensor
    number = 0
    for i in range(len(x)):
        file_name = str(x[i])
        if file_name.find(Sensor_Name) != -1:
            start = file_name.find("V", len(Sensor_Name))
            end = file_name.find(".", len(Sensor_Name))
            if (start < 0) or (end < 0):  # Wenn die Datei keiin V oder . im Namen hat
                pass
            else:  # wenn die Datei ein V und . im Namen hat
                s_number = file_name[start + 1 : end]
                # print(s_number)
                number = int(s_number)
                if number > number:
                    number = number
                    # y=x[i]
    if number == 0:
        print("Kein Korrekturdatensatz vorhanden, muss Erstellt werden")  # Error Meldungen in GUI?
        return -1
    else:
        file_path = os.sep.join([dir_path, Sensor_Name + "_V" + str(number) + ".png"])
        BPM = imp.import_function(file_path)  # ???
        return BPM[0]


global dir_path
dir_path = core.QStandardPaths.writableLocation(core.QStandardPaths.AppDataLocation)
dir_path = os.sep.join([dir_path, "Bad_Pixel Maps"])
print(dir_path)
if not os.path.exists(dir_path):
    os.makedirs(dir_path)

# Python program to write JSON
# to a file

# data to be written
global read_flag
read_flag = False  # start vom Programm
InitConfigData = {
    "Firma": "Roematek",
    "Autor": "Julian und Andy",
    "Datum": str(date.today()),
    "Sensors": [
        # {
        #     "Sensor_Name" : "",
        #     "Erstell_Datum" : "1995-01-01",
        #     "Anz_Bilder" : 0,
        #     "Anz_PixelFehler" : 0,
        #     "last_Fensterbreite_advWindow" : 88,
        #     "last_Faktor_advWindow" : 3,
        #     "last_Schwellwert_oben" : 99,
        #     "last_Schwellwert_unten" : 1,
        #     "last_Faktor_Dynamik" : 8,
        #     "last_korrekturmethode" : 3, #int(cfg.Methoden.NSRC),
        #     "last_Fenster_Nachbar" : 5,
        #     "last_Fenster_Gradient" : 5,
        #     "Flat_Field_vorhanden" : False,
        #     "Aenderungs_Datum" : str(date.today())
        # }
    ],
    "last_GenutzterSensor": "erzeuge einen sensor",
    "Import_Pfad": " ",
    "Export_Pfad": " ",
}


def read_json():
    json_path = os.sep.join([dir_path, "config.json"])
    # Json Suchen bzw Anlegen.
    if not os.path.exists(json_path):
        write_json(InitConfigData)  # dump
        print("Json config nicht vorhanden. Erstellen...")
        # return -1
    # Json Laden (Open ...)
    with open(json_path, "r") as open_file:
        # Reading from json file
        json_object = json.load(open_file)
    # print(json_object)
    # print(type(json_object))
    read_flag = True
    return json_object


def write_json(data):  # Oder immer zu Laufzeit
    # Serializing json
    json_object = json.dumps(data, indent=4, sort_keys=True)
    json_path = os.sep.join([dir_path, "config.json"])
    with open(json_path, "w") as outfile:
        outfile.write(json_object)
    return 0


def which_sensors(data):
    num = len(data["Sensors"])
    sensor = []
    for i in range(num):
        buf = data["Sensors"][i]["Sensor_Name"]
        sensor.append(buf)
    return num, sensor


def sensor_create(name, data):
    # Prüfen ob vorhanden:
    for i in range(len(data["Sensors"])):
        if name == data["Sensors"][i]["Sensor_Name"]:
            return -1
    data["Sensors"].append(
        {
            "Sensor_Name": str(name),
            "Erstell_Datum": str(date.today()),
            "Anz_Bilder": 0,
            "Anz_PixelFehler": 0,
            "last_Fensterbreite_advWindow": 88,
            "last_Faktor_advWindow": 3,
            "last_Schwellwert_oben": 99,
            "last_Schwellwert_unten": 1,
            "last_Faktor_Dynamik": 8,
            "last_korrekturmethode": 3,  # int(cfg.Methoden.NSRC),
            "last_Fenster_Nachbar": 5,
            "last_Fenster_Gradient": 5,
            "Flat_Field_vorhanden": False,
            "Aenderungs_Datum": str(date.today()),
        }
    )
    return 0


def sensor_delete(name, data):
    # Prüfen ob vorhanden:
    for i in range(len(data["Sensors"])):
        if name == data["Sensors"][i]["Sensor_Name"]:
            del data["Sensors"][i]
            # print("geloescht") # verursachen Bugs unter Mac OS. WTF? Lag an ö
            return 0
    # print("Nicht gefunden")
    return -1


def which_BPM(name):
    global dir_path
    if os.path.isdir(dir_path):  # os.path.exists(dirname): # wenn der Pfad überhaupt existiert
        files = os.listdir(dir_path)
        files = os_sorted(files)
        files.reverse()

        BPM_files = []
        if name == "":  # alle Sensoren wurden gelöscht
            return BPM_files  # keine BPM anzeigen
        for current_file in files:
            if current_file.find(name) == 0:  # Wenn der name im Dateinahme vorkommt
                if current_file.find("_V", len(name)) == len(name):  # Kommt nach dem Sensorname gleich die Nummerierung
                    BPM_files.append(current_file)

        return BPM_files


# which_BPM("test")
def BPM_read_selected(BPM_name):
    file_path = os.path.join(dir_path, BPM_name)
    BPM = imp.import_function(file_path)
    # print(BPM) debug
    return BPM[0]


# BPM_read_selected("Igel_V2.png")


def get_mod_time_BPM(BPM_name):
    file_path = os.path.join(dir_path, BPM_name)
    timestamp = os.path.getmtime(file_path)
    value = datetime.datetime.fromtimestamp(timestamp)
    return value.strftime("%Y-%m-%d %H:%M:%S")


def get_num_err_BPM(BPM_name):
    BPM_map = BPM_read_selected(BPM_name)
    num_err = np.count_nonzero(BPM_map)
    return num_err


def delete_BPM(BPM_name):
    global dir_path
    file_path = os.path.join(dir_path, BPM_name)
    os.remove(file_path)


def delete_all_BPM(Sensor_Name):
    global dir_path
    if os.path.isdir(dir_path):  # os.path.exists(dirname): # wenn der Pfad überhaupt existiert
        files = os.listdir(dir_path)
        BPM_files = []
        if Sensor_Name == "":  # alle Sensoren wurden gelöscht
            return  # keine BPM anzeigen
        for current_file in files:
            if current_file.find(Sensor_Name) == 0:  # Wenn der name am Anfang steht
                if current_file.find("_V", len(Sensor_Name)) == len(Sensor_Name):  # Kommt nach dem Sensorname gleich die Nummerierung
                    # print("wird geloescht") # Achtung Bug unter Mac
                    os.remove(os.path.join(dir_path, current_file))



def save_FFK(Sensor_Name, bright_pic, dark_pic):
    if os.path.isdir(dir_path):  # os.path.exists(dirname): # wenn der Pfad überhaupt existiert
        file_path = os.path.join(dir_path, Sensor_Name + "_FFK_Hellbild.png")
        cv2.imwrite(file_path, bright_pic)
        file_path = os.path.join(dir_path, Sensor_Name + "_FFK_dark_pic.png")
        cv2.imwrite(file_path, dark_pic)


def load_FFK(Sensor_Name, flag_show=False):
    bright_pic = []
    dark_pic = []
    if os.path.isdir(dir_path):  # os.path.exists(dirname): # wenn der Pfad überhaupt existiert
        files = os.listdir(dir_path)
        for current_file in files:
            if current_file.find(Sensor_Name) == 0:  # Wenn der name am Anfang steht
                if current_file.find("_FFK_Hellbild.png", len(Sensor_Name)) == len(Sensor_Name):  # Kommt nach dem Sensorname gleich _FFK_Hellbild.png
                    bright_pic = imp.import_function(os.path.join(dir_path, current_file))[0]
                    if flag_show:
                        cv2.imshow("FFK_Hellbild", bright_pic)
                    print("bright_pic")  # debug
                elif current_file.find("_FFK_dark_pic.png", len(Sensor_Name)) == len(Sensor_Name):  # Kommt nach dem Sensorname gleich _FFK_dark_pic.png
                    dark_pic = imp.import_function(os.path.join(dir_path, current_file))[0]
                    print("dark_pic")  # debug
                    if flag_show:
                        win_name = "FFK_Dunkelbild"
                        cv2.namedWindow(win_name)  # Create a named window
                        cv2.moveWindow(win_name, 512, 0)  # Move it to (40,30)
                        cv2.imshow(win_name, dark_pic)
    return bright_pic, dark_pic
