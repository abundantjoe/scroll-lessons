2026-10-01T17:19:52Z fl-pherc0191 PHerc0268: GP env ok
2026-10-01T17:19:55Z fl-pherc0191 PHerc0268: seed list (e386079b510e)
2026-10-01T17:20:39Z fl-pherc0191 PHerc0268: grow pherc0268_fl-pherc0191_i3 area=11.667720895411993 selfx=0 kept=true
2026-10-01T18:25:33Z fl-pherc0191 PHerc0268: GP B forward pherc0268_fl-pherc0191_i3: 1 tiles
2026-10-01T18:31:40Z fl-pherc0191 PHerc0268: BUG in tools/fl4/run.sh push(): 'for d in 2 4 8 16 32' clobbers the global segment dir $d, so after a grow push the render uses --segmentation 2 and line 83 copies the tifxyz into ./2; from the 2nd segment on a lane renders a STALE tifxyz under a new name. Here i3 (1st segment) is safe: ./2 = i3's own tifxyz (x.tif sha 885443b2.. identical). Local fix: 'local d' in push() (run.sh restarted). ASK orchestrator: fix tools/fl4/run.sh upstream (go.sh re-copies the buggy file) and check other lanes' 2nd+ segments (manifest/tifxyz sha vs render input).
2026-10-01T18:31:43Z fl-pherc0191 PHerc0268: GP B forward pherc0268_fl-pherc0191_i3: 4 cells 1 window
2026-10-02T06:05:48Z fl-pherc0191 PHerc0268: GP env ok
2026-10-02T07:08:05Z fl-pherc0191 PHerc0268: GP B reverse pherc0268_fl-pherc0191_i3: 4 cells 1 window
2026-10-02T07:08:08Z fl-pherc0191 PHerc0268: segment pherc0268_fl-pherc0191_i3 done
2026-10-02T07:09:01Z fl-pherc0191 PHerc0268: grow pherc0268_fl-pherc0191_i19 area=11.669311875048864 selfx=0 kept=true
