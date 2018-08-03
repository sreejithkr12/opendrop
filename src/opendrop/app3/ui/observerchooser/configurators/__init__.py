import sys

from opendrop.utility.misc import recursive_load
from .bases import Configurator

recursive_load(sys.modules[__name__])
