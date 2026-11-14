import sys, os, re, subprocess, html
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageOps, ImageFilter
from content1 import P as P1, TAGS
from content2 import P as P2
from content3 import P as P3
POSTS = P1 + P2 + P3

LIB = "/mnt/project-files/"
REPO = "/home/user/repo/instagram/"
RAW = open(os.path.dirname(os.path.abspath(__file__))+"/raw.txt").read().strip()
FONT = "'Noto Sans JP', sans-serif"
SERIF = "'Cormorant Garamond', serif"
C_TEXT = "#3d3530"; C_BODY = "#4d4642"; C_SAGE = "#8f9c80"; C_ROSE = "#c27c6a"; C_GRAY = "#8a8582"; C_BG = "#f6f2ec"; C_BOX = "#ebe0d5"

def load_photo(src, t):
    p = LIB + src
    if src.endswith(".mp4"):
        out = "/tmp/claude-0/-home-user/2c1f4fd5-c4d0-5f9f-9d39-a5e643cc321c/scratchpad/fr_%s_%s.png" % (os.path.basename(src), t)
        if not os.path.exists(out):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", p, "-frames:v", "1", out], check=True)
        p = out
    return ImageOps.exif_transpose(Image.open(p)).convert("L")

def cover_bg(post, W, H, gtop):
    src, t, yf = post["photo"]
    im = load_photo(src, t)
    w, h = im.size
    Hp = min(H, gtop + 140)
    s = max(W / w, Hp / h)
    im = im.resize((int(w * s + 0.5), int(h * s + 0.5)), Image.LANCZOS)
    w, h = im.size
    top = int((h - Hp) * yf); left = (w - W) // 2
    im = im.crop((left, top, left + W, top + Hp))
    im = ImageOps.autocontrast(im, cutoff=0.5).convert("RGB")
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    canvas.paste(im, (0, 0))
    g1 = gtop + 20; g0 = g1 - 300
    blur = canvas.filter(ImageFilter.GaussianBlur(6))
    white = Image.new("RGB", (W, H), (255, 255, 255))
    mask_b = Image.new("L", (W, H), 0); mask_w = Image.new("L", (W, H), 0)
    for y in range(H):
        a = 0 if y < g0 else min(1, (y - g0) / (g1 - g0))
        mask_b.paste(int(255 * min(1, a * 1.6)), (0, y, W, y + 1))
        mask_w.paste(int(255 * (a ** 1.3) * 0.97), (0, y, W, y + 1))
    canvas = Image.composite(blur, canvas, mask_b)
    canvas = Image.composite(white, canvas, mask_w)
    return canvas

def md(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r'<span style="color:%s;font-weight:700">\1</span>' % C_ROSE, s)
    return s.replace("\n", "<br>")

def nlines(s):
    return s.count("\n") + 1

class Page:
    def __init__(self, W, H, bg=None, img=None):
        self.W, self.H, self.bg, self.img = W, H, bg, img
        self.els = []
    def text(self, x, y, w, s, size, color=C_TEXT, weight=400, lh=1.6, family=FONT, ls=0, align="left", italic=False):
        st = "position:absolute;left:%dpx;top:%dpx;width:%dpx;font-family:%s;font-size:%dpx;line-height:%.2f;color:%s;font-weight:%d;letter-spacing:%dpx;text-align:%s;%s" % (
            x, y, w, family, size, lh, color, weight, ls, align, "font-style:italic;" if italic else "")
        self.els.append('<div style="%s">%s</div>' % (st, s))
        return y + int(size * lh * nlines_html(s))
    def box(self, x, y, w, h, color, r=24):
        self.els.append('<div style="position:absolute;left:%dpx;top:%dpx;width:%dpx;height:%dpx;background:%s;border-radius:%dpx"></div>' % (x, y, w, h, color, r))
    def line(self, x, y, w, color="#d9d0c6"):
        self.els.append('<div style="position:absolute;left:%dpx;top:%dpx;width:%dpx;height:2px;background:%s"></div>' % (x, y, w, color))
    def render(self, label):
        bg = "background:%s;" % self.bg if self.bg else ""
        inner = ""
        if self.img:
            inner += '<img src="%s" style="position:absolute;left:0;top:0;width:%dpx;height:%dpx">' % (self.img, self.W, self.H)
        inner += "\n".join(self.els)
        return '<div data-document-role="page" data-label="%s" style="position:relative;width:%dpx;height:%dpx;overflow:hidden;%s">%s</div>' % (label, self.W, self.H, bg, inner)

def nlines_html(s):
    return s.count("<br>") + 1

