import sys
import math
import numpy as np
import time
from configparser import ConfigParser
#import pyvisa
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QTimer
from mainWindow import *


class MyForm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.field = 0
        self.angle = 0

        self.initDevices()
        self.ui.pushButton.clicked.connect(self.setDefaultConfig)

        self.fieldTimer = QTimer()
        self.fieldTimer.timeout.connect(self.getField)
        self.fieldTimer.start(250)

        # self.angleTimer = QTimer()
        # self.angleTimer.timeout.connect(self.setAngle)
        # self.angleTimer.start(250)
        self.setField(500)

    def initDevices(self):
        # Load ini-file (can be modified using the GUI or manually in the presets.ini file)
        config = ConfigParser()

        check = config.read("config.ini")

        if not check:
            print("Could not find config.ini\nCreating config.ini with default settings!")
            self.setDefaultConfig()
            config.read("config.ini")

        self.config = config

        #print(config["Magnet Powersupply"].get("address"))

    def getField(self):
        # Get field value from Hall sensor
        # Sense command:
        #         "F\r"
        self.field += 1
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
            abs( self.field - val ) / float( self.config["Magnet Powersupply"].get("Maximum field rate [mT/s]") )
        )

        for fieldStep in np.linspace(self.field, val, num=steps+1):
            print(fieldStep)
            self.field = fieldStep
            #set field: to fieldStep
            time.sleep(1)

        self.ui.fieldlabel.setStyleSheet("background-color: lime")

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
