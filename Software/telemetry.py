import cv2
import numpy as np

# import matplotlib.pyplot as plt
import cProfile
import detection
import os
from datetime import datetime
import verpixler


def mark_pixels(bpm, picture, thresh=100, bgr=1, Bildname="Bildname", Algorithmus="Suchalgorithmus", Parameter="Parameter",):
    cv2.imwrite(Bildname + "_original.png", picture)
    # cv2.imwrite(Bildname + "_original.png", picture[0])
    colorPicture = cv2.cvtColor(picture, cv2.COLOR_GRAY2RGB)
    if np.shape(picture) != np.shape(bpm):  # Wann kann das passieren?
        print("Digga schau das die Dimensionen passen!")
    hoehe, breite = np.shape(picture)
    for z in range(hoehe):
        for s in range(breite):
            if bpm[z, s] >= thresh:
                colorPicture = drawPlus(colorPicture, z, s, hoehe, breite, bgr)
    
    cv2.imwrite(Bildname + "_" + Algorithmus + "_" + Parameter + ".png", colorPicture, [cv2.IMWRITE_PNG_COMPRESSION, 1],)



def mark_pixel_virtual(bpm, pBild, bgr=1, erstes=False):  # für die Vorschau
    Dummy = np.zeros((np.shape(pBild)[0], np.shape(pBild)[1]), dtype=pBild.dtype)
    if np.shape(Dummy) == np.shape(pBild):  # Wenn die Array eine andere Größe besitzen, d.h. wenn es kein Farbbild ist
        colorPicture = cv2.cvtColor(pBild, cv2.COLOR_GRAY2RGB)
    else:
        colorPicture = pBild
    if np.shape(bpm) == ():  # if(np.shape(picture[2]) !=np.shape(bpm)):
        print("BPM ist leer")
        return pBild  # Wenn die BPM noch nicht da ist kommt das Orginal zurück.
    hoehe, breite, farbe = np.shape(colorPicture)
    for z in range(hoehe):
        for s in range(breite):
            if bpm[z, s] != 0:
                colorPicture = drawPlus(colorPicture, z, s, hoehe, breite, bgr)
    return colorPicture


