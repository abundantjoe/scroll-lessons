Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal (builder; not a declaration): name the 2.4 um text order by render frame

Evidence: logs/sib/chain2um/REPORT.md section 1 (w043 control, 0.185 cm^2).

1. The C5 render is `vc_render_tifxyz -n 63 --flip-normals` (slice k = offset k - 31 along the negated normal). It is accepted as organizer-frame only if it matches the organizer 2.399 um surface volume slices k + 23 on >= 4 code-chosen 256 x 256 regions with pooled Pearson >= 0.9999 (measured 0.999997-0.999998). On 0841, where no organizer 2.4 um SV is fetched, the equivalent check is made on a few fetched SV chunks before any inference.
2. The text order of ink_canonical_2um on such a render is the official FORWARD order (optimized_inference infer, is_reverse_segment False, layers [0, 62)). Measured on w043: r = 0.99999 vs the organizer map, AUC 0.888 vs labels; official REVERSE: r = -0.06, AUC 0.47.
3. Records that say "REVERSE" for the text order (the recorded GATE-E2E values, DECL-CHAINVALID wording) are read as "the text order in a render frame with the opposite normal". Rule R on 0841 is stated as a frame plus an official order flag, never as a bare word.
4. GATE-E2E-0139 scoring overlaps are named explicitly (segment, bbox, label set) before scoring. Because the organizer map itself scores AUC 0.888 on the w043 control, the orchestrator may add a companion bar "r vs organizer map >= 0.95 on the same pixels". That is an addition, not a replacement: the declared AUC >= 0.90 bar stays as declared unless the orchestrator records otherwise.
