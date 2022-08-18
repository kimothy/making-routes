from abc import ABC, abstractmethod
from typing import Callable, List, Literal, Tuple, Any, ForwardRef
from many_more_routes.models import UnvalidatedTemplate
from many_more_routes.models import ValidatedTemplate
from many_more_routes.ducks import OutputRecord
from dataclasses import dataclass


Plugin = ForwardRef('Plugin')


@dataclass
class Button:
    """
    Button object. Call a function (callback) at the press of a button. 
    """
    name: str
    callback: Callable


@dataclass
class Trigger:
    """
    Trigger object. Call a function (callback) at a given event.
    """
    event: Literal[
        'ON_LOAD',
        'ON_SAVE',
        'ON_VALIDATE',
        'ON_PROCESS'
    ]
    callback: Callable


class PluginInterfaceBase(ABC):
    """
    Plugin interface base class to be implemented by the core application.
    """
    @staticmethod
    @abstractmethod
    def list_records() -> List[UnvalidatedTemplate|ValidatedTemplate]|None:
        """
        Returns a list of records from the template.
        """

    @staticmethod
    @abstractmethod
    def update_record(index: int, record: UnvalidatedTemplate|ValidatedTemplate) -> UnvalidatedTemplate|ValidatedTemplate|None:
        """
        Update a record at a given index.
        """

    @abstractmethod
    def append_record(record: OutputRecord) -> None:
        """
        Add a new record to the list.
        """

    @staticmethod
    @abstractmethod
    def prompt_error(error_message: str) -> None:
        """
        Prompt with a error message.
        """

    @staticmethod
    @abstractmethod
    def prompt(header: str, message: str,  text: str) -> Tuple[Any, Any]:
        """
        Prompt with an input box.
        """

    @staticmethod
    @abstractmethod
    def register(plugin: Plugin) -> None:
        """
        Register a plugin
        """

    @staticmethod
    @abstractmethod
    def list_plugins(self) -> List[Plugin]:
        """
        Unregister a plugin
        """

    @abstractmethod
    def list_all_records(self) -> List[OutputRecord]:
        """
        List all records.
        """

    @abstractmethod
    def trigger(self, event: Literal[
        'ON_LOAD',
        'ON_SAVE',
        'ON_VALIDATE',
        'ON_PROCESS'
    ]):
        """
        Call registered triggers for all plugins
        """


class Plugin(ABC):
    """
    Base class to implement new plugins.    
    """
    def __init__(self, interface: PluginInterfaceBase):
        """
        Init function. The plugin will register itself to the given
        plugin interface
        """
        self.interface = interface
        self.interface.register(self)

    def buttons(self) -> List[Button]:
        """
        Returns a list of button objects.
        Implement this function if special buttons are requirede to invoke some function
        """
        return []

    def triggers(self) -> List[Trigger]:
        """
        Returns a list of triggers, used by the plugin interface to determine when the given
        functions should be implemented.
        """
        return []

    @property
    def enabled(self) -> bool:
        """
        Set the property to True if the plugin should load.
        """
        return False