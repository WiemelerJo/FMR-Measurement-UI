import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
import matplotlib

matplotlib.use('Qt5Agg')
from PyQt5 import QtWidgets, QtCore
from PyQt5.Qt import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas, NavigationToolbar2QT as NavigationToolbar


class SpinBox_custom(pg.SpinBox):
    def __init__(self, parent=None):
        super(SpinBox_custom, self).__init__(parent, siPrefix=True, compactHeight=False, dec=True)


class MplCanvas(Canvas):
    def __init__(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        Canvas.__init__(self, self.fig)
        Canvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        Canvas.updateGeometry(self)


class PlotWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)  # Inherit from QWidget
        self.canvas = MplCanvas()  # Create canvas object
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.vbl = QtWidgets.QVBoxLayout()  # Set box for plotting
        self.vbl.addWidget(self.toolbar)
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)


class Colour_Plot(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)  # Inherit from QWidget
        self.layout = QtWidgets.QVBoxLayout()
        self.win = pg.GraphicsLayoutWidget()
        self.view = self.win.addViewBox(0, 1)

        xScale = pg.AxisItem(orientation='bottom', linkView=self.view)
        self.win.addItem(xScale, 1, 1)
        yScale = pg.AxisItem(orientation='left', linkView=self.view)
        self.win.addItem(yScale, 0, 0)

        yScale.setLabel('Magnetic Field', units='mT')
        xScale.setLabel('Angle', units='Deg')

        self.img = pg.ImageItem(border='w')

        self.view.addItem(self.img)

        hist = pg.HistogramLUTItem()
        hist.setImageItem(self.img)
        self.win.addItem(hist, 0, 2)

        self.layout.addWidget(self.win)
        self.setLayout(self.layout)


class Small_Plot(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)  # Inherit from QWidget
        self.layout = QtWidgets.QVBoxLayout()
        self.win = pg.GraphicsLayoutWidget()

        # Z = np.asarray(args[0])
        # self.Z = np.transpose(Z)

        # chunk = args[1]
        # winkel_max = args[2]

        # win = pg.GraphicsLayoutWidget()
        self.view = self.win.addViewBox(0, 1)

        xScale = pg.AxisItem(orientation='bottom', linkView=self.view)
        self.win.addItem(xScale, 1, 1)
        yScale = pg.AxisItem(orientation='left', linkView=self.view)
        self.win.addItem(yScale, 0, 0)

        # self.label = pg.TextItem(text='Hover Event', anchor=(0, 0))
        # self.view.addItem(self.label, ignoreBounds=True)

        yScale.setLabel('Magnetic Field', units='mT')
        xScale.setLabel('Angle', units='Deg')

        self.img = pg.ImageItem(border='w')
        self.img2 = pg.ImageItem(border='w')

        # data = np.array(self.Z)

        # img.setImage(data)
        # self.img.hoverEvent = self.imageHoverEvent

        # self.img.setRect(QtCore.QRect(0, 0, chunk, winkel_max))
        self.view.addItem(self.img)
        self.view.addItem(self.img2)
        self.img2.setZValue(10)

        hist = pg.HistogramLUTItem()
        hist.setImageItem(self.img)
        self.win.addItem(hist, 0, 2)

        self.layout.addWidget(self.win)
        self.setLayout(self.layout)


class Plot_pyqtgraph(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)  # Inherit from QWidget
        self.vbl = QtWidgets.QVBoxLayout()
        self.win = pg.GraphicsLayoutWidget()

        #self.win.setBackground("w")

        self.plt = self.win.addPlot()
        self.plt.setLabel('left', "Lock-In Signal R", units='V')  # Y-Axis
        self.plt.setLabel('bottom', 'Magnetic field', units='T')  # X-Axis
        self.plt.showGrid(True, True)  # Show Grid
        self.plt.setAxisItems({"right": pg.AxisItem("right"), "top": pg.AxisItem("top")})

        self.plt.addLegend()
        self.vbl.addWidget(self.win)
        self.setLayout(self.vbl)

        self.plotX = self.plt.plot()
        self.plotY = self.plt.plot()


class ParameterPlot(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)  # Inherit from QWidget
        self.vbl = QtWidgets.QVBoxLayout()
        self.win = pg.GraphicsLayoutWidget()

        self.plt_slope = self.win.addPlot(title="Slope")
        self.plt_slope.addLegend()
        self.plt_offset = self.win.addPlot(title="Offset")
        self.plt_offset.addLegend()
        self.plt_alpha = self.win.addPlot(title="Alpha")
        self.plt_alpha.addLegend()

        self.win.nextRow()

        self.plt_db = self.win.addPlot(title="Linewidth dB")
        self.plt_db.addLegend()
        self.plt_R = self.win.addPlot(title="Resonance Field R")
        self.plt_R.addLegend()
        self.plt_A = self.win.addPlot(title="Amplitude A")
        self.plt_A.addLegend()

        self.vbl.addWidget(self.win)
        self.setLayout(self.vbl)


class Single_Plot(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)  # Inherit from QWidget
        self.vbl = QtWidgets.QVBoxLayout()
        self.win = pg.GraphicsLayoutWidget()

        self.plt = self.win.addPlot()
        self.plt.setLabel('left', "Resonance Field", units='T')  # Y-Axis
        self.plt.setLabel('bottom', 'Angle', units='Deg')  # X-Axis
        self.plt.showGrid(True, True)  # Show Grid

        self.plt.addLegend()
        self.vbl.addWidget(self.win)
        self.setLayout(self.vbl)


