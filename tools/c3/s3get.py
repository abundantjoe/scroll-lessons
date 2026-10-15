# Provenance: Project HERCULES | owner the owner | [id removed]
# Download listed keys from s3://vesuvius-challenge-open-data (anonymous) into /work/c3/data/s3/<key>
import sys, os, hashlib, boto3
from botocore import UNSIGNED
from botocore.config import Config
s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
root = '/work/c3/data/s3'
for key in sys.argv[1:]:
    dst = os.path.join(root, key)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst):
        s3.download_file('vesuvius-challenge-open-data', key, dst)
    h = hashlib.sha256(open(dst, 'rb').read()).hexdigest()
    print(key, os.path.getsize(dst), h)
