"""
Configure routes for M3
"""
import sys
try:
    from importlib import metadata as importlib_metadata
except ImportError:
    # Backwards compatibility - importlib.metadata was added in Python 3.8
    import importlib_metadata

from typing import Iterator, List, Dict

from PySide6.QtGui import QAction
from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QStyle
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QTabWidget
from PySide6.QtWidgets import QStatusBar
from PySide6.QtWidgets import QToolBar
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import QInputDialog
from PySide6.QtWidgets import QMessageBox



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
from many_more_routes.sequence import increment
from many_more_routes.sequence import is_sequenceNumber_valid

from making_routes.models import ErrorModel, OutputRecordView

from pydantic.error_wrappers import ValidationError

def make_errors(index, exception: ValidationError, record: OutputRecord) -> List[ErrorModel]:
    for error in exception.errors():
        return ErrorModel(
            source=record._api,
            row=index,
            field=', '.join(error['loc']), 
            message=error['msg'],
            error=error['type'],
            data=getattr(record, error['loc'][0]) if hasattr(record, error['loc'][0]) else ''
        )


def make_routes(record: Template) -> Iterator[OutputRecord]:
    yield MakeRoute(record.copy())
    for departure in MakeDeparture(record.copy()): yield departure
    yield MakeSelection(record.copy())
    for cugex in MakeCustomerExtension(record.copy()): yield cugex
    for cugexex in MakeCustomerExtensionExtended(record.copy()): yield cugexex


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
        self.resize(1200, 800)
        self.show()

    def _init_toolbar(self):
        toolbar1 = QToolBar()

        pixmap1 = getattr(QStyle, 'SP_DialogOpenButton')
        pixmap2 = getattr(QStyle, 'SP_DialogSaveButton')
        pixmap5 = getattr(QStyle, 'SP_FileIcon')

        icon1 = self.style().standardIcon(pixmap1)
        icon2 = self.style().standardIcon(pixmap2)
        icon5 = self.style().standardIcon(pixmap5)


        action1 = QAction("Open from File", self)
        action2 = QAction("Save to File", self)
        action3 = QAction("Assign Routes", self)
        action4 = QAction("Update Outputs", self)
        action5 = QAction("New template", self)

        action1.setIcon(icon1)
        action2.setIcon(icon2)
        action5.setIcon(icon5)

        action1.triggered.connect(self._load_template_cb)
        action2.triggered.connect(self._save_tables_cb)
        action3.triggered.connect(self._assign_routes_cb)
        action4.triggered.connect(self._process_template_cb)
        action5.triggered.connect(self._new_template_cb)


        toolbar1.addAction(action5)
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

    def _new_template_cb(self):
        self.clearTabs()

        self.setStatusTip(f'New template {self.filename}')

        data = []
        table1 = OutputRecordView(data)

        self.addTab(table1, 'TEMPLATE_V3')

        self.tables = {'TEMPLATE_V3': table1}  

    def _load_template_cb(self):
        dialog1 = QFileDialog(self, 'Open Template File...')
        dialog1.setNameFilter("Template (*.xlsx)")
        dialog1.exec()

        if dialog1.selectedFiles():
            self.filename = dialog1.selectedFiles()[0]
            
            data: List[Template] = []
            errors: List[ErrorModel] = []
    
            try:
                for index, row in enumerate(load_excel(self.filename, 'TEMPLATE_V3')):
                    try:
                        data.append(Template(**row))
        
                    except ValidationError as exception:
                        record = Template.construct(**row)
                        for error in exception.errors():
                            print(error)
                            error_record = ErrorModel(
                                source='TEMPLATE_V3',
                                row=index,
                                field=', '.join(error['loc']), 
                                message=error['msg'],
                                error=error['type'],
                                data=getattr(record, error['loc'][0]) if hasattr(record, error['loc'][0]) else ''
                            )
                            
                            errors.append(error_record)
                        data.append(record)

            except KeyError as error:
                QMessageBox.critical(self, 'Error', str(error))

            else:
                table1 = OutputRecordView(data, editable=True)
                table2 = OutputRecordView(errors)
                self.setStatusTip(f'Loaded template {self.filename}')
                self.clearTabs()
                self.addTab(table1, 'TEMPLATE_V3')
                self.tables = {'TEMPLATE_V3': table1}

                if errors:
                    self.addTab(table2, 'WARNINGS')
                    self.tables['WARNINGS'] = table2


    def _save_tables_cb(self):
        dialog1 = QFileDialog(self, 'Open Template File...')
        dialog1.setAcceptMode(QFileDialog.AcceptSave)
        dialog1.setNameFilter("Template (*.xlsx)")
        dialog1.exec()

        if dialog1.selectedFiles():
            filename = dialog1.selectedFiles()[0]
            self.setStatusTip(f'Saved template {self.filename}')

            records = [record for table in self.tables.values() for record in table.get()]

            if not records == []:
                save_excel(records, filename)
            else:
                save_template(Template, filename)

    def _assign_routes_cb(self):
        template1 = self.tables['TEMPLATE_V3'].get()

        try:
            maxseed = increment(max(filter(is_sequenceNumber_valid, [record.ROUT for record in template1])))
    
        except:
            maxseed = ''

        text, ok = QInputDialog.getText(self, 'Set Route Seed', 'Enter Next Route:', text=maxseed)


        if ok and is_sequenceNumber_valid(text):
            self.setStatusTip(f'Assign routes seed: {text}')
            routegen = generator(text)
        
        elif not is_sequenceNumber_valid(text):
            self.setStatusTip(f'{text} is not a valid seed!')

        else:
            self.setStatusTip(f'Cancelled assignment of routes')
            return None
    
        counter = 0
        for record in template1:
            if not record.ROUT:
                record.ROUT = next(routegen)
                counter += 1

        self.setStatusTip(f'Assigned routes for {counter} records!')


    def _process_template_cb(self):
        self.clearTabs()
        
        data = self.tables['TEMPLATE_V3'].get()

        records:    List[OutputRecord] = []
        routes:     List[OutputRecord] = []
        departures: List[OutputRecord] = []
        selection:  List[OutputRecord] = []
        cugex:      List[OutputRecord] = []
        cugexex:    List[OutputRecord] = []
        errors:     List[ErrorModel] = []

        for index, row in enumerate(data):
                try:
                    record = Template(**row.dict())
                    records.append(record)

                except ValidationError as exception:
                    record = Template.construct(**row.dict())
                    records.append(record)
                    errors.append(make_errors(index, exception, record))

                try:
                    routes.append(MakeRoute(record.copy()))

                except ValidationError as exception:
                    errors.append(make_errors(index, exception, record))
        
                try:
                    for departure in MakeDeparture(record.copy()):
                        departures.append(departure)

                except ValidationError as exception: 
                    errors.append(make_errors(index, exception, record))

                try:
                    selection.append(MakeSelection(record.copy()))

                except ValidationError as exception: 
                    errors.append(make_errors(index, exception, record))
                    
                try:
                    for cusex in MakeCustomerExtension(record.copy()):
                        cugex.append(cusex)

                except ValidationError as exception: 
                    errors.append(make_errors(index, exception, record))

                try:
                    for cusexex in MakeCustomerExtensionExtended(record.copy()):
                        cugexex.append(cusexex)

                except ValidationError as exception:
                    errors.append(make_errors(index, exception, record))



        outputs = [lst for lst in [records, routes, departures, selection, cugex, cugexex] if lst != []]
        sheetnames = [each[0]._api for each in outputs]

        self.tables = {}
        for name, data in zip(sheetnames, outputs):
            table0 = OutputRecordView(data)
            self.tables.update({name: table0})
            self.addTab(table0, name)

        if errors:
            table1 = OutputRecordView(errors)
            self.tables.update({'ERRORS': table1})
            self.addTab(table1, 'ERRORS')
            self.setStatusTip(f'Outputs updated. {len(errors)} errors!')

        else:
            self.setStatusTip(f'Outputs updated. No errors!')
        self.show()


def main():
    app_module = sys.modules['__main__'].__package__
    metadata = importlib_metadata.metadata(app_module)

    QApplication.setApplicationName(metadata['Formal-Name'])
    print(f"{metadata['Formal-Name']} version {metadata['version']}")
    print(f"many_more_routes version {importlib_metadata.version('many_more_routes')}")

    app = QApplication(sys.argv)
    main_window = MakingRoutes()
    sys.exit(app.exec())