class GradWidget(QtWidgets.QWidget):
    sigGradientChanged = QtCore.Signal(object)

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)  # Inherit from QWidget
        self.vbl = QtWidgets.QVBoxLayout()
        self.w = pg.GradientWidget()
        self.w.loadPreset('magma')  # Magma colormap set as default
        self.vbl.addWidget(self.w)
        self.setLayout(self.vbl)
        self.w.sigGradientChanged.connect(
            self.sigGradientChanged)  # If GradientWidget is changed this will receive a Signal

    def get_colormap(self):
        return self.w.colorMap()

    def print_colormap(self):
        print(self.w.colorMap())


class Popup_View(QtWidgets.QWidget):
    # Standalone Widget; Displayed in popup window
    def __init__(self, *args):
        super().__init__()
        Z = np.asarray(args[0])
        chunk_min = args[1]
        chunk_max = args[2]
        winkel_min = args[3]
        winkel_max = args[4]
        self.Z = np.transpose(Z)

        layout = QtWidgets.QGridLayout()
        # win = pg.GraphicsLayoutWidget()
        win = pg.GraphicsLayoutWidget(show=True)
        # win.setBackground("w")
        view = win.addViewBox(0, 1)

        '''topScale = pg.AxisItem(orientation='top', linkView=view)
    win.addItem(topScale, 0, 1)
    rightScale = pg.AxisItem(orientation='right', linkView=view)
    win.addItem(rightScale, 0, 2)'''

        xScale = pg.AxisItem(orientation='bottom', linkView=view)
        win.addItem(xScale, 1, 1)

        yScale = pg.AxisItem(orientation='left', linkView=view)
        win.addItem(yScale, 0, 0)

        self.label = pg.TextItem(text='Hover Event', anchor=(0, 0))
        view.addItem(self.label, ignoreBounds=True)

        xScale.setLabel('Magnetic Field', units='T')
        yScale.setLabel('Angle', units='Deg')

        img = pg.ImageItem(border='w')
        self.img = img
        data = np.array(self.Z)
        img.setImage(data)
        img.hoverEvent = self.imageHoverEvent

        # QRect (x, y, width, height)
        # x,y are the origin point
        img.setRect(
            QtCore.QRectF(chunk_min / 1000, winkel_min, chunk_max / 1000 - chunk_min / 1000, winkel_max - winkel_min))
        view.addItem(img)

        hist = pg.HistogramLUTItem()
        hist.setImageItem(img)
        win.addItem(hist, 0, 2)

        layout.addWidget(win, 0, 1, 3, 1)
        self.setLayout(layout)

    def imageHoverEvent(self, event):
        """Show the position, pixel, and value under the mouse cursor.
    """
        if event.isExit():
            self.label.setText("")
            return
        pos = event.pos()
        i, j = pos.y(), pos.x()
        i = int(np.clip(i, 0, self.Z.shape[0] - 1))
        j = int(np.clip(j, 0, self.Z.shape[1] - 1))
        val = self.Z[j][i]
        ppos = self.img.mapToParent(pos)
        x, y = ppos.x(), ppos.y()
        self.label.setText("Pos (Field,Angle): %0.1f, %0.1f     Amplitude: %g" % (x, y, val))


class Fit_Log(QtWidgets.QScrollArea):
    def __init__(self, *args, **kwargs):
        QtWidgets.QScrollArea.__init__(self, *args, **kwargs)
        self.setWidgetResizable(True)
        content = QtWidgets.QWidget(self)
        self.setWidget(content)
        lay = QtWidgets.QVBoxLayout(content)
        self.label = QtWidgets.QLabel(content)
        self.label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.label.setWordWrap(True)
        lay.addWidget(self.label)

    def setText(self, text):
        self.text = text
        self.label.setText(self.text)

    def getText(self):
        return self.text


class CustomDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    incrementChanged = QtCore.pyqtSignal(QtWidgets.QDoubleSpinBox)

    def __init__(self):
        super(CustomDoubleSpinBox, self).__init__()

    def wheelEvent(self, event: QtGui.QWheelEvent, *args, **kwargs) -> None:
        angle_delta = event.angleDelta().y()
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        increment = self.singleStep()

        if modifiers == Qt.ControlModifier:

            if angle_delta > 0:
                # Positiver Step
                step = 1
                increment *= 10
            else:
                # Negativer Step
                step = -1
                increment /= 10

            if increment > 1000.0:
                increment = 1000.0
            elif increment < 1e-05:
                increment = 1e-05

            self.setSingleStep(increment)
            # self.incrementChanged.emit(increment)
            self.incrementChanged.emit(self)
        else:
            # Process normal WheelEvent
            if angle_delta > 0:
                # self.setValue(self.value() + increment)
                self.stepUp()
            else:
                # self.setValue(self.value() - increment)
                self.stepDown()


class CustomTable(QtWidgets.QTableWidget):
    def __init__(self, parent):
        super(CustomTable, self).__init__()

    def wheelEvent(self, a0: QtGui.QWheelEvent) -> None:
        pass