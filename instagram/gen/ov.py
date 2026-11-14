import glob,sys
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'.')
P=[]
for m in ['content1','content2','content3']:
    P+=__import__(m).P
F=ImageFont.truetype('/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf',26)
circ=lambda n: chr(0x2460+n-1) if n<=20 else (chr(0x3251+n-21) if n<=35 else chr(0x32B1+n-36))
kind={'C':'カルーセル','R':'リール','P':'本人投稿'}
groups=[P[i:i+5] for i in range(0,30,5)]
TH=330; TW=None
for gi,g in enumerate(groups):
    rows=[]
    for p in g:
        fs=sorted(glob.glob(f"pvall2/{p['no']:02d}_*.png"))
        ims=[]
        for f in fs:
            im=Image.open(f).convert('RGB'); w=int(im.width*TH/im.height); ims.append(im.resize((w,TH)))
        rows.append((p,ims))
    W=max(sum(i.width+8 for i in ims) for _,ims in rows)+20
    H=sum(TH+60 for _ in rows)+20
    S=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(S); y=10
    for p,ims in rows:
        d.text((12,y+8),f"{circ(p['no'])} {p['date']}（{kind[p['kind']]}）{p['slug'].split('_',1)[1]}",fill=(60,50,45),font=F)
        x=12
        for im in ims: S.paste(im,(x,y+48)); x+=im.width+8
        y+=TH+60
    a,b=g[0]['no'],g[-1]['no']
    S.save(f"/mnt/project-files/instagram-posts/15-44_一覧/一覧_{a}-{b}.jpg",quality=85)
    print(a,b,S.size)
