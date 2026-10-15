Provenance: Project HERCULES | owner the owner | [id removed]

# p4-purple-mo RESUME
- Done and pushed:
  - PROTOCOL.md with amendment A1;
  - unit_tests.json (pass);
  - tface.json (T_face 79);
  - posctl.json (FAIL by the declared rule: heights are recovered, but the glyph AUC is 0.60).
- COMPLETE: gate.json and REPORT.md pushed; nothing is running.
  - Relaunch: `for w in 0 1 2; do nohup python3 tools/sib/p4-purple/mo/gate.py /tmp/claude-0/mo compute $w 3 > /tmp/claude-0/mo/w$w.log 2>&1 & done`
  - Needs: pip numpy scipy opencv-python-headless tifffile requests imagecodecs.
- Then:
  - `python3 tools/sib/p4-purple/mo/gate.py /tmp/claude-0/mo analyse`, which writes gate.json;
  - REPORT.md (<= 30 lines, integrity line).
