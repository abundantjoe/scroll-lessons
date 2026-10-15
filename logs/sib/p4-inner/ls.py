import sys,urllib.request,xml.etree.ElementTree as ET,urllib.parse
B="https://vesuvius-challenge-open-data.s3.amazonaws.com/"
ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
def ls(prefix,delim='/'):
    tok=None;out=[];pre=[]
    while True:
        q={'list-type':'2','prefix':prefix}
        if delim:q['delimiter']=delim
        if tok:q['continuation-token']=tok
        r=ET.fromstring(urllib.request.urlopen(B+'?'+urllib.parse.urlencode(q)).read())
        out+=[(c.find('s:Key',ns).text,int(c.find('s:Size',ns).text)) for c in r.findall('s:Contents',ns)]
        pre+=[c.find('s:Prefix',ns).text for c in r.findall('s:CommonPrefixes',ns)]
        t=r.find('s:NextContinuationToken',ns)
        if t is None:break
        tok=t.text
    return out,pre
if __name__=='__main__':
    o,p=ls(sys.argv[1],None if len(sys.argv)>2 else '/')
    for x in p:print('D',x)
    for k,s in o:print(s,k)
