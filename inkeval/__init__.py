"""inkeval - honest evaluation tools for ink detection in carbonised-scroll CT.

    from inkeval import judge, judge_classes, pixel_auc, stroke_auc, local_stroke_auc
    from inkeval import bootstrap_ci, paired_bootstrap, label_swap_null, rank_mean, export_png

See README.md and docs/METHODS.md. Every metric is a line-for-line port of the research script that produced the published numbers.
"""
__version__ = "1.0.0"

from .metrics import auc, judge, judge_classes, local_stroke_auc, pixel_auc, stroke_auc
from .stats import bootstrap_ci, label_swap_null, paired_bootstrap, trunc
from .ensemble import rank_mean
from .io import export_png, load_map

__all__ = ["auc", "judge", "judge_classes", "pixel_auc", "stroke_auc", "local_stroke_auc", "bootstrap_ci", "paired_bootstrap",
           "label_swap_null", "trunc", "rank_mean", "export_png", "load_map", "__version__"]
