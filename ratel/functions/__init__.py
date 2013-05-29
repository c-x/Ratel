"""
Load functions into Ratel via __all__ variable.

Each function must :
- define a main() function
- define the _signature variable to catch arguments

"""

from os import path
from glob import glob

__all__ = [path.basename(f)[:-3] for f in glob(path.dirname(__file__) + "/*.py")]

