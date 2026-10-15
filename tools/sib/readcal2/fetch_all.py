# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fetch plan for readcal2 (official bucket only; every object hashed in downloads.jsonl).
- every PHerc0139 and PHerc0814 segment: the 9.362 um organizer tifxyz (x/y/z/meta; ~0.8 MB per band)
- candidate segments: the organizer 2.399 um reference ink map (20260417190342 new_canon, ~80 MB) + ink-detection listing
- volume metadata.json of the 9.362 um volumes (voxel size, I9)
No surface volume, CT volume or image is downloaded here."""
import sys
import s3fetch as F

NINE = {'PHerc0139': '20250728140407', 'PHerc0814': '20250804134230'}
VOLS = {'PHerc0139': '20250728140407-9.362um-1.2m-113keV-masked.zarr',
        'PHerc0814': '20250804134230-9.362um-1.2m-113keV-masked.zarr'}
CAND_0139 = ['w024', 'w047', 'w053', 'w023', 'w025', 'w026', 'w037', 'w048', 'w049', 'w050', 'w051', 'w052',
             'w054', 'w055', 'w056', 'w057']
CAND_0814 = ['20250925204843', '20250926165636', '20251001060526', '20250925222237', '20250925212701',
             '20260226123353', '20260225160055']


def segs(scroll):
    _, pre = F.ls(f'{scroll}/segments/', '/')
    return [p.split('/')[-2] for p in pre if not p.endswith('raw/')]


def main(what):
    for scroll in ('PHerc0139', 'PHerc0814'):
        for k in ('metadata.json', '.zattrs', '.zgroup'):
            objs, _ = F.ls(f'{scroll}/volumes/{VOLS[scroll]}/{k}')
            for o in objs:
                F.get(o['Key'], o['Size'], o['ETag'])
        for sid in segs(scroll):
            ts = sid.split('-')[0]
            objs, _ = F.ls(f'{scroll}/segments/{sid}/mesh/{ts}-on-{NINE[scroll]}-')
            for o in objs:
                F.get(o['Key'], o['Size'], o['ETag'])
            short = sid.split('-')[1].split('_')[0] if scroll == 'PHerc0139' else ts
            cand = CAND_0139 if scroll == 'PHerc0139' else CAND_0814
            if what == 'all' and short in cand:
                objs, _ = F.ls(f'{scroll}/segments/{sid}/ink-detection/', '/')
                for o in objs:
                    if '20260417190342' in o['Key'] and o['Key'].endswith('.tif') and '2.399um' in o['Key']:
                        F.get(o['Key'], o['Size'], o['ETag'])
                        print('ink', sid, o['Size'], flush=True)
            print('mesh', sid, flush=True)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'all')
