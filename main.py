import sys
import math
import numpy as np
import time
from configparser import ConfigParser
import pyvisa

from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QTimer, QThread
from mainWindow import *
from devices import *
from scipy.interpolate import interp1d
from datetime import datetime
from array import array
from customwidgets import *

from Measurement import SweepMeasurement, FreqSweepMeasurement

from contextlib import ExitStack


class MyForm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.angle = 0
        self.desiredField = 0.0
        self.field = 0.0

        self.measurementTypes = {0: self.startFieldSweep, 1: self.startFreqSweep,
                                 2: self.startFieldAngDep, 3: self.startFreqAngDep}

        self.sweepDirections = {0: "up", 1: "down"}

        self.initDevices()
        self.ui.pushButton.clicked.connect(self.setDefaultConfig)
        self.ui.fieldfromval.editingFinished.connect(self.setFieldRange)
        self.ui.fieldtoval.editingFinished.connect(self.setFieldRange)
        self.ui.dBspinboxFieldIncr.valueChanged.connect(self.setFieldRange)
        self.ui.stopbutton.clicked.connect(self.stopThread)

        self.ui.comboBox.currentIndexChanged.connect(self.changeMeasurementType)
        self.changeMeasurementType()

        self.fieldTimer = QTimer()
        self.fieldTimer.timeout.connect(self.timerGetField)
        self.fieldTimer.start(250)

        self.checkDesiredFieldTimer = QTimer()
        self.checkDesiredFieldTimer.timeout.connect(self.timerCheckDesiredField)
        self.checkDesiredFieldTimer.start(100)

        # self.angleTimer = QTimer()
        # self.angleTimer.timeout.connect(self.setAngle)
        # self.angleTimer.start(250)
        #self.setField(500)

        self.xDataPen = pg.mkPen(color="g")
        self.yDataPen = pg.mkPen(color="r")
        self.plotXState = True
        self.plotYState = True

    def initDevices(self):
        # Load ini-file (can be modified using the GUI or manually in the presets.ini file)
        config = ConfigParser()

        check = config.read("config.ini")

        if not check:
            print("Could not find config.ini\nCreating config.ini with default settings!")
            self.setDefaultConfig()
            config.read("config.ini")

        self.config = config
        self.loadFieldCalibration()

        self.TslMeter = HallSensor(stack.enter_context(rm.open_resource(self.config["Hall Sensor"].get("address"))))
        #self.RedLab = RedLab()
        #self.LockIn = LockIn_SR830(stack.enter_context(rm.open_resource('GPIB0::8::INSTR')))

        self.FreqGen = FreqGenerator(stack.enter_context(rm.open_resource(self.config["R&S-Frequency Generator"].get("address"))))
        #self.Kthly = Keithley2000(stack.enter_context(rm.open_resource(self.config["Keithley 2000"].get("address"))))

        self.LockIn = LockIn_Zurich()
        self.Magnet = MagnetPowerRedLab(self.calibration) #MagnetPowerSupply(self.config["Magnet Powersupply"].get("address"))
        self.setField(0.0)

    def changeMeasurementType(self):
        # Combobox index
        # 0: Field Sweep
        # 1: Frequency Sweep
        # 2: Ang-Dep-Field-Domain
        # 3: Ang-Dep-Freq-Domain
        measType = self.ui.comboBox.currentIndex()
        self.ui.startbutton.pressed.connect(self.measurementTypes[measType])

        self.ui.sampleAngleTo.setEnabled(False)
        self.ui.sampleAngleFrom.setEnabled(False)
        self.ui.spinBoxAngleStep.setEnabled(False)
        self.ui.frequenciesTo.setEnabled(False)
        self.ui.frequenciesFrom.setEnabled(False)
        self.ui.spinBoxFreqStep.setEnabled(False)

        if measType == 1:
            # FreqSweep
            self.ui.frequenciesTo.setEnabled(True)
            self.ui.frequenciesFrom.setEnabled(True)
            self.ui.spinBoxFreqStep.setEnabled(True)
        elif measType == 2:
            # Angdep
            self.ui.sampleAngleTo.setEnabled(True)
            self.ui.sampleAngleFrom.setEnabled(True)
            self.ui.spinBoxAngleStep.setEnabled(True)
        elif measType == 3:
            # FreqAngdep
            self.ui.sampleAngleTo.setEnabled(True)
            self.ui.sampleAngleFrom.setEnabled(True)
            self.ui.spinBoxAngleStep.setEnabled(True)
            self.ui.frequenciesTo.setEnabled(True)
            self.ui.frequenciesFrom.setEnabled(True)
            self.ui.spinBoxFreqStep.setEnabled(True)
        #self.checkNeededDevices()
        self.measType = measType

    def checkNeededDevices(self):
        # Function to check if necessary devices are present and working
        if self.measType == 0:
            return

    def loadFieldCalibration(self):
        calib_raw = np.loadtxt("calibMagnet.dat")
        self.calibration = interp1d(calib_raw[:,2], calib_raw[:,0]) # Volt(field)
        #print("Wrong calibration!!! Testing output for now!")

    def setFieldRange(self):
        try:
            minField = float(self.ui.fieldfromval.text())
            maxField = float(self.ui.fieldtoval.text())

            self.fieldRange = (minField, maxField)

            self.fieldStep = float(self.ui.dBspinboxFieldIncr.value())
            sweepRange = abs(maxField - minField)
            self.measPoints = int(sweepRange/self.fieldStep)
            self.ui.calcsteplabel.setText("= " + str(self.measPoints) + "Points")
        except ValueError:
            pass
        except Exception as e:
            print(e)
            pass

    def timerGetField(self):
        # Get field value from Hall sensor
        # Sense command:
        #         "F\r"
        #self.field = self.hallDevice.getField()
        self.field = self.TslMeter.getField()
        self.ui.fieldlabel.setText(str(self.field) + " [mT]")

    def timerCheckDesiredField(self):
        diff = abs(self.field - self.desiredField)
        if diff > 1.5:
            self.ui.fieldlabel.setStyleSheet("background-color: red")
        else:
            self.ui.fieldlabel.setStyleSheet("background-color: lime")

    def toggleFieldTimer(self, inUse:bool):
        if inUse:
            self.fieldTimer.stop()
        elif not inUse:
            self.fieldTimer.start()

    def isFieldMoving(self, val:bool):
        self.desiredField = val*1000

    def gatherInfos(self):
        print("---------------gatherInfos is not correctly implemented!---------------")
        self.infos = {}
        self.infos["range"] = self.fieldRange
        self.infos["stepSize"] = self.fieldStep
        print("TimeConstant" ,float(self.ui.spinBoxTC.value()))
        self.infos["TC"] = float(self.ui.spinBoxTC.value())
        self.infos["ModFreq"] = float(self.ui.spinBoxModFreq.value())
        self.infos["avrg"] = 1
        self.infos["maxFieldSpeed"] = self.config["Magnet Powersupply"].get("Maximum field rate [mT/s]")
        self.infos["calibration"] = self.calibration
        self.infos["sweepDirection"] = self.sweepDirections[self.ui.comboBox_sweepDirection.currentIndex()]
        self.infos["MWFreq"] = 10 # GHz
        self.infos["MWPow"] = 13 # dBm


        self.infos["FreqSweep"] = [] # List of driven Frequencies

    def measThreadTogglePause(self):
        if self.ui.pausebutton.text() == "Pause":
            self.measThread.pause = True
            self.ui.pausebutton.setText("Resume")
        else:
            self.measThread.pause = False
            self.ui.pausebutton.setText("Pause")

    def errorMSG(self, *args):
        print(args)

    def startFieldSweep(self):
        self.gatherInfos()
        self.measThread = SweepMeasurement(self.Magnet, self.TslMeter, self.FreqGen, self.LockIn, self.infos)

        self.measThread.start()
        self.measThread.dataOutSig.connect(self.getSweepData)
        self.measThread.fieldMoveSig.connect(self.isFieldMoving)
        self.measThread.meterUsageSig.connect(self.toggleFieldTimer)
        self.measThread.errorSig.connect(self.errorMSG)

        self.ui.progressBar.setMaximum(99)

        self.newDataFile("FieldSweep")
        self.outputFile.write("Magnetic Field [T]\tX-Channel\tY-Channel\tPhase\n")
        self.clearPlotData()

    def stopThread(self):
        if self.measThread.isRunning():
            self.measThread.terminate()
            self.toggleFieldTimer(False)
            self.outputFile.close()
            self.LockIn.outputOff()
            self.FreqGen.outputOff()
            self.FreqGen.setFreq(5.0)
            self.FreqGen.setPower(5.0)
            self.setField(0.0)

    def startFreqSweep(self):
        self.gatherInfos()

        self.measThread = FreqSweepMeasurement(self.Magnet, self.TslMeter,self.LockIn, self.FreqGen, self.infos)
        self.measThread.start()
        self.measThread.dataOutSig.connect(self.getFreqSweepData)
        self.measThread.fieldMoveSig.connect(self.isFieldMoving)
        self.measThread.meterUsageSig.connect(self.toggleFieldTimer)
        self.measThread.errorSig.connect(self.errorMSG)

        self.ui.progressBar.setMaximum(99)

        self.newDataFile("FreqSweep")
        self.outputFile.write("Magnetic Field [T]\tX-Channel\tY-Channel\tPhase\tFrequency [GHz]\n")
        self.clearPlotData()

    def startFieldAngDep(self):
        return

    def startFreqAngDep(self):
        return

    def clearPlotData(self):
        self.plotData = {}

        self.plotData["x"] = array("d") # One could also use list() here, array() just seems to be more convenient
        self.plotData["y"] = array("d")
        self.plotData["phase"] = array("d")
        self.plotData["field"] = array("d")

        self.ui.graphicsView.vb.plot1CheckBox.stateChanged.connect(self.togglePlot1)
        self.ui.graphicsView.vb.plot2CheckBox.stateChanged.connect(self.togglePlot2)

    def togglePlot1(self, *args):
        if args[0]:
            self.ui.graphicsView.plotX.setData(self.plotData["field"], self.plotData["x"]
                                               , pen=self.xDataPen, symbolPen=None, symbolSize=4, symbolBrush=('g'))
            self.plotXState = True
        else:
            self.ui.graphicsView.plotX.clear()
            self.plotXState = False

    def togglePlot2(self, *args):
        if args[0]:
            self.ui.graphicsView.plotY.setData(self.plotData["field"], self.plotData["y"]
                                               , pen=self.yDataPen, symbolPen=None, symbolSize=4, symbolBrush=('r'))
            self.plotYState = True
        else:
            self.ui.graphicsView.plotY.clear()
            self.plotYState = False

    def getSweepData(self, data:dict):
        self.field = data["field"]
        self.ui.fieldlabel.setText(str(self.field) + " [mT]")

        data = data["data"]
        self.plotData["field"].append(self.field/1000)
        self.plotData["x"].append(float(data["x"]))
        self.plotData["y"].append(float(data["y"]))
        self.plotData["phase"].append(float(data["phase"]))

        self.outputFile.write(f"{self.field}\t{self.plotData['x'][-1]}\t{self.plotData['y'][-1]}\t{self.plotData['phase'][-1]}\n")

        self.updatePlot()

    def getFreqSweepData(self, data:dict):
        self.field = data["field"]
        self.ui.fieldlabel.setText(str(self.field) + " [mT]")

        data = data["data"]
        self.plotData["field"].append(self.field/1000)
        self.plotData["x"].append(float(data["x"]))
        self.plotData["y"].append(float(data["y"]))
        self.plotData["phase"].append(float(data["phase"]))

        self.outputFile.write(f"{self.field}\t{self.plotData['x'][-1]}\t{self.plotData['y'][-1]}\t{self.plotData['phase'][-1]}\t{data['freq']}\n")

        self.updatePlot()

    def updatePlot(self):
        # Add functionality to choose what to plot

        if self.plotXState:
            self.ui.graphicsView.plotX.setData(self.plotData["field"], self.plotData["x"]
                                               , pen=self.xDataPen, symbolPen=None, symbolSize=4, symbolBrush=('g'))

        if self.plotYState:
            self.ui.graphicsView.plotY.setData(self.plotData["field"], self.plotData["y"]
                                               , pen=self.yDataPen, symbolPen=None, symbolSize=4, symbolBrush=('r'))

    def newDataFile(self, measType:str):
        try:
            self.outputFile.close()
        except:
            pass
        now = datetime.now()
        name = measType + "_" + now.strftime("%d-%m-%y_%H-%M-%S") + ".dat"
        self.outputFile = stack.enter_context(open(name, "x"))

    def setField(self, val:float):
        self.desiredField = val
        self.fieldWorker = FieldMove(self.Magnet,self.calibration, self.field, val, channel=2)
        self.fieldWorker.start()

    def changePolarisation(self, pol:str):
        # Change polaristaion of the field
        # To switch the polarisation the field must be at 0.0 -> powersupply in idle
        self.setField(0.0)

        if pol == "negative":
            self.polarsierDevice.setNegRange(self.field)
        elif pol == "positive":
            self.polarsierDevice.setPosRange(self.field)
        else:
            raise ValueError("Unkown polarisation state")

    def setAngle(self):
        self.angle += 1
        self.ui.anglelabel.setText(str(self.angle) + " [°]")

    def setDefaultConfig(self):
        # Reset config file to default; also used for debugging
        config = ConfigParser()
        config["Magnet Powersupply"] = {
            "address": 1,
            "Voltage Limit [V]": 230,
            "Current Limit [A]": 60,
            "Allow negative current?": False,
            "Calibration-File": "magnet-calib.dat",
            "Maximum field rate [mT/s]": 50
        }

        config["Lock-In"] = {
            "Time Constant [ms]": 100,
            "Sensitivity [mV]": 1,
            "Modulation Frequency [kHz]": 3
        }

        config["R&S-Frequency Generator"] = {
            "address": 'GPIB0::28::INSTR'
        }

        config["Hall Sensor"] = {
            "address": 'GPIB0::10::INSTR'
        }

        config["Keithley 2000"] = {
            "address": 'GPIB0::16::INSTR'
        }

        with open("config.ini", "w") as f:
            config.write(f)


if __name__=="__main__":
    rm = pyvisa.ResourceManager()

    with ExitStack() as stack:


        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        w = MyForm()
        w.show()
        sys.exit(app.exec_())
