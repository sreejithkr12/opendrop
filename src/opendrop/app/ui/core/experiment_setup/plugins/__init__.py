import sys
from typing import List, Type

from opendrop.utility.misc import recursive_load

from ..plugin import ExperimentSetupPlugin


_plugins = []  # type: List[Type[ExperimentSetupPlugin]]


def register_plugin(plugin_cls: Type[ExperimentSetupPlugin]) -> None:
    _plugins.append(plugin_cls)


def get_plugins() -> List[Type[ExperimentSetupPlugin]]:
    return _plugins


current_module = sys.modules[__name__]

# Recursively load all the modules in `plugins` so they get returned in ExperimentSetupPlugin.__subclasses__()
recursive_load(current_module)
