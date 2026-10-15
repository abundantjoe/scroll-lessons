2026-10-01T02:10:35Z env OK
2026-10-01T02:53:32Z pherc0191_auto_0 official tiles=18 area_cm2=55.627296694435444 source=decl-fl-1-auto
2026-10-01T03:24:00Z pherc0191_auto_1 official tiles=8 area_cm2=32.419461302741134 source=decl-fl-1-auto
2026-10-01T03:50:57Z pherc0191_auto_2 official tiles=8 area_cm2=31.524629177901602 source=decl-fl-1-auto
2026-10-01T06:23:20Z pherc0191_auto_3 official tiles=8 area_cm2=31.143065180697466 source=decl-fl-1-auto
2026-10-01T06:26:08Z pherc0191_fl-pherc0191_s0 grow rc=0 area_cm2=31.225360033433724 selfx=0 kept=true
2026-10-01T06:55:48Z pherc0191_fl-pherc0191_s0 official tiles=8 area_cm2=31.225360033433724 source=auto
2026-10-01T06:57:12Z pherc0191_fl-pherc0191_s2 grow rc=0 area_cm2=29.06720193943149 selfx=0 kept=true
2026-10-01T07:26:39Z pherc0191_fl-pherc0191_s2 official tiles=8 area_cm2=29.06720193943149 source=auto
2026-10-01T07:27:48Z pherc0191_fl-pherc0191_s4 grow rc=0 area_cm2=31.13116041310758 selfx=0 kept=true
2026-10-01T07:58:18Z pherc0191_fl-pherc0191_s4 official tiles=8 area_cm2=31.13116041310758 source=auto
2026-10-01T07:59:33Z pherc0191_fl-pherc0191_s6 grow rc=0 area_cm2=31.134539140957138 selfx=0 kept=true
2026-10-01T08:30:26Z pherc0191_fl-pherc0191_s6 tiles FAILED
2026-10-01T08:30:29Z official pass complete (4 grow attempts)
2026-10-01T08:34:32Z BUG+FIX: push() retry loop clobbered the global segment-dir $d (=2) after the first grow push, so pherc0191_fl-pherc0191_s2 and _s4 were RENDERED AND TILED FROM s0's mesh (manifest tifxyz_sha256 3d8567cd = s0); their 16 official tiles are WITHDRAWN (deleted) and will be redone; s6 tiles had failed for the same reason. s0 rendered a byte-identical copy of its own mesh (sha verified) and stands; auto_0..3 unaffected (own hashes). Grow gates (measure, selfcross) ran before the push and stand. Fix: local d in push(). Also: template fl.py seeds has an 8-entry plan, so round 0 gave 8 seeds (4 in lane 0); seed list extended with round 1 (48-entry plan, fl.py seeds ... 1), NSEEDS 40->80.
2026-10-01T09:05:45Z pherc0191_fl-pherc0191_s2 official tiles=8 area_cm2=29.06720193943149 source=auto
2026-10-01T09:39:28Z pherc0191_fl-pherc0191_s4 official tiles=8 area_cm2=31.13116041310758 source=auto
2026-10-01T10:15:57Z pherc0191_fl-pherc0191_s6 official tiles=8 area_cm2=31.134539140957138 source=auto
2026-10-01T10:19:19Z pherc0191_fl-pherc0191_r1s0 grow rc=0 area_cm2=31.132272427920103 selfx=0 kept=true
2026-10-01T10:47:16Z pherc0191_fl-pherc0191_r1s0 official tiles=8 area_cm2=31.132272427920103 source=auto
2026-10-01T10:48:30Z pherc0191_fl-pherc0191_r1s2 grow rc=0 area_cm2=31.137042819714832 selfx=0 kept=true
2026-10-01T11:16:51Z pherc0191_fl-pherc0191_r1s2 official tiles=8 area_cm2=31.137042819714832 source=auto
2026-10-01T11:17:56Z pherc0191_fl-pherc0191_r1s4 grow rc=0 area_cm2=31.130914002386685 selfx=0 kept=true
2026-10-01T11:51:26Z pherc0191_fl-pherc0191_r1s4 official tiles=8 area_cm2=31.130914002386685 source=auto
2026-10-01T11:52:36Z pherc0191_fl-pherc0191_r1s6 grow rc=0 area_cm2=31.132229399474326 selfx=0 kept=true
2026-10-01T12:25:01Z pherc0191_fl-pherc0191_r1s6 official tiles=8 area_cm2=31.132229399474326 source=auto
2026-10-01T12:26:12Z pherc0191_fl-pherc0191_r1s8 grow rc=0 area_cm2=31.13086679188979 selfx=0 kept=true
2026-10-01T12:55:44Z pherc0191_fl-pherc0191_r1s8 official tiles=8 area_cm2=31.13086679188979 source=auto
2026-10-01T12:56:55Z pherc0191_fl-pherc0191_r1s10 grow rc=0 area_cm2=31.132899099308567 selfx=0 kept=true
2026-10-01T13:25:34Z pherc0191_fl-pherc0191_r1s10 official tiles=8 area_cm2=31.132899099308567 source=auto
2026-10-01T13:26:57Z pherc0191_fl-pherc0191_r1s12 grow rc=0 area_cm2=31.16139497734547 selfx=0 kept=true
2026-10-01T13:57:36Z pherc0191_fl-pherc0191_r1s12 official tiles=8 area_cm2=31.16139497734547 source=auto
2026-10-01T13:58:47Z pherc0191_fl-pherc0191_r1s14 grow rc=0 area_cm2=31.132538136861253 selfx=0 kept=true
2026-10-01T14:37:14Z pherc0191_fl-pherc0191_r1s14 official tiles=8 area_cm2=31.132538136861253 source=auto
2026-10-01T14:38:23Z pherc0191_fl-pherc0191_r1s16 grow rc=0 area_cm2=31.135020490024143 selfx=0 kept=true
2026-10-01T15:07:58Z pherc0191_fl-pherc0191_r1s16 official tiles=8 area_cm2=31.135020490024143 source=auto
2026-10-01T15:09:16Z pherc0191_fl-pherc0191_r1s18 grow rc=0 area_cm2=31.136709410195678 selfx=0 kept=true
2026-10-01T15:42:03Z pherc0191_fl-pherc0191_r1s18 official tiles=8 area_cm2=31.136709410195678 source=auto
2026-10-01T15:43:11Z pherc0191_fl-pherc0191_r1s20 grow rc=0 area_cm2=31.130538517629894 selfx=0 kept=true
2026-10-01T16:23:17Z pherc0191_fl-pherc0191_r1s20 official tiles=8 area_cm2=31.130538517629894 source=auto
2026-10-01T16:24:37Z pherc0191_fl-pherc0191_r1s22 grow rc=0 area_cm2=31.139764990013987 selfx=0 kept=true
2026-10-01T17:02:20Z pherc0191_fl-pherc0191_r1s22 official tiles=8 area_cm2=31.139764990013987 source=auto
2026-10-01T17:03:42Z pherc0191_fl-pherc0191_r1s24 grow rc=0 area_cm2=31.132732210315236 selfx=0 kept=true
2026-10-01T17:18:57Z STOPPED by DECL-FL-4-A1 (orchestrator 17:18Z: whole fleet on PHerc0268/PHerc0490A); FL2 PHerc0191 outputs as pushed
