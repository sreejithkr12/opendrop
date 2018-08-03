import sys

from opendrop.utility.misc import recursive_load

# Recursively load all modules in this package to allow the preview controllers to perform their registration.
recursive_load(sys.modules[__name__])
