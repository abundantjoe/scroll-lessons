import boto3, sys
from botocore import UNSIGNED
from botocore.config import Config
s3=boto3.client('s3',config=Config(signature_version=UNSIGNED))
B='vesuvius-challenge-open-data'
def ls(prefix,delim='/'):
    p=s3.get_paginator('list_objects_v2'); pre=[];obj=[]
    for page in p.paginate(Bucket=B,Prefix=prefix,Delimiter=delim) if delim else p.paginate(Bucket=B,Prefix=prefix):
        pre+= [c['Prefix'] for c in page.get('CommonPrefixes',[])]
        obj+= [(o['Key'],o['Size']) for o in page.get('Contents',[])]
    return pre,obj
if __name__=='__main__':
    pre,obj=ls(sys.argv[1], None if len(sys.argv)>2 else '/')
    for x in pre: print('P',x)
    for k,s in obj: print('O',k,s)