# Daten: 2-D Array (1. Spalte: eingestellter Parameter, 2. Spalte: dazugehöriger Funktionswert, z.B. Fehleranzahl)
# Bildname: String Name des gespeicherten Bildes
# Algorithmus: String Verwendeter Suchalgorithmus
# Parameter: String Modifizierter Parameter
#
#
"""
def plotData(Daten, Pfadname="Testbilder/", Bildname="Bildname", Algorithmus="Suchalgorithmus", Parameter="Parameter", xBeschriftung="Parameter", yBeschriftung="gefundene Fehler"):    
    plt.clf()
    plt.plot(Daten[0], Daten[1], Daten[0], Daten[1], 'kx')
    plt.xlabel(xBeschriftung)
    plt.ylabel(yBeschriftung)
    plt.title(Bildname + " - " + Algorithmus + " - " + Parameter)
    #plt.text(60, .025, r'$\mu=100,\ \sigma=15$')
    plt.grid(True)
    aktuelleZeit = str(datetime.now())[:-7].replace(":","-") # aktuelle Zeit mit Datum und Uhrzeit
    #plt.savefig(Bildname + "_" + Algorithmus + "_" + Parameter + "_" + aktuelleZeit, bbox_inches='tight', dpi=300)
    #plt.savefig(Pfadname + Bildname + "_" + Algorithmus + "_" + Parameter + "_" + "_lin", bbox_inches='tight', dpi=300)
    #plt.savefig("plotbild", bbox_inches='tight', dpi=300)
    plt.savefig(Pfadname + Bildname + "_" + Algorithmus + "_" + Parameter + "_" + "_lin", bbox_inches='tight', dpi=300)
    #plt.show()

def plotDataLog(Daten, Pfadname="Testbilder/", Bildname="Bildname", Algorithmus="Suchalgorithmus", Parameter="Parameter", xBeschriftung="Parameter", yBeschriftung="gefundene Fehler"):    
    plt.clf()
    plt.plot(Daten[0], Daten[1], Daten[0], Daten[1], 'kx')
    plt.xlabel(xBeschriftung)
    plt.ylabel(yBeschriftung)
    plt.title(Bildname + " - " + Algorithmus + " - " + Parameter)
    plt.xscale('linear')
    plt.yscale('symlog')
    #plt.text(60, .025, r'$\mu=100,\ \sigma=15$')
    plt.grid(True)
    aktuelleZeit = str(datetime.now())[:-7].replace(":","-") # aktuelle Zeit mit Datum und Uhrzeit
    print(aktuelleZeit)
    #plt.savefig(Bildname + "_" + Algorithmus + "_" + Parameter + "_" + aktuelleZeit + "_log", bbox_inches='tight', dpi=300)
    plt.savefig(Pfadname + Bildname + "_" + Algorithmus + "_" + Parameter + "_" + "_log", bbox_inches='tight', dpi=300)
    #plt.show()

def plotDataAuswertung(Daten, Pfadname="Testbilder/", Bildname="Bildname", Algorithmus="Suchalgorithmus", Parameter="Parameter", xBeschriftung="Parameter", yBeschriftung="gefundene Fehler"):    
    plt.clf()
    plt.plot(Daten[0], Daten[1], label='richtig gefundene Fehler')
    plt.plot(Daten[0], Daten[1], 'kx') 
    plt.plot(Daten[0], Daten[2], label='falsch gefundene Fehler')
    plt.plot(Daten[0], Daten[2], 'kx')
    plt.xscale('linear')
    plt.yscale('linear')
    plt.xlabel(xBeschriftung)
    plt.ylabel(yBeschriftung)
    plt.title(Bildname + " - " + Algorithmus + " - " + Parameter)
    plt.grid(True)
    plt.legend()
    aktuelleZeit = str(datetime.now())[:-7].replace(":","-") # aktuelle Zeit mit Datum und Uhrzeit
    #plt.savefig(Bildname + "_" + Algorithmus + "_" + Parameter + "_" + aktuelleZeit, bbox_inches='tight', dpi=300)
    plt.savefig(Pfadname + Bildname + "_" + Algorithmus + "_" + Parameter + "_" + "_lin", bbox_inches='tight', dpi=300)
    #plt.show()

def plotDataAuswertungLog(Daten, Pfadname="Testbilder/", Bildname="Bildname", Algorithmus="Suchalgorithmus", Parameter="Parameter", xBeschriftung="Parameter", yBeschriftung="gefundene Fehler"):    
    plt.clf()
    plt.plot(Daten[0], Daten[1], label='richtig gefundene Fehler')
    plt.plot(Daten[0], Daten[1], 'kx') 
    plt.plot(Daten[0], Daten[2], label='falsch gefundene Fehler')
    plt.plot(Daten[0], Daten[2], 'kx')
    plt.xscale('linear')
    plt.yscale('symlog')
    plt.xlabel(xBeschriftung)
    plt.ylabel(yBeschriftung)
    plt.title(Bildname + " - " + Algorithmus + " - " + Parameter)
    plt.grid(True)
    plt.legend()
    aktuelleZeit = str(datetime.now())[:-7].replace(":","-") # aktuelle Zeit mit Datum und Uhrzeit
    #plt.savefig(Bildname + "_" + Algorithmus + "_" + Parameter + "_" + aktuelleZeit, bbox_inches='tight', dpi=300)
    plt.savefig(Pfadname + Bildname + "_" + Algorithmus + "_" + Parameter + "_" + "_log", bbox_inches='tight', dpi=300)
    #plt.show()
"""


