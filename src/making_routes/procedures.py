from . models import Template
from . models import Route
from . models import Departure
from . models import Selection
from . models import CustomerExtension
from . models import CustomerExtensionExtended
from . models import ErrorModel

from many_more_routes.ducks import OutputRecord

from many_more_routes.construct import MakeRoute
from many_more_routes.construct import MakeDeparture
from many_more_routes.construct import MakeSelection
from many_more_routes.construct import MakeCustomerExtension
from many_more_routes.construct import MakeCustomerExtensionExtended

from pydantic import BaseModel, PrivateAttr
from pydantic.error_wrappers import ValidationError

from typing import Iterable, List, Optional, Any


class RouteConfiguration(BaseModel):
    record: Optional[Template]
    route: Optional[Route]
    departures: Optional[List[Departure]]
    selection: Optional[Selection]
    cugex: Optional[List[CustomerExtension]] = []
    cugexex: Optional[List[CustomerExtensionExtended]] = []
    errors: Optional[List[Any]] = []


class ExceptionOutput(BaseModel):
    _api: str = PrivateAttr(default='WARNINGS')
    row: Optional[int]
    error: Optional[str]

def validate_record(record: OutputRecord) -> OutputRecord:
        return type(record)(**record.dict())

def yield_records(record: Template) -> OutputRecord:
    try:
        yield record
        for r in MakeRoute(record): yield r
        for r in MakeRoute(record): yield r
        for r in MakeDeparture(record): yield r
        for r in MakeSelection(record): yield r
        for r in MakeCustomerExtension(record): yield r
        for r in MakeCustomerExtensionExtended(record): yield r
    except Exception as exception:
        yield ErrorModel(source='yield_records', field='', message=str(exception))


def MakeRouteConfiguration(record: Template) -> Iterable[OutputRecord]:
    record = record.copy()

    for output in yield_records(record):
        try:
            yield validate_record(output)

        except ValidationError as exception:
            yield output
            for e in exception.errors():
                yield ErrorModel(
                    source=output._api,    
                    field=', '.join(e['loc']), 
                    message=str(e['msg']) + ' ' + str(e['type']) + str(getattr(record, e['loc'][0])) if hasattr(record, e['loc'][0]) else ''
                )
            