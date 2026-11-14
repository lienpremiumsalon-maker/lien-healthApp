import json,sys
m=json.load(open('media.json')); r=json.load(open('reuse.json'))
def pages(n):
    h=open(f'/home/user/repo/instagram/{n:02d}/post.html').read()
    ps=h.split('data-document-role')[1:]
    return [i+1 for i,p in enumerate(ps) if 'ph.jpg' in p and i>0]
def mid(k):
    k=r.get(k,k); return m.get(k)
for n in map(int,sys.argv[1:]):
    out=[(p,mid(f'{n:02d}_{p:02d}')) for p in pages(n)]
    print(n,'cover',m.get(f'c{n}'),out)
