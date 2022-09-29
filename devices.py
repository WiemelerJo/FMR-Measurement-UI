import pyvisa

from scipy.interpolate import interp1d

from mcculw import ul
from mcculw.device_info import DaqDeviceInfo

import zhinst.utils
import zhinst.core as ziPython

class RedLab:
    # The class is very focused on the usage of ME3101 as of usage in polariser and powersupply regultor
    # If I have time and motivation later, I will generalise it more
    def __init__(self, boardNum=0):
        self.boardNum = boardNum
        self.deviceInfo = DaqDeviceInfo(boardNum)
        self.ranges = self.deviceInfo.get_ao_info().supported_ranges

    def VOut(self, channel, value):
        ul.v_out(self.boardNum, channel, self.ranges[0], value)


class Keithley2000():
    def __init__(self, device:pyvisa.Resource):
        print("Keithley2000 connected!")
        print(device.query("*IDN?"))

        self.device = device

    def write(self, com:str):
        self.device.write(com)

    def query(self, com:str) -> str:
        return self.device.query(com)

    def sense(self) -> float:
        return float(self.query('SENSE:DATA:FRESH?').split(",")[0][:-3])


class FreqGenerator():
    def __init__(self, device:pyvisa.Resource):
        print("Frequency generator connected!")
        print(device.query("*IDN?"))

        self.device = device

        self.deviceInit()

    def deviceInit(self):
        self.write(':OUTP1:STAT OFF')
        self.write(f':POW {0}')
        self.write(':POW:MODE CW')

    def write(self, com:str):
        self.device.write(com)

    def query(self, com:str) -> str:
        return self.device.query(com)

    def outputOn(self):
        self.write(':OUTP1:STAT ON')

    def outputOff(self):
        self.write(':OUTP1:STAT OFF')

    def setPower(self,pow:float):
        self.write(f":POW {pow}")

    def getPower(self) -> str:
        return self.query(':POW?')

    def setFreq(self, freq:float):
        self.write(f':SOUR:FREQ:CW {freq} GHz')

    def getFreq(self) -> str:
        return self.query(':SOUR:FREQ?')

    def close(self):
        self.setFreq(1.0)
        self.setPower(1.0)
        self.toggleOff()


class HallSensor():
    def __init__(self, device:pyvisa.Resource):
        print("Hall Sensor connected!\n")

        self.device = device
        self.ranges = {0.3: "R0", 0.6: "R1", 1.2: "R2", 3.0: "R3"} # numbers in Tesla

    def write(self, com:str):
        self.device.write(com)

    def query(self, com:str) -> str:
        return self.device.query(com)

    def getField(self) -> float:
        return float(self.query("F"))*1000

    def switchRange(self, range:float):
        rang = self.ranges[range]
        self.write(rang)


class Polariser:
    def __init__(self, device):


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


class MagnetPowerRedLab(RedLab):
    def __init__(self, calibration:interp1d, channel=2):
        super(MagnetPowerRedLab, self).__init__()
        self.calib = calibration

    def setField(self, desiredField:float):
        #volt = self.calib(desiredField)
        volt = 7.99/0.509 * desiredField
        if volt < 0:
            volt = 0

        print(volt, desiredField)
        self.VOut(2, volt)

class MagnetPowerSupply:
    def __init__(self, device:pyvisa.Resource, calibration:interp1d):
        print("Powersupply connected")
        print(device.query('*IDN?'))

        self.device = device
        self.calib = calibration

        self.deviceInit()

    def deviceInit(self):
        self.write(b"SOUR:VOL 0.0\n")
        self.write(b"SOUR:CUR 0.0\n")

        self.write("SYST:LIM:VOL 230.0, 1")
        self.write("SYST:LIM:CUR 60.0, 1")

    def write(self, com:str):
        self.device.write(com)

    def query(self, com:str) -> str:
        return self.device.query(com)

    def setCurrent(self, val:float):
        self.write("SOUR:CUR %f" % val)

    def getCurrent(self) -> float:
        return float(self.query("SOUR:CUR ?"))

    def setVoltage(self, va:float):
        self.write("SOUR:VOL %f" % val)

    def getVoltage(self) -> float:
        return float(self.query("SOUR:VOL ?"))

    def setField(self, desiredField:float):
        currVal = self.calib(desiredField)
        self.write(f"SOUR:CUR {currVal}")

    def close(self):
        self.write(b"SOUR:VOL 0.0\n")
        self.write(b"SOUR:CUR 0.0\n")


