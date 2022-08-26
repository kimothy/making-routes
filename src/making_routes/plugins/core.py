from __future__ import annotations

from pydantic import ValidationError

from making_routes.models import SimpleErrorModel, SimpleValidationModel

from ..plugin import Plugin
from ..plugin import Button
from ..plugin import Trigger

from route_sequence import RouteSequence

from many_more_routes.construct import MakeRoute
from many_more_routes.construct import MakeDeparture
from many_more_routes.construct import MakeSelection
from many_more_routes.construct import MakeCustomerExtension
from many_more_routes.construct import MakeCustomerExtensionExtended

from typing import Callable, List, NewType

class AssignRoutes(Plugin):
    enabled = True

    def buttons(self) -> List[Button]:
        return [Button(name='Assign Routes', callback=self.main)]

    def main(self, *args, **kwargs) -> None:
        interface = self.interface

        records = interface.list_records()
        try:
            seed = str(RouteSequence(max(list(filter(lambda x: RouteSequence.is_valid_str(x), [r.ROUT for r in records])))) + 1)
        except:
            seed = ''

        text, ok = interface.prompt(header='Route Seed', message='Set seed', text=seed)
    
        if not RouteSequence.is_valid_str(text) and ok:
            interface.prompt_error(f'Seed {text} is invalid')
            return

        elif ok:
            for (index, record), route in zip([r for r in enumerate(records) if not getattr(r[1], 'ROUT', None)], RouteSequence(text) - 1):
                setattr(record, 'ROUT', str(route))
                interface.update_record(index, record)


MakeClass = NewType('MakeClass', Plugin)
def make_plugin_factory(make_funtion: Callable, enable=True) -> MakeClass:

    class MakeClass(Plugin):
        enabled = enable

        def triggers(self) -> List[Trigger]:
            return [Trigger('ON_PROCESS', self.main)]

        def main(self, *args, **kwargs) -> None:
            for index, record in enumerate(self.interface.list_records('TEMPLATE_V3')):
                try:
                    for result in make_funtion(record):
                        try:
                            self.interface.append_record(
                                type(result)(
                                    **result.dict()
                                )
                            )

                        except ValidationError as e:
                            self.interface.append_record(
                                type(result).construct(
                                    **result.dict()
                                )
                            )

                except Exception as e:
                    self.interface.append_record(
                        SimpleErrorModel(
                            message = f"Error processing row {index}; {make_funtion.__name__}; {str(e.with_traceback(None))}"
                            )
                        )

    return MakeClass

MakeRoutePlugin = make_plugin_factory(MakeRoute)
MakeDeparturePlugin = make_plugin_factory(MakeDeparture)
MakeSelectionPlugin = make_plugin_factory(MakeSelection)
MakeCustomerExtensionPlugin = make_plugin_factory(MakeCustomerExtension)
MakeCustomerExtensionExtendedPlugin = make_plugin_factory(MakeCustomerExtensionExtended)


class ValidatePlugin(Plugin):
    enabled = True

    def buttons(self) -> List[Button]:
        return [Button('Validate', self.main)]

    def main(self) -> None:
        try:
            for n, record in self.interface.list_all_records():
                try:
                    type(record)(**record.dict())

                except ValidationError as exception:
                    for error in exception.errors():
                        self.interface.append_record(
                            SimpleValidationModel(
                                message=f"[{record._api}] (Line {n})   {error['loc'][0]} = {getattr(record, error['loc'][0], None)}   {error['msg']}"
                            )
                        )

        except Exception as exception:
            self.interface.prompt_error(str(exception))