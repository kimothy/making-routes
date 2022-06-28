from PySide6.QtCore import Qt
from PySide6.QtCore import QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import QTableView


from many_more_routes.ducks import OutputRecord


from typing import Any, List, Dict, Optional
from pydantic import BaseModel
from pydantic import PrivateAttr


class ProcedureException(RuntimeError):
    """ A runtime error to be used when runtime exceptions happens in procedures """
    def __init__(self, error, source: str, message: str, data: str):
        self.source = source
        self.message = message
        self.data = data

    def dict(self):
        return {'source': self.source, 'message': self.message, 'data': self.data}


class SimpleErrorModel(BaseModel):
    """A data model that can be has the same signature as a Output Record.
    This facilitets the use for the OutputRecordModel for error messages"""
    _api: str = PrivateAttr(default='VALIDATION')
    message: str

class ErrorModel(BaseModel):
    """A data model that can be has the same signature as a Output Record.
    This facilitets the use for the OutputRecordModel for error messages"""
    _api: str = PrivateAttr(default='VALIDATION') 
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
                self._schema = {'properties': {'': None}}
        
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

        try:
            return getattr(self._data[index.row()], list(self._schema['properties'].keys())[index.column()])
        except AttributeError:
            return None

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

        try:
            new_record = type(record)(**record.dict())
            self._data[index.row()] = new_record
        except:
            new_record = type(record).construct(**record.dict())
            self._data[index.row()] = new_record

        
        return True


    


class OutputRecordView(QTableView):
    def __init__(self, data: List[OutputRecord], editable: bool = False):
        super().__init__()
        self.editable = editable
        self.update(data)
        
    def update(self, data: List[OutputRecord]) -> None:
        self.model = OutputRecordModel(data, editable=self.editable)
        self.setModel(self.model)
        self.viewport().update()

    def clear(self):
        self.model = OutputRecordModel([], editable=self.editable, schema=self.model._schema)
        self.setModel(self.model)
        self.viewport().update()
    
    def get(self) -> List[OutputRecord]:
        return self.model._data

    def toggle_editable(self):
        self.model.editable = not self.model.editable