class LockIn_SR830:
    def __init__(self, device:pyvisa.Resource):
        self.device = device

    @property
    def TC(self):
        return self._TC

    @TC.setter
    def TC(self, val: float):
        self.write(f'OFLT {int(val)}')
        self._TC = val

    @property
    def modFreq(self):
        return self._modFreq

    @modFreq.setter
    def modFreq(self, val: float):
        self.write(f"FREQ {val}")  # Set modulation frequency
        self._modFreq = val

    def outputOn(self):
        return

    def outputOff(self):
        return

    def write(self, com: str):
        self.device.write(com)

    def query(self, com: str) -> str:
        return self.device.query(com)

    def getData(self):
        return {"x": float(self.query('OUTP? 1')), "y": float(self.query('OUTP? 2')), 'phase': float(self.query('OUTP? 4'))}


class LockIn_Zurich:
    def __init__(self, dev='dev280'):
        d = zhinst.core.ziDiscovery()
        props = d.get(d.find(dev))
        daq = zhinst.core.ziDAQServer(props['serveraddress'], props['serverport'], props['apilevel'])
        daq.connectDevice(dev, props['interfaces'][0])
        # Enable the demodulator output and set the transfer rate.
        # This ensure the device actually pushes data to the Data Server.
        daq.setInt('/dev280/demods/0/enable', 1) # activate channel 1
        daq.setDouble('/dev280/demods/0/rate', 10e3) # Select sample rate
        daq.subscribe('/dev280/demods/0/sample') # subscribe to output
        daq.setDouble('/dev280/oscs/0/freq', 3000) # Set modulation frequency
        daq.setInt('/dev280/sigouts/0/on', 0) # Toggle output off
        daq.setDouble('/dev280/sigouts/0/amplitudes/6', 0.5) # Set modulation amp to 5V peak to peak
        daq.setInt('/dev280/demods/0/order', 8) # Set low pass filter bandpass to 8th order
        daq.setInt('/dev280/demods/0/sinc', 1) # Activate Sinc filtering
        daq.setInt('/dev280/sigins/0/diff', 0) # Switch differential measurement off
        daq.setInt('/dev280/sigins/0/imp50', 1) # Switch On 50 Ohm input
        daq.setInt('/dev280/sigins/0/ac', 1) # Switch on AC filtering


        daq.setDouble('/dev280/demods/0/timeconstant', 0.1) # TC in s; from rough testing ~0.01 s might be usable

        print("Connected to Zürich Instruments Lock-In!")

        self.daq = daq

    @property
    def TC(self):
        return self._TC

    @TC.setter
    def TC(self, val:float):
        self.daq.setDouble('/dev280/demods/0/timeconstant', val)
        self._TC = val

    @property
    def modFreq(self):
        return self._modFreq

    @modFreq.setter
    def modFreq(self, val:float):
        self.daq.setDouble('/dev280/oscs/0/freq', val)  # Set modulation frequency
        self._modFreq = val

    def outputOff(self):
        self.daq.setInt('/dev280/sigouts/0/on', 0)

    def outputOn(self):
        self.daq.setInt('/dev280/sigouts/0/on', 1)

    def getData(self) -> list:
        return self.daq.getSample("/dev280/demods/0/sample")

    def getX(self) -> float:
        return float(self.daq.getSample("/dev280/demods/0/sample")["x"])

    def getY(self) -> float:
        return float(self.daq.getSample("/dev280/demods/0/sample")["y"])

    def getTheta(self) -> float:
        return float(self.daq.getSample("/dev280/demods/0/sample")["phase"])


if __name__ == '__main__':
    # Get all available Serial connections
    print("Test")
