"""Shim so batch_ink.sh (RENDER_FILL=reflect) can call the packaged fill: python render_fill.py SRC.zarr DST.zarr"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from stripqc.fill import main  # noqa: E402

main()
