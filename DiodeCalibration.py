import numpy as np
import time
import pyvisa
import sys
import pyqtgraph as pg

from scipy.signal import argrelextrema

from typing import List
from datetime import datetime
from configparser import ConfigParser
from devices import Keithley2000, FreqGenerator, FreqUmschalter, RedLabDigital
from DiodeUI import *
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QTimer, QThread, pyqtSignal

from contextlib import ExitStack

class Worker(QThread):
    dataSig = pyqtSignal(list)
    errorSig = pyqtSignal(str)

    def __init__(self, Kthly:Keithley2000, FreqGen:FreqGenerator, freqRange:np.array, Umschalter:FreqUmschalter=None, timeout=0.05):
        super(Worker, self).__init__()

        self.Kthly = Kthly
        self.FreqGen = FreqGen
        self.Umschalter = Umschalter

        self.freqRange = freqRange
        self.timeout = timeout

    def run(self) -> None:
        try:
            if self.Umschalter is not None:
                zirkulators = self.Umschalter.freqRanges

            self.FreqGen.outputOn()
            for freq in self.freqRange:
                if self.Umschalter is not None:
                    if not (26.0 < freq < 27.0) and not (freq > 40.0) and not (freq < 8.0):
                        for key, range in zirkulators.items():
                            if (range[0] <= freq <= range[1]):
                                self.Umschalter.setZirkulator(freq)
                self.FreqGen.setFreq(freq)
                time.sleep(self.timeout)
                val = self.Kthly.sense()

                data = [float(freq), float(val)]
                self.dataSig.emit(data)
            self.FreqGen.outputOff()
        except Exception as e:
            self.FreqGen.outputOff()
            self.errorSig.emit(e)


class EqualiseWorker(QThread):
    # This thread is used to equalise the diode voltage to a specific value e.g. -0.3V
    # Creating Freq to dB calibration
    dataSig = pyqtSignal(list)
    errorSig = pyqtSignal(str)

    def __init__(self, Kthly:Keithley2000, FreqGen:FreqGenerator, freqRange:np.array, Umschalter:FreqUmschalter=None, timeout=0.05):
        super(EqualiseWorker, self).__init__()

        self.Kthly = Kthly
        self.FreqGen = FreqGen
        self.Umschalter = Umschalter

        self.freqRange = freqRange # These are the frequencies of the local maxima
        self.timeout = timeout

        self.wantedVolt = -0.3

    def run(self) -> None:
        # Adjusts the diode voltage by changing the output power
        # A linear slope is set between two points of width stepWidth
        # From this slope estimate the power needed for -0.3V
        # Because the output voltage is proportional to the input power in a sqrt law,
        # this calculation needs some iterations till convergence

        stepWidth = 1.0 # in dB
        power = 1.0 # in dB
        voltTreshold = 0.05 # in V

        y0 = self.Kthly.sense()

        self.FreqGen.outputOn()

        try:
            if self.Umschalter is not None:
                zirkulators = self.Umschalter.freqRanges

            for freq in self.freqRange:
                if self.Umschalter is not None:
                    if not (26.0 < freq < 27.0) and not (freq > 40.0) and not (freq < 8.0):
                        for key, range in zirkulators.items():
                            if (range[0] <= freq <= range[1]):
                                self.Umschalter.setZirkulator(freq)

                self.FreqGen.setFreq(freq)
                self.FreqGen.setPower(power)
                volt = self.Kthly.sense()

                while not self.wantedVolt - voltTreshold < volt < self.wantedVolt + voltTreshold:
                    a = volt

                    self.FreqGen.setPower(power + stepWidth)
                    b = self.Kthly.sense()

                    m = (b-a) / ((power+stepWidth) - power)

                    power = (self.wantedVolt - y0) / m
                    self.FreqGen.setPower(power)
                    volt = self.Kthly.sense()
                    print("Power:",power, "Voltage:",volt)

                self.dataSig.emit([freq, power])
                power = 1.0
            self.FreqGen.outputOff()
        except Exception as e:
            self.FreqGen.outputOff()
            self.errorSig.emit(e)


