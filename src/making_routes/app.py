"""
Configure routes for M3
"""
import sys
import pandas as pd

try:
    from importlib import metadata as importlib_metadata
except ImportError:
    # Backwards compatibility - importlib.metadata was added in Python 3.8
    import importlib_metadata

from typing import Iterator, List
from itertools import chain

from PySide6 import QtCore
from PySide6.QtCore import QAbstractTableModel
from PySide6.QtCore import Qt
from PySide6.QtCore import QModelIndex

from PySide6.QtGui import QAction

from PySide6.QtWidgets import QStyle
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QTabWidget
from PySide6.QtWidgets import QStatusBar
from PySide6.QtWidgets import QTableView
from PySide6.QtWidgets import QToolBar
from PySide6.QtWidgets import QFileDialog

from many_more_routes.construct import MakeRoute
from many_more_routes.construct import MakeDeparture
from many_more_routes.construct import MakeSelection
from many_more_routes.construct import MakeCustomerExtension
from many_more_routes.construct import MakeCustomerExtensionExtended

from many_more_routes.ducks import OutputRecord
from many_more_routes.models import Template

from many_more_routes.io import load_excel
from many_more_routes.io import save_excel
from many_more_routes.io import save_template

from many_more_routes.sequence import generator
from many_more_routes.sequence import is_sequenceNumber_valid


def make_routes(record: Template) -> Iterator[OutputRecord]:
    yield MakeRoute(record)
    for departure in MakeDeparture(record): yield departure
    yield MakeSelection(record)
    for cugex in MakeCustomerExtension(record): yield cugex
    for cugexex in MakeCustomerExtensionExtended(record): yield cugexex



class PandasModel(QAbstractTableModel): 
    def __init__(self, df = pd.DataFrame(), parent=None): 
        QAbstractTableModel.__init__(self, parent=parent)
        self._df = df.copy()

    def toDataFrame(self):
        return self._df.copy()

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except (IndexError, ):
                return None
        elif orientation == Qt.Vertical:
            try:
                # return self.df.index.tolist()
                return self._df.index.tolist()[section]
            except (IndexError, ):
                return None

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if not index.isValid():
            return None

        return str(self._df.iloc[index.row(), index.column()])

    def setData(self, index, value, role):
        row = self._df.index[index.row()]
        col = self._df.columns[index.column()]
        if hasattr(value, 'toPyObject'):
            # PyQt4 gets a QVariant
            value = value.toPyObject()
        else:
            # PySide gets an unicode
            dtype = self._df[col].dtype
            if dtype != object:
                value = None if value == '' else dtype.type(value)
        self._df.set_value(row, col, value)
        return True

    def rowCount(self, parent=QModelIndex()): 
        return len(self._df.index)

    def columnCount(self, parent=QModelIndex()): 
        return len(self._df.columns)

    def sort(self, column, order):
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(colname, ascending= order == Qt.AscendingOrder, inplace=True)
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()


class PandasTable(QTableView):
    def __init__(self, data):
        super().__init__()
        self.update(data)

    def update(self, data: pd.DataFrame) -> None:
        self.model = PandasModel(data)
        self.setModel(self.model)

    def get(self) -> pd.DataFrame:
        return self.model._df


