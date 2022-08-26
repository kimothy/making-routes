"""
Configure routes for M3
"""
import sys

try:
    from importlib import metadata as importlib_metadata
except ImportError:
    # Backwards compatibility - importlib.metadata was added in Python 3.8
    import importlib_metadata

from typing import List, Dict, ForwardRef, Optional, Any, Tuple, Set, Literal, Union

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QStyle
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QTabWidget
from PySide6.QtWidgets import QStatusBar
from PySide6.QtWidgets import QToolBar
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import QInputDialog
from PySide6.QtWidgets import QMessageBox

from many_more_routes.ducks import OutputRecord
from many_more_routes.models import UnvalidatedTemplate
from many_more_routes.models import ValidatedTemplate

from many_more_routes.io import load_excel
from many_more_routes.io import save_excel
from many_more_routes.io import save_template

from making_routes.models import OutputRecordView
from making_routes.plugin import Plugin, PluginInterfaceBase

from pydantic.error_wrappers import ValidationError

from .models import OutputRecordView

from .plugins.core import AssignRoutes
from .plugins.core import MakeRoutePlugin
from .plugins.core import MakeCustomerExtensionExtendedPlugin
from .plugins.core import MakeCustomerExtensionPlugin
from .plugins.core import MakeDeparturePlugin
from .plugins.core import MakeSelectionPlugin
from .plugins.core import ValidatePlugin

MakingRoutes = ForwardRef('MakingRoutes')

class ModelViewController:
    views: Dict[str, OutputRecordView] = {}
    protected: Set[str]

    def append_record(self, record: OutputRecord) -> None:
        try:
            self.views[record._api].append(record)

        except KeyError:
            self.views[record._api] = OutputRecordView([record])


    def protect(self, name: str) -> None:
        if not name in self.views.keys():
            raise LookupError(f"No view exists for {name}.")

        self.protected.add(name)

    def get_view(self, name: str) -> OutputRecordView:
        return self.views[name]

    def clear(self, force: bool = False):
        if not force:
            keys = list(self.views.keys())
            for key in keys:
                if key not in self.protected:
                    self.views.pop(key)
        else:
            self.views = {}
            self.protected = set()


class PluginInterface(PluginInterfaceBase):
    def __init__(self, parent=QMainWindow, view: Optional[OutputRecordView] = None, errors: Optional[OutputRecordView] = None):
        self.parent = parent
        self.mvc = ModelViewController()
        self.__plugins: Set[Plugin] = set()

    def list_records(self, model: Union[int, str] = 0) -> List[UnvalidatedTemplate|ValidatedTemplate]:
        if isinstance(model, int):
            model = list(self.mvc.views.keys())[model]

        if isinstance(model, str):
            if model not in self.mvc.views.keys():
                raise ValueError(f"Cannot find {model} in the MVC")

        return self.mvc.views[model].list()

    def update_record(self, index: int, record: UnvalidatedTemplate|ValidatedTemplate) -> None:
        self.mvc.views[record._api].update(index, record)

    def append_record(self, record: OutputRecord) -> None:
        self.mvc.append_record(record)

    def prompt_error(self, error_message: str):
        QMessageBox.critical(self.parent, 'Error', error_message)

    def prompt(self, header: str, message: str, text: Optional[str] = '') -> Tuple[Any, Any]:
        return QInputDialog.getText(self.parent, header, message, text=text)

    def register(self, plugin: Plugin) -> None:
        self.__plugins.add(plugin)

    def list_plugins(self) -> List[Plugin]:
        return list(self.__plugins)

    def list_all_records(self):
        return [(n, record) for key in self.mvc.views.keys() for n, record in enumerate(self.list_records(key))]

    def trigger(self, event: Literal[
        'ON_LOAD',
        'ON_SAVE',
        'ON_VALIDATE',
        'ON_PROCESS'
    ]):
        for plugin in filter(lambda x: x.enabled, self.list_plugins()):
            for trigger in plugin.triggers():
                if trigger.event == event:
                    trigger.callback()


