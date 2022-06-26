from . models import Template
from . models import Route
from . models import Departure
from . models import Selection
from . models import CustomerExtension
from . models import CustomerExtensionExtended
from . models import ErrorModel
from . models import OutputRecord

from many_more_routes.construct import MakeRoute
from many_more_routes.construct import MakeDeparture
from many_more_routes.construct import MakeSelection
from many_more_routes.construct import MakeCustomerExtension
from many_more_routes.construct import MakeCustomerExtensionExtended

from pydantic import BaseClass
from pydantic.error_wrappers import ValidationError

from typing import List, Optional



class RouteConfiguration(BaseClass):
    record: Template
    routes: Route
    departures: List[Departure]
    selection: Selection
    cugex: Optional[List[CustomerExtension]] = []
    cugexex: Optional[List[CustomerExtensionExtended]] = []
    errors: Optional[List[ValidationError]] = []


def MakeRouteConfiguration(record: Template) -> RouteConfiguration:
    error_list: List[Exception] = []

    try:
        record = Template(**record.dict())

    except ValidationError as exception:
        error_list.append(exception)

    try:
        route = MakeRoute(record)

    except ValidationError as exception:
        error_list.append(exception)
        
    try:
        departures: List[Departure] = []
        for departure in MakeDeparture(record):
            departures.append(departure)

    except ValidationError as exception: 
        error_list.append(exception)

    try:
        selection = MakeSelection(record)

    except ValidationError as exception: 
        error_list.append(exception)
                    
    try:
        cugexs: List[CustomerExtension] = []
        for cugex in MakeCustomerExtension(record):
            cugexs.append(cugex)

    except ValidationError as exception: 
        error_list.append(exception)

    try:
        cugexexs: List[CustomerExtension] = []
        for cugexex in MakeCustomerExtensionExtended(record):
            cugexexs.append(cugexex)

    except ValidationError as exception:
        error_list.append(exception)

    return RouteConfiguration(
        record=record,
        route=route,
        departures=departures,
        selection=selection,
        cugex=cugexs,
        cugexex=cugexexs,
        errors=error_list
    )




def create_output_tables(self, data=List[Template]) -> List[List[OutputRecord]]:
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
            working_list.append(record)
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
