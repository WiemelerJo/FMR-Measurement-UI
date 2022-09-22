from devices import RedLab, LockIn_Zurich
import numpy as np
import time
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

RedLab().VOut(2, 0.0)

app = pg.mkQApp("Plotting Example")
#mw = QtWidgets.QMainWindow()
#mw.resize(800,800)
win = pg.GraphicsLayoutWidget(show=True)
win.resize(1000,600)

p = win.addPlot()
curve = p.plot()



RedLab = RedLab()
LockIn = LockIn_Zurich()

vMin = 1.5
vMax = 3.5
vStep = 0.005
v_range = np.arange(vMin, vMax, vStep)

LockIn.TC = 0.1
LockIn.outputOn()

data = []
ptr = 0

def update():
    global curve, data, ptr, p, LockIn

    RedLab.VOut(2, v_range[ptr])
    time.sleep(LockIn.TC * 7)
    data.append(LockIn.getX())
    curve.setData(data)
    ptr += 1

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)

if __name__ == '__main__':
    pg.exec()