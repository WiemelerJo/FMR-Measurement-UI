import numpy as np
import time
import pyvisa
import sys
import pyqtgraph as pg

from typing import List
from datetime import datetime
from configparser import ConfigParser
from devices import Keithley2000, FreqGenerator
from DiodeUI import *
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QTimer, QThread, pyqtSignal

from contextlib import ExitStack

class Worker(QThread):
    dataSig = pyqtSignal(List[float, float])
    errorSig = pyqtSignal(str)

    def __init__(self, Kthly:Keithley2000, FreqGen:FreqGenerator, freqRange:np.array, Umschalter=None, timeout=0.15):
        super(Worker, self).__init__()

        self.Kthly = Kthly
        self.FreqGen = FreqGen
        self.Umschalter = Umschalter

        self.freqRange = freqRange
        self.timeout = 0.15

    def run(self) -> None:
        try:
            for freq in self.freqRange:
                self.FreqGen.setFreq(freq)
                time.sleep(self.timeout)
                val = self.Kthly.sense()

                data = [float(freq), float(val)]
                self.dataSig.emit(data)
        except Exception as e:
            self.errorSig.emit(e)


class MyForm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.pushButtonStart.pressed.connect(self.startCalibration)
        self.Kthly = Keithley2000(stack.enter_context(rm.open_resource(kthlyAddr)))
        self.FreqGen = FreqGenerator(stack.enter_context(rm.open_resource(RSFreq)))

        self.plot = self.ui.graphicsView.plt.plot()

        self.xData = []
        self.yData = []

    def startCalibration(self) -> None:
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

        try:
            self.outputFile.close()
        except:
            pass
        now = datetime.now()
        name = FrequenzListe + "_" + now.strftime("%d-%m-%y_%H-%M-%S") + ".dat"
        self.outputFile = stack.enter_context(open(name, "x"))

        self.thread = Worker(self.Kthly, self.FreqGen, self.freqRange)
        self.thread.start()
        self.thread.dataSig.connect(self.updateData)
        self.thread.errorSig.connect(self.errorSignal)

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
