from PySide6.QtCore import Qt
from PySide6.QtCore import QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import QTableView

from many_more_routes.models import Template
from many_more_routes.models import Route
from many_more_routes.models import Departure
from many_more_routes.models import Selection
from many_more_routes.models import CustomerExtension
from many_more_routes.models import CustomerExtensionExtended
from many_more_routes.ducks import OutputRecord


from typing import Any, List, Dict, Optional
from pydantic import BaseModel

class ErrorModel(BaseModel):
    source: Any
    row: Any
    field: Any
    message: Any
    error: Any
    data: Any


class OutputRecordModel(QAbstractTableModel):
    def __init__(self, data: List[OutputRecord], schema: dict = None, editable: bool = False, parent=None): 
        QAbstractTableModel.__init__(self, parent=parent)
        if schema:
            self._schema = schema
        else:
            try:
                self._schema = data[0].schema()
            except:
                self._schema = Template.schema()

        self._data = data.copy()
        self.editable = editable

    def flags(self, index):
        if self.editable:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int: 
        return len(self._schema['properties'].keys())

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if not index.isValid():
            return None

        return list(self._data[index.row()].dict().values())[index.column()]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            try:
                return list(self._schema['properties'].keys())[section]
            except (IndexError, ):
                return None
        elif orientation == Qt.Vertical:
            try:
                # return self.df.index.tolist()
                return section
            except (IndexError, ):
                return None

    def setData(self, index, value, role=None) -> Optional[bool]:
        if hasattr(value, 'toPyObject'):
            # PyQt4 gets a QVariant
            value = value.toPyObject()

        if value == '':
            value = None

        record = self._data[index.row()]
        setattr(record, self.headerData(index.column(), Qt.Horizontal), value)
        
        return True



class OutputRecordView(QTableView):
    def __init__(self, data: List[OutputRecord], editable: bool = False):
        super().__init__()
        self.editable = editable
        self.update(data)
        
    def update(self, data: List[OutputRecord]) -> None:
        self.model = OutputRecordModel(data, editable=self.editable)

        self.setModel(self.model)

    def get(self) -> List[OutputRecord]:
        return self.model._data

    def set(self, row: int, field: str) -> None:
        col = list(self._schema['properties'].keys())[field]

        self.model.headerData(index.column(), Qt.Horizontal)
        headers = self.model.headerData(index.column(), Qt.Horizontal)