class MakingRoutes(QMainWindow):
    def __init__(self):
        super().__init__()

        self.filename = None
        self.endpoint = None
        self.outputs = []
        self.sheetnames = []
        self.tables = {}

        self._init_toolbar()
        self._init_statusbar()
        self._init_tabs()

        self.setWindowTitle('Making Routes')
        self.show()

    def _init_toolbar(self):
        toolbar1 = QToolBar()

        pixmap1 = getattr(QStyle, 'SP_DialogOpenButton')
        pixmap2 = getattr(QStyle, 'SP_DialogSaveButton')

        icon1 = self.style().standardIcon(pixmap1)
        icon2 = self.style().standardIcon(pixmap2)

        action1 = QAction("Open from File", self)
        action2 = QAction("Save to File", self)
        action3 = QAction("Assign Routes", self)
        action4 = QAction("Update Outputs", self)

        action1.setIcon(icon1)
        action2.setIcon(icon2)

        action1.triggered.connect(self._load_template_cb)
        action2.triggered.connect(self._save_template_cb)
        action3.triggered.connect(self._assign_routes_cb)
        action4.triggered.connect(self._process_template_cb)

        toolbar1.addAction(action1)
        toolbar1.addAction(action2)
        toolbar1.addSeparator()
        toolbar1.addAction(action3)
        toolbar1.addAction(action4)

        self.addToolBar(toolbar1)

    def _init_statusbar(self):
        statusbar1 = QStatusBar(self)

        self.setStatusBar(statusbar1)

    def _init_tabs(self):
        tabs1 = QTabWidget()
        tabs1.setTabPosition(tabs1.North)
        self.setCentralWidget(tabs1)

        self.addTab = tabs1.addTab
        self.clearTabs = tabs1.clear
  

    def _load_template_cb(self):
        dialog1 = QFileDialog(self, 'Open Template File...')
        dialog1.setNameFilter("Template (*.xlsx)")
        dialog1.exec()

        if dialog1.selectedFiles():
            self.clearTabs()

            self.filename = dialog1.selectedFiles()[0]
            self.setStatusTip(f'Loaded template {self.filename}')


            table1 = PandasTable(pd.DataFrame(load_excel(self.filename)))

            self.addTab(table1, 'TEMPLATE_V3')

            self.tables = {'TEMPLATE_V3': table1}


    def _save_template_cb(self):
        dialog1 = QFileDialog(self, 'Open Template File...')
        dialog1.setAcceptMode(QFileDialog.AcceptSave)
        dialog1.setNameFilter("Template (*.xlsx)")
        dialog1.exec()

        if dialog1.selectedFiles():
            filename = dialog1.selectedFiles()[0]
            self.setStatusTip(f'Saved template {self.filename}')


            template1 = self.tables['TEMPLATE_V3'].get()
            records = [item for row in template1.to_dict('records') for item in make_routes(Template(**row))]

            save_excel(records, filename)

    def _assign_routes_cb(self):
        template1 = self.tables['TEMPLATE_V3'].get()

        seed = max(filter(is_sequenceNumber_valid, template1['ROUT']))

        if seed:
            routegen = generator(seed)
            next(routegen)
            template1['ROUT'] = template1['ROUT'].apply(lambda x: next(routegen) if not x else x)

        self.tables['TEMPLATE_V3'].update(template1)


    def _process_template_cb(self):
        template1 = self.tables['TEMPLATE_V3'].get()

        records = list(map(lambda x: Template(**x), template1.to_dict('records')))

        routes:     List[OutputRecord] = []
        departures: List[OutputRecord] = []
        selection:  List[OutputRecord] = []
        cugex:      List[OutputRecord] = []
        cugexex:    List[OutputRecord] = []

        for record in records:
            routes.append(MakeRoute(record))
        
            for departure in MakeDeparture(record):
                departures.append(departure)

            selection.append(MakeSelection(record))

            for cusex in MakeCustomerExtension(record):
                cugex.append(cusex)

            for cusexex in MakeCustomerExtensionExtended(record):
                cugexex.append(cusexex)

        self.clearTabs()

        outputs = [lst for lst in [records, routes, selection, cugex, cugexex] if lst != []]
        sheetnames = [each[0]._api for each in outputs]


        for name, data in zip(sheetnames, outputs):
            table0 = PandasTable(pd.DataFrame([row.dict() for row in data]))
            self.tables.update({name: table0})
            self.addTab(table0, name)

        self.show()


def main():
    app_module = sys.modules['__main__'].__package__
    metadata = importlib_metadata.metadata(app_module)

    QApplication.setApplicationName(metadata['Formal-Name'])

    app = QApplication(sys.argv)
    main_window = MakingRoutes()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()