from mcculw import ul
from mcculw.device_info import DaqDeviceInfo

class RedLab:
    # The class is very focused on the usage of ME3101 as of usage in polariser and powersupply regultor
    # If I have time and motivation later, I will generalise it more
    def __init__(self, boardNum=0):
        self.boardNum = boardNum
        self.deviceInfo = DaqDeviceInfo(boardNum)
        self.ranges = self.deviceInfo.get_ao_info().supported_ranges

    def VOut(self, channel, value):
        ul.v_out(self.boardNum, channel, self.ranges[0], value)

if __name__ == "__main__":
    #print(DaqDeviceInfo(0).get_ao_info().supports_v_out)
    deviceInfo = DaqDeviceInfo(0).get_ao_info()

    board_num = 0
    channel = 1
    ao_range = deviceInfo.supported_ranges[0]
    voltage = 5 # V
    data_val = volts(5)


    ul.v_out(board_num, channel, ao_range,0)

