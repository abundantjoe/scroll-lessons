"""flatcheck: flattening-quality checks and SLIM/ARAP re-flattening for tifxyz meshes."""

from .api import METHODS, collapse_flags, flatten, metrics, nominal_step, report
from .geometry import angle_defects, grid_uv, worst_windows
from .tifxyz import read_tifxyz, read_uv, write_tifxyz, write_uv

__version__ = "0.1.0"
__all__ = ["METHODS", "angle_defects", "collapse_flags", "flatten", "grid_uv", "metrics", "nominal_step",
           "read_tifxyz", "read_uv", "report", "worst_windows", "write_tifxyz", "write_uv", "__version__"]