class MyForm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.pushButtonStart.pressed.connect(self.startCalibration)
        self.Kthly = Keithley2000(stack.enter_context(rm.open_resource(kthlyAddr)))
        self.FreqGen = FreqGenerator(stack.enter_context(rm.open_resource(RSFreq)))

        self.FreqGen.outputOff()

        self.plot = self.ui.graphicsView.plt.plot()

    def startCalibration(self) -> None:
        self.xData = []
        self.yData = []

        self.fMin = float(self.ui.spinBoxFrom.value())
        self.fMax = float(self.ui.spinBoxTo.value())
        self.fStep = float(self.ui.spinBoxStep.value())
        self.fPow = float(self.ui.spinBoxPower.value())

        if self.fMin > self.fMax:
            raise ValueError("Minimum frequency is higher than maximum frequency")
        if self.fStep > self.fMax:
            raise ValueError("Frequency step width is too big")

        if self.ui.checkBoxUmschalter.isChecked():
            print("Implement Umschalter idiot!")

        self.freqRange = np.arange(self.fMin, self.fMax, self.fStep)
        self.FreqGen.setPower(self.fPow)  # in dBm

        self.Umschalter = None
        self.useUmschalter = self.ui.checkBoxUmschalter.isChecked()
        if self.useUmschalter:
            self.Umschalter = FreqUmschalter(stack.enter_context(RedLabDigital(1)))

        try:
            self.outputFile.close()
        except:
            pass
        self.now = datetime.now()
        name = "FrequenzListe" + "_" + self.now.strftime("%d-%m-%y_%H-%M-%S") + ".dat"
        self.outputFile = stack.enter_context(open(name, "x"))

        self.thread = Worker(self.Kthly, self.FreqGen, self.freqRange, self.Umschalter)
        self.thread.start()
        self.thread.dataSig.connect(self.updateData)
        self.thread.errorSig.connect(self.errorSignal)
        self.thread.finished.connect(self.voltageScanDone)

    def voltageScanDone(self):
        # This function is called if Worker is finished
        # It searches for local maxima in a window of 8 measurement

        try:
            self.outputFile.close()
        except:
            pass
        name_EQ = "FrequenzListe_dB" + "_" + self.now.strftime("%d-%m-%y_%H-%M-%S") + ".dat"
        name_Maxima = "FrequenzListe_Maxima" + "_" + self.now.strftime("%d-%m-%y_%H-%M-%S") + ".dat"
        self.outputFile = stack.enter_context(open(name_EQ, "x"))

        self.eqXdata = []
        self.eqYdata = []

        findMax = argrelextrema(volt, np.greater, axis=0, order=8)
        self.maximaFreq = self.xData[findMax]
        self.maximaVolt = self.yData[findMax]

        np.savetxt(name_Maxima, np.array([self.maximaFreq, self.maximaFreq]).flatten().transpose())

        self.eqThread = EqualiseWorker(self.Kthly, self.FreqGen, self.freqRange, self.Umschalter)
        self.eqThread.start()
        self.eqThread.dataSig.connect(self.updateEQdata)
        self.eqThread.errorSig.connect(self.errorSignal)

    def updateEQdata(self, data:list):
        self.eqXdata.append(data[0])
        self.eqYdata.append(data[1])
        self.outputFile.write(f"{data[0]}\t{data[1]}\n")

        self.plot.setData(self.eqXdata, self.eqYdata)

    def updateData(self, data: list):
        self.xData.append(data[0]) # Frequency
        self.yData.append(data[1]) # Diode voltage
        self.outputFile.write(f"{data[0]}\t{data[1]}\n")

        self.plot.setData(self.xData, self.yData)

    def errorSignal(self, e: str):
        print(e)


if __name__ == "__main__":
    # Load ini-file (can be modified using the GUI or manually in the presets.ini file)
    config = ConfigParser()
    check = config.read("config.ini")
    if not check:
        raise FileNotFoundError("Could not find config.ini")

    kthlyAddr = config["Keithley 2000"].get("address")
    RSFreq = config["R&S-Frequency Generator"].get("address")

    rm = pyvisa.ResourceManager()
    with ExitStack() as stack:
    #with rm.open_resource(kthlyAddr) as Kthly, rm.open_resource(RSFreq) as FreqGen:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        w = MyForm()
        w.show()
        sys.exit(app.exec_())
