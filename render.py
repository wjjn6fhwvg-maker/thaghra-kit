import json, sys, os, html, subprocess, re
from playwright.sync_api import sync_playwright
THEMES = {"warn": ("#F97316", "249,115,22"), "hack": ("#A78BFA", "167,139,250"), "new": ("#2DD4BF", "45,212,191"),
 "rumor": ("#EF4444", "239,68,68"), "aware": ("#38BDF8", "56,189,248"), "local": ("#4ADE80", "74,222,128")}
ICONS = {
 "warn": '<path d="M12 3 L22 20 H2 Z"/><path d="M12 9v5"/><path d="M12 17.2v.1"/>',
 "hack": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 7.6-1.7"/><path d="M12.5 12.5l-1.5 3 2 1.2-1.5 3"/>',
 "new": '<rect x="6" y="2.5" width="11" height="19" rx="2.2"/><path d="M10.5 18.5h2"/><path d="M20 1.5v4M18 3.5h4"/>',
 "rumor": '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6"/><path d="M15 9l-6 6"/>',
 "aware": '<path d="M12 2.5l8 3v6c0 5-3.5 8.6-8 10.5-4.5-1.9-8-5.5-8-10.5v-6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
 "local": '<path d="M12 21.5s7-6.5 7-11.5a7 7 0 0 0-14 0c0 5 7 11.5 7 11.5z"/><circle cx="12" cy="10" r="2.6"/>'}
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:%(w)dpx;height:%(h)dpx;background:#0B1220;overflow:hidden}
body{font-family:'Readex Pro',sans-serif;color:#F1F5F9;direction:rtl;position:relative;
 background-image:repeating-linear-gradient(0deg,rgba(148,163,184,.06) 0 1px,transparent 1px 54px),
 repeating-linear-gradient(90deg,rgba(148,163,184,.06) 0 1px,transparent 1px 54px)}
.slash{position:absolute;left:-200px;right:-200px;top:%(slash)dpx;height:14px;background:#0B1220;
 transform:rotate(-8deg);border-top:2px solid %(a)s;border-bottom:2px solid %(a)s;opacity:.28;
 box-shadow:0 0 30px rgba(%(ag)s,.35)}
.top{position:absolute;top:%(pad)dpx;right:84px;left:84px;display:flex;justify-content:space-between;align-items:center}
.logo{position:relative;font-weight:700;font-size:56px;line-height:1.1}
.logo i{position:absolute;left:-12px;right:-12px;top:50%%;height:6px;background:#0B1220;transform:rotate(-14deg);
 border-top:1.5px solid %(a)s;border-bottom:1.5px solid %(a)s;box-shadow:0 0 12px rgba(%(ag)s,.6)}
