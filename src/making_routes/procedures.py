from many_more_routes.models import ValidatedTemplate
from many_more_routes.models import UnvalidatedTemplate
from many_more_routes.models import ValidatedTemplate

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


class ExceptionOutput(BaseModel):
    _api: str = PrivateAttr(default='WARNINGS')
    row: Optional[int]
    error: Optional[str]

def validate_record(record: ValidatedTemplate) -> OutputRecord:
        return type(record)(**record.dict())

def yield_records(record: ValidatedTemplate) -> OutputRecord:
    try:
        yield record
        for r in MakeRoute(record): yield r
        for r in MakeDeparture(record): yield r
        for r in MakeSelection(record): yield r
        for r in MakeCustomerExtension(record): yield r
        for r in MakeCustomerExtensionExtended(record): yield r
    except Exception as exception:
        yield ErrorModel(source='yield_records', field='', message=str(exception))


def MakeRouteConfiguration(record: ValidatedTemplate) -> Iterable[OutputRecord]:
    try:
        record = ValidatedTemplate(**dict(record))

    except ValidationError:
        record = UnvalidatedTemplate(**dict(record))
    
    for output in yield_records(record):
        try:
            yield type(output)(**dict(output))
            print(type(output))

        except ValidationError as exception:
            yield output
            for e in exception.errors():
                yield ErrorModel(
                    source=output._api,    
                    field=', '.join(e['loc']), 
                    message=str(e['msg']) + ' ' + str(e['type']) + str(getattr(record, e['loc'][0])) if hasattr(record, e['loc'][0]) else ''
                )
