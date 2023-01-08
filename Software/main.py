"""
/*
 * @Author: Julian Schweizerhof und Andreas Bank
 * @Email: diegruppetg@gmail.com
 * @Date: 2020-10-16 12:09:24
 * @Last Modified by: JLS666
 * @Last Modified time: 2021-03-05 22:42:34
 * @Last Modified by: Carlo Piotrowski
 * @Last Modified time: 2022-02-01 22:42:34
 * @Description: Main des Projektes, primär ermöglicht diese Datei die GUI
 */
"""

""" Import der Bibliotheken:__________________________________________________________________________________"""
# globale Bibliotheken
from fbs_runtime.application_context.PyQt5 import ApplicationContext  # für das fbs
import sys
import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets
import PyQt5.QtGui as gui
import PyQt5.uic as uic

# import types
import os
import numpy as np
from _thread import start_new_thread, allocate_lock                 # oder mit therading lib.
import threading
import platform                                                     # für das Öffnen des File Explores
import subprocess                                                   # für das Öffnen des File Explores
from datetime import datetime
import shutil
import copy
import cv2

# lokale Bibliotheken
import import_pictures as imp
import export_pictures as exp
import save
import config as cfg
import detection
import correction
import telemetry

# LS: Globale Variablen waren vorher an erster Stelle in der __main__ (Test Auslagerung Methoden)
""" Globale Variablen:___________________________________________________________________________________ """
current_tab = 0        # Zustand des Tabs der GUI
num_pictures = 0        # Anzahl der importierten Bilder für die Zeilenanzahl der Tabelle
num_pictures_bright = 0    # Anzahl der importierten Bilder Hell für die Zeilenanzahl der Tabelle Flat-Field-Korrektur
num_pictures_dark = 0  # Anzahl der importierten Bilder Dunkel für die Zeilenanzahl der Tabelle Flat-Field-Korrektur
sensor_list = ["Bitte Ihren Sensor auswählen"]
image_data = 0           # hier werden die importierten Bilder gespeichert, 3D-Array: [num_pictures][Zeilen][Spalten]
image_data_bright = (0)     # hier werden die importierten Bilder gespeichert, 2D-Array: [Zeilen][Spalten]
image_data_dark = (0)       # hier werden die importierten Bilder gespeichert, 2D-Array: [Zeilen][Spalten]
DATA = 0                    # Die Daten für die Speicherung der Config Datei
mean_pictures = 0           # Mittelwert aller importierten Bilder
flag_BPM_prev = False       # Flag für die Anzeige der BPM-Vorschau auf dem ersten Tab
BAD_total = 0               # für das Speichern der BAD Pixel Map

