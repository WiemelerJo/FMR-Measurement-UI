import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, \
    QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt
import pandas as pd

#Widget adapted from https://learndataanalysis.org/source-code-how-to-import-excel-data-to-a-qtablewidget-pyqt6-tutorial/


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.window_width, self.window_height = 700, 500
        self.resize(self.window_width, self.window_height)
        self.setWindowTitle('Load Excel (or CSV) data to QTableWidget')

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.button = QPushButton('&Load Data')
        self.button.clicked.connect(
            lambda _, xl_path=excel_file_path, sheet_name=worksheet_name: self.loadExcelData(xl_path, sheet_name))
        layout.addWidget(self.button)

        self.debugButton = QPushButton('&Debug')
        self.debugButton.clicked.connect(self.degub)
        layout.addWidget(self.debugButton)

        self.excelItems = ['measName', 'FilenName', 'Sample', 'Frequency', 'Power', 'Field', 'ModFreq', 'ModAmp', 'TC',
                           'Calib', 'Notes', 'Short', 'VNA', 'Steps']

    def degub(self):
        self.addTableRow()

    def loadExcelData(self, excel_file_dir, worksheet_name):
        self.df = pd.read_excel(excel_file_dir, worksheet_name)
        if self.df.size == 0:
            return

        self.df.fillna('', inplace=True)
        self.table.setRowCount(self.df.shape[0])
        self.table.setColumnCount(self.df.shape[1])
        self.table.setHorizontalHeaderLabels(self.df.columns)


        # returns pandas array object
        for row in self.df.iterrows():
            values = row[1]
            for col_index, value in enumerate(values):
                if isinstance(value, (float, int)):
                    value = '{0:0,.0f}'.format(value)
                tableItem = QTableWidgetItem(str(value))
                self.table.setItem(row[0], col_index, tableItem)

        #self.table.setColumnWidth(2, 300)

    def gatherInfos(self):
        self.infos = {}

        self.infos["measName"] = "1"
        self.infos["FilenName"] = "2"
        self.infos["Sample"] = "3"
        self.infos["Frequency"] = "4"
        self.infos["Power"] = "5"
        self.infos["Field"] = "6"
        self.infos["ModFreq"] = "7"
        self.infos["ModAmp"] = "8"
        self.infos["TC"] = "9"
        self.infos["Calib"] = "00"
        self.infos["Notes"] = "00"
        self.infos["Short"] = "00"
        self.infos["VNA"] = "0"
        self.infos["Steps"] = "00"

    def addTableRow(self):
        self.gatherInfos() # Get infos

        #Add new row to table
        row = self.table.rowCount()+1
        self.table.setRowCount(row)

        # Fill new row and add new row to df
        infos = {}
        for colIndex, excelColumn in enumerate(self.excelItems):
            tableItem = QTableWidgetItem().setText(str(self.infos.get(excelColumn)))
            infos[self.df.columns[colIndex]] = str(self.infos.get(excelColumn))
            self.table.setItem(row, colIndex, tableItem)

        infos = pd.DataFrame(infos, columns=infos.keys(), index=[0])
        self.df = pd.concat([self.df, infos])

    def saveExcelData(self, excel_file_path, worksheet_name):
        self.df.to_excel(excel_file_path, worksheet_name, index=False)


if __name__ == '__main__':
    # don't auto scale when drag app to a different monitor.
    # QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    excel_file_path = 'LogBook.xlsx'
    worksheet_name = 'Tabelle1'

    app = QApplication(sys.argv)
    app.setStyleSheet('''
        QWidget {
            font-size: 25px;
        }
    ''')

    myApp = MyApp()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print('Closing Window...')