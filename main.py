import sys
import math
import numpy as np
import time
from configparser import ConfigParser
#import pyvisa
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QTimer
from mainWindow import *
from devices import *
from scipy.interpolate import interp1d
from customwidgets import *


class MyForm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.angle = 0

        self.initDevices()
        self.ui.pushButton.clicked.connect(self.setDefaultConfig)
        self.ui.fieldfromval.editingFinished.connect(self.setFieldRange)
        self.ui.fieldtoval.editingFinished.connect(self.setFieldRange)

        self.ui.comboBox.currentIndex.connect(self.changeMeasurementType)

        self.fieldTimer = QTimer()
        self.fieldTimer.timeout.connect(self.getField)
        self.fieldTimer.start(250)


        # self.angleTimer = QTimer()
        # self.angleTimer.timeout.connect(self.setAngle)
        # self.angleTimer.start(250)
        #self.setField(500)

    def initDevices(self):
        # Load ini-file (can be modified using the GUI or manually in the presets.ini file)
        config = ConfigParser()

        check = config.read("config.ini")

        if not check:
            print("Could not find config.ini\nCreating config.ini with default settings!")
            self.setDefaultConfig()
            config.read("config.ini")

        self.config = config

        #______remove for testing and usage
        self.magnetDevice = MagnetPowerSupply(self.config["Magnet Powersupply"].get("address"))
        self.hallDevice = HallSensor(self.config["Hall Sensor"].get("address"))
        self.polarsierDevice = Polariser()
        #print(config["Magnet Powersupply"].get("address"))

    def changeMeasurementType(self, *args, **kwargs):
        # Combobox index
        # 0: Field Sweep
        # 1: Frequency Sweep
        # 2: Ang-Dep-Field-Domain
        # 3: Ang-Dep-Freq-Domain
        self.measType = self.ui.comboBox.currentIndex()
        self.checkNeededDevices()

    def checkNeededDevices(self):
        # Function to check if necessary devices are present and working
        if self.measType == 0:


    def calibrateMagnet(self):
        # Increase current from 0A to max, in defined steps, wait 1 second to stabelise the field, then read field value
        # save data file
        self.fieldTimer.stop()

        self.magCalibStep = 0.1 # [A]
        maxCurrent = 60 # [A]

        calib = [[], []]

        for curr in range(0, maxCurrent, self.magCalibStep):
            self.magnetDevice.setCurrent(curr)
            calib[0].append(curr)
            field = self.hallDevice.getField()
            calib[1].append(field)

            #self.calibration = interp1d(calib[0], calib[1])

            np.savetxt("MagneticFieldCalibration.dat", np.array(calib).transpose())

        self.fieldTimer.start(250)

    def loadFieldCalibration(self):
        calib_raw = np.loadtxt("MagneticFieldCalibration.dat")
        self.calibration = interp1d(calib_raw[0], calib_raw[1]) # field(ampere)

    def setFieldRange(self):
        minField = self.ui.fieldtoval.text()
        maxField = self.ui.fieldfromval.text()

        try:
            self.fieldRange = (float(minField), float(maxField))

            fieldStep = self.ui.dBspinboxFieldIncr.value()
            sweepRange = minField - maxField
            measPoints = sweepRange/fieldStep
            self.ui.calcsteplabel.setText("= " + str(measPoints) + "Points")
        except Exception as e:
            pass

    def getField(self):
        # Get field value from Hall sensor
        # Sense command:
        #         "F\r"
        self.field = self.hallDevice.getField()
        self.ui.fieldlabel.setText(str(self.field) + " [mT]")

    def setField(self, val: float) -> float:
        # This function changes the magnetic field to value "val" according to the calibration,
        # then reads out the tesla meter and returns this value
        # Output commands (termination character "\n"):
        #         SOUR:VOL 0.0\n
        #         SOUR:CUR 0.0\n
        #         SOUR:CUR:NEG 0.0\n

        self.ui.fieldlabel.setStyleSheet("background-color: red")

        # First get current field value and determine the distance to the next field step "val"
        # if distance bigger than maximum field rate (default: 100 mT/s) safely change the field according to field rate

        #self.field = self.getField()        # Read field value

        # Amount of steps needed to safely reach desired field; math.ceil() rounds up to smallest bigger integer
        steps = math.ceil(
            abs( self.field - val ) / float( self.config["Magnet Powersupply"].get("Maximum field rate [mT/s]") ) )

        for fieldStep in np.linspace(self.field, val, num=10*steps+1):
            self.magnetDevice.setCurrent( self.calibration(fieldStep))
            time.sleep(0.1)

        self.ui.fieldlabel.setStyleSheet("background-color: lime")

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
            "Maximum field rate [mT/s]": 100
        }

        config["Lock-In"] = {
            "Time Constant [ms]": 300,
            "Sensitivity [mV]": 1,
            "Modulation Frequency [kHz]": 13
        }

        config["R&S-Frequency Generator"] = {
            "address": 8
        }

        config["Hall Sensor"] = {
            "address": 14
        }

        with open("config.ini", "w") as f:
            config.write(f)

if __name__=="__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MyForm()
    w.show()
    sys.exit(app.exec_())