def drawPlus(colorPicture, zeile, spalte, hoehe, breite, bgr, wert=65535,):
    colorPicture[bottom(zeile - 2), spalte, bgr] = wert
    colorPicture[bottom(zeile - 1), spalte, bgr] = wert
    colorPicture[zeile, bottom(spalte - 2), bgr] = wert
    colorPicture[zeile, bottom(spalte - 1), bgr] = wert
    colorPicture[zeile, top(spalte + 1, breite), bgr] = wert
    colorPicture[zeile, top(spalte + 2, breite), bgr] = wert
    colorPicture[top(zeile + 1, hoehe), spalte, bgr] = wert
    colorPicture[top(zeile + 2, hoehe), spalte, bgr] = wert
    bgr = bgr + 1
    if (bgr) > 2:
        bgr = 0
    colorPicture[bottom(zeile - 2), spalte, bgr] = 0
    colorPicture[bottom(zeile - 1), spalte, bgr] = 0
    colorPicture[zeile, bottom(spalte - 2), bgr] = 0
    colorPicture[zeile, bottom(spalte - 1), bgr] = 0
    colorPicture[zeile, top(spalte + 1, breite), bgr] = 0
    colorPicture[zeile, top(spalte + 2, breite), bgr] = 0
    colorPicture[top(zeile + 1, hoehe), spalte, bgr] = 0
    colorPicture[top(zeile + 2, hoehe), spalte, bgr] = 0
    bgr = bgr + 1
    if (bgr) > 2:
        bgr = 0
    colorPicture[bottom(zeile - 2), spalte, bgr] = 0
    colorPicture[bottom(zeile - 1), spalte, bgr] = 0
    colorPicture[zeile, bottom(spalte - 2), bgr] = 0
    colorPicture[zeile, bottom(spalte - 1), bgr] = 0
    colorPicture[zeile, top(spalte + 1, breite), bgr] = 0
    colorPicture[zeile, top(spalte + 2, breite), bgr] = 0
    colorPicture[top(zeile + 1, hoehe), spalte, bgr] = 0
    colorPicture[top(zeile + 2, hoehe), spalte, bgr] = 0
    return colorPicture


def bottom(aktuellerWert, minWert=0):
    if aktuellerWert < minWert:
        return minWert
    else:
        return aktuellerWert


def top(aktuellerWert, maxWert):
    if aktuellerWert > maxWert - 1:
        return maxWert - 1
    else:
        return aktuellerWert


def timeTest(pythonFile="detection", funktionsAufruf="movingWindow(bildDaten[0])"):
    cProfile.run(pythonFile + "." + funktionsAufruf)