class MakingRoutes(QMainWindow):
    def __init__(self):
        super().__init__()

        self.filename = None
        self.endpoint = None
        self.outputs = []
        self.sheetnames = []
        self.tables = {}

        interface = PluginInterface(self)
        AssignRoutes(interface)
        MakeRoutePlugin(interface)
        MakeDeparturePlugin(interface)
        MakeSelectionPlugin(interface)
        MakeCustomerExtensionPlugin(interface)
        MakeCustomerExtensionExtendedPlugin(interface)
        ValidatePlugin(interface)


        self.interface = interface

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
        action4 = QAction("Update Outputs", self)
        action5 = QAction("New template", self)

        action1.setIcon(icon1)
        action2.setIcon(icon2)
        action5.setIcon(icon5)

        action1.triggered.connect(self._load_template_cb)
        action2.triggered.connect(self._save_tables_cb)
        action4.triggered.connect(self._process_template_cb)
        action5.triggered.connect(self._new_template_cb)

        toolbar1.addAction(action5)
        toolbar1.addAction(action1)
        toolbar1.addAction(action2)
        toolbar1.addSeparator()
        for plugin in filter(lambda x: x.enabled, self.interface.list_plugins()):
            for button in plugin.buttons():
                action = QAction(button.name, self)
                action.triggered.connect(button.callback)
                action.triggered.connect(self.refresh)
                toolbar1.addAction(action)

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

        data = [ValidatedTemplate]
        table1 = OutputRecordView(data)

        self.addTab(table1, 'TEMPLATE_V3')

        self.tables = {'TEMPLATE_V3': table1}
    
    def _load_template_cb(self):
        dialog1 = QFileDialog(self, 'Open Template File...')
        dialog1.setNameFilter("Template (*.xlsx)")
        dialog1.exec()

        self.interface.mvc.clear(True)

        if dialog1.selectedFiles():
            self.filename = dialog1.selectedFiles()[0]
                
            try:
                for record in load_excel(self.filename, 'TEMPLATE_V3'):
                    unvalidated_record = UnvalidatedTemplate(**record)

                    try:
                        self.interface.append_record(ValidatedTemplate(**unvalidated_record.dict()))

                    except ValidationError:
                        self.interface.append_record(ValidatedTemplate.construct(**unvalidated_record.dict()))

            except KeyError as error:
                QMessageBox.critical(self, 'Error', str(error))

            else:
                self.interface.mvc.protect('TEMPLATE_V3')
                self.refresh()

    def _process_template_cb(self):
        self.interface.mvc.clear()
        self.interface.trigger('ON_PROCESS')
        self.refresh()

    def refresh(self):
        self.clearTabs()
        for name, view in self.interface.mvc.views.items():
            self.addTab(view, name)

    def _save_tables_cb(self):
        dialog1 = QFileDialog(self, 'Open Template File...')
        dialog1.setAcceptMode(QFileDialog.AcceptSave)
        dialog1.setNameFilter("Template (*.xlsx)")
        dialog1.exec()

        if dialog1.selectedFiles():
            filename = dialog1.selectedFiles()[0]
            self.setStatusTip(f'Saved template {self.filename}')

            records = [record for table in self.interface.mvc.views.values() for record in table.get()]

            if not records == []:
                save_excel(records, filename)
            else:
                save_template(ValidatedTemplate, filename)


def main():
    app_module = sys.modules['__main__'].__package__
    metadata = importlib_metadata.metadata(app_module)

    QApplication.setApplicationName(metadata['Formal-Name'])
    print(f"{metadata['Formal-Name']} version {metadata['version']}")
    print(f"many_more_routes version {importlib_metadata.version('many_more_routes')}")
    print(f"route_sequence version {importlib_metadata.version('route_sequence')}")

    app = QApplication(sys.argv)
    main_window = MakingRoutes()
    sys.exit(app.exec())
