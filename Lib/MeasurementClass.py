import json

import numpy as np
import pandas as pd

try:
    from lib.Spectra import Spectra
except ModuleNotFoundError:
    from Spectra import Spectra
from typing import List, Union


class Measurement(list):
    # Advanced List to store, load, save and maybe modify Spectra objects
    # Callable, by Measurement(int, int, ..) of unspecific amount of int
    # or Measurement([int, int, int, ..]) of list int
    # __call__ will sort self before spitting out desired spectra

    def __init__(self, FMR_type='angdep', anisotropy=None, damping=None, g_factor=None, magnetisation=None):
        super(Measurement, self).__init__()
        self.FMR_type = FMR_type  # Either angdep, or freqdep
        self.anisotropy = anisotropy
        self.damping = damping
        self.g_factor = g_factor
        self.magnetisation = magnetisation

    def loadFitFile(self):
        # Load previously fitted and saved file
        self.clear()
        raise NotImplementedError

    @staticmethod
    def checkHeader(path: str) -> int:
        # Search the header and count unusable columns
        with open(path, 'r') as f:
            line_index = 1
            no_header_cnt = 0
            skip_value = 0
            while True:
                if line_index > 20 or no_header_cnt > 3:
                    # If read more than 20 lines or found more than 3 line without letters, break loop
                    break

                temp_line = f.readline()

                for i in temp_line:
                    if i not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '+', '\n', '.', ' ']:
                        # Find character different from list and declare a possible found header for this line
                        # print('Found possible Header', i, line_index)
                        skip_value = line_index
                        no_header_cnt = 0
                        break
                    elif i != ' ':  # Check if found data just a space, if not, then we have data.
                        # If no_header_cnt is bigger than 3, we found the header.
                        # skip_value then defines how many rows to skip
                        # print(no_header_cnt, i)
                        no_header_cnt += 1
                        break
                line_index += 1
        return skip_value

    def loadMeasurement(self, path: str):
        # Load new measurement from file
        self.clear()

        if path[-3:] == 'DTA' or path[-3:] == 'par':
            path = self.convert_bruker_to_ascii(path)

        row_skip = self.checkHeader(path)
        df = pd.read_csv(path, names=['index', 'Field [G]', 'Sample Angle [deg]', 'Intensity []']
                         , skiprows=row_skip, sep='\s+')

        counts = np.unique(df['Field [G]'].to_numpy()).shape[0]
        # Counts is equivalent to the  number of Magnetic field steps in the measurement e.g. 1024,2048,4096....
        chunksize = int(df.shape[0] / counts)  # Number of measurements with length counts

        FieldData = np.split(np.true_divide(df['Field [G]'].to_numpy(), 10000), chunksize)
        AmplData = np.split(df['Intensity []'].to_numpy(), chunksize)
        AngleData = np.split(df['Sample Angle [deg]'].to_numpy(), chunksize)

        for n in range(chunksize):
            spec = Spectra(FieldData[n], AmplData[n], AngleData[n][0], n)
            self.add(spec)

    def convert_bruker_to_ascii(self, path):
        raise NotImplementedError

    def dumps(self):
        pre_dict = {'FMR_type': self.FMR_type, 'anisotropy': self.anisotropy, 'damping': self.damping,
                    'g-factor': self.g_factor, 'magnetisation': self.magnetisation}

        spectra_json = {spectra.spectra_index: spectra.dumps() for spectra in self}
        dict_to_json = pre_dict | spectra_json
        return json.dumps(dict_to_json)

    def add(self, spectra: Spectra):
        # Add spectra to existing Measurement object
        index = spectra.spectra_index
        if not self.isIndexed(spectra):
            self.insert(index, spectra)
        else:
            raise IndexError("Spectra with same Index already in use!\nSpectra:" + str(index))

    def append(self, spectra: Spectra) -> None:
        self.add(spectra)

    def delete(self, item: Union[Spectra, int]):
        # item:int deletes list index not spectra index!

        if item == type(int):
            self.pop(item)
        else:
            for spec in self:
                if spec == item:
                    self.remove(spec)

    def isIndexed(self, spectra: Spectra):
        # Look up if spectra with index spectra.spectra_index is already indexed in self
        # index = spectra.spectra_index
        try:
            indexed_spec = self[spectra.spectra_index]
            if indexed_spec == spectra:
                return True
            return False
        except IndexError:
            return False

    def __add__(self, other: Spectra):
        if isinstance(other, Spectra):
            self.add(other)
        else:
            raise NotImplementedError('Operation __add__ not implemented for object type: {}'.format(type(other)))

    def __str__(self) -> str:
        # return str([i.spectra_index for i in self])
        length = len(self)
        if length == 0:
            return "No Spectra indexed!"
        return str(length) + " Spectra indexed!"

    def __call__(self, *args, **kwargs) -> List[Spectra]:
        if args:
            self.sort()
            rtn_stmnt = []
            for arg in args:
                if isinstance(arg, int):
                    rtn_stmnt.append(self[arg])
                elif isinstance(arg, list):
                    for ar in arg:
                        rtn_stmnt.append(self[ar])
            return rtn_stmnt
        elif kwargs:
            raise NotImplementedError("Kwargs not Implemented")
        print("Supply argument of type Measurement(int, int, int, ...) or Measurement([int, int, int])!")


if __name__ == '__main__':
    meas1 = Measurement()

    for i in range(0, 360):
        meas1.append(Spectra(np.arange(0, 4096, 1), np.arange(0, 4096, 1), float(i), int(i)))

    print(len(meas1))
    meas1.loadMeasurement(r"C:\Users\Jonas\Desktop\exp_data - Kopie - Kopie.dat")
    print(len(meas1))

    print(meas1.dumps())
    # random.shuffle(meas1)
    # print(meas1(1 ,2, 3))
    # print(max(meas1).spectra_index)
    # print(meas1.isIndexed(test_spec))