# ---------- v2 layout: fixed text heights + content photos ----------
GEN_COVER = {15,17,18,20,23,24,25,29,30,32,33,34,36,37,38,39,40,41}
FACE_COVER = {21,28,35,42,44}
COVER_TOP = {False: 700, True: 880}   # label y (carousel / reel)
TSIZE = {False: 84, True: 88}
IMGKINDS = ("point", "lead", "text")

def cover_photo_h(reel):
    return COVER_TOP[reel] + 10 + 140

def make_overlay(W, H, gtop, path):
    from PIL import Image
    g1 = gtop + 20; g0 = g1 - 300
    im = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    px = im.load()
    for y in range(H):
        a = 0 if y < g0 else min(1, (y - g0) / (g1 - g0))
        al = int(255 * min(1, (a ** 1.3) * 0.97 + (0.03 if a >= 1 else 0)))
        for x in range(W):
            px[x, y] = (255, 255, 255, al)
    im.save(path)

def fit_body(text, size, lh, maxh, minsize):
    while size > minsize and int(size * lh * nlines_html(text)) > maxh:
        size -= 2
    return size

def build(post):
    reel = post["kind"] == "R"
    W, H = (1080, 1920) if reel else (1080, 1350)
    nn = "%02d" % post["no"]
    d = REPO + nn + "/"
    os.makedirs(d, exist_ok=True)
    pages = []
    total = len(post["slides"]) + 1
    X = 80; TW = W - 160
    no = post["no"]

    # ---- cover (fixed title top)
    c = post["cover"]
    gtop = COVER_TOP[reel] + 10
    if no in GEN_COVER or no in FACE_COVER:
        pg = Page(W, H, None)
        hp = cover_photo_h(reel)
        pg.els.append('<img src="%sph_cover.jpg" style="position:absolute;left:0;top:0;width:%dpx;height:%dpx">' % (RAW, W, hp))
        pg.els.append('<img src="%soverlay_%s.png" style="position:absolute;left:0;top:0;width:%dpx;height:%dpx">' % (RAW, "r" if reel else "c", W, H))
    else:
        pg = Page(W, H, "#ffffff", RAW + nn + "/cover_bg.jpg")
        cover_bg(post, W, H, gtop).save(d + "cover_bg.jpg", quality=88)
    lines = c["title"]
    tsize = TSIZE[reel]; tlh = 1.38
    pre = c["pre"] if c["pre"] not in ("保存版",) else ""
    label = "保存版｜食べて整える栄養メモ" if not reel else "食べて整える栄養メモ"
    hook = c.get("hook") or ""
    S = (lambda v: int(v * 1.18)) if reel else (lambda v: v)
    y = COVER_TOP[reel]
    y = pg.text(X, y, TW, html.escape(label), S(28), "#7a7470", 400, 1.6, ls=6)
    y = pg.text(X, y, TW, html.escape(pre) if pre else "&nbsp;", S(40), "#3a3330", 500, 1.5)
    ttl = "<br>".join(html.escape(l) for l in lines)
    if c.get("u"):
        ttl = ttl.replace(html.escape(c["u"]), '<span style="text-decoration:underline">%s</span>' % html.escape(c["u"]), 1)
    y = pg.text(X - 4, y, TW + 20, ttl, tsize, "#2b2522", 700, tlh)
    if hook:
        pg.text(X, y + 30, TW, html.escape(hook), S(28), "#5a5450", 400, 1.6)
    pg.text(W - 80 - 300, H - 70 if not reel else H - 420, 300, "@k_routine22", S(22), "#8a8582", 400, 1.4, align="right")
    pages.append(pg.render("表紙"))

    # ---- content pages
    PH_Y = 150 if not reel else 360
    PH_H = 500 if not reel else 500
    TY_IMG = PH_Y + PH_H + 60
    TY_NOIMG = PH_Y + 40
    LIMIT = H - 130 if not reel else H - 470
    for i, sl in enumerate(post["slides"], start=2):
        pg = Page(W, H, C_BG)
        top_y = 70 if not reel else 260
        pg.text(X, top_y, 500, "食べて整える栄養メモ", 26, C_SAGE, 400, 1.4, ls=2)
        if not reel:
            pg.text(W - 80 - 300, top_y, 300, "%02d / %02d" % (i, total), 26, C_ROSE, 400, 1.4, ls=4, align="right")
        pg.text(W - 80 - 300, H - 70 if not reel else H - 420, 300, "@k_routine22", 22, "#9a9592", 400, 1.4, align="right")
        kind = sl[0]
        if kind in IMGKINDS:
            pg.els.append('<img src="%sph.jpg" style="position:absolute;left:%dpx;top:%dpx;width:%dpx;height:%dpx;border-radius:24px">' % (RAW, X, PH_Y, TW, PH_H))
            y = TY_IMG
            if kind == "lead":
                _, eb, hd, body = sl
                pre_t = (md(eb), 32, C_SAGE, 400, 1.5, 14, FONT, False)
            elif kind == "point":
                _, num, hd, body = sl
                ser = bool(re.match(r"^[0-9A-Za-z]+$", num))
                pre_t = (html.escape(num), 84 if ser else 52, C_ROSE, 400 if ser else 700, 1.1, 8, SERIF if ser else FONT, ser)
            else:
                _, hd, body = sl
                pre_t = None
            if pre_t:
                pg.text(X, y, TW, pre_t[0], pre_t[1], pre_t[2], pre_t[3], pre_t[4], family=pre_t[6], italic=pre_t[7])
                y += int(pre_t[1] * pre_t[4] * nlines_html(pre_t[0])) + pre_t[5]
            hds = md(hd)
            hsz = 52 if kind != "text" else 46
            pg.text(X, y, TW, hds, hsz, C_TEXT, 700, 1.45)
            y += int(hsz * 1.45 * nlines_html(hds)) + 24
            bd = md(body)
            bsz = fit_body(bd, 34, 1.75, LIMIT - y, 26)
            pg.text(X, y, TW, bd, bsz, C_BODY, 400, 1.75)
        else:
            y = TY_NOIMG
            if kind == "check":
                _, eb, items, note = sl
                y = pg.text(X, y, TW, md(eb), 38, C_SAGE, 400, 1.5) + 30
                for it in items:
                    pg.els.append('<div style="position:absolute;left:%dpx;top:%dpx;width:26px;height:26px;border:2px solid #b9aea4;border-radius:4px;background:#ffffff"></div>' % (X, y + 22))
                    pg.text(X + 52, y + 8, TW - 52, md(it), 42, C_TEXT, 400, 1.5)
                    pg.line(X, y + 96, TW)
                    y += 102
                pg.text(X, y + 30, TW, md(note), 26, C_GRAY, 400, 1.6)
            elif kind == "compare":
                _, eb, hd, rows, heads = sl
                y = pg.text(X, y, TW, md(eb), 32, C_SAGE, 400, 1.5) + 14
                y = pg.text(X, y, TW, md(hd), 52, C_TEXT, 700, 1.45) + 40
                cw = (TW - 40) // 2
                pg.text(X, y, cw, html.escape(heads[0]), 30, C_GRAY, 700, 1.5, align="center")
                pg.text(X + cw + 40, y, cw, html.escape(heads[1]), 30, C_ROSE, 700, 1.5, align="center")
                y += 60
                for a, bb in rows:
                    rh = int(34 * 1.55 * max(nlines(a), nlines(bb))) + 60
                    pg.box(X, y, cw, rh, "#ffffff", 20)
                    pg.box(X + cw + 40, y, cw, rh, C_BOX, 20)
                    pg.text(X + 20, y + 30, cw - 40, md(a), 34, C_GRAY, 400, 1.55, align="center")
                    pg.text(X + cw + 60, y + 30, cw - 40, md(bb), 34, C_TEXT, 700, 1.55, align="center")
                    pg.text(X + cw - 2, y + rh // 2 - 26, 44, "→", 34, C_ROSE, 700, 1.4, align="center")
                    y += rh + 30
            elif kind == "summary":
                _, items, cta, note = sl
                y = pg.text(X, y, TW, "まとめ", 52, C_TEXT, 700, 1.4) + 30
                hh = len(items) * int(36 * 1.9) + 100
                pg.box(X, y, TW, hh, C_BOX, 28)
                pg.text(X + 44, y + 50, TW - 88, "<br>".join(md(s_) for s_ in items), 36, C_TEXT, 400, 1.9)
                y += hh + 40
                y = pg.text(X, y, TW, md(cta), 34, C_BODY, 400, 1.7) + 24
                if note and note.startswith("Lien"):
                    y = pg.text(X, y, TW, md(note), 28, C_BODY, 400, 1.6) + 14
                y = pg.text(X, y, TW, "フォローで毎日の栄養メモが届きます", 30, C_ROSE, 700, 1.6) + 14
                if note and not note.startswith("Lien"):
                    pg.text(X, y, TW, md(note), 26, C_GRAY, 400, 1.6)
        pages.append(pg.render("%02d" % i))

    doc = '<!doctype html><html><head><meta charset="utf-8"><title>%s</title><style>body{margin:0}</style></head><body>\n%s\n</body></html>' % (post["slug"], "\n".join(pages))
    open(d + "post.html", "w").write(doc)
    return nn

if __name__ == "__main__":
    only = set(int(a) for a in sys.argv[1:])
    for p in POSTS:
        if only and p["no"] not in only:
            continue
        print(build(p), p["slug"], len(p["slides"]) + 1)
