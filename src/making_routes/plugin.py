from abc import ABC, abstractmethod
from typing import Callable, List, TypedDict, Literal, Optional, Tuple, Any, ForwardRef
from many_more_routes.models import UnvalidatedTemplate
from many_more_routes.models import ValidatedTemplate
from many_more_routes.ducks import OutputRecord
from dataclasses import dataclass

Plugin = ForwardRef('Plugin')

class PluginInterfaceBase(ABC):

    @staticmethod
    @abstractmethod
    def list_records() -> List[UnvalidatedTemplate|ValidatedTemplate]|None:
        ...

    @staticmethod
    @abstractmethod
    def update_record(index: int) -> UnvalidatedTemplate|ValidatedTemplate|None:
        ...

    @abstractmethod
    def append_record(record: OutputRecord) -> None:
        ...

    @staticmethod
    @abstractmethod
    def prompt_error(error_message: str) -> None:
        ...

    @staticmethod
    @abstractmethod
    def prompt(header: str, message: str,  text: str) -> Tuple[Any, Any]:
        ...

    @staticmethod
    @abstractmethod
    def register(plugin: Plugin) -> None:
        ...

    @staticmethod
    @abstractmethod
    def list_plugins(self) -> List[Plugin]:
        ...

    @abstractmethod
    def list_all_records(self) -> List[OutputRecord]:
        ...

@dataclass
class Button:
    name: str
    callback: Callable

@dataclass
class Trigger:
    event: Literal[
        'ON_LOAD',
        'ON_SAVE',
        'ON_VALIDATE',
        'ON_PROCESS'
    ]
    callback: Callable


class Plugin(ABC):
    def __init__(self, interface: PluginInterfaceBase):
        self.interface = interface
        self.interface.register(self)

    def buttons(self) -> List[Button]:
        return []

    def triggers(self) -> List[Trigger]:
        return []

    @property
    def enabled(self) -> bool:
        return False