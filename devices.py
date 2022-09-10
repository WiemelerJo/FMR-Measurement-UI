#import pyvisa
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from Redbox_driver import *



class FreqGenerator(QSerialPort):
    def __init__(self, address):
        super(FreqGenerator, self).__init__()

        print("Frequency generator at port", address)
        self.writeData(b"*IDN?")
        print(self.readData(64))


class HallSensor(QSerialPort):
    def __init__(self, address:str):
        super(HallSensor, self).__init__()

        print("Hall Sensor at Port", address)
        self.writeData(b"*IDN?")
        print(self.readData(64))

    def getField(self) -> float:
        self.writeData(b"F\r")
        return float(self.readData(64).decode("ascii"))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class Polariser:
    def __init__(self):
        try:
            usb3100 = usb_3101()
            # configure channel 0 for 0-10V output
            usb3100.AOutConfig(0, usb3100.UP_10_00V)
            # zero output
            self.channel = 0
            self.gain = usb3100.UP_10_00V
            voltage = 0.0
            value = usb3100.volts(self.gain, voltage)
            usb3100.AOutConfig(self.channel, self.gain)
            usb3100.AOut(self.channel, value, 0)

            self.redbox = usb3100
            self.redbox_init = True

        except Exception as e:
            print(e)

        self.posRange = 0.0  # V
        self.negRange = 5.0  # V

    def setPosRange(self, zeroverify:float):
        # Function uses variable zeroverify to verify,
        # that the powersupply is set to zero before switching the polarisation
        if zeroverify == 0.0:
            value = self.redbox.volts(self.gain, self.posRange)  # Calc calibrated output value
            self.redbox.AOut(self.channel, value, 0)  # Output value
        else:
            print("Powersupply not in IDLE, polarisation will not be switched!")

    def setNegRange(self, zeroverify:float):
        # Function uses variable zeroverify to verify,
        # that the powersupply is set to zero before switching the polarisation
        if zeroverify == 0.0:
            value = self.redbox.volts(self.gain, self.negRange)  # Calc calibrated output value
            self.redbox.AOut(self.channel, value, 0)  # Output value
        else:
            print("Powersupply not in IDLE, polarisation will not be switched!")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.redbox.exit()


class MagnetPowerSupply(QSerialPort):
    def __init__(self, address:str):
        super(MagnetPowerSupply, self).__init__()
        print("Powersupply at Port", address)
        self.writeData(b"*IDN?")
        print(self.readData(64))

        self.writeData(b"SOUR:VOL 0.0\n")
        self.writeData(b"SOUR:CUR 0.0\n")

    def setCurrent(self, val):
        self.writeData(b"SOUR:CUR %f\n" % val)

    def getCurrent(self) -> float:
        self.write(b"SOUR:CUR ?\n")
        val = self.readData(64).decode("ascii")
        return float(val)

    def setVoltage(self, val):
        self.writeData(b"SOUR:VOL %f\n" % val)

    def getVoltage(self) -> float:
        self.write(b"SOUR:VOL ?\n")
        val = self.readData(64).decode("ascii")
        return float(val)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    # Get all available Serial connections
    print(QSerialPortInfo.availablePorts())
