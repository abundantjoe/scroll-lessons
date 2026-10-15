"""flatcheck: quality checks and alternatives for tifxyz flattenings."""

from .api import METHODS, FlatResult, collapse_flags, flatten, metrics, read_package, verify_package, write_package
from .report import grid_report

__version__ = "0.1.0"
__all__ = ["METHODS", "FlatResult", "collapse_flags", "flatten", "metrics", "read_package", "verify_package",
           "write_package", "grid_report", "__version__"]
