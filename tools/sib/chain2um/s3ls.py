# Provenance: Project HERCULES | owner the owner | [id removed]
# Anonymous S3 listing of s3://vesuvius-challenge-open-data (REST, no credentials). Prints key and size.
import sys, re, urllib.request, urllib.parse
B = 'https://vesuvius-challenge-open-data.s3.amazonaws.com/'
def ls(prefix, delim='/', maxn=100000):
    tok = None; out = []; pre = []
    while True:
        q = {'list-type': '2', 'prefix': prefix}
        if delim: q['delimiter'] = delim
        if tok: q['continuation-token'] = tok
        t = urllib.request.urlopen(B + '?' + urllib.parse.urlencode(q)).read().decode()
        for c in re.findall(r'<Contents>(.*?)</Contents>', t, re.S):
            out.append((re.search(r'<Key>(.*?)</Key>', c).group(1), int(re.search(r'<Size>(\d+)</Size>', c).group(1))))
        pre += re.findall(r'<CommonPrefixes><Prefix>(.*?)</Prefix></CommonPrefixes>', t)
        m = re.search(r'<NextContinuationToken>(.*?)</NextContinuationToken>', t)
        if not m or len(out) >= maxn: return out, pre
        tok = m.group(1)
if __name__ == '__main__':
    d = '' if (len(sys.argv) > 2 and sys.argv[2] == 'r') else '/'
    o, p = ls(sys.argv[1], d)
    for x in p: print('DIR', x)
    for k, s in o: print(s, k)
