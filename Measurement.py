import numpy as np
import math
import pyvisa
import time

from PyQt5.QtCore import QThread, pyqtSignal, QObject


class SweepMeasurement(QThread):
    dataOutSig = pyqtSignal(dict)
    fieldMoveSig = pyqtSignal(float)
    changeParasSig = pyqtSignal(dict)
    meterUsageSig = pyqtSignal(bool)
    errorSig = pyqtSignal(str)
    startSig = pyqtSignal()
    doneSig = pyqtSignal()

    def __init__(self, MagnetPWR:pyvisa.Resource, TeslaMeter:pyvisa.Resource,
                        FreqGen:pyvisa.Resource, LockIn, infos:dict):
        super(SweepMeasurement, self).__init__()
        
        self.pause = False

        self.changeParasSig.connect(self.setUpParas)

        self.setUpParas(infos)

        self.Magnet = MagnetPWR
        self.TeslaM = TeslaMeter
        self.LockIn = LockIn
        self.FreqGen = FreqGen

        if self.sweepDirection == "up":
            self.sweepRange = np.arange(self.range[0], self.range[1], self.stepSize)
        elif self.sweepDirection == "down":
            self.sweepRange = np.arange(self.range[1], self.range[0], -self.stepSize)
        #print(self.range, self.sweepRange, self.stepSize)
        #self.setFieldSafe(self.sweepRange[0]/1000) # Safely move field to start val

    def run(self):
        def setFieldSafe(val):
            print("Setting field save!")
            # drive the field to value according to maxFieldSpeed
            # First get current field value and determine the distance to the next field step "val"
            # if distance bigger than maximum field rate (default: 100 mT/s) safely change the field according to field rate
            self.meterUsageSig.emit(True)

            self.field = self.TeslaM.getField()  # Read field value

            self.meterUsageSig.emit(False)

            # Amount of steps needed to safely reach desired field val; math.ceil() rounds up to smallest bigger integer
            steps = math.ceil(abs(self.field - val) / self.maxFieldSpeed)
            print("Number ov steps", steps)

            for fieldStep in np.linspace(self.field, val, num=10*steps+1):
                self.fieldMoveSig.emit(fieldStep / 1000)
                self.Magnet.setField(fieldStep / 1000)
                print("Set field to:", fieldStep)
                time.sleep(0.1)

        setFieldSafe(self.sweepRange[0] / 1000)  # Safely move field to start val
        try:
            self.meterUsageSig.emit(True)
            #self.fieldMoveSig.emit(True)

            self.LockIn.TC = self.TC
            self.LockIn.modFreq = self.ModFreq
            self.LockIn.outputOn()

            self.FreqGen.setFreq(self.MWFreq)
            self.FreqGen.setPower(self.MWPow)
            self.FreqGen.outputOn()

            dataOut = {}
            for fieldStep in self.sweepRange:
                if self.pause:
                    while self.pause: time.sleep(0.2)
                self.Magnet.setField(fieldStep/1000)
                self.fieldMoveSig.emit(fieldStep/1000)
                time.sleep( 7 * self.TC )
                field = self.TeslaM.getField()
                data = self.LockIn.getData()

                dataOut["data"] = data
                dataOut["field"] = field
                self.dataOutSig.emit(dataOut)

            self.LockIn.outputOff()
            self.FreqGen.outputOff()

            setFieldSafe(0.0)

            #self.fieldMoveSig.emit(False)
            self.meterUsageSig.emit(False)
        except Exception as e:
            self.errorSig.emit(e)

    def setUpParas(self, infos:dict):
        self.range = infos.get("range")
        self.stepSize = float(infos.get("stepSize"))
        self.TC = float(infos.get("TC"))
        self.ModFreq = float(infos.get("ModFreq"))
        self.avrg = int(infos.get("avrg"))
        self.maxFieldSpeed = float(infos.get("maxFieldSpeed"))
        self.calib = infos.get("calibration")
        self.sweepDirection = infos.get("sweepDirection")
        self.MWFreq = float(infos.get("MWFreq"))
        self.MWPow = float(infos.get("MWPow"))

    def setFieldSafe(self, val):
        # drive the field to value according to maxFieldSpeed
        # First get current field value and determine the distance to the next field step "val"
        # if distance bigger than maximum field rate (default: 100 mT/s) safely change the field according to field rate

        self.meterUsageSig.emit(True)

        self.field = self.TeslaM.getField()   # Read field value

        self.meterUsageSig.emit(False)

        # Amount of steps needed to safely reach desired field val; math.ceil() rounds up to smallest bigger integer
        steps = math.ceil( abs( self.field - val ) / self.maxFieldSpeed )

        #self.fieldMoveSig.emit(True)

        for fieldStep in np.linspace(self.field, val, num=steps):
            self.fieldMoveSig.emit(fieldStep/1000)
            self.Magnet.setField(fieldStep/1000)
            time.sleep(0.1)

        #self.fieldMoveSig.emit(False)

    def sweep(self):
        self.meterUsageSig.emit(True)
        #self.fieldMoveSig.emit(True)

        self.LockIn.TC = self.TC
        self.LockIn.modFreq = self.ModFreq
        self.LockIn.outputOn()

        self.FreqGen.setFreq(self.MWFreq)
        self.FreqGen.setPower(self.MWPow)
        self.FreqGen.outputOn()

        dataOut = {}
        for fieldStep in self.sweepRange:
            if self.pause:
                while self.pause: time.sleep(0.2)
            self.Magnet.setField(fieldStep/1000)
            self.fieldMoveSig.emit(fieldStep/1000)
            time.sleep( 7 * self.TC )
            field = self.TeslaM.getField()
            data = self.LockIn.getData()

            dataOut["data"] = data
            dataOut["field"] = field
            self.dataOutSig.emit(dataOut)

        self.LockIn.outputOff()
        self.FreqGen.outputOff()

        self.setFieldSafe(0.0)

        #self.fieldMoveSig.emit(False)
        self.meterUsageSig.emit(False)


class AngularDependence(SweepMeasurement):
    def __init__(self, MagnetPWR:pyvisa.Resource, TeslaMeter:pyvisa.Resource,
                        FreqGen:pyvisa.Resource, LockIn, infos:dict):
        super(AngularDependence, self).__init__(MagnetPWR, TeslaMeter, FreqGen, LockIn, infos)

if __name__ == "__main__":
    AngularDependence(1, 2, 3, 5, 4)
