import sys, os, re, subprocess, html
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageOps, ImageFilter
from content1 import P as P1, TAGS
from content2 import P as P2
from content3 import P as P3
POSTS = P1 + P2 + P3

LIB = "/mnt/project-files/"
REPO = "/home/user/repo/instagram/"
RAW = "https://raw.githubusercontent.com/lienpremiumsalon-maker/lien-healthApp/77f518608ba5eb4416fa7773042910de26e67c42/instagram/"
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

def build(post):
    reel = post["kind"] == "R"
    W, H = (1080, 1920) if reel else (1080, 1350)
    nn = "%02d" % post["no"]
    d = REPO + nn + "/"
    os.makedirs(d, exist_ok=True)
    pages = []
    total = len(post["slides"]) + 1
    X = 80; TW = W - 160
    S = (lambda v: int(v * 1.18)) if reel else (lambda v: v)

    # ---- cover
    c = post["cover"]
    pg = Page(W, H, "#ffffff", RAW + nn + "/cover_bg.jpg")
    lines = c["title"]
    maxlen = max(len(l) for l in lines)
    tsize = min(S(84), int(TW / (maxlen + 0.3)))
    tlh = 1.38
    pre = c["pre"] if c["pre"] not in ("保存版",) else ""
    label = "保存版｜食べて整える栄養メモ" if not reel else "食べて整える栄養メモ"
    hook = c.get("hook") or ""
    bottom = H - 120 if not reel else H - 470
    hgt = int(S(28) * 1.6) + (int(S(40) * 1.5) if pre else 0) + int(tsize * tlh * len(lines)) + (int(S(28) * 1.6) + 30 if hook else 0)
    y = bottom - hgt
    cover_bg(post, W, H, y + 10).save(d + "cover_bg.jpg", quality=88)
    y = pg.text(X, y, TW, html.escape(label), S(28), "#7a7470", 400, 1.6, ls=6)
    if pre:
        y = pg.text(X, y, TW, html.escape(pre), S(40), "#3a3330", 500, 1.5)
    ttl = "<br>".join(html.escape(l) for l in lines)
    if c.get("u"):
        ttl = ttl.replace(html.escape(c["u"]), '<span style="text-decoration:underline">%s</span>' % html.escape(c["u"]), 1)
    y = pg.text(X - 4, y, TW + 20, ttl, tsize, "#2b2522", 700, tlh)
    if hook:
        pg.text(X, y + 30, TW, html.escape(hook), S(28), "#5a5450", 400, 1.6)
    pg.text(W - 80 - 300, H - 70 if not reel else H - 420, 300, "@k_routine22", S(22), "#8a8582", 400, 1.4, align="right")
    pages.append(pg.render("表紙"))

    # ---- content pages
    for i, sl in enumerate(post["slides"], start=2):
        pg = Page(W, H, C_BG)
        top_y = 70 if not reel else 260
        pg.text(X, top_y, 500, "食べて整える栄養メモ", S(26), C_SAGE, 400, 1.4, ls=2)
        if not reel:
            pg.text(W - 80 - 300, top_y, 300, "%02d / %02d" % (i, total), S(26), C_ROSE, 400, 1.4, ls=4, align="right")
        pg.text(W - 80 - 300, H - 70 if not reel else H - 420, 300, "@k_routine22", S(22), "#9a9592", 400, 1.4, align="right")
        kind = sl[0]
        blocks = []  # (callable, height)
        if kind == "lead":
            _, eb, hd, body = sl
            blocks = [("t", md(eb), S(36), C_SAGE, 400, 1.5, 24), ("t", md(hd), S(60), C_TEXT, 700, 1.5, 44), ("t", md(body), S(38), C_BODY, 400, 1.8, 0)]
        elif kind == "point":
            _, num, hd, body = sl
            numsize = S(130) if len(num) <= 3 else S(70)
            fam = SERIF if re.match(r"^[0-9A-Za-z]+$", num) else FONT
            blocks = [("t", html.escape(num), numsize, C_ROSE, 400 if fam == SERIF else 700, 1.15, 20, fam, fam == SERIF),
                      ("t", md(hd), S(60), C_TEXT, 700, 1.5, 44), ("t", md(body), S(38), C_BODY, 400, 1.8, 0)]
        elif kind == "text":
            _, hd, body = sl
            blocks = [("t", md(hd), S(46), C_TEXT, 700, 1.5, 40), ("t", md(body), S(36), C_BODY, 400, 1.85, 0)]
        elif kind == "check":
            _, eb, items, note = sl
            blocks = [("t", md(eb), S(38), C_SAGE, 400, 1.5, 40), ("check", items), ("t", md(note), S(26), C_GRAY, 400, 1.6, 0)]
        elif kind == "compare":
            _, eb, hd, rows, heads = sl
            blocks = [("t", md(eb), S(36), C_SAGE, 400, 1.5, 24), ("t", md(hd), S(56), C_TEXT, 700, 1.45, 44), ("cmp", rows, heads)]
        elif kind == "summary":
            _, items, cta, note = sl
            blocks = [("t", "まとめ", S(56), C_TEXT, 700, 1.4, 40), ("sum", items), ("t", md(cta), S(34), C_BODY, 400, 1.7, 30)]
            if note == "" or note.startswith("Lien"):
                if note:
                    blocks.append(("t", md(note), S(30), C_BODY, 400, 1.6, 10))
                blocks.append(("t", "フォローで毎日の栄養メモが届きます", S(30), C_ROSE, 700, 1.6, 20))
            else:
                blocks.append(("t", "フォローで毎日の栄養メモが届きます", S(30), C_ROSE, 700, 1.6, 20))
                blocks.append(("t", md(note), S(26), C_GRAY, 400, 1.6, 0))
        # measure
        def bh(b):
            if b[0] == "t":
                return int(b[2] * b[5] * nlines_html(b[1])) + b[6]
            if b[0] == "check":
                return len(b[1]) * S(102) + 30
            if b[0] == "sum":
                return len(b[1]) * int(S(36) * 1.9) + 2 * S(50) + 40
            if b[0] == "cmp":
                return S(60) + sum(S(30) + int(S(34) * 1.55 * max(nlines(a), nlines(bb))) + S(30) for a, bb in b[1]) + 10
        tot = sum(bh(b) for b in blocks)
        area_top = 170 if not reel else 420
        area_bot = H - 140 if not reel else H - 500
        y = max(area_top, area_top + (area_bot - area_top - tot) // 2 - 20)
        for b in blocks:
            if b[0] == "t":
                fam = b[7] if len(b) > 7 else FONT
                it = b[8] if len(b) > 8 else False
                pg.text(X, y, TW, b[1], b[2], b[3], b[4], b[5], family=fam, italic=it)
                y += bh(b)
            elif b[0] == "check":
                for it in b[1]:
                    pg.box(X, y + S(22), S(30), S(30), "#ffffff", 4)
                    pg.els.append('<div style="position:absolute;left:%dpx;top:%dpx;width:%dpx;height:%dpx;border:2px solid #b9aea4;border-radius:4px"></div>' % (X, y + S(22), S(30) - 4, S(30) - 4))
                    pg.text(X + S(52), y + S(8), TW - S(52), md(it), S(42), C_TEXT, 400, 1.5)
                    pg.line(X, y + S(96), TW)
                    y += S(102)
                y += 30
            elif b[0] == "sum":
                hh = len(b[1]) * int(S(36) * 1.9) + 2 * S(50)
                pg.box(X, y, TW, hh, C_BOX, 28)
                pg.text(X + S(44), y + S(50), TW - S(88), "<br>".join(md(s) for s in b[1]), S(36), C_TEXT, 400, 1.9)
                y += hh + 40
            elif b[0] == "cmp":
                rows, heads = b[1], b[2]
                cw = (TW - 40) // 2
                pg.text(X, y, cw, html.escape(heads[0]), S(30), C_GRAY, 700, 1.5, align="center")
                pg.text(X + cw + 40, y, cw, html.escape(heads[1]), S(30), C_ROSE, 700, 1.5, align="center")
                y += S(60)
                for a, bb in rows:
                    rh = int(S(34) * 1.55 * max(nlines(a), nlines(bb))) + 2 * S(30)
                    pg.box(X, y, cw, rh, "#ffffff", 20)
                    pg.box(X + cw + 40, y, cw, rh, C_BOX, 20)
                    pg.text(X + 20, y + S(30), cw - 40, md(a), S(34), C_GRAY, 400, 1.55, align="center")
                    pg.text(X + cw + 60, y + S(30), cw - 40, md(bb), S(34), C_TEXT, 700, 1.55, align="center")
                    pg.text(X + cw - 2, y + rh // 2 - S(26), 44, "→", S(34), C_ROSE, 700, 1.4, align="center")
                    y += rh + S(30)
        pages.append(pg.render("%02d" % i))

    doc = '<!doctype html><html><head><meta charset="utf-8"><title>%s</title><style>body{margin:0}</style></head><body>\n%s\n</body></html>' % (post["slug"], "\n".join(pages))
    open(d + "post.html", "w").write(doc)
    cap = post["caption"].strip() + "\n\n" + TAGS + " " + post["tags"] + "\n"
    open(d + "caption.txt", "w").write(cap)
    lib = LIB + "instagram-posts/" + post["slug"] + "/"
    os.makedirs(lib, exist_ok=True)
    open(lib + "キャプション.txt", "w").write(cap)
    return nn

if __name__ == "__main__":
    only = set(int(a) for a in sys.argv[1:])
    for p in POSTS:
        if only and p["no"] not in only:
            continue
        print(build(p), p["slug"], len(p["slides"]) + 1)