"""
def logDetection(picture, bpmFehlerthreshrt = 100, startwert = 0, stopwert = 2, messpunkte = 10, BPM0 = 0):
    #Andys Funktion:
    #Bild, BPM0 = verpixler.verpixeln(picture, 8000, 4, 0)
    #picture = Bild
    # Andys Funktion Ende
    Bild3D = picture
    picture = picture[0]

    xArray = np.linspace(start= startwert, stop= stopwert, num= messpunkte,dtype= np.float) # erstellen von der x-Achse
    yArray = np.zeros((messpunkte),dtype= np.float) # erstellen von der y-Achse

    ergAuswertung = np.zeros((messpunkte, 6),dtype= np.float) # Auswertung

    hoehe, breite = np.shape(picture)
    bpm = np.zeros((hoehe,breite))
    print("Das x-Array: ", xArray, type(xArray))
    print("Das y-Array: ", yArray, type(yArray))
    aktuelleZeit = str(datetime.now())[:-7].replace(":","-") # aktuelle Zeit mit Datum und Uhrzeit
    aktuellerPfad = "Testbilder/" + aktuelleZeit
    aktuellerPfadBilder = aktuellerPfad + "/Bilder/"
    os.mkdir(aktuellerPfad)
    os.mkdir(aktuellerPfadBilder)
    for index in range(len(xArray)):
        #bpm = detection.movingWindow(picture,xArray[index],1000)             # Schwellwert unten
        #bpm = detection.movingWindow(picture,0,xArray[index])                # Schwellwert oben
        #bpm = detection.movingWindow(picture,1 - xArray[index],1 + xArray[index])    # Schwelltwert beide
        #bpm = detection.advancedMovingWindow(picture,10,Faktor=xArray[index]) [0]
        
        bpm = detection.MultiPicturePixelCompare(Bild3D, 1-xArray[index],0+xArray[index]) [0]
        print("Aktuelle Messreihe: ", index)
        mark_pixels(bpm, picture, bpmFehlerthreshrt, 1,  aktuellerPfadBilder + "/Simulationsbild Bauteil", "Moving Window Advance", "Schwellwert_" + "{:.3f}".format(round(xArray[index],3))   )

        ergAuswertung[index] = verpixler.auswertung(bpm,BPM0) [0]

        #mark_pixels(bpm, picture, bpmFehlerthreshrt, 1,  aktuellerPfad + "/Simulationsbild", "Advanced Moving Window", "Fensterbreite_" + "{:.3f}".format(round(xArray[index],3))   )
        for z in range(hoehe):
            for s in range(breite):
                if bpm[z,s] >= bpmFehlerthreshrt:
                    yArray[index] += 1 
    dataArray = np.array([xArray, yArray],dtype= np.float)
    print(dataArray)
    #plotData(dataArray,"Simulationsbild","Moving Window", "Schwellwert Dead-Pixel")
    #plotDataLog(dataArray,"Simulationsbild","Moving Window", "Schwellwert Dead-Pixel")
    np.savetxt(aktuellerPfad + "/messdaten.csv", dataArray, delimiter=";", fmt="%1.3f")

    np.savetxt(aktuellerPfad + "/Auswertung.csv", ergAuswertung,fmt="%1.3f")

    plotData(dataArray, aktuellerPfad + "/", "Simulationsbild Bauteil","Moving Window Advance", "Schwellwert", xBeschriftung="Schwellwert")
    plotDataLog(dataArray, aktuellerPfad + "/", "Simulationsbild Bauteil","Moving Window Advance", "Schwellwert", xBeschriftung="Schwellwert")
    print(ergAuswertung)
    #ergAuswertungPlotten2 = [ [1, 2, 3, 4 ], [4 ,3 ,2,1 ], [1, 2, 3, 4,] ]
    ergAuswertungPlotten = np.array( [ ergAuswertung[:,5], ergAuswertung[:,4]  ] )
    ergAuswertungPlotten2 = np.array([xArray,ergAuswertung[:,0], ergAuswertung[:,3]])   # richtigen Werte und falsch erkanten Werte
    plotData(ergAuswertungPlotten, aktuellerPfad + "/", "Simulationsbild Bauteil","Moving Window Advance", Parameter="ROC-Kurve" , xBeschriftung="false positive rate", yBeschriftung="true positive rate")
    plotDataAuswertungLog(ergAuswertungPlotten2, aktuellerPfad + "/", "Simulationsbild Bauteil","Moving Window Advance", Parameter="Gefundene Fehler" , xBeschriftung="Schwellwert", yBeschriftung="gefundene Fehler")
    plotDataAuswertung(ergAuswertungPlotten2, aktuellerPfad + "/", "Simulationsbild Bauteil","Moving Window Advance", Parameter="Gefundene Fehler" , xBeschriftung="Schwellwert", yBeschriftung="gefundene Fehler")


def logDetectionOld(picture, bpmFehlerthreshrt = 100, startwert = 0, stopwert = 2, messpunkte = 10):
    
    #Andys Funktion:
    #Bild, BPM0 = verpixler.verpixeln(picture, 8000, 4, 0)
    #fullBild = picture
    #picture = picture[0]
    # Andys Funktion Ende

    xArray = np.linspace(start= startwert, stop= stopwert, num= messpunkte,dtype= np.float) # erstellen von der x-Achse
    yArray = np.zeros((messpunkte),dtype= np.float) # erstellen von der y-Achse

    ergAuswertung = np.zeros((messpunkte, 6),dtype= np.float) # Auswertung

    hoehe, breite = np.shape(picture)
    #hoehe, breite = np.shape(picture)
    bpm = np.zeros((hoehe,breite))
    print("Das x-Array: ", xArray, type(xArray))
    print("Das y-Array: ", yArray, type(yArray))
    aktuelleZeit = str(datetime.now())[:-7].replace(":","-") # aktuelle Zeit mit Datum und Uhrzeit
    aktuellerPfad = "Testbilder/" + aktuelleZeit
    aktuellerPfadBilder = aktuellerPfad + "/Bilder/"
    os.mkdir(aktuellerPfad)
    os.mkdir(aktuellerPfadBilder)
    for index in range(len(xArray)):
        #bpm = detection.movingWindow(picture,xArray[index],1000)             # Schwellwert unten
        #bpm = detection.movingWindow(picture,0,xArray[index])                # Schwellwert oben
        bpm = detection.movingWindow(picture,0 + 1 - xArray[index],1+ xArray[index])    # Schwelltwert beide
        #bpm = detection.advancedMovingWindow(picture,Fensterbreite=12, Faktor=xArray[index]) [0]
        print("Aktuelle Messreihe: ", index)
        #bpm = detection.MultiPicturePixelCompare(fullBild, 1-xArray[index],0+xArray[index])[0]
        mark_pixels(bpm, picture, bpmFehlerthreshrt, 1,  aktuellerPfadBilder + "/Bildserie2_160kV_70uA_mittelwert", "Moving Window", "Fensterbreite_" + "{:.3f}".format(round(xArray[index],3))   )

        #ergAuswertung[index] = verpixler.auswertung(bpm,BPM0) [0]

        #mark_pixels(bpm, picture, bpmFehlerthreshrt, 1,  aktuellerPfad + "/Simulationsbild", "Moving Window", "Fensterbreite_" + "{:.3f}".format(round(xArray[index],3))   )
        for z in range(hoehe):
            for s in range(breite):
                if bpm[z,s] >= bpmFehlerthreshrt:
                    yArray[index] += 1 
    dataArray = np.array([xArray, yArray],dtype= np.float)
    print(dataArray)
    #plotData(dataArray,"Simulationsbild","Moving Window", "Schwellwert Dead-Pixel")
    #plotDataLog(dataArray,"Simulationsbild","Moving Window", "Schwellwert Dead-Pixel")
    np.savetxt(aktuellerPfad + "/messdaten.csv", dataArray, delimiter=";", fmt="%1.3f")

    #np.savetxt(aktuellerPfad + "/Auswertung.csv", ergAuswertung,fmt="%1.3f")
    plotData(dataArray, aktuellerPfad + "/", "Bildserie2_160kV_70uA_mittelwert","Moving Window", "Schwellwert", xBeschriftung="Schwellwert")
    plotDataLog(dataArray, aktuellerPfad + "/", "Bildserie2_160kV_70uA_mittelwert","Moving Window", "Schwellwert", xBeschriftung="Schwellwert")
    #print(ergAuswertung)
    #ergAuswertungPlotten2 = [ [1, 2, 3, 4 ], [4 ,3 ,2,1 ], [1, 2, 3, 4,] ]
    #ergAuswertungPlotten = np.array( [ ergAuswertung[:,5], ergAuswertung[:,4]  ] )
    #ergAuswertungPlotten2 = np.array([xArray,ergAuswertung[:,0], ergAuswertung[:,3]])   # richtigen Werte und falsch erkanten Werte
    #plotData(ergAuswertungPlotten, aktuellerPfad + "/", "Simulationsbild","Moving Window", Parameter="ROC-Kurve" , xBeschriftung="false positive rate", yBeschriftung="true positive rate")
    #plotDataAuswertungLog(ergAuswertungPlotten2, aktuellerPfad + "/", "Simulationsbild","Moving Window", Parameter="Gefundene Fehler" , xBeschriftung="Schwellwert", yBeschriftung="gefundene Fehler")
    #plotDataAuswertung(ergAuswertungPlotten2, aktuellerPfad + "/", "Simulationsbild","Moving Window", Parameter="Gefundene Fehler" , xBeschriftung="Schwellwert", yBeschriftung="gefundene Fehler")    


    """
