# Provenance: Project HERCULES | owner the owner | [id removed]
"""Window pipeline: organizer 9 um mesh + a window on the organizer canvas ->
levelled, reading-oriented render and exact coordinate maps.

Modules
-------
canvas  : the official renderer's pixel <-> mesh-grid convention, crop /
          auto-crop origins, slice offsets and --flip-normals (derived from the
          villa 41701aa source and verified on synthetic volumes).
centre  : centre curves (official umbilicus JSON, level-4 CT-mask centroid,
          geometry-only fallbacks).
window  : cut, level, orient, the exact organizer <-> levelled maps,
          resampling, tifxyz writing, render-command builder and the
          alignment gate.
"""
