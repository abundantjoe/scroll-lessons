Provenance: Project HERCULES | owner the owner | [id removed]

DRAFT - NOT SUBMITTED - the owner files (DECL-P4-1); the organizers' papyrologists read the image; the project names no title words
DRY RUN - NOT A CANDIDATE - NOT FOR SUBMISSION

## Methodology (TP-09, TP-10, TP-11)

Scan: PHerc. Paris 4 (Scroll 1), volume 00000000000000, voxel size 2.4 um from the volume's metadata.json (TP-06).

Ink map: the organizers' published prediction of model DRYRUN-MODEL on volume 00000000000000 for segment DRYRUN-SEGMENT (sha256 3333333333333333333333333333333333333333333333333333333333333333), used exactly as published. No ink model was trained or run by the project.

Surface: official mesh dryrun_p4_crop.tifxyz (sha256 4444444444444444444444444444444444444444444444444444444444444444), cropped by code to the candidate tile plus 10 mm on each side and flattened with vc_flatten (FLAT-1); quads whose edges all lie within 5 % of their three-dimensional lengths: 95 % (declared reporting bar 93.1 %).

Images (TP-02, TP-03, TP-05): the official prediction over the crop, raw; and a linear 1 to 99 percentile window slab-mean render of CT volume 00000000000000 over the same crop. Both come from the submitted mesh by code, without any annotation of characters or text.

Search: the prediction canvas was cut into tiles of 20 mm; 171 tiles (684 cm²) were read once each in the census by fresh blind machine readers, and candidates were confirmed by fresh readers in a second phase (DECL-P4-2). Reader key sheet: sigma2 (lunate and normal sigma shown) (DECL-P4-2-A2; sha256 6666666666666666666666666666666666666666666666666666666666666666).

Reproduction: container dryrun/container:v1 (sha256 5555555555555555555555555555555555555555555555555555555555555555); system requirements: 4 vCPU, 15 GB RAM, no GPU. Human in the loop: none (no manual annotation; the owner files).