.count{font-family:'IBM Plex Mono',monospace;font-size:26px;color:#94A3B8;direction:ltr}
.main{position:absolute;right:84px;left:84px;top:50%%;transform:translateY(-50%%);display:flex;flex-direction:column;gap:34px}
.kicker{align-self:flex-start;background:%(a)s;color:#0B1220;font-weight:700;font-size:34px;padding:10px 30px;border-radius:999px}
.num{font-family:'IBM Plex Mono',monospace;font-size:120px;color:%(a)s;line-height:1;direction:ltr;text-align:right}
.title{font-weight:700;font-size:%(tsize)dpx;line-height:1.35}
.body{font-weight:400;font-size:42px;line-height:1.6;color:#CBD5E1;white-space:pre-line}
.foot{position:absolute;bottom:%(pad)dpx;right:84px;left:84px;display:flex;justify-content:space-between;align-items:center;
 font-size:30px;color:#94A3B8}
.foot b{font-family:'IBM Plex Mono',monospace;font-weight:500;color:%(a)s;direction:ltr}
.swipe{color:#F1F5F9}
.lt{direction:ltr;unicode-bidi:isolate;white-space:nowrap}
.icon{width:130px;height:130px;align-self:flex-start;filter:drop-shadow(0 0 18px rgba(%(ag)s,.6))}
.icon *{fill:none;stroke:%(a)s;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.claim{position:relative;align-self:flex-start;font-size:44px;color:#94A3B8;line-height:1.4}
.claim s{position:absolute;right:-10px;left:-10px;top:52%%;height:7px;background:%(a)s;border-radius:4px}
.stamp{position:absolute;left:0;top:0;border:7px solid %(a)s;color:%(a)s;font-weight:700;font-size:70px;padding:4px 32px;border-radius:18px;transform:rotate(-12deg);background:rgba(11,18,32,.6)}
"""
LAT = re.compile(r'[A-Za-z][A-Za-z0-9+&_\-]*(?:[ .][A-Za-z0-9][A-Za-z0-9+&_\-]*)*')
def bidi(t):
    o, i = [], 0
    for m in LAT.finditer(t):
        o.append(html.escape(t[i:m.start()]) + '<span class="lt">' + html.escape(m.group()) + '</span>')
        i = m.end()
    return ''.join(o) + html.escape(t[i:])
def slide_html(s, i, n, w, h, theme='new'):
    e = lambda k: bidi(str(s.get(k, "")))
    kind = s.get("kind", "point")
    big = kind in ("hook", "cta")
    a, ag = THEMES.get(theme, THEMES["new"])
    css = CSS % {"w": w, "h": h, "a": a, "ag": ag, "pad": 110 if h > 1500 else 76,
                 "slash": int(h * 0.80), "tsize": 84 if big else 64}
    parts = []
    if kind == "hook":
        parts.append(f'<svg class="icon" viewBox="0 0 24 24">{ICONS.get(theme, ICONS["aware"])}</svg>')
        if theme == "rumor":
            parts.append('<div class="stamp">إشاعة</div>')
    if kind == "hook" and s.get("kicker"):
        parts.append(f'<div class="kicker">{e("kicker")}</div>')
    if kind == "point" and s.get("num"):
        parts.append(f'<div class="num">{e("num")}</div>')
    if kind == "hook" and s.get("claim"):
        parts.append(f'<div class="claim">{e("claim")}<s></s></div>')
    parts.append(f'<div class="title">{e("title")}</div>')
    if s.get("body"):
        parts.append(f'<div class="body">{e("body")}</div>')
    swipe = '<span class="swipe">اسحب ←</span>' if i < n - 1 else '<span>تابع ثغرة للمزيد 🔒</span>'
    return f"""<!doctype html><html lang="ar"><head><meta charset="utf-8"><style>{css}</style></head><body>
<div class="slash"></div>
<div class="top"><div class="logo">ثغرة<i></i></div><div class="count">{i+1}/{n}</div></div>
<div class="main">{''.join(parts)}</div>
<div class="foot">{swipe}<b>@thaghra_ar</b></div></body></html>"""
def main(src, out):
    post = json.load(open(src, encoding="utf-8"))
    slides, slug, theme = [dict(s, num=f"{int(s['num']):02d}") if str(s.get("num", "")).isdigit() else s for s in post["slides"]], post.get("slug", "post"), post.get("theme", "new")
    os.makedirs(out, exist_ok=True)
    car, vid = [], []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for (w, h, tag, acc) in ((1080, 1350, "carousel", car), (1080, 1920, "story", vid)):
            pg = b.new_page(viewport={"width": w, "height": h})
            for i, s in enumerate(slides):
                pg.set_content(slide_html(s, i, len(slides), w, h, theme))
                pg.evaluate("document.fonts.ready")
                pg.wait_for_timeout(150)
                f = os.path.join(out, f"{slug}_{tag}_{i+1}.png")
                pg.screenshot(path=f)
                acc.append(f)
        b.close()
    d, x = 4.0, 0.5
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for f in vid:
        cmd += ["-loop", "1", "-t", str(d), "-i", f]
    fc, last = [], "0:v"
    for i in range(1, len(vid)):
        o = f"v{i}"
        fc.append(f"[{last}][{i}:v]xfade=transition=slideleft:duration={x}:offset={i*(d-x):.2f}[{o}]")
        last = o
    mp4 = os.path.join(out, f"{slug}_reel.mp4")
    if fc:
        cmd += ["-filter_complex", ";".join(fc), "-map", f"[{last}]"]
    cmd += ["-r", "30", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "20", mp4]
    subprocess.run(cmd, check=True)
    cover = os.path.join(out, f"{slug}_cover.png")
    os.replace(vid[0], cover)
    for f in vid[1:]:
        os.remove(f)
    print("\n".join(car + [cover, mp4]))
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