""" Beginn der Hauptfunktion:__________________________________________________________________________________"""
if __name__ == "__main__":

    """Laden der Gui-UI-Dateien:___________________________________________________________________________________"""
    app = widgets.QApplication(sys.argv)
    mW = uic.loadUi("badPixelMainWindow.ui")  # UI-Fenster MainWindow laden
    nB = uic.loadUi("neueBPM.ui")
    eS = uic.loadUi("einstellungenSuchen.ui")
    eK = uic.loadUi("einstellungenKorrigieren.ui")
    fF = uic.loadUi("flatFieldKorrektur.ui")
    progress = uic.loadUi("fortschritt.ui")
    image_window = uic.loadUi("bildFenster.ui")
    msg_box = widgets.QMessageBox()  # Die Message Box

    """ Funktionen für die GUI:___________________________________________________________________________________ """
    ############ Allgemeine Funktionen ########################################################################################
    def start_clicked():  # Funktion wenn der start-Button geklickt wird
        global current_tab
        # Speichern wie bei forward
        save.write_json(DATA)  # Schreiben am Ende   # Julian: eigentlich unnötig, da startClicked einem Forward Klick entspricht

        # Check BPM is valid
        if (DATA["Sensors"] == [] and mW.checkBoxRohbilderSpeichern.isChecked() == False):  # wenn es keine Sensoren gibt
            open_msg_box(
                icon=widgets.QMessageBox.Information,
                text="Für die Suche und der Korrektur muss zuerst ein Sensor erstellt werden.",
                informativeText="",
                windowTitle="Sie müssen hierfür zuerst einen Sensor erstellen",
                standardButtons=widgets.QMessageBox.Ok,
                pFunction=msg_button_click,
            )
            mW.tabWidget.setCurrentIndex(0)
            return False
        elif DATA["Sensors"] == [] and (
            mW.checkBoxAlgorithmusSuchen.isChecked() == True
            or mW.checkBoxAlgorithmusKorrigieren.isChecked() == True
        ):  # wenn etwas außer Rohbilder angehakt wurde und kein Sensor gibt
            open_msg_box(
                icon=widgets.QMessageBox.Information,
                text="Für die Suche und der Korrektur muss zuerst ein Sensor erstellt werden.",
                informativeText="",
                windowTitle="Sie müssen hierfür zuerst einen Sensor erstellen",
                standardButtons=widgets.QMessageBox.Ok,
                pFunction=msg_button_click,
            )
            mW.tabWidget.setCurrentIndex(0)
            return False
        # Check Bilddaten are valid
        if mW.tableWidgetBilddaten.rowCount() == 0:
            open_msg_box(
                icon=widgets.QMessageBox.Information,
                text="Bitte importieren Sie Bilder.",
                informativeText="",
                windowTitle="Keine Bilder importiert",
                standardButtons=widgets.QMessageBox.Ok,
                pFunction=msg_button_click,
            )
            current_tab = 1
            mW.tabWidget.setCurrentIndex(current_tab)
            return False
        for aktuelleZeile in range(mW.tableWidgetBilddaten.rowCount()): # Beim Suchen und Korrigieren wird folgendes überprüft...
            if (
                mW.checkBoxAlgorithmusSuchen.isChecked()
                or mW.checkBoxAlgorithmusKorrigieren.isChecked()
            ):
                # ...ob die Auflösung der Bilder identisch ist, Rohbilder können auch mit verschieden Auflösungen exportiert werden.

                if (
                    mW.tableWidgetBilddaten.item(0, 1).text()
                    != mW.tableWidgetBilddaten.item(aktuelleZeile, 1).text()
                ):
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Die Auflösung der importierten Bilder ist unterschiedlich",
                        informativeText="Bitte entfernen Sie die falschen Bilder.",
                        windowTitle="Falsche Auflösung",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                        )
                    
                    current_tab = 1
                    mW.tabWidget.setCurrentIndex(current_tab)
                    return False
                                   

                # ...ob die Farbtiefe der Bilder identisch ist, Rohbilder können auch mit verschieden Farbtiefen exportiert werden.
                if (
                    mW.tableWidgetBilddaten.item(0, 3).text()
                    != mW.tableWidgetBilddaten.item(aktuelleZeile, 3).text()
                ):
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Die Farbtiefe der importierten Bilder ist unterschiedlich",
                        informativeText="Bitte entfernen Sie die falschen Bilder.",
                        windowTitle="Falsche Farbtiefe",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,)
                    
                    current_tab = 1
                    mW.tabWidget.setCurrentIndex(current_tab)
                    return False
                    
              
                # ...ob die Auflösung der Bilder und der BPM identisch sind, Rohbilder können trotzdem exportiert werden.
                """
                if mW.tableWidgetBilddaten.item(aktuelleZeile, 1).text() != "": # todo: Überprüfen ob die Auflösung der Bilder und der BPM identisch sind, Format: "rows x cols", Beachte: wenn es noch keine gibt, muss es übersprungen werden
                    open_msg_box(icon=widgets.QMessageBox.Information, text="Auslösung der Bad-Pixel-Map und der importierten Bilder sind unterschiedlich",informativeText="Die Auflösung des Bildes aus der " + str(aktuelleZeile) + " Zeile ist nicht mit der Auflösung der Bad-Pixel identisch. Bitte die falschen Bilder löschen oder einen anderen Sensor auswählen.",windowTitle="Falsche Auflösung BPM oder Bilder",standardButtons=widgets.QMessageBox.Ok,pFunction=msgButtonClick)
                    return False  
                """
        # Check Speicherort is valid
        if (
            mW.checkBoxAlgorithmusKorrigieren.isChecked()
            or mW.checkBoxRohbilderSpeichern.isChecked()
        ):  # Speicherort ist beim Suchalgorithmus nicht notwendig.
            if (
                os.path.isdir(mW.lineEditSpeicherort.text()) == False
            ):  # exists(mW.lineEditSpeicherort.text()) == False:
                open_msg_box(
                    icon=widgets.QMessageBox.Information,
                    text="Der eingegebene Pfad für den Speicherort ist nicht gültig",
                    informativeText='Der Pfad: "'
                    + mW.lineEditSpeicherort.text()
                    + '" ist kein gültiger Ordnerpfad. Bitte ändern Sie den eingegebenen Pfad.',
                    windowTitle="Kein gültiger Pfad",
                    standardButtons=widgets.QMessageBox.Ok,
                    pFunction=msg_button_click,
                )
                current_tab = 2
                mW.tabWidget.setCurrentIndex(current_tab)
                return False
        # Check Algorithmus is valid
        if mW.checkBoxAlgorithmusSuchen.isChecked() == True:
            if (mW.checkBoxAlgorithmusWindow.isChecked() and num_pictures > 8):  # Nur Warnung
                open_msg_box(
                    icon=widgets.QMessageBox.Information,
                    text="Eine große Zahl an Bildern führt zu erhöhten Laufzeiten bei dem Moving-Window-Algorithmus.",
                    informativeText="Wählen Sie andere Algorithmen, oder wenden Sie den Moving-Window-Algorithmus nur auf eine Untermenge der Importe an. Für die Korrektur können anschließend alle Ihrer Importe ohne Suchen verarbeitet werden.",
                    windowTitle="Laufzeitwarnung Moving-Window",
                    standardButtons=widgets.QMessageBox.Ok,
                    pFunction=msg_button_click,
                )
            if mW.checkBoxAlgorithmusDynamic.isChecked() and num_pictures < 3:
                open_msg_box(
                    icon=widgets.QMessageBox.Information,
                    text="Die Anzahl an Bildern ist zu gering für einen Dynamic Algorithmus",
                    informativeText="Erhöhen Sie die Importe, oder wählen Sie z.B. Moving Window",
                    windowTitle="geringe Anzahl an Bildern Dynamic",
                    standardButtons=widgets.QMessageBox.Ok,
                    pFunction=msg_button_click,
                )
                return False
        # wenn nicht angekreuzt wurde:
        if (
            mW.checkBoxAlgorithmusSuchen.isChecked() == False
            and mW.checkBoxAlgorithmusKorrigieren.isChecked() == False
            and mW.checkBoxRohbilderSpeichern.isChecked() == False
        ):
            open_msg_box(
                icon=widgets.QMessageBox.Information,
                text="Bitte wählen sie mind. eine Checkbox für den Suchalgorithmus aus.",
                informativeText="",
                windowTitle="Sie haben nichts für den Suchalgorithmus ausgewählt",
                standardButtons=widgets.QMessageBox.Ok,
                pFunction=msg_button_click,
            )
            return False
        # wenn nichts innerhalb von Suchen angekreuzt wurde:
        if mW.checkBoxAlgorithmusSuchen.isChecked():
            if (
                mW.checkBoxAlgorithmusSchwellwertfilter.isChecked() == False
                and mW.checkBoxAlgorithmusDynamic.isChecked() == False
                and mW.checkBoxAlgorithmusWindow.isChecked() == False
            ):
                open_msg_box(
                    icon=widgets.QMessageBox.Information,
                    text="Bitte wählen sie mind. eine Checkbox für den Suchalgorithmus aus.",
                    informativeText="",
                    windowTitle="Sie haben nichts für den Suchalgorithmus ausgewählt",
                    standardButtons=widgets.QMessageBox.Ok,
                    pFunction=msg_button_click,
                )
                return False

        # Check Flat-Field-Korrektur ist valid:
        if (
            mW.checkBoxAlgorithmusFFK.isChecked()
            and mW.checkBoxAlgorithmusKorrigieren.isChecked()
        ):
            pass

        # Update UI
        progress.textEdit.clear()  # Info Textfeld löschen
        progress.buttonBox.button(widgets.QDialogButtonBox.Ok).setEnabled(
            False
        )  # Okay Button disable

        # wenn nur Suchen ausgewählt ist, soll nicht der Speicherort anzeigen Button erscheinen
        if (
            mW.checkBoxAlgorithmusSuchen.isChecked() == True
            and mW.checkBoxAlgorithmusKorrigieren.isChecked() == False
            and mW.checkBoxRohbilderSpeichern.isChecked() == False
        ):
            progress.pushButtonOeffnen.setVisible(False)
        else:
            progress.pushButtonOeffnen.setVisible(True)
       
        # Import Pictures
        global image_data
        global mean_pictures
        pathlist = []
        for index in range(num_pictures):  # alle Pfade aus der Tabelle in eine Liste schreiben
            pathlist.append(mW.tableWidgetBilddaten.item(index, 4).text())
        if mW.checkBoxRohbilderSpeichern.isChecked():
            image_data = imp.import_ui_function(
                pathlist,
                pMittelwert=True,
                pExport=True,
                pExportPath=mW.lineEditSpeicherort.text(),
            )
            progress.textEdit.insertPlainText(
                'Rohbilder wurden unter: "'
                + mW.lineEditSpeicherort.text()
                + '" gespeichert.\n'
            )
        else:
            image_data = imp.import_ui_function(pathlist, pMittelwert=True, pExport=False)
        mean_pictures = imp.import_ui_function(pImportPath=pathlist, pMittelwertGesamt=True)

        # Import Flatfield Bilder
        if (
            mW.checkBoxAlgorithmusFFK.isChecked()
            and mW.checkBoxAlgorithmusKorrigieren.isChecked()
        ):
            if fF.radioButtonNeueBilder.isChecked():  # neue Bilder werden eingefügt
                global num_pictures_bright
                global num_pictures_dark
                global image_data_bright
                global image_data_dark
                pathlistHell = []
                pathlistDunkel = []
                for index in range(num_pictures_bright):  # alle Pfade aus der Tabelle in eine Liste schreiben
                    pathlistHell.append(fF.tableWidgetHell.item(index, 4).text())
                image_data_bright = imp.import_ui_function(pImportPath=pathlistHell, pMittelwertGesamt=True)
                for index in range(num_pictures_dark):
                    pathlistDunkel.append(fF.tableWidgetDunkel.item(index, 4).text())
                image_data_dark = imp.import_ui_function(pImportPath=pathlistDunkel, pMittelwertGesamt=True)

                # FFK Bilder speichern
                save.save_FFK(mW.comboBoxBPMSensor.currentText(), image_data_bright, image_data_dark)

            else:  # Bilder sollen geladen werden
                image_data_bright, image_data_dark = save.load_FFK(mW.comboBoxBPMSensor.currentText())
                if image_data_bright == []:
                    print("Fehler")
                if image_data_dark == []:
                    print("Fehler")

        # Ladebalken init
        cfg.loading_bar = 0
        if mW.checkBoxAlgorithmusSuchen.isChecked():
            Anz = (
                int(mW.checkBoxAlgorithmusSchwellwertfilter.isChecked())
                + int(mW.checkBoxAlgorithmusWindow.isChecked())
                + int(mW.checkBoxAlgorithmusDynamic.isChecked())
            )
        else:
            Anz = 0
        cfg.loading_bar_max = Anz * np.shape(image_data)[0] + Anz
        print("Rechenschritte=", cfg.loading_bar_max)
        # Suchen Treads
        IDs = []
        if mW.checkBoxAlgorithmusSuchen.isChecked():
            if mW.checkBoxAlgorithmusSchwellwertfilter.isChecked():
                # BPM_Schwellwert=detection.MultiPicturePixelCompare(bildDaten,GrenzeHot=0.995,GrenzeDead=0.1)[0]
                T_ID_MPPC = threading.Thread(
                    name="MPPC",
                    target=detection.multi_picture_pixel_compare,
                    args=(
                        image_data,
                        float(eS.labelSchwellwertHot.text()),
                        float(eS.labelSchwellwertDead.text()),
                    ),
                )
                IDs.append(T_ID_MPPC)
                T_ID_MPPC.start()
            if mW.checkBoxAlgorithmusDynamic.isChecked():
                # BPM_Dynamik=detection.dynamicCheck(bildDaten,Faktor=1.03)[0]
                T_ID_dC = threading.Thread(
                    name="dc",
                    target=detection.dynamic_check,
                    args=(image_data, float(eS.labelDynamicSchwellwert.text())),
                )
                IDs.append(T_ID_dC)
                T_ID_dC.start()
            if mW.checkBoxAlgorithmusWindow.isChecked():
                # BPM_Window=detection.advancedMovingWindow(bildDaten[0],Faktor=2.0,Fensterbreite=10)[0]
                T_ID_aMW = threading.Thread(
                    name="aMW",
                    target=detection.advanced_moving_window,
                    args=(
                        image_data,
                        int(eS.labelMovingFensterbreite.text()),
                        float(eS.labelMovingSchwellwert.text()),
                    ),
                )
                IDs.append(T_ID_aMW)
                T_ID_aMW.start()
        # ====Jetzt wird gesucht!====#
        timer.start(cfg.recall_time)  # ms heruntersetzen für Performance
        """
        pixmap = gui.QPixmap(" ")
        
        fortschritt.label.setPixmap(pixmap)
        fortschritt.label.setScaledContents(True)
        fortschritt.label.resize(pixmap.width(), pixmap.height())
        """

        progress.progressBar.setValue(0)
        if progress.exec() == widgets.QDialog.Rejected:  # Abbrechen
            print("Gecancelt gedrueckt")  # hier muss dann der process gestoppt werden.
            cfg.kill_flag_threads = True  # alle Treads killen
            cfg.loading_bar = 0
            timer.stop()  # process ist damit abgeschalten.
            print("Try to join")
            for ID in IDs:
                if ID.is_alive():
                    ID.join()
                    print(ID, "der leuft ja noch!")
            print("Treads sind alle tot")
            cfg.kill_flag_threads = False
            cv2.destroyAllWindows()
        else:
            if (mW.checkBoxAlgorithmusSuchen.isChecked()):  # nur eine neue Bad Pixelmap speichern, wenn auch Fehler gesucht wurden
                save.BPM_save(BAD_total * 150, mW.comboBoxBPMSensor.currentText())  # BPM Speichern
            cv2.destroyAllWindows()
            update_BPM()
            update_text_BPM()  # Text auf dem erstem Tab aktualisieren
            show_BPM()
        print("startClicked")  # Debug
        """
        fortschritt.label.setPixmap(pixmap)
        fortschritt.label.setScaledContents(True)
        fortschritt.label.resize(pixmap.width(), pixmap.height())
        """
        progress.progressBar.setValue(0)
        if progress.exec() == widgets.QDialog.Rejected:  # Abbrechen
            print("Gecancelt gedrueckt")  # hier muss dann der process gestoppt werden.
            cfg.kill_flag_threads = True  # alle Treads killen
            cfg.loading_bar = 0
            timer.stop()  # process ist damit abgeschalten.
            print("Try to join")
            for ID in IDs:
                if ID.is_alive():
                    ID.join()
                    print(ID, "der leuft ja noch!")
            print("Treads sind alle tot")
            cfg.kill_flag_threads = False
            cv2.destroyAllWindows()
        else:
            if (mW.checkBoxAlgorithmusSuchen.isChecked()):  # nur eine neue Bad Pixelmap speichern, wenn auch Fehler gesucht wurden
                save.BPM_save(BAD_total * 150, mW.comboBoxBPMSensor.currentText())  # BPM Speichern
            cv2.destroyAllWindows()
            update_BPM()
            update_text_BPM()  # Text auf dem erstem Tab aktualisieren
            show_BPM()
        print("startClicked")  # Debug

    def msg_button_click(): 
        print("message")
        pass

    def open_msg_box(icon, text, informativeText, windowTitle, standardButtons, pFunction):
        msg_box.setIcon(icon)  # msgBox.setIcon(widgets.QMessageBox.Information)
        msg_box.setText(text)  # msgBox.setText("Der eingegebene Pfad für den Speicherort ist nicht gültig")
        msg_box.setInformativeText(informativeText)  # msgBox.setInformativeText("Der Pfad: \"" + mW.lineEditSpeicherort.text() + "\" ist kein gültiger Pfad. Bitte ändern Sie den eingegebenen Pfad.")
        msg_box.setWindowTitle(windowTitle)          # msgBox.setWindowTitle("Kein gültiger Pfad")
        msg_box.setStandardButtons(standardButtons)  # msgBox.setStandardButtons(widgets.QMessageBox.Ok) # | widgets.QMessageBox.Cancel)
        msg_box.buttonClicked.connect(pFunction)  # msgBox.buttonClicked.connect(msgButtonClick)
        returnValue = msg_box.exec()
        if returnValue == widgets.QMessageBox.Ok:
            print("OK clicked")  # Debug
        return returnValue

    def mW_pushbutton_main_back():
        global current_tab  # ohne diese Zeile kommt darunter eine Fehlermeldung
        if current_tab > 0:
            current_tab = current_tab - 1
        mW.tabWidget.setCurrentIndex(current_tab)
        if current_tab < 3:
            mW.pushButtonMainForward.setText("Weiter")
        if current_tab <= 0:
            mW.pushButtonMainBack.setVisible(False)

    def mW_pushbutton_main_forward():
        global current_tab  # ohne diese Zeile kommt darunter eine Fehlermeldung
        if current_tab == 0:
            global flag_BPM_prev
            cv2.destroyAllWindows()
            flag_BPM_prev = False
            mW.pushButtonBPMVorschau.setText("BPM-Vorschau an")
        if current_tab >= 3:
            start_clicked()
            return
        if current_tab < 3:
            current_tab = current_tab + 1
        mW.tabWidget.setCurrentIndex(current_tab)
        if current_tab >= 3:
            mW.pushButtonMainForward.setText("start")
        if current_tab > 0:
            mW.pushButtonMainBack.setVisible(True)

        save.write_json(DATA)  # Schreiben am Ende

    def mW_tab_widget():
        global current_tab
        current_tab = mW.tabWidget.currentIndex()
        if current_tab != 0:  # BPM Vorschau deaktivieren
            global flag_BPM_prev
            cv2.destroyAllWindows()
            flag_BPM_prev = False
            mW.pushButtonBPMVorschau.setText("BPM-Vorschau an")

        if current_tab >= 3:
            mW.pushButtonMainForward.setText("start")
        if current_tab > 0:
            mW.pushButtonMainBack.setVisible(True)
        if current_tab < 3:
            mW.pushButtonMainForward.setText("Weiter")
        if current_tab <= 0:
            mW.pushButtonMainBack.setVisible(False)

    def ui_setup():  # alles was beim Laden passieren soll
        # Aktuelle Tab speichern
        global current_tab
        global DATA
        global sensor_list
        current_tab = mW.tabWidget.currentIndex()
        DATA = save.read_json()  # Lesen zu Beginn #-1 Abfangen?!
        # Tab-Widget
        if current_tab >= 3:
            mW.pushButtonMainForward.setText("start")
        if current_tab > 0:
            mW.pushButtonMainBack.setVisible(True)
        if current_tab < 3:
            mW.pushButtonMainForward.setText("Weiter")
        if current_tab <= 0:
            mW.pushButtonMainBack.setVisible(False)
        # Tab: Sensor/BPM
        sensor_list = save.which_sensors(DATA)[1]
        mW.comboBoxBPMSensor.clear()
        mW.comboBoxBPMSensor.addItems(sensor_list) 
        mW.comboBoxBPMSensor.setCurrentText(DATA["last_GenutzterSensor"])
        update_BPM()      # Comboboxes aktualisieren
        update_text_BPM()  # Text auf dem erstem Tab aktualisieren
        show_BPM()
        # Tab: Algorithmus - GroupBox Pixelfehler finden enablen
        if mW.checkBoxAlgorithmusSuchen.isChecked():
            mW.groupBoxSuchen.setEnabled(True)
        else:
            mW.groupBoxSuchen.setEnabled(False)

        # Tab: Algorithmus - GroupBox Pixelfehler korrigieren enablen
        if mW.checkBoxAlgorithmusKorrigieren.isChecked():
            mW.groupBoxKorrigieren.setEnabled(True)
        else:
            mW.groupBoxKorrigieren.setEnabled(False)

        mW.checkBoxBilddaten.setVisible(False)  # noch nicht implementiert
        # Werte Suchen Laden
        if DATA["Sensors"] == []:
            print("Keine Sensoren")  # debug
        else:
            eS.horizontalSliderSchwellwertHot.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Schwellwert_oben"]
            )
            eS.horizontalSliderSchwellwertDead.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Schwellwert_unten"]
            )
            eS.horizontalSliderMovingFensterbreite.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Fensterbreite_advWindow"]
            )
            eS.horizontalSliderMovingSchwellwert.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Faktor_advWindow"]
            )
            eS.horizontalSliderDynamicSchwellwert.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Faktor_Dynamik"]
            )

        # Einstellungen Suchen
        eS_horizontal_slider_thresh_hot()
        eS_horizontal_slider_thresh_dead()
        eS_horizontal_slider_moving_window_width()
        eS_horizontal_slider_moving_thresh()
        eS_horizontal_slider_dynamic_thresh()
        eS.line_3.setVisible(False)  # nicht implementiert
        eS.pushButtonVorschau.setVisible(False)  # nicht implementiert
        # Einstellungen Korrigieren
        eK_horizontal_slider_neighbor_window_width()
        eK_horizontal_slider_gradient_window_width()
        eK.line_3.setVisible(False)  # nicht implementiert
        eK.pushButtonVorschau.setVisible(False)  # nicht implementiert
        # Werte Korrekur Laden
        if DATA["Sensors"] == []:
            print("Keine Sensoren")  # debug
        else:
            eK.horizontalSliderNachbarFensterbreite.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Fenster_Nachbar"]
            )
            eK.horizontalSliderGradientFensterbreite.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Fenster_Gradient"]
            )
        # Fortschritt Fenster
        progress.buttonBox.button(widgets.QDialogButtonBox.Ok).setEnabled(False)  # Okay Button disable

    def update_BPM():
        mW.comboBoxBPMBPM.clear()
        bpmList = save.which_BPM(mW.comboBoxBPMSensor.currentText())
        mW.comboBoxBPMBPM.addItems(bpmList)
        if len(bpmList) <= 0:
            set_enabled_BPM(False)
        else:
            set_enabled_BPM(True)

    def update_text_BPM():
        mW.textEditBPM.clear()
        if platform.system() == "Windows":
            mW.textEditBPM.setFontPointSize(11)
        else:
            mW.textEditBPM.setFontPointSize(15)
        if mW.comboBoxBPMSensor.currentText() == "":  # wenn es keinen Sensor gibt

            print("Es gibt kein Sensor!")
            set_enabled_BPM(False)
            mW.textEditBPM.insertPlainText("Herzlich willkomen zum Bad-Pixel-Programm.\n\n")
            mW.textEditBPM.insertPlainText("Bitte wechseln zu den Reiter \"Speicherort\" und wählen Sie ein Zielverzeichnis aus.\n\n\n")
            mW.textEditBPM.insertPlainText("Sie haben noch keinen Sensor erstellt.\n")
            mW.textEditBPM.insertPlainText('Drücken Sie hierfür bitte den Knopf "Neuer Sensor erstellen ...".\n')
            mW.textEditBPM.insertPlainText('Außerdem können Sie üben den Knopf "Sensoren laden ..." bereits erstellte Sensoren importieren.\n\n')

            set_enabled_sensor(False)
            return
        set_enabled_sensor(True)
        lokalBPM = save.BPM_read(mW.comboBoxBPMSensor.currentText())
        aufloesung = np.shape(lokalBPM)

        if aufloesung == ():  # noch keine BPM vorhanden
            if platform.system() == "Windows":
                mW.textEditBPM.insertPlainText(
                    "Name des Sensors:\t\t\t"
                    + DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["Sensor_Name"]
                    + "\n"
                )
                mW.textEditBPM.insertPlainText("\nEs wurde noch keine Pixelfehler-Liste (Bad-Pixel-Map) angelegt.")
                mW.textEditBPM.insertPlainText("\n_________________________________________________\n")
                mW.textEditBPM.insertPlainText("   Hinweis: \n\n")
                mW.textEditBPM.insertPlainText("\tPro Detektor muss nur einmal eine BPM erstellt werden.\n")
                mW.textEditBPM.insertPlainText("_________________________________________________\n")
                mW.textEditBPM.insertPlainText("\n\nBitte wechseln zu den Reiter \"Algorithmus\" und klicken Sie auf \"Neue Pixelfehler suchen.\"\n\n")
                mW.textEditBPM.insertPlainText("Wählen Sie anschließend mindestens eine Auswahlmöglichkeit aus.\n")
                mW.textEditBPM.insertPlainText("Unter den Reiter \"weitere Einstellungen ...\" können Sie die Schwellwerte anpassen.\n")
                mW.textEditBPM.insertPlainText("\nFalls Sie noch keine Bilder importiert haben, können Sie unter dem Reiter \"Bilddaten\" auf \"Durchsuchen ...\" Ihren Bilderordner anwählen.\n")
                mW.textEditBPM.insertPlainText("Anschließend können Sie unter \"Bilder importieren\" die Bilder reinladen.\n")

             
            else:
                mW.textEditBPM.insertPlainText("Name des Sensors:\t\t" + DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["Sensor_Name"] + "\n")
                mW.textEditBPM.insertPlainText("\nEs wurde noch keine Pixelfehler-Liste (Bad-Pixel-Map) angelegt.")
                mW.textEditBPM.insertPlainText("\n_________________________________________________\n")
                mW.textEditBPM.insertPlainText("   Hinweis: \n\n")
                mW.textEditBPM.insertPlainText("\tPro Detektor muss nur einmal eine BPM erstellt werden.\n")
                mW.textEditBPM.insertPlainText("_________________________________________________\n")
                mW.textEditBPM.insertPlainText("\n\nBitte wechseln zu den Reiter \"Algorithmus\" und klicken Sie auf \"Neue Pixelfehler suchen.\"\n\n")
                mW.textEditBPM.insertPlainText("Wählen Sie anschließend mindestens eine Auswahlmöglichkeit aus.\n")
                mW.textEditBPM.insertPlainText("Unter den Reiter \"weitere Einstellungen ...\" können Sie die Schwellwerte anpassen.\n")
                mW.textEditBPM.insertPlainText("\nFalls Sie noch keine Bilder importiert haben, können Sie unter dem Reiter \"Bilddaten\" auf \"Durchsuchen ...\" Ihren Bilderordner anwählen.\n")
                mW.textEditBPM.insertPlainText("Anschließend können Sie unter \"Bilder importieren\" die Bilder reinladen.\n")

        else:
            zeilen, spalten = aufloesung
            geleseneBilder = DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["Anz_Bilder"]

            anzahlPixelfehler = save.get_num_err_BPM(mW.comboBoxBPMBPM.currentText())
            mW.textEditBPM.insertPlainText(
                "Name des Sensors:\t\t"
                + DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["Sensor_Name"]
                + "\n"
            )
            mW.textEditBPM.insertPlainText("Sensor Auflösung:\t\t" + str(zeilen) + " x " + str(spalten) + "\n")
            mW.textEditBPM.insertPlainText(
                "Sensor Erstelldatum:\t\t"
                + str(DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["Erstell_Datum"])
                + "\n"
            )
            mW.textEditBPM.insertPlainText("Gelesene Bilder des Sensors:\t" + str(geleseneBilder) + "\n")
            mW.textEditBPM.insertPlainText("Anzahl Pixelfehler:\t\t" + str(anzahlPixelfehler) + "\n")
            mW.textEditBPM.insertPlainText(
                "Anteil Pixelfehler:\t\t"
                + str(round(anzahlPixelfehler / (spalten * zeilen) * 100, 2))
                + " % \n"
            )
            mW.textEditBPM.insertPlainText(
                "Letzte Änderung:\t\t"
                + str(save.get_mod_time_BPM(mW.comboBoxBPMBPM.currentText()))
                + "\n"
            )

    def show_BPM():
        global flag_BPM_prev
        if flag_BPM_prev == True:
            cv2.destroyAllWindows()
            if (mW.comboBoxBPMBPM.count() != 0):  # wenn's eine BPM gibt diese auch anzeigen
                akutelleBPM = save.BPM_read_selected(mW.comboBoxBPMBPM.currentText())
                akutelleBPM = akutelleBPM.astype(np.uint8)  # weil es sonst ein 16 Bit Bild ist
                textWindow = "Bad-Pixel-Map von " + mW.comboBoxBPMBPM.currentText()
                cv2.imshow(textWindow, akutelleBPM)
            else:  # Wenns noch keine gibt.
                print("keine BPM")
                open_msg_box(
                    icon=widgets.QMessageBox.Information,
                    text="Es gibt noch keine Bad-Pixel-Map (BPM) für diesen Sensor",
                    informativeText="Sie müssen erst Pixelfehler suchen, damit eine BPM erstellt wird.",
                    windowTitle="Keine BPM vorhanden!",
                    standardButtons=widgets.QMessageBox.Ok,
                    pFunction=msg_button_click,
                )

    def set_enabled_BPM(flag):
        mW.labelBPMchoose.setEnabled(flag)
        mW.comboBoxBPMBPM.setEnabled(flag)

    def set_enabled_sensor(flag):
        mW.labelSensorChoose.setEnabled(flag)
        mW.comboBoxBPMSensor.setEnabled(flag)

    def open_FFK_window():
        global num_pictures_bright
        global num_pictures_dark
        if fF.exec() == widgets.QDialog.Accepted:
            cv2.destroyAllWindows()
            if fF.radioButtonNeueBilder.isChecked():  # wenn neue Bilder gesucht werden
                if num_pictures_bright == 0:
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Bitte importieren Sie Hellbilder",
                        informativeText="",
                        windowTitle="Sie haben keine Hellbilder importiert",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    open_FFK_window()
                    return False
                if num_pictures_dark == 0:
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Bitte importieren Sie Dunkelbilder",
                        informativeText="",
                        windowTitle="Sie haben keine Dunkelbilder importiert",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    open_FFK_window()
                    return False
                for aktuelleZeile in range(fF.tableWidgetHell.rowCount()):
                    # ...ob die Auflösung der Bilder identisch ist, Rohbilder können auch mit verschieden Auflösungen exportiert werden.
                    if (
                        fF.tableWidgetHell.item(0, 1).text()
                        != fF.tableWidgetHell.item(aktuelleZeile, 1).text()
                    ):
                        open_msg_box(
                            icon=widgets.QMessageBox.Information,
                            text="Die Auflösung der importierten Bilder ist unterschiedlich",
                            informativeText="Bitte entfernen Sie die falschen Bilder bei den Hellbildern von der Flatfield-Korrektur.",
                            windowTitle="Falsche Auflösung",
                            standardButtons=widgets.QMessageBox.Ok,
                            pFunction=msg_button_click,
                        )
                        open_FFK_window()
                        return False
                    # ...ob die Farbtiefe der Bilder identisch ist, Rohbilder können auch mit verschieden Farbtiefen exportiert werden.
                    if (
                        fF.tableWidgetHell.item(0, 3).text()
                        != fF.tableWidgetHell.item(aktuelleZeile, 3).text()
                    ):
                        open_msg_box(
                            icon=widgets.QMessageBox.Information,
                            text="Die Farbtiefe der importierten Bilder ist unterschiedlich",
                            informativeText="Bitte entfernen Sie die falschen Bilder bei den Hellbildern von der Flatfield-Korrektur.",
                            windowTitle="Falsche Farbtiefe",
                            standardButtons=widgets.QMessageBox.Ok,
                            pFunction=msg_button_click,
                        )
                        open_FFK_window()
                        return False
                    # ...ob die Auflösung der Bilder und der BPM identisch sind, Rohbilder können trotzdem exportiert werden.
                    """
                    if fF.tableWidgetHell.item(aktuelleZeile, 1).text() != "": # todo: Überprüfen ob die Auflösung der Bilder und der BPM identisch sind, Format: "rows x cols", Beachte: wenn es noch keine gibt, muss es übersprungen werden
                        open_msg_box(icon=widgets.QMessageBox.Information, text="Auslösung der Bad-Pixel-Map und der importierten Bilder sind unterschiedlich",informativeText="Die Auflösung des Bildes aus der " + str(aktuelleZeile) + " Zeile ist nicht mit der Auflösung der Bad-Pixel identisch. Bitte die falschen Bilder bei den Hellbildern von der Flatfield-Korrektur löschen oder einen anderen Sensor auswählen.",windowTitle="Falsche Auflösung BPM oder Bilder",standardButtons=widgets.QMessageBox.Ok,pFunction=msgButtonClick)
                        openFFKWindow()
                        return False  
                    """
                    if (
                        fF.tableWidgetHell.item(aktuelleZeile, 1).text()
                        != fF.tableWidgetDunkel.item(0, 1).text()
                    ):
                        open_msg_box(
                            icon=widgets.QMessageBox.Information,
                            text="Die Auflöung der importierten Bilder ist unterschiedlich",
                            informativeText="Bitte entfernen Sie die falschen Bilder aus der Flatfield-Korrektur.",
                            windowTitle="Falsche Auslösung",
                            standardButtons=widgets.QMessageBox.Ok,
                            pFunction=msg_button_click,
                        )
                        open_FFK_window()
                        return False
                    if (
                        fF.tableWidgetHell.item(aktuelleZeile, 3).text()
                        != fF.tableWidgetDunkel.item(0, 3).text()
                    ):
                        open_msg_box(
                            icon=widgets.QMessageBox.Information,
                            text="Die Farbtiefe der importierten Bilder ist unterschiedlich",
                            informativeText="Bitte entfernen Sie die falschen Bilder aus der Flatfield-Korrektur.",
                            windowTitle="Falsche Farbtiefe",
                            standardButtons=widgets.QMessageBox.Ok,
                            pFunction=msg_button_click,
                        )
                        open_FFK_window()
                        return False

                for aktuelleZeile in range(fF.tableWidgetDunkel.rowCount()):
                    # ...ob die Auflösung der Bilder identisch ist, Rohbilder können auch mit verschieden Auflösungen exportiert werden.
                    if (
                        fF.tableWidgetDunkel.item(0, 1).text()
                        != fF.tableWidgetDunkel.item(aktuelleZeile, 1).text()
                    ):
                        open_msg_box(
                            icon=widgets.QMessageBox.Information,
                            text="Die Auflösung der importierten Bilder ist unterschiedlich",
                            informativeText="Bitte entfernen Sie die falschen Bilder bei den Dunkelbildern von der Flatfield-Korrektur.",
                            windowTitle="Falsche Auflösung",
                            standardButtons=widgets.QMessageBox.Ok,
                            pFunction=msg_button_click,
                        )
                        open_FFK_window()
                        return False
                    # ...ob die Farbtiefe der Bilder identisch ist, Rohbilder können auch mit verschieden Farbtiefen exportiert werden.
                    if (
                        fF.tableWidgetDunkel.item(0, 3).text()
                        != fF.tableWidgetDunkel.item(aktuelleZeile, 3).text()
                    ):
                        open_msg_box(
                            icon=widgets.QMessageBox.Information,
                            text="Die Farbtiefe der importierten Bilder ist unterschiedlich",
                            informativeText="Bitte entfernen Sie die falschen Bilder bei den Dunkelbildern von der Flatfield-Korrektur.",
                            windowTitle="Falsche Farbtiefe",
                            standardButtons=widgets.QMessageBox.Ok,
                            pFunction=msg_button_click,
                        )
                        open_FFK_window()
                        return False
                    # ...ob die Auflösung der Bilder und der BPM identisch sind, Rohbilder können trotzdem exportiert werden.
                    """
                    if fF.tableWidgetDunkel.item(aktuelleZeile, 1).text() != "": # todo: Überprüfen ob die Auflösung der Bilder und der BPM identisch sind, Format: "rows x cols", Beachte: wenn es noch keine gibt, muss es übersprungen werden
                        open_msg_box(icon=widgets.QMessageBox.Information, text="Auslösung der Bad-Pixel-Map und der importierten Bilder sind unterschiedlich",informativeText="Die Auflösung des Bildes aus der " + str(aktuelleZeile) + " Zeile ist nicht mit der Auflösung der Bad-Pixel identisch. Bitte die falschen Bilder bei den Dunkelbildern von der Flatfield-Korrektur löschen oder einen anderen Sensor auswählen.",windowTitle="Falsche Auflösung BPM oder Bilder",standardButtons=widgets.QMessageBox.Ok,pFunction=msgButtonClick)
                        openFFKWindow()
                        return False  
                    """
        else:  # wenn Abbrechen geklickt wird
            cv2.destroyAllWindows()
            mW.checkBoxAlgorithmusFFK.setChecked(False)
            # alle Tabellen sollen gelöscht werden
            fF.tableWidgetHell.setRowCount(0)
            num_pictures_bright = 0
            fF.tableWidgetDunkel.setRowCount(0)
            num_pictures_dark = 0

    def update_FFK():
        if fF.radioButtonNeueBilder.isChecked():  # wenn neue Bilder gewählt ist
            fF.groupBox.setEnabled(True)
            fF.pushButtonGespeicherteBilder.setEnabled(False)
        else:  # wenn alte Bilder geladen werden
            fF.groupBox.setEnabled(False)
            fF.pushButtonGespeicherteBilder.setEnabled(True)

    ############ Ende Allgemeine Funktionen ########################################################################################
    #### ######## Funktionen von dem ab Sensor / BPM ########################################################################################

    def mW_combobox_BPM_sensor():  # wird aufgerufen, wenn ein neues Element ausgewählt wird
        DATA["last_GenutzterSensor"] = mW.comboBoxBPMSensor.currentText()
        update_BPM()
        update_text_BPM()
        show_BPM()

    def mW_combobox_BPM_BPM():
        update_text_BPM()
        show_BPM()

    def mW_pushbutton_BPM_new_sensor():
        # Ordner auswählen: getExistingDirectory(), Datei auswählen: getOpenFileName(), Dateien auswählen: filename = widgets.QFileDialog.getOpenFileNames() [0]

        if nB.exec() == widgets.QDialog.Accepted:
            global sensor_list
            tempSensor = [tempSensor.lower() for tempSensor in sensor_list]
            if nB.lineEditNeueBPM.text().lower() in tempSensor:
                print("So einen Sensor gibt es schon")  # debug
                open_msg_box(
                    icon=widgets.QMessageBox.Information,
                    text="Es gibt bereits einen Sensor mit dem selben Namen. Bitte wählen Sie einen anderen Namen für den neuen Sensor.",
                    informativeText="",
                    windowTitle="Achtung diesen Sensor gibt es schon!",
                    standardButtons=widgets.QMessageBox.Ok,
                    pFunction=msg_button_click,
                )
                return

            save.sensor_create(nB.lineEditNeueBPM.text(), DATA)
            sensor_list = save.which_sensors(DATA)[1]

            mW.comboBoxBPMSensor.addItem(sensor_list[-1])  # -1 letzes Elemt
            mW.comboBoxBPMSensor.setCurrentIndex(len(sensor_list) - 1)  # -1 da Informatiker ab 0 zählen
            DATA["last_GenutzterSensor"] = mW.comboBoxBPMSensor.currentText()
            update_BPM()
            update_text_BPM()
            show_BPM()
            save.write_json(DATA)  # Schreiben am Ende
        print("NeueBPM geöffnet")  # debug

    def mW_pushbutton_BPM_load_sensor():
        dirname = widgets.QFileDialog.getExistingDirectory()
        if dirname == "":  # wenn  auf abbrechen gedrückt wird
            return
        backValue = widgets.QMessageBox.Ok  # für das untere If
        if (mW.comboBoxBPMSensor.currentText() != ""):  # wenn es keinen Sensor gibt, soll die Message box nicht angzeigt werden
            backValue = open_msg_box(
                icon=widgets.QMessageBox.Information,
                text="Wenn sie Ihre alten Sensoren weiterhin behalten wollen, müssen Sie diese erst exportieren. Ist dies der Fall, hier auf Abbrechen oder Cancel klicken. ",
                informativeText="",
                windowTitle="Achtung Ihre alten Sensoren werden überschrieben.",
                standardButtons=widgets.QMessageBox.Ok | widgets.QMessageBox.Cancel,
                pFunction=msg_button_click,
            )
        if backValue == widgets.QMessageBox.Ok:

            # Kopieren(dirname,Speichern.dir_path) #ist ein Einzeiler
            files = os.listdir(save.dir_path)
            for aktuellesFile in files:
                os.remove(os.path.join(save.dir_path, aktuellesFile))
            files = os.listdir(dirname)
            for aktuellesFile in files:
                path = os.path.join(dirname, aktuellesFile)
                shutil.copy(path, save.dir_path)
            ui_setup()
            save.write_json(DATA)  # Schreiben am Ende
        print(dirname)

    def mW_pushbutton_BPM_save_sensor():
        dirname = widgets.QFileDialog.getExistingDirectory()
        if dirname == "":  # wenn  auf abbrechen gedrückt wird
            return  # Funktion verlassen
        # hier wird der Ordner  kopiert
        aktuelleZeit = str(datetime.now())[:-7].replace(":", "-")  # aktuelle Zeit speichern
        destination = shutil.copytree(save.dir_path, os.path.join(dirname, "Bad-Pixel-Map " + aktuelleZeit))  # Weil der Zielordner nicht existieren darf
        open_msg_box(
            icon=widgets.QMessageBox.Information,
            text="Ihre Daten wurden erfolgreich gespeichert.",
            informativeText="Die Daten wurden unter " + destination + " gespeichert.",
            windowTitle="Speichern erfolgreich",
            standardButtons=widgets.QMessageBox.Ok,
            pFunction=msg_button_click,
        )

    def mW_pushbutton_BPM_preview():
        global flag_BPM_prev
        if flag_BPM_prev == False:
            mW.pushButtonBPMVorschau.setText("BPM-Vorschau aus")
            flag_BPM_prev = True
            show_BPM()
        else:
            mW.pushButtonBPMVorschau.setText("BPM-Vorschau an")
            cv2.destroyAllWindows()
            flag_BPM_prev = False

    def mW_pushbutton_BPM_delete_sensor():
        aktuellerIndex = mW.comboBoxBPMSensor.currentIndex()
        currentText = mW.comboBoxBPMSensor.currentText()
        if currentText == "":  # es gibt kein Sensor
            open_msg_box(
                icon=widgets.QMessageBox.Information,
                text="Es gibt keinen Sensor der gelöscht werden kann.",
                informativeText="",
                windowTitle="Es gibt keine Sensoren",
                standardButtons=widgets.QMessageBox.Ok,
                pFunction=msg_button_click,
            )
        else:
            backValue = open_msg_box(
                icon=widgets.QMessageBox.Information,
                text='Möchten Sie den Sensor und alle dessen BPM löschen, dann drücken Sie bitte "OK"',
                informativeText="",
                windowTitle="Achtung der Sensor und alle dessen BPM werden gelöscht",
                standardButtons=widgets.QMessageBox.Ok | widgets.QMessageBox.Cancel,
                pFunction=msg_button_click,
            )
            if backValue == widgets.QMessageBox.Ok:
                del sensor_list[aktuellerIndex]
                mW.comboBoxBPMSensor.removeItem(aktuellerIndex)
                save.sensor_delete(currentText, DATA)
                save.delete_all_BPM(currentText)
                update_BPM()
                update_text_BPM()
                show_BPM()
                save.write_json(DATA)  # Schreiben am Ende

    def mW_pushbutton_BPM_delete_BPM():
        if mW.comboBoxBPMBPM.currentText() == "":  # wenn es keine BPM gibt
            open_msg_box(
                icon=widgets.QMessageBox.Information,
                text="Sie müssen hierfür erst mit einem Sensor eine BPM erzeugen.",
                informativeText="",
                windowTitle="Es gibt keine BPM zum Löschen",
                standardButtons=widgets.QMessageBox.Ok,
                pFunction=msg_button_click,
            )
            return
        save.delete_BPM(mW.comboBoxBPMBPM.currentText())
        update_BPM()
        update_text_BPM()
        show_BPM()
        save.write_json(DATA)  # Schreiben am Ende

    ### Tab Bilddaten
    def mW_pushbutton_find_dir():  # Ordner importieren
        if DATA["Import_Pfad"] == " ":
            dirname = widgets.QFileDialog.getExistingDirectory(
                directory=core.QStandardPaths.writableLocation(core.QStandardPaths.DocumentsLocation)
            )
        else:
            dirname = widgets.QFileDialog.getExistingDirectory(
                directory=DATA["Import_Pfad"]
            )
        if dirname != "":  # wenn nicht auf abbrechen gedrückt wird
            mW.lineEditBilddatenDurchsuchen.setText(dirname)
            print(os.listdir(dirname))
        else:
            print("Abgebrochen")
        # Sind die Daten valide? Umlaute usw. nur für Windows erforderlich
        if platform.system() == "Windows":
            tempPath = dirname.lower()
            if tempPath.find("ä") != -1:
                open_msg_box(
                    icon=widgets.QMessageBox.Information,
                    text="Es befindet sich ein ä im Datei- oder Pfadname",
                    informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                    + dirname,
                    windowTitle="Umlaut im Datei- oder Pfadname",
                    standardButtons=widgets.QMessageBox.Ok,
                    pFunction=msg_button_click,
                )
                return

            if tempPath.find("ö") != -1:
                open_msg_box(
                    icon=widgets.QMessageBox.Information,
                    text="Es befindet sich ein ö im Datei- oder Pfadname",
                    informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                    + dirname,
                    windowTitle="Umlaut im Datei- oder Pfadname",
                    standardButtons=widgets.QMessageBox.Ok,
                    pFunction=msg_button_click,
                )
                return

            if tempPath.find("ü") != -1:
                open_msg_box(
                    icon=widgets.QMessageBox.Information,
                    text="Es befindet sich ein ü im Datei- oder Pfadname",
                    informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                    + dirname,
                    windowTitle="Umlaut im Datei- oder Pfadname",
                    standardButtons=widgets.QMessageBox.Ok,
                    pFunction=msg_button_click,
                )
                return

            if tempPath.find("ß") != -1:
                open_msg_box(
                    icon=widgets.QMessageBox.Information,
                    text="Es befindet sich ein ß im Datei- oder Pfadname",
                    informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad: ist "
                    + dirname,
                    windowTitle="Umlaut im Datei- oder Pfadname",
                    standardButtons=widgets.QMessageBox.Ok,
                    pFunction=msg_button_click,
                )
                return
        # Valide Daten check zu Ende
        print("Ordnerdialog Bilddaten geöffnet", dirname)

    def mW_pushbutton_import_dir():
        global num_pictures
        dirname = str(mW.lineEditBilddatenDurchsuchen.text())
        if os.path.isdir(dirname):  # os.path.exists(dirname): # wenn der Pfad überhaupt existiert
            if (mW.checkBoxBilddaten.isChecked()):  # Unterordner auch importieren noch nicht implementiert
                print("Unterordner werden auch importiert")
            else:  # keine Unterordner importieren
                files = os.listdir(dirname)  # bug, wenn dirname kein bekannter Pfad ist --> behoben
                print(files, type(files))

                imageFiles = []
                for aktuellesFile in files:
                    dateiEndung = (os.path.splitext(aktuellesFile)[1]).lower()  # lower für Windows
                    if (
                        dateiEndung == ".png"
                        or dateiEndung == ".jpg"
                        or dateiEndung == ".jpeg"
                        or dateiEndung == ".tif"
                        or dateiEndung == ".tiff"
                        or dateiEndung == ".his"
                    ):
                        imageFiles.append(aktuellesFile)
                        # TO DO Ü Ü Ö ß  mit or Verknüpfung 
                        # Sind die Daten valide? Umlaute usw. nur für Windows erforderlich
                        if platform.system() == "Windows":
                            tempPath = aktuellesFile.lower()
                            if tempPath.find("ä") != -1:
                                open_msg_box(
                                    icon=widgets.QMessageBox.Information,
                                    text="Es befindet sich ein ä im Datei- oder Pfadname",
                                    informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                                    + dirname
                                    + "/"
                                    + aktuellesFile,
                                    windowTitle="Umlaut im Datei- oder Pfadname",
                                    standardButtons=widgets.QMessageBox.Ok,
                                    pFunction=msg_button_click,
                                )
                                return
                            if tempPath.find("ö") != -1:
                                open_msg_box(
                                    icon=widgets.QMessageBox.Information,
                                    text="Es befindet sich ein ö im Datei- oder Pfadname",
                                    informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                                    + dirname
                                    + "/"
                                    + aktuellesFile,
                                    windowTitle="Umlaut im Datei- oder Pfadname",
                                    standardButtons=widgets.QMessageBox.Ok,
                                    pFunction=msg_button_click,
                                )
                                return
                            if tempPath.find("ü") != -1:
                                open_msg_box(
                                    icon=widgets.QMessageBox.Information,
                                    text="Es befindet sich ein ü im Datei- oder Pfadname",
                                    informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                                    + dirname
                                    + "/"
                                    + aktuellesFile,
                                    windowTitle="Umlaut im Datei- oder Pfadname",
                                    standardButtons=widgets.QMessageBox.Ok,
                                    pFunction=msg_button_click,
                                )
                                return
                            if tempPath.find("ß") != -1:
                                open_msg_box(
                                    icon=widgets.QMessageBox.Information,
                                    text="Es befindet sich ein ß im Datei- oder Pfadname",
                                    informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad: ist "
                                    + dirname
                                    + "/"
                                    + aktuellesFile,
                                    windowTitle="Umlaut im Datei- oder Pfadname",
                                    standardButtons=widgets.QMessageBox.Ok,
                                    pFunction=msg_button_click,
                                )
                                return
                        # Valide Daten check zu Ende

                if len(imageFiles) <= 0:
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Keine Bilder im aktuellen Verzeichnis",
                        informativeText='Das Verzeichnis: "'
                        + dirname
                        + '" enthält keine gültigen Bilddateien. Es sind nur Bilder im PNG, JPG, TIF und HIS Format kompatibel. Bitte ändern Sie den eingegebenen Pfad.',
                        windowTitle="Keine Bilder im Verzeichnis",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                num_pictures = num_pictures + len(imageFiles)
                mW.tableWidgetBilddaten.setRowCount(num_pictures)  # Soviele Zeilen in der Tabelle aktivieren, wie es Bilder gibt.
                for index in range(len(imageFiles)):  # Alle importieren Bilder durchgehen
                    mW.tableWidgetBilddaten.setItem(
                        (index + (num_pictures - len(imageFiles))),
                        0,
                        widgets.QTableWidgetItem(imageFiles[index]),
                    )  # Den Dateinamen aller markierten Bilder in die erste Spalte schreiben
                    print(dirname + "/" + imageFiles[index])
                    (
                        rows,
                        cols,
                        anzahlHisBilder,
                        farbtiefe,
                    ) = imp.get_picture_data(os.path.join(dirname, imageFiles[index]))
                    mW.tableWidgetBilddaten.setItem(
                        (index + (num_pictures - len(imageFiles))),
                        1,
                        widgets.QTableWidgetItem(str(rows) + " x " + str(cols)),
                    )  # Die Auflösung aller markierten Bilder in die erste Spalte schreiben
                    mW.tableWidgetBilddaten.setItem(
                        (index + (num_pictures - len(imageFiles))),
                        2,
                        widgets.QTableWidgetItem(str(int(anzahlHisBilder))),
                    )
                    if type(farbtiefe) == str:
                        mW.tableWidgetBilddaten.setItem(
                            (index + (num_pictures - len(imageFiles))),
                            3,
                            widgets.QTableWidgetItem(farbtiefe),
                        )
                    else:
                        mW.tableWidgetBilddaten.setItem(
                            (index + (num_pictures - len(imageFiles))),
                            3,
                            widgets.QTableWidgetItem(farbtiefe.name),
                        )
                    mW.tableWidgetBilddaten.setItem(
                        (index + (num_pictures - len(imageFiles))),
                        4,
                        widgets.QTableWidgetItem(str(os.path.join(dirname, imageFiles[index]))),
                    )  # Die Pfade aller Bilder in die dritten Spalte schreiben
                    # zentrieren
                    mW.tableWidgetBilddaten.item((index + (num_pictures - len(imageFiles))), 1).setTextAlignment(core.Qt.AlignCenter)
                    mW.tableWidgetBilddaten.item((index + (num_pictures - len(imageFiles))), 2).setTextAlignment(core.Qt.AlignCenter)
                    mW.tableWidgetBilddaten.item((index + (num_pictures - len(imageFiles))), 3).setTextAlignment(core.Qt.AlignCenter)
                # else:
                # print("Abgebbrochen")
                print("Keine Unterordner importieren")
                # imp.import_ui_function(mW.tableWidgetBilddaten.item(0,4).text(),True)
                # exp.exportPictures(mW.lineEditSpeicherort.text(), mW.tableWidgetBilddaten.item(0,0).text(),GOOD)
            # Pfad Speichern
            DATA["Import_Pfad"] = dirname
        else:
            open_msg_box(
                icon=widgets.QMessageBox.Information,
                text="Der eingegebene Pfad ist nicht gültig",
                informativeText='Der Pfad: "'
                + dirname
                + '" ist kein gültiger Ordnerpfad. Bitte ändern Sie den eingegebenen Pfad.',
                windowTitle="Kein gültiger Pfad",
                standardButtons=widgets.QMessageBox.Ok,
                pFunction=msg_button_click,
            )

    def mW_pushbutton_import_image_data():  # Bilddateien importieren
        global num_pictures  # globale Variable Anzahl der Bilder bekannt machen
        # file Dialog, kompatible Dateien: *.his *.png *.jpg *.jpeg *.tif *.tiff,
        # Alle Pfäde der Dateien werden in filename gespeichert
        # filename = widgets.QFileDialog.getOpenFileNames(directory = core.QStandardPaths.writableLocation(core.QStandardPaths.DocumentsLocation), filter = "Bild-Dateien (*.his *.png *.jpg *.jpeg *.tif *.tiff)") [0]
        filename = widgets.QFileDialog.getOpenFileNames(filter="Bild-Dateien (*.his *.png *.jpg *.jpeg *.tif *.tiff)")[0]  # directory wird vom OS gewählt
        # print(filename) # debug

        # Sind die Daten valide? Umlaute usw. nur für Windows erforderlich
        if platform.system() == "Windows":
            for file in filename:
                tempPath = file.lower()
                if tempPath.find("ä") != -1:
                    # print("Es befindet sich ein ä im Datei- oder Pfadname") # debug
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Es befindet sich ein ä im Datei- oder Pfadname",
                        informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                        + file,
                        windowTitle="Umlaut im Datei- oder Pfadname",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    return
                if tempPath.find("ö") != -1:
                    # print("Es befindet sich ein ö im Datei- oder Pfadname") # debug
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Es befindet sich ein ö im Datei- oder Pfadname",
                        informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                        + file,
                        windowTitle="Umlaut im Datei- oder Pfadname",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    return
                if tempPath.find("ü") != -1:
                    # print("Es befindet sich ein ü im Datei- oder Pfadname") # debug
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Es befindet sich ein ü im Datei- oder Pfadname",
                        informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                        + file,
                        windowTitle="Umlaut im Datei- oder Pfadname",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    return
                if tempPath.find("ß") != -1:
                    # print("Es befindet sich ein ß im Datei- oder Pfadname") # debug
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Es befindet sich ein ß im Datei- oder Pfadname",
                        informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad: ist "
                        + file,
                        windowTitle="Umlaut im Datei- oder Pfadname",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    return
        # Valide Daten check zu Ende

        num_pictures = num_pictures + len(filename)  # Anzahl der Bilder aktualisieren
        mW.tableWidgetBilddaten.setRowCount(num_pictures)  # Soviele Zeilen in der Tabelle aktivieren, wie es Bilder gibt.
        for index in range(len(filename)):  # Alle importieren Bilder durchgehen
            mW.tableWidgetBilddaten.setItem((index + (num_pictures - len(filename))), 0,
                widgets.QTableWidgetItem(os.path.basename(filename[index])),)  # Den Dateinamen aller markierten Bilder in die erste Spalte schreiben
            (
                rows,
                cols,
                anzahlHisBilder,
                farbtiefe,
            ) = imp.get_picture_data(filename[index])
            mW.tableWidgetBilddaten.setItem((index + (num_pictures - len(filename))), 1,
                widgets.QTableWidgetItem(str(rows) + " x " + str(cols)),)  # Die Auflösung aller markierten Bilder in die erste Spalte schreiben
            mW.tableWidgetBilddaten.setItem((index + (num_pictures - len(filename))), 2,
                widgets.QTableWidgetItem(str(int(anzahlHisBilder))),)
            if type(farbtiefe) == str:
                mW.tableWidgetBilddaten.setItem((index + (num_pictures - len(filename))), 3,
                    widgets.QTableWidgetItem(farbtiefe),)
            else:
                mW.tableWidgetBilddaten.setItem((index + (num_pictures - len(filename))), 3,
                    widgets.QTableWidgetItem(farbtiefe.name),)
            mW.tableWidgetBilddaten.setItem((index + (num_pictures - len(filename))), 4,
                widgets.QTableWidgetItem(str(filename[index])),)  # Die Pfade aller Bilder in die dritten Spalte schreiben
            mW.tableWidgetBilddaten.item((index + (num_pictures - len(filename))), 1).setTextAlignment(core.Qt.AlignCenter)
            mW.tableWidgetBilddaten.item((index + (num_pictures - len(filename))), 2).setTextAlignment(core.Qt.AlignCenter)
            mW.tableWidgetBilddaten.item((index + (num_pictures - len(filename))), 3).setTextAlignment(core.Qt.AlignCenter)

    def mW_pushbutton_delete_image_data():
        global num_pictures
        zeilen = mW.tableWidgetBilddaten.selectedItems()
        print(zeilen)
        zeilenLoeschen = []
        alterWert = -1
        for index in zeilen:
            if alterWert != index.row():
                zeilenLoeschen.append(index.row())
            alterWert = index.row()

        print(zeilenLoeschen)
        zeilenLoeschen.sort()
        print(zeilenLoeschen)
        zeilenLoeschen.reverse()
        print(zeilenLoeschen)
        for index in range(len(zeilenLoeschen)):
            mW.tableWidgetBilddaten.removeRow(zeilenLoeschen[index])
        num_pictures = num_pictures - len(zeilenLoeschen)
        print(num_pictures)

    def mW_pushbutton_delete_all_image_data():
        mW.tableWidgetBilddaten.setRowCount(0)
        global num_pictures
        num_pictures = 0

    ### Tab Speicherort
    def mW_pushbutton_search_dir():
        if DATA["Export_Pfad"] == " ":
            filename = widgets.QFileDialog.getExistingDirectory(
                directory=core.QStandardPaths.writableLocation(core.QStandardPaths.DocumentsLocation)
            )
        else:
            filename = widgets.QFileDialog.getExistingDirectory(directory=DATA["Export_Pfad"])
        mW.lineEditSpeicherort.setText(filename)
        DATA["Export_Pfad"] = filename

    ### Tab Algorithmus
    def mW_checkbox_find_algorithm():
        if mW.checkBoxAlgorithmusSuchen.isChecked():
            mW.groupBoxSuchen.setEnabled(True)

        else:
            mW.groupBoxSuchen.setEnabled(False)

    def mW_checkbox_algorithm_correction():
        if mW.checkBoxAlgorithmusKorrigieren.isChecked():
            mW.groupBoxKorrigieren.setEnabled(True)
        else:
            mW.groupBoxKorrigieren.setEnabled(False)

    def mW_pushbutton_find_algorithm_settings():
        if DATA["Sensors"] == []:  # wenn es keine Sensoren gibt
            open_msg_box(
                icon=widgets.QMessageBox.Information,
                text="Sie müssen hierfür zuerst einen Sensor erstellen",
                informativeText="Für die Einstellungen muss zuerst ein Sensor erstellt werden.",
                windowTitle="Sie müssen hierfür zuerst einen Sensor erstellen",
                standardButtons=widgets.QMessageBox.Ok,
                pFunction=msg_button_click,
            )
            mW.tabWidget.setCurrentIndex(0)
            return
        # Laden
        eS.horizontalSliderSchwellwertHot.setValue(
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Schwellwert_oben"]
        )
        eS.horizontalSliderSchwellwertDead.setValue(
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Schwellwert_unten"]
        )
        eS.horizontalSliderMovingFensterbreite.setValue(
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Fensterbreite_advWindow"]
        )
        eS.horizontalSliderMovingSchwellwert.setValue(
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Faktor_advWindow"]
        )
        eS.horizontalSliderDynamicSchwellwert.setValue(
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Faktor_Dynamik"]
        )
        if eS.exec() == widgets.QDialog.Accepted:
            # Speichern
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Schwellwert_oben"] = eS.horizontalSliderSchwellwertHot.value()
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Schwellwert_unten"] = eS.horizontalSliderSchwellwertDead.value()
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Fensterbreite_advWindow"] = eS.horizontalSliderMovingFensterbreite.value()
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Faktor_advWindow"] = eS.horizontalSliderMovingSchwellwert.value()
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Faktor_Dynamik"] = eS.horizontalSliderDynamicSchwellwert.value()
        else:  # Die alten Werte wiederherstellen, da auf Abbrechnen geklickt wurde
            eS.horizontalSliderSchwellwertHot.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Schwellwert_oben"])
            eS.horizontalSliderSchwellwertDead.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Schwellwert_unten"])
            eS.horizontalSliderMovingFensterbreite.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Fensterbreite_advWindow"])
            eS.horizontalSliderMovingSchwellwert.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Faktor_advWindow"])
            eS.horizontalSliderDynamicSchwellwert.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Faktor_Dynamik"])

    def mW_pushbutton_correct_algorithm_settings():
        if DATA["Sensors"] == []:  # wenn es keine Sensoren gibt
            open_msg_box(
                icon=widgets.QMessageBox.Information,
                text="Für die Einstellungen muss zuerst ein Sensor erstellt werden.",
                informativeText="",
                windowTitle="Sie müssen hierfür zuerst einen Sensor erstellen",
                standardButtons=widgets.QMessageBox.Ok,
                pFunction=msg_button_click,
            )
            mW.tabWidget.setCurrentIndex(0)
            return
        eK.horizontalSliderNachbarFensterbreite.setValue(
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Fenster_Nachbar"])
        eK.horizontalSliderGradientFensterbreite.setValue(
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Fenster_Gradient"])
        Methode = DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_korrekturmethode"]
        eK.radioButtonMedian.setChecked(Methode == cfg.Methods.NMFC.value)
        eK.radioButtonMittelwert.setChecked(Methode == cfg.Methods.NARC.value)
        eK.radioButtonReplacement.setChecked(Methode == cfg.Methods.NSRC.value)
        if eK.exec() == widgets.QDialog.Accepted:
            if eK.radioButtonMedian.isChecked():
                Methode = cfg.Methods.NMFC
            elif eK.radioButtonMittelwert.isChecked():
                Methode = cfg.Methods.NARC
            else:
                Methode = cfg.Methods.NSRC
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Fenster_Nachbar"] = eK.horizontalSliderNachbarFensterbreite.value()
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Fenster_Gradient"] = eK.horizontalSliderGradientFensterbreite.value()
            DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_korrekturmethode"] = int(Methode.value)
        else:  # Die alten Werte wiederherstellen, da auf Abbrechnen geklickt wurde
            eK.horizontalSliderNachbarFensterbreite.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Fenster_Nachbar"])
            eK.horizontalSliderGradientFensterbreite.setValue(
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_Fenster_Gradient"])
            eK.radioButtonMedian.setChecked(Methode == cfg.Methods.NMFC)
            eK.radioButtonMittelwert.setChecked(Methode == cfg.Methods.NARC)
            eK.radioButtonReplacement.setChecked(Methode == cfg.Methods.NSRC)

    def mW_checkbox_algorithm_FFK():
        if mW.checkBoxAlgorithmusFFK.isChecked():
            hellbild, dunkelbild = save.load_FFK(mW.comboBoxBPMSensor.currentText())
            if (hellbild == []) or (dunkelbild == []):  # wenn es einer von beiden Bildern nicht gibt
                alteFFKBilder = False
            else:  # wenn es alte Bilder von dem Sensor gibt
                alteFFKBilder = True
            if alteFFKBilder:
                fF.radioButtonGespeicherteBilder.setEnabled(True)
                fF.radioButtonGespeicherteBilder.setChecked(True)
                update_FFK()
            else:
                fF.radioButtonGespeicherteBilder.setEnabled(False)
                fF.radioButtonNeueBilder.setChecked(True)
                update_FFK()
            open_FFK_window()

    ### Flat-Field-Korrektur

    def fF_radiobutton_saved_pictures():
        update_FFK()

    def fF_pushbutton_bright_add():
        global num_pictures_bright  # globale Variable Anzahl der Bilder bekannt machen
        # file Dialog, kompatible Dateien: *.his *.png *.jpg *.jpeg *.tif *.tiff,
        # Alle Pfäde der Dateien werden in filename gespeichert
        filename = widgets.QFileDialog.getOpenFileNames(
            directory=DATA["Import_Pfad"],
            filter="Bild-Dateien (*.his *.png *.jpg *.jpeg *.tif *.tiff)",
        )[0]

        # Sind die Daten valide? Umlaute usw. nur für Windows erforderlich
        if platform.system() == "Windows":
            for file in filename:
                tempPath = file.lower()
                if tempPath.find("ä") != -1:
                    # print("Es befindet sich ein ä im Datei- oder Pfadname") # debug
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Es befindet sich ein ä im Datei- oder Pfadname",
                        informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                        + file,
                        windowTitle="Umlaut im Datei- oder Pfadname",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    return
                if tempPath.find("ö") != -1:
                    # print("Es befindet sich ein ö im Datei- oder Pfadname") # debug
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Es befindet sich ein ö im Datei- oder Pfadname",
                        informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                        + file,
                        windowTitle="Umlaut im Datei- oder Pfadname",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    return
                if tempPath.find("ü") != -1:
                    # print("Es befindet sich ein ü im Datei- oder Pfadname") # debug
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Es befindet sich ein ü im Datei- oder Pfadname",
                        informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                        + file,
                        windowTitle="Umlaut im Datei- oder Pfadname",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    return
                if tempPath.find("ß") != -1:
                    # print("Es befindet sich ein ß im Datei- oder Pfadname") # debug
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Es befindet sich ein ß im Datei- oder Pfadname",
                        informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad: ist "
                        + file,
                        windowTitle="Umlaut im Datei- oder Pfadname",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    return
        # Valide Datencheck zu Ende

        num_pictures_bright = num_pictures_bright + len(filename)  # Anzahl der Bilder aktualisieren
        fF.tableWidgetHell.setRowCount(num_pictures_bright)  # Soviele Zeilen in der Tabelle aktivieren, wie es Bilder gibt.

        for index in range(len(filename)):  # Alle importieren Bilder durchgehen
            fF.tableWidgetHell.setItem(
                (index + (num_pictures_bright - len(filename))),
                0,
                widgets.QTableWidgetItem(os.path.basename(filename[index])),
            )  # Den Dateinamen aller markierten Bilder in die erste Spalte schreiben
            (
                rows,
                cols,
                anzahlHisBilder,
                farbtiefe,
            ) = imp.get_picture_data(filename[index])
            fF.tableWidgetHell.setItem(
                (index + (num_pictures_bright - len(filename))),
                1,
                widgets.QTableWidgetItem(str(rows) + " x " + str(cols)),
            )  # Die Auflösung aller markierten Bilder in die erste Spalte schreiben
            fF.tableWidgetHell.setItem(
                (index + (num_pictures_bright - len(filename))),
                2,
                widgets.QTableWidgetItem(str(int(anzahlHisBilder))),
            )
            if type(farbtiefe) == str:
                fF.tableWidgetHell.setItem(
                    (index + (num_pictures_bright - len(filename))),
                    3,
                    widgets.QTableWidgetItem(farbtiefe),
                )
            else:
                fF.tableWidgetHell.setItem(
                    (index + (num_pictures_bright - len(filename))),
                    3,
                    widgets.QTableWidgetItem(farbtiefe.name),
                )
            fF.tableWidgetHell.setItem(
                (index + (num_pictures_bright - len(filename))),
                4,
                widgets.QTableWidgetItem(str(filename[index])),
            )  # Die Pfade aller Bilder in die dritten Spalte schreiben

            fF.tableWidgetHell.item(
                (index + (num_pictures_bright - len(filename))), 1
            ).setTextAlignment(core.Qt.AlignCenter)
            fF.tableWidgetHell.item(
                (index + (num_pictures_bright - len(filename))), 2
            ).setTextAlignment(core.Qt.AlignCenter)
            fF.tableWidgetHell.item(
                (index + (num_pictures_bright - len(filename))), 3
            ).setTextAlignment(core.Qt.AlignCenter)

    def fF_pushbutton_bright_delete():
        global num_pictures_bright
        zeilen = fF.tableWidgetHell.selectedItems()
        print(zeilen)
        zeilenLoeschen = []
        alterWert = -1
        for index in zeilen:  # weiß nicht was das macht
            if alterWert != index.row():
                zeilenLoeschen.append(index.row())
            alterWert = index.row()

        zeilenLoeschen.sort()
        zeilenLoeschen.reverse()

        for index in range(len(zeilenLoeschen)):
            fF.tableWidgetHell.removeRow(zeilenLoeschen[index])
        num_pictures_bright = num_pictures_bright - len(zeilenLoeschen)

    def fF_pushbutton_bright_delete_all():
        fF.tableWidgetHell.setRowCount(0)
        global num_pictures_bright
        num_pictures_bright = 0

    def fF_pushbutton_dark_add():
        global num_pictures_dark  # globale Variable Anzahl der Bilder bekannt machen
        # file Dialog, kompatible Dateien: *.his *.png *.jpg *.jpeg *.tif *.tiff,
        # Alle Pfäde der Dateien werden in filename gespeichert
        filename = widgets.QFileDialog.getOpenFileNames(
            directory=DATA["Import_Pfad"],
            filter="Bild-Dateien (*.his *.png *.jpg *.jpeg *.tif *.tiff)",
        )[0]

        # Sind die Daten valide? Umlaute usw. nur für Windows erforderlich
        if platform.system() == "Windows":
            for file in filename:
                tempPath = file.lower()
                if tempPath.find("ä") != -1:
                    # print("Es befindet sich ein ä im Datei- oder Pfadname") # debug
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Es befindet sich ein ä im Datei- oder Pfadname",
                        informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                        + file,
                        windowTitle="Umlaut im Datei- oder Pfadname",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    return
                if tempPath.find("ö") != -1:
                    # print("Es befindet sich ein ö im Datei- oder Pfadname") # debug
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Es befindet sich ein ö im Datei- oder Pfadname",
                        informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                        + file,
                        windowTitle="Umlaut im Datei- oder Pfadname",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    return
                if tempPath.find("ü") != -1:
                    # print("Es befindet sich ein ü im Datei- oder Pfadname") # debug
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Es befindet sich ein ü im Datei- oder Pfadname",
                        informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad ist: "
                        + file,
                        windowTitle="Umlaut im Datei- oder Pfadname",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    return
                if tempPath.find("ß") != -1:
                    # print("Es befindet sich ein ß im Datei- oder Pfadname") # debug
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Es befindet sich ein ß im Datei- oder Pfadname",
                        informativeText="Dieses Programm kann leider nicht mit Datei- oder Pfadnamen mit Umlauten arbeiten.  Bitte bennen Sie denjenigen Ordner oder Datei um.  Ihr importierter Pfad: ist "
                        + file,
                        windowTitle="Umlaut im Datei- oder Pfadname",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    return
        # Valide Daten check zu Ende

        num_pictures_dark = num_pictures_dark + len(filename)     # Anzahl der Bilder aktualisieren
        fF.tableWidgetDunkel.setRowCount(num_pictures_dark)        # Soviele Zeilen in der Tabelle aktivieren, wie es Bilder gibt.

        for index in range(len(filename)):  # Alle importieren Bilder durchgehen
            fF.tableWidgetDunkel.setItem(
                (index + (num_pictures_dark - len(filename))),
                0,
                widgets.QTableWidgetItem(os.path.basename(filename[index])),
            )  # Den Dateinamen aller markierten Bilder in die erste Spalte schreiben
            (
                rows,
                cols,
                anzahlHisBilder,
                farbtiefe,
            ) = imp.get_picture_data(filename[index])
            fF.tableWidgetDunkel.setItem(
                (index + (num_pictures_dark - len(filename))),
                1,
                widgets.QTableWidgetItem(str(rows) + " x " + str(cols)),
            )  # Die Auflösung aller markierten Bilder in die erste Spalte schreiben
            fF.tableWidgetDunkel.setItem(
                (index + (num_pictures_dark - len(filename))),
                2,
                widgets.QTableWidgetItem(str(int(anzahlHisBilder))),
            )
            if type(farbtiefe) == str:
                fF.tableWidgetDunkel.setItem(
                    (index + (num_pictures_dark - len(filename))),
                    3,
                    widgets.QTableWidgetItem(farbtiefe),
                )
            else:
                fF.tableWidgetDunkel.setItem(
                    (index + (num_pictures_dark - len(filename))),
                    3,
                    widgets.QTableWidgetItem(farbtiefe.name),
                )
            fF.tableWidgetDunkel.setItem(
                (index + (num_pictures_dark - len(filename))),
                4,
                widgets.QTableWidgetItem(str(filename[index])),
            )  # Die Pfade aller Bilder in die dritten Spalte schreiben

            fF.tableWidgetDunkel.item(
                (index + (num_pictures_dark - len(filename))), 1
            ).setTextAlignment(core.Qt.AlignCenter)
            fF.tableWidgetDunkel.item(
                (index + (num_pictures_dark - len(filename))), 2
            ).setTextAlignment(core.Qt.AlignCenter)
            fF.tableWidgetDunkel.item(
                (index + (num_pictures_dark - len(filename))), 3
            ).setTextAlignment(core.Qt.AlignCenter)

    def fF_pushbutton_dark_delete():
        global num_pictures_dark
        zeilen = fF.tableWidgetDunkel.selectedItems()
        print(zeilen)
        zeilenLoeschen = []
        alterWert = -1
        for index in zeilen:  # weiß nicht was das macht
            if alterWert != index.row():
                zeilenLoeschen.append(index.row())
            alterWert = index.row()

        zeilenLoeschen.sort()
        zeilenLoeschen.reverse()
        for index in range(len(zeilenLoeschen)):
            fF.tableWidgetDunkel.removeRow(zeilenLoeschen[index])
        num_pictures_dark = num_pictures_dark - len(zeilenLoeschen)

    def fF_pushbutton_dark_delete_all():
        fF.tableWidgetDunkel.setRowCount(0)
        global num_pictures_dark
        num_pictures_dark = 0

    def fF_radiobutton_new_pictures():
        update_FFK()

    def fF_pushbutton_saved_pictures():
        save.load_FFK(mW.comboBoxBPMSensor.currentText(), flag_show=True)

    ### Einstellungen Suchen
    # Andy Vorgabe Multi: Hell: min 1 max 0,95 ival 0,002 Dunkel: min 0 max 0,05 ival 0,005 # früher: ival 0,01
    # Andy Vorgabe Moving Fenster: min 5 max 17 ival 2  Faktor: min 2 max 3,5 ival 0,1
    # Andy Vorgabe Dynamic Empfindlichkeit: min 1.03 max 2 ival 0.01
    eS.horizontalSliderSchwellwertHot.setMinimum(0)
    eS.horizontalSliderSchwellwertHot.setMaximum(50)  # Vill etwas mehr.
    eS.horizontalSliderSchwellwertHot.setTickInterval(1)

    def eS_horizontal_slider_thresh_hot():
        value = eS.horizontalSliderSchwellwertHot.value()
        eS.labelSchwellwertHot.setText(str(round(value * (-0.002) + 1, 3)))

    eS.horizontalSliderSchwellwertDead.setMinimum(0)
    eS.horizontalSliderSchwellwertDead.setMaximum(50)  # Vill etwas mehr.
    eS.horizontalSliderSchwellwertDead.setTickInterval(1)

    def eS_horizontal_slider_thresh_dead():
        value = eS.horizontalSliderSchwellwertDead.value()
        eS.labelSchwellwertDead.setText(str(round(value * 0.002, 3)))

    eS.horizontalSliderMovingFensterbreite.setMinimum(0)
    eS.horizontalSliderMovingFensterbreite.setMaximum(6)
    eS.horizontalSliderMovingFensterbreite.setTickInterval(1)

    def eS_horizontal_slider_moving_window_width():
        value = eS.horizontalSliderMovingFensterbreite.value()
        eS.labelMovingFensterbreite.setText(str(value * 2 + 5))

    eS.horizontalSliderMovingSchwellwert.setMinimum(0)
    eS.horizontalSliderMovingSchwellwert.setMaximum(15)
    eS.horizontalSliderMovingSchwellwert.setTickInterval(1)

    def eS_horizontal_slider_moving_thresh():
        value = eS.horizontalSliderMovingSchwellwert.value()
        eS.labelMovingSchwellwert.setText(str(round(value * (-0.1) + 3.5, 2)))

    eS.horizontalSliderDynamicSchwellwert.setMinimum(0)
    eS.horizontalSliderDynamicSchwellwert.setMaximum(97)
    eS.horizontalSliderDynamicSchwellwert.setTickInterval(1)

    def eS_horizontal_slider_dynamic_thresh():
        value = eS.horizontalSliderDynamicSchwellwert.value()
        eS.labelDynamicSchwellwert.setText(str(round(value * (-0.01) + 2, 2)))

    def eS_pushbutton_preview():  # Detection #Beim Drücken soll eine Vorschau von Bild Nr 1 mit Aktuellen Einstellungen entstehen.
        image_window.exec()
        # Aufrugf der Vorschaufunktion/process. /Eigentlich wie startbutton blos ohne Speichern.

    ### Einstellungen Korrektur
    eK.horizontalSliderNachbarFensterbreite.setMinimum(0)  # Andy Vorgabe: min 3 max 21 ival 2
    eK.horizontalSliderNachbarFensterbreite.setMaximum(9)
    eK.horizontalSliderNachbarFensterbreite.setTickInterval(2)

    def eK_horizontal_slider_neighbor_window_width():
        value = eK.horizontalSliderNachbarFensterbreite.value()
        eK.labelNachbarFensterbreite.setText(str((value * 2) + 3))  # 3, 5, 7, 9 ... 21

    eK.horizontalSliderGradientFensterbreite.setMinimum(0)  # Andy Vorgabe: min 4 max 24 ival 2
    eK.horizontalSliderGradientFensterbreite.setMaximum(10)  # länge des Gradienten
    eK.horizontalSliderGradientFensterbreite.setTickInterval(2)

    def eK_horizontal_slider_gradient_window_width():
        value = eK.horizontalSliderGradientFensterbreite.value()
        eK.labelGradientFensterbreite.setText(str((value * 2) + 4))  # 4, 6, 8 ... 22

    def eK_pushbutton_preview():
        image_window.exec()

    ### Fortschritt Fenster
    def progress_push_button():
        path = mW.lineEditSpeicherort.text()
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    """ GUI Image Funktionen :___________________________________________________________________________________________________ """
    import socket
    import time

    ContinuousStopFlag = False

    def my_start(self):
        threading.Thread(target=start).start()

    def start():
        Mode = mW.comboBoxMode.currentIndex()
        Timermode = mW.comboBoxTimermode.currentIndex()
        Triggermode = mW.comboBoxTriggermode.currentIndex()

        print("Mode: " + str(Mode))
        print("Timermode: " + str(Timermode))
        print("Triggermode: " + str(Triggermode))

        ADDR = ("127.0.0.1", 1234)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if Mode == 0:

            client.connect(ADDR)
            Send1 = np.array([1, Timermode, Triggermode], dtype=np.ushort)
            client.send(Send1.tobytes())

            x = 0
            global ContinuousStopFlag
            newpAcqBuffer = np.zeros((512, 512), dtype=np.ushort)
            while True:

                client.send(ContinuousStopFlag.to_bytes(4, byteorder="little"))
                if ContinuousStopFlag == True:
                    break

                ByteImg = client.recv(512 * 512 * 2)
                Img1D = np.frombuffer(ByteImg, dtype=np.ushort)
                if len(Img1D) != 512 * 512:
                    x = x + 1
                    print("Fehler Nr." + str(x) + " mit len " + str(len(Img1D)))
                else:
                    newpAcqBuffer = np.reshape(Img1D, (-1, 512))
                    pixmap = gui.QPixmap(
                        gui.QImage(
                            newpAcqBuffer.data,
                            newpAcqBuffer.shape[0],
                            newpAcqBuffer.shape[1],
                            gui.QImage.Format_Grayscale16,
                        )
                    )
                    Width = mW.mylabel.width()
                    Height = mW.mylabel.height()
                    scaledpixmap = pixmap.scaled(Width, Width, core.Qt.KeepAspectRatio)
                    mW.mylabel.setPixmap(scaledpixmap)

            ContinuousStopFlag = False
            client.close()
            print("End Continuous")

        elif Mode == 1:

            client.connect(ADDR)
            Send1 = np.array([2, Timermode, Triggermode], dtype=np.ushort)
            client.send(Send1.tobytes())
            ByteImg = client.recv(512 * 512 * 2)
            Img1D = np.frombuffer(ByteImg, dtype=np.ushort)
            if len(Img1D) != 512 * 512:
                print("Fehler")
            else:
                newpAcqBuffer = np.reshape(Img1D, (-1, 512))

                if mW.checkBoxAlgorithmusKorrigieren.isChecked():
                    aktuelleZeit = str(datetime.now())[:-7].replace(":", "-")  # aktuelle Zeit speichern
                    Methode = DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_korrekturmethode"]

                    if mW.checkBoxAlgorithmusFFK.isChecked():  # FCC Vorbereiten
                        if mW.radioButtonAlgorithmusNachbar.isChecked():
                            Hell_Mittel_Bild = np.uint16(
                                correction.neighbor_2(
                                    image_data_bright,
                                    BAD_total,
                                    Methode,
                                    int(eK.labelNachbarFensterbreite.text()),
                                )
                            )
                            Dunkel_Mittel_Bild = np.uint16(
                                correction.neighbor_2(
                                    image_data_dark,
                                    BAD_total,
                                    Methode,
                                    int(eK.labelNachbarFensterbreite.text()),
                                )
                            )
                        elif mW.radioButtonAlgorithmusGradient.isChecked():             #LS: s entfernt (GradienSt)
                            Hell_Mittel_Bild = np.uint16(
                                correction.gradient(
                                    image_data_bright,
                                    BAD_total,
                                    Methode,
                                    int(eK.labelGradientFensterbreite.text()),
                                )
                            )
                            Dunkel_Mittel_Bild = np.uint16(
                                correction.gradient(
                                    image_data_dark,
                                    BAD_total,
                                    Methode,
                                    int(eK.labelGradientFensterbreite.text()),
                                )
                            )
                    # Korrektur
                    cfg.loading_bar_exp = cfg.loading_bar_exp + 1

                    if mW.radioButtonAlgorithmusNachbar.isChecked():
                        GOOD = np.uint16(
                            correction.neighbor_2(
                                newpAcqBuffer,
                                BAD_total,
                                Methode,
                                int(eK.labelNachbarFensterbreite.text()),
                            )
                        )
                    elif mW.radioButtonAlgorithmusGradient.isChecked():
                        GOOD = np.uint16(
                            correction.gradient(
                                newpAcqBuffer,
                                BAD_total,
                                Methode,
                                int(eK.labelGradientFensterbreite.text()),
                            )
                        )

                    if mW.checkBoxAlgorithmusFFK.isChecked():
                        print("FFC start")
                        GOOD = correction.flatfield(GOOD, Hell_Mittel_Bild, Dunkel_Mittel_Bild)[0]
                        print("FFC Ende")
                    # Export Aufruf______________________________________________________________
                    if np.shape(GOOD) == ():  # wenn GOOD eine -1 (Integer) ist
                        open_msg_box(
                            icon=widgets.QMessageBox.Information,
                            text="Die Auflösung der Bad-Pixel-Map und des Bildes sind unterschiedlich",
                            informativeText="Bitte verwenden Sie andere Bilder.",
                            windowTitle="Unterschiedliche Auflösungen",
                            standardButtons=widgets.QMessageBox.Ok,
                            pFunction=msg_button_click,
                        )
                        flagExportFehler = True
                    else:
                        exp.export_pictures(
                            path=mW.lineEditSpeicherort.text(),
                            image_name=mW.tableWidgetBilddaten.item(1, 0).text(),
                            image=GOOD,
                            time=aktuelleZeit,
                        )

                else:
                    aktuelleZeit = str(datetime.now())[:-7].replace(":", "-")  # aktuelle Zeit speichern
                    Methode = DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_korrekturmethode"]
            
                    exp.export_pictures(
                        path=mW.lineEditSpeicherort.text(),
                        image_name="test",
                        image=newpAcqBuffer,
                        time=aktuelleZeit,
                    )

                mW.mylabel.setPixmap(
                    gui.QPixmap(
                        gui.QImage(
                            newpAcqBuffer.data,
                            newpAcqBuffer.shape[0],
                            newpAcqBuffer.shape[1],
                            gui.QImage.Format_Grayscale16,
                        )
                    )
                )

            client.close()
            print("End Single_Shot")

        elif Mode == 2:

            client.connect(ADDR)
            nFrames = 10
            Send1 = np.array([3, Timermode, Triggermode], dtype=np.ushort)
            client.send(Send1.tobytes())
            ListAcqBuffer = []

            for z in range(nFrames):
                ByteImg = client.recv(512 * 512 * 2)
                Img1D = np.frombuffer(ByteImg, dtype=np.ushort)
                if len(Img1D) != 512 * 512:
                    print("Fehler")
                else:
                    newpAcqBuffer = np.reshape(Img1D, (-1, 512))
                    mW.mylabel.setPixmap(
                        gui.QPixmap(
                            gui.QImage(
                                newpAcqBuffer.data,
                                newpAcqBuffer.shape[0],
                                newpAcqBuffer.shape[1],
                                gui.QImage.Format_Grayscale16,
                            )
                        )
                    )

                ListAcqBuffer.append(newpAcqBuffer)

            client.close()
            print("End Sequence")

    def my_stop():
        global ContinuousStopFlag
        ContinuousStopFlag = True

    ### Tab Image
    mW.myStart.clicked.connect(my_start)
    mW.myStop.clicked.connect(my_stop)

    """ GUI-Elemente mit Funktionen verbinden:___________________________________________________________________________________ """
    #### UI Aktionen ####
    ### Allgemein
    ui_setup()
    mW.pushButtonMainBack.clicked.connect(mW_pushbutton_main_back)
    mW.pushButtonMainForward.clicked.connect(mW_pushbutton_main_forward)
    mW.tabWidget.currentChanged.connect(mW_tab_widget)

    ### Tab Sensor / BPM
    mW.comboBoxBPMSensor.activated.connect(mW_combobox_BPM_sensor)
    mW.comboBoxBPMBPM.activated.connect(mW_combobox_BPM_BPM)
    mW.pushButtonBPMNeuerSensor.clicked.connect(mW_pushbutton_BPM_new_sensor)
    mW.pushButtonBPMSensorLaden.clicked.connect(mW_pushbutton_BPM_load_sensor)
    mW.pushButtonBPMSensorSpeichern.clicked.connect(mW_pushbutton_BPM_save_sensor)
    mW.pushButtonBPMVorschau.clicked.connect(mW_pushbutton_BPM_preview)
    mW.pushButtonBPMSensorLoeschen.clicked.connect(mW_pushbutton_BPM_delete_sensor)
    mW.pushButtonBPMBPMLoeschen.clicked.connect(mW_pushbutton_BPM_delete_BPM)

    ### Tab Bilddaten
    mW.pushButtonBilddatenOrdnerDurchsuchen.clicked.connect(mW_pushbutton_find_dir)
    mW.pushButtonBilddatenImportieren.clicked.connect(mW_pushbutton_import_dir)
    mW.pushButtonBilddatenAdd.clicked.connect(mW_pushbutton_import_image_data)
    mW.pushButtonBilddatenDelete.clicked.connect(mW_pushbutton_delete_image_data)
    mW.pushButtonBilddatenDeleteAll.clicked.connect(mW_pushbutton_delete_all_image_data)

    ### Tab Speicherort
    mW.pushButtonSpeicherortDurchsuchen.clicked.connect(mW_pushbutton_search_dir)

    ### Tab Algorithmus
    mW.checkBoxAlgorithmusSuchen.stateChanged.connect(mW_checkbox_find_algorithm)
    mW.pushButtonAlgorithmusSuchenEinstellungen.clicked.connect(mW_pushbutton_find_algorithm_settings)
    mW.checkBoxAlgorithmusKorrigieren.stateChanged.connect(mW_checkbox_algorithm_correction)
    mW.pushButtonAlgorithmusKorrigierenEinstellungen.clicked.connect(mW_pushbutton_correct_algorithm_settings)
    mW.checkBoxAlgorithmusFFK.clicked.connect(mW_checkbox_algorithm_FFK)  # statt clicked kann auch toggled verwendet werden stateChanged funktioniert nicht

    ### Flat-Field-Korrektur
    fF.radioButtonGespeicherteBilder.clicked.connect(fF_radiobutton_saved_pictures)
    fF.pushButtonHellAdd.clicked.connect(fF_pushbutton_bright_add)
    fF.pushButtonHellDelete.clicked.connect(fF_pushbutton_bright_delete)
    fF.pushButtonHellDeleteAll.clicked.connect(fF_pushbutton_bright_delete_all)
    fF.pushButtonDunkelAdd.clicked.connect(fF_pushbutton_dark_add)
    fF.pushButtonDunkelDelete.clicked.connect(fF_pushbutton_dark_delete)
    fF.pushButtonDunkelDeleteAll.clicked.connect(fF_pushbutton_dark_delete_all)
    fF.radioButtonNeueBilder.clicked.connect(fF_radiobutton_new_pictures)
    fF.pushButtonGespeicherteBilder.clicked.connect(fF_pushbutton_saved_pictures)

    ### Einstellungen Suchen
    eS.horizontalSliderSchwellwertHot.valueChanged.connect(eS_horizontal_slider_thresh_hot)
    eS.horizontalSliderSchwellwertDead.valueChanged.connect(eS_horizontal_slider_thresh_dead)
    eS.horizontalSliderMovingFensterbreite.valueChanged.connect(eS_horizontal_slider_moving_window_width)
    eS.horizontalSliderMovingSchwellwert.valueChanged.connect(eS_horizontal_slider_moving_thresh)
    eS.horizontalSliderDynamicSchwellwert.valueChanged.connect(eS_horizontal_slider_dynamic_thresh)
    eS.pushButtonVorschau.clicked.connect(eS_pushbutton_preview)
    eS.groupBoxSchwellwert.setToolTip("Hinweise für die Einstellung des Schwellwertfilters: \nJe weiter rechts der Schieberegler ist, \ndesto mehr Pixelfehler werden erkannt. \nEmpfohlener Wert ist 0,95 für helle Pixel bzw. 0,05 für dunkle Pixel.")
    eS.groupBoxDynamic.setToolTip("Hinweise für die Einstellung des Dynamic-Check: \nAchtung ein Schwellwert über 0,1 ist Lebensmüde!")
    eS.groupBoxMoving.setToolTip("Hinweise für die Einstellung des Moving-Window: \nGroße Fensterbreiten haben einen hohen Rechenaufwand.\nJe geringer der Schwellwert ist, desto mehr Fehler werden entdeckt. Empfohlene Fensterbreite 7\nEmpfohlener Schwellwert 3,5")

    ### Einstellungen Korrektur
    eK.horizontalSliderNachbarFensterbreite.valueChanged.connect(eK_horizontal_slider_neighbor_window_width)
    eK.horizontalSliderGradientFensterbreite.valueChanged.connect(eK_horizontal_slider_gradient_window_width)
    eK.pushButtonVorschau.clicked.connect(eK_pushbutton_preview)

    ### Fortschritt Fenster
    progress.pushButtonOeffnen.clicked.connect(progress_push_button)

    #### QT UI anzeigen####
    mW.show()

    def cofunction(BPM, F):  # Korrigieren
        flagExportFehler = False
        if mW.checkBoxAlgorithmusKorrigieren.isChecked():
            global image_data
            aktuelleZeit = str(datetime.now())[:-7].replace(":", "-")  # aktuelle Zeit speichern
            Methode = DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["last_korrekturmethode"]
            progress.textEdit.insertPlainText("Bilder korrigiert und gespeichert: ")
            if mW.checkBoxAlgorithmusFFK.isChecked():  # FCC Vorbereiten
                if mW.radioButtonAlgorithmusNachbar.isChecked():
                    Hell_Mittel_Bild = np.uint16(
                        correction.neighbor_2(
                            image_data_bright,
                            BPM,
                            Methode,
                            int(eK.labelNachbarFensterbreite.text()),
                        )
                    )
                    Dunkel_Mittel_Bild = np.uint16(
                        correction.neighbor_2(
                            image_data_dark,
                            BPM,
                            Methode,
                            int(eK.labelNachbarFensterbreite.text()),
                        )
                    )
                elif mW.radioButtonAlgorithmusGradient.isChecked():
                    Hell_Mittel_Bild = np.uint16(
                        correction.gradient(
                            image_data_bright,
                            BPM,
                            Methode,
                            int(eK.labelGradientFensterbreite.text()),
                        )
                    )
                    Dunkel_Mittel_Bild = np.uint16(
                        correction.gradient(
                            image_data_dark,
                            BPM,
                            Methode,
                            int(eK.labelGradientFensterbreite.text()),
                        )
                    )
            # Korrektur Loop
            for i in range(np.shape(image_data)[0]):
                cfg.loading_bar_exp = cfg.loading_bar_exp + 1
                if cfg.kill_flag_threads == True:
                    return -1
                if mW.radioButtonAlgorithmusNachbar.isChecked():
                    GOOD = np.uint16(
                        correction.neighbor_2(
                            image_data[i],
                            BPM,
                            Methode,
                            int(eK.labelNachbarFensterbreite.text()),
                        )
                    )
                elif mW.radioButtonAlgorithmusGradient.isChecked():
                    GOOD = np.uint16(
                        correction.gradient(
                            image_data[i],
                            BPM,
                            Methode,
                            int(eK.labelGradientFensterbreite.text()),
                        )
                    )
                #if mW.radioButtonAlgorithmusNagao():               #######TO DO!!!! 
                if mW.checkBoxAlgorithmusFFK.isChecked():
                    print("FFC start")
                    GOOD = correction.flatfield(GOOD, Hell_Mittel_Bild, Dunkel_Mittel_Bild)[0]
                    print("FFC Ende")
                # Export Aufruf______________________________________________________________
                if np.shape(GOOD) == ():  # wenn GOOD eine -1 (Integer) ist
                    open_msg_box(
                        icon=widgets.QMessageBox.Information,
                        text="Die Auflösung der Bad-Pixel-Map und des Bildes sind unterschiedlich",
                        informativeText="Bitte verwenden Sie andere Bilder.",
                        windowTitle="Unterschiedliche Auflösungen",
                        standardButtons=widgets.QMessageBox.Ok,
                        pFunction=msg_button_click,
                    )
                    progress.textEdit.insertPlainText("\nFehler beim Korrigieren.\n")
                    flagExportFehler = True
                else:
                    exp.export_pictures(
                        path=mW.lineEditSpeicherort.text(),
                        image_name=mW.tableWidgetBilddaten.item(i, 0).text(),
                        image=GOOD,
                        time=aktuelleZeit,
                    )
                    progress.textEdit.insertPlainText(str(cfg.loading_bar_exp) + " ")
            progress.textEdit.insertPlainText("\nKorrektur ist abgeschlossen.\n")
            if flagExportFehler == False:
                progress.textEdit.insertPlainText("Alle Bilder wurden gespeichert.\n")
        progress.textEdit.insertPlainText("Fertig.\n")
        progress.buttonBox.button(widgets.QDialogButtonBox.Ok).setEnabled(True)  # Okay Button able
        if mW.checkBoxAlgorithmusSuchen.isChecked():
            progress.textEdit.insertPlainText("Wenn Sie die neue Bad-Pixel-Map speichern möchten, drücken Sie bitte OK. Ansonsten bitte Cancel oder Abbrechen drücken.")
        cfg.global_BPM_dynamic = 0
        cfg.global_BPM_moving = 0
        cfg.global_BPM_multi = 0  # Alles wieder zurücksetzen.
        cfg.error_collect["aMW"] = 0
        cfg.error_collect["MPPC"] = 0
        cfg.error_collect["dC"] = 0

    def process():  # Hauptprocess nach start
        global mean_pictures
        global BAD_total
        vorschauBild = 0
        # Vorschau Live__________
        if cfg.loading_bar > 0 and mW.checkBoxAlgorithmusSuchen.isChecked():
            vorschauBild = copy.copy(mean_pictures)  # Bild erstellen
            if np.shape(cfg.global_BPM_dynamic) != ():
                vorschauBild = telemetry.mark_pixel_virtual(bpm=cfg.global_BPM_dynamic, pBild=vorschauBild, bgr=2)  # Dynamic =rot
            if np.shape(cfg.global_BPM_moving) != ():
                vorschauBild = telemetry.mark_pixel_virtual(bpm=cfg.global_BPM_moving, pBild=vorschauBild, bgr=0)  # MovingW = blau
            if np.shape(cfg.global_BPM_multi) != ():
                vorschauBild = telemetry.mark_pixel_virtual(bpm=cfg.global_BPM_multi, pBild=vorschauBild, bgr=1)  # Multi=grün
            # Vorschau anzeigen...
            cv2.imshow("Gefundene Pixelfehler", vorschauBild)

            exportPath = exp.export_pictures_easy(
                path=save.dir_path,
                image_name="bpmVorschau.png",
                image=vorschauBild,
            )
            pixmap = gui.QPixmap(exportPath)

        if cfg.loading_bar_max != 0:
            progress.progressBar.setValue(int(cfg.loading_bar / cfg.loading_bar_max * 100))
        else:
            progress.progressBar.setValue(100)
        print("ladebalken = ", cfg.loading_bar)

        # Abfrage Fertig_________
        FertigFlag = False
        cfg.lock.acquire()
        if cfg.loading_bar == cfg.loading_bar_max:
            progress.progressBar.setValue(int(100))
            print("Done")
            FertigFlag = True
        cfg.lock.release()

        if FertigFlag:
            timer.stop()
            if np.shape(cfg.global_BPM_dynamic) != ():
                vorschauBild = telemetry.mark_pixel_virtual(bpm=cfg.global_BPM_dynamic, pBild=vorschauBild, bgr=2)  # Dynamic =rot
            if np.shape(cfg.global_BPM_moving) != ():
                vorschauBild = telemetry.mark_pixel_virtual(bpm=cfg.global_BPM_moving, pBild=vorschauBild, bgr=0)  # MovingW = blau
            if np.shape(cfg.global_BPM_multi) != ():
                vorschauBild = telemetry.mark_pixel_virtual(bpm=cfg.global_BPM_multi, pBild=vorschauBild, bgr=1)  # Multi=grün
            if mW.checkBoxAlgorithmusSuchen.isChecked():
                cv2.imshow("Gefundene Pixelfehler", vorschauBild)  # so kommt beim Mac immer alle Fehler der BPM
            # Zusammenfassen + Speichern oder Laden
            if mW.checkBoxAlgorithmusSuchen.isChecked():
                progress.textEdit.insertPlainText("Pixelfehler-Suche ist abgeschlossen.\n")
                BAD_total = (
                    detection.mapping(
                        cfg.global_BPM_moving,
                        cfg.global_BPM_multi,
                        cfg.global_BPM_dynamic,
                    ) * 100
                )  # Digital*100
                # BPM Speichern vill auch am Ende.
                # Speichern.BPM_Save(BAD_Ges*150,mW.comboBoxBPMSensor.currentText()) #BPM Speichern    #Nur wenn alles gut war!  und wenn Pixel gesucht wurden.
                Fehlerzahl = (
                    cfg.error_collect["aMW"]
                    + cfg.error_collect["MPPC"]
                    + cfg.error_collect["dC"]
                )
                print("BPM enthaelt ", Fehlerzahl, " Pixel")
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["Anz_PixelFehler"] = Fehlerzahl  # anzahl an pixeln.
                DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["Anz_Bilder"] = (
                    DATA["Sensors"][int(mW.comboBoxBPMSensor.currentIndex())]["Anz_Bilder"]
                    + num_pictures
                )
                # Abschließend noch Speichern in JSON!
            else:  # laden
                # BAD_Ges=Speichern.BPM_Read(mW.comboBoxBPMSensor.currentText())        # Alter Stand, wo es nur eine BPM pro Sensor gibt
                BAD_total = save.BPM_read_selected(mW.comboBoxBPMBPM.currentText())
                # print(mW.comboBoxBPMBPM.currentText())
                if np.shape(BAD_total) == ():  # Wenns noch keine gibt.
                    progress.textEdit.insertPlainText("Es gibt noch keinen Datensatz. Suchen Erforderlich!\n")
                    return
            ID_T = threading.Thread(name="Korrektur", target=cofunction, args=(BAD_total, 12))
            ID_T.start()
            # exp.exportPictures(pPath= mW.lineEditSpeicherort.text(), pImagename= "Vorschau", pImage= vorschauBild, pZeit= "aktuelleZeit") #Debug Vorschau
            update_BPM()  # Tab 1 updaten
            update_text_BPM()

    timer = core.QTimer()
    timer.timeout.connect(process)
    sys.exit(app.exec_())
