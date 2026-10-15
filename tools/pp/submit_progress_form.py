# Provenance: Project HERCULES | owner the owner | [id removed]
"""Submit one entry to the official September 2026 Progress Prizes Google Form (RULES.md DECL-PP-1, -A1;
OWNER-STANDING-ORDER-4 item 3). The owner authorised submission, pre-accepted the form's terms, and granted the
permission (owner message 2026-09-27 ~01:25Z: "All permissions were granted ... submit the forms individually for
all three").

usage: submit_progress_form.py <tool> [--send]
  The URL and contribution text come from logs/pp/SUBMIT_SHEET.md (the "## N. <tool>: contribution text" section
  and the status table). The entrant's name, email and team line come from /work/pp/entrant.json (local only; no
  personal data in the repository).
  Without --send: re-fetch the live form, check the field ids and title, and print the payload keys and sizes.
  With --send: refuse unless the sheet marks the tool READY; POST to formResponse; append a record without
  personal data to logs/pp/submissions.jsonl; exit 2 if the confirmation page is not returned.
"""
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request

FORM = 'https://docs.google.com/forms/d/e/1FAIpQLScNBMj25FMnphngRG1Ciryv_2_Mkdq2YPJOD9WqPfZExII2iQ'
FIELDS = {'1208722520': 'name', '1602765710': 'team', '2107367529': 'discord', '1701067692': 'url',
          '1993829763': 'contribution', '564712824': 'terms'}
TERMS = 'Yes, I agree'
SHEET = 'logs/pp/SUBMIT_SHEET.md'
LOG = 'logs/pp/submissions.jsonl'


def live_form():
    h = urllib.request.urlopen(FORM + '/viewform', timeout=60).read().decode('utf-8', 'ignore')
    d = json.loads(re.search(r'FB_PUBLIC_LOAD_DATA_ = (.*?);</script>', h, re.S).group(1))
    ids = {str(it[4][0][0]) for it in d[1][1] if it[4]}
    fbzx = re.search(r'name="fbzx" value="([^"]+)"', h).group(1)
    return d[1][8], ids, fbzx


def from_sheet(tool):
    s = open(SHEET, encoding='utf-8').read()
    row = re.search(r'^\| ' + re.escape(tool) + r' \| (\S+) \| ([^|]+)\|', s, re.M)
    sec = re.search(r'^## \d+\. ' + re.escape(tool) + r': contribution text\n(.*?)(?=\n---\n|\n## |\Z)', s, re.M | re.S)
    assert row and sec, f'{tool}: not found in the sheet'
    return row.group(1), row.group(2).strip(), sec.group(1).strip()


def main(tool, send=False):
    url, status, text = from_sheet(tool)
    who = json.load(open('/work/pp/entrant.json'))
    title, ids, fbzx = live_form()
    assert set(FIELDS) <= ids, f'form changed: missing {sorted(set(FIELDS) - ids)}'
    assert title.startswith('September 2026 Progress Prizes'), title
    data = {'entry.1208722520': who['name'], 'entry.1602765710': who['team'], 'entry.1701067692': url,
            'entry.1993829763': text, 'entry.564712824': TERMS, 'emailAddress': who['email'],
            'fvv': '1', 'pageHistory': '0', 'fbzx': fbzx}
    if who.get('discord'):
        data['entry.2107367529'] = who['discord']
    print(json.dumps({'form': title, 'tool': tool, 'url': url, 'status': status, 'keys': sorted(data),
                      'contribution_chars': len(text)}))
    if not send:
        return
    assert status.startswith('READY'), f'{tool} is not READY in the sheet: {status}'
    req = urllib.request.Request(FORM + '/formResponse', data=urllib.parse.urlencode(data).encode(),
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
    r = urllib.request.urlopen(req, timeout=60)
    page = r.read().decode('utf-8', 'ignore')
    ok = r.status == 200 and ('response has been recorded' in page.lower()
                              or 'freebirdFormviewerViewResponseConfirmationMessage' in page)
    rec = {'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'tool': tool, 'url': url, 'http': r.status,
           'confirmed': ok, 'form': title, 'contribution_sha256': hashlib.sha256(text.encode()).hexdigest()}
    with open(LOG, 'a') as fh:
        fh.write(json.dumps(rec) + '\n')
    print(json.dumps(rec))
    if not ok:
        sys.exit(2)


if __name__ == '__main__':
    main(sys.argv[1], '--send' in sys.argv[2:])
