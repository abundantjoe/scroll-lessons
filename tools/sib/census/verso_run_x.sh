#!/bin/bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# EXTRA list (DECL-P4-26-A2-E2, logs/p4/verso_assign_x.json extra.census). Verso-mode (and forward) S1 maps for "census" (RULES.md DECL-P4-26-A2, -E1; tools/p4/BRIEF_VERSO.md sha256 377fa355...).
# Lanes: A takes verso list items 0,2,4,6; B takes 1,3,5,7. Per tile: verso map (tools/p4/infer_verso.py, staging
# /work/own/verso_<lane>), then, if the tile is on the forward list, its forward map (infer.py, /work/own/fwdx_<lane>),
# back to back so its CT chunks are fetched once. Code, model, options and lists unchanged. Maps are never opened.
cd /home/user/dominion
ST=logs/sib/census/STATUS.md
BR=claude/gifted-bell-gavnl5-sib-census
VOUT=logs/sib/census/verso/tiles
FOUT=logs/sib/census/fwd_x/tiles
MODEL="--model /work/own/arm_S1/model_final.pth --summary /work/own/arm_S1/summary.json"
MSGTAIL='

Provenance: Project HERCULES | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01FkYMAaqXwtCQvWWKzL2Gvv'
chk() { [ "$(sha256sum "$1" | cut -d' ' -f1)" = "$2" ] || { echo "sha256 mismatch $1"; exit 5; }; }
chk tools/p4/infer_verso.py a1bd1f248cc6b49263f9a01dd7041b1123864f571b129fad643779c4ccb92b90
chk tools/sib/own-lead/own_common.py ddf9077087a85a7bce44139b6ea56e6ea1dbed37353c30e3a25af58ba1daf3b9
chk tools/sib/own-lead/infer.py 36a64e1ac07eea859bb586a484300ace048e732420167f9bf77516befaccdf2e
chk logs/p4/verso_assign_x.json a3a7083d19bf5201769081170ffbe0b6da06f4b88af3ea4511b4fa14a0cfc1ad
chk /work/own/arm_S1/model_final.pth bfa9f7a62097374b93e87c7b406a9c3eba6b77dca3d9f79c10300fa0114daea5
mkdir -p $VOUT $FOUT

status() {
  flock /work/own/git.lock bash -c '
    echo "$(date -u +%FT%TZ) $1" >> '"$ST"'
    git add '"$ST"'; git commit -q -m "census: verso status (DECL-P4-26-A2-E2)$2" -- '"$ST"'
    for n in 1 2 3 4; do git push -q origin HEAD:'"$BR"' && break; sleep $((2**n)); done' _ "$1" "$MSGTAIL"
}

push() {  # $1 staging dir, $2 name, $3 dest dir, $4 kind
  flock /work/own/git.lock bash -c '
    set -e
    cp '"$1"'/tiles/'"$2"'.png '"$1"'/tiles/'"$2"'.png.json '"$3"'/
    git add '"$3"'/'"$2"'.png '"$3"'/'"$2"'.png.json
    git commit -q -m "census: '"$4"' S1 map '"$2"' (DECL-P4-26-A2-E2)$1" -- '"$3"'/'"$2"'.png '"$3"'/'"$2"'.png.json
    for n in 1 2 3 4; do git push -q origin HEAD:'"$BR"' && break; sleep $((2**n)); done' _ "$MSGTAIL"
  status "$4 $2 png_sha256 $(sha256sum $3/$2.png | cut -d' ' -f1)"
}

/opt/ckb/bin/python - <<'EOF'
import json
h = json.load(open('logs/p4/verso_assign_x.json'))['extra']['census']
v, f = h['verso'], set(h.get('forward', []))
for L, items in (('A', v[0::2]), ('B', v[1::2])):
    open(f'/work/own/versox_lane_{L}.txt', 'w').write(''.join(f"{t} {'F' if t in f else '-'}\n" for t in items))
extra = f - set(v)
assert not extra, f'forward tiles not on the verso list: {extra}'
EOF
status "verso EXTRA start (DECL-P4-26-A2-E2): infer_verso.py a1bd1f24..., infer.py 36a64e1a..., own_common.py ddf90770..., model bfa9f7a6..., extra list a3a7083d..."

lane() {
  L=$1
  while read t fw; do
    seg=${t%%:*}; rc=${t#*:}; r=${rc%,*}; c=${rc#*,}; name=${seg}_r${r}_c${c}
    if ! git cat-file -e origin/$BR:$VOUT/$name.png.json 2>/dev/null; then
      if OWN_WORK=/work/own /opt/ckb/bin/python tools/p4/infer_verso.py $MODEL --tiles "$t" --out /work/own/verso_$L --threads 2 >> /work/own/verso_lane$L.log 2>&1; then
        push /work/own/verso_$L $name $VOUT verso
      else status "FAILED verso $name lane $L"; fi
    fi
    if [ "$fw" = F ] && ! git cat-file -e origin/$BR:$FOUT/$name.png.json 2>/dev/null; then
      if OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/infer.py $MODEL --tiles "$t" --out /work/own/fwdx_$L --threads 2 >> /work/own/fwdx_lane$L.log 2>&1; then
        push /work/own/fwdx_$L $name $FOUT forward
      else status "FAILED forward $name lane $L"; fi
    fi
    git fetch -q origin $BR
  done < /work/own/versox_lane_$L.txt
}

lane A & PA=$!
lane B & PB=$!
wait $PA $PB
git fetch -q origin $BR
NV=$(git ls-tree --name-only origin/$BR $VOUT/ | grep -c '\.png\.json$')
NF=$(git ls-tree --name-only origin/$BR $FOUT/ | grep -c '\.png\.json$')
status "END verso (incl. EXTRA): $NV verso and $NF forward maps pushed"
echo "VERSO_DONE $NV $NF"
