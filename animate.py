import json, sys, os, subprocess, shutil, tempfile
from playwright.sync_api import sync_playwright
FPS = 30
DUR = {"hook": 3.6, "point": 3.0, "cta": 3.6}
from render import THEMES as RT, ICONS as RI
THEMES = {k: {"a": v[0], "ag": v[1]} for k, v in RT.items()}
JICONS = json.dumps({k: v.replace('/>', ' pathLength="1"/>') for k, v in RI.items()})
PAGE = r"""<!doctype html><html lang="ar"><head><meta charset="utf-8"><style>
:root{--a:__A__;--ag:__AG__}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0B1220}
body{font-family:'Readex Pro',sans-serif;color:#F1F5F9;direction:rtl;position:relative}
#grid{position:absolute;inset:-120px;background-image:repeating-linear-gradient(0deg,rgba(148,163,184,.07) 0 1px,transparent 1px 60px),repeating-linear-gradient(90deg,rgba(148,163,184,.07) 0 1px,transparent 1px 60px)}
#glow{position:absolute;width:1400px;height:1400px;border-radius:50%;background:radial-gradient(circle,rgba(var(--ag),.17),transparent 62%);left:-160px;top:260px}
#scan{position:absolute;left:0;right:0;height:180px;background:linear-gradient(180deg,transparent,rgba(var(--ag),.07),transparent)}
#vig{position:absolute;inset:0;box-shadow:inset 0 0 260px rgba(var(--ag),.55);opacity:0}
#fx{position:absolute;inset:0;overflow:hidden}
.rain{position:absolute;top:0;font-family:'IBM Plex Mono',monospace;font-size:30px;line-height:1.25;color:var(--a);opacity:.13;white-space:pre;direction:ltr}
.spark{position:absolute;width:8px;height:8px;border-radius:50%;background:var(--a);box-shadow:0 0 14px rgba(var(--ag),.9)}
#slash{position:absolute;left:-300px;right:-300px;height:16px;top:1460px;background:#0B1220;transform:rotate(-8deg);border-top:2px solid var(--a);border-bottom:2px solid var(--a);box-shadow:0 0 34px rgba(var(--ag),.5)}
.top{position:absolute;top:120px;right:90px;left:90px;display:flex;justify-content:space-between;align-items:center;z-index:5}
.logo{position:relative;font-weight:700;font-size:62px;line-height:1.1}
.logo i{position:absolute;left:-12px;right:-12px;top:50%;height:7px;background:#0B1220;transform:rotate(-14deg);border-top:1.5px solid var(--a);border-bottom:1.5px solid var(--a);box-shadow:0 0 12px rgba(var(--ag),.7)}
#bar{position:absolute;top:70px;right:90px;left:90px;height:6px;border-radius:3px;background:rgba(148,163,184,.18);overflow:hidden;z-index:5;direction:ltr}
#bar b{display:block;height:100%;width:0;background:var(--a);margin-left:auto}
.foot{position:absolute;bottom:130px;right:90px;left:90px;display:flex;justify-content:center;font-family:'IBM Plex Mono',monospace;font-size:34px;color:var(--a);direction:ltr;z-index:5}
.scene{position:absolute;right:90px;left:90px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:40px;opacity:0}
.icon{width:190px;height:190px;align-self:flex-start;filter:drop-shadow(0 0 22px rgba(var(--ag),.6))}
.icon *{fill:none;stroke:var(--a);stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.kicker{align-self:flex-start;background:var(--a);color:#0B1220;font-weight:700;font-size:40px;padding:12px 36px;border-radius:999px}
.claim{position:relative;align-self:flex-start;font-size:54px;color:#94A3B8;line-height:1.4}
.claim s{position:absolute;right:-10px;top:52%;height:8px;background:var(--a);border-radius:4px;width:0;box-shadow:0 0 16px rgba(var(--ag),.8)}
.stamp{position:absolute;left:30px;top:30px;border:8px solid var(--a);color:var(--a);font-weight:700;font-size:92px;padding:6px 40px;border-radius:22px;opacity:0;letter-spacing:2px;background:rgba(11,18,32,.6)}
.num{font-family:'IBM Plex Mono',monospace;font-size:170px;color:var(--a);line-height:1;direction:ltr;text-align:right;text-shadow:0 0 40px rgba(var(--ag),.45)}
.title{font-weight:700;line-height:1.35}
.title span{display:inline-block;white-space:pre}
.lt{direction:ltr;unicode-bidi:isolate;white-space:nowrap}
.body{font-size:48px;line-height:1.6;color:#CBD5E1}
.body div{opacity:0}
.big{font-size:96px}.mid{font-size:76px}
#flash{position:absolute;inset:0;background:var(--a);opacity:0;z-index:9;mix-blend-mode:screen}
.rgb{text-shadow:-6px 0 rgba(255,0,80,.7),6px 0 rgba(0,255,255,.7)}
</style></head><body>
<div id="grid"></div><div id="glow"></div><div id="fx"></div><div id="scan"></div><div id="vig"></div><div id="slash"></div>
<div id="bar"><b></b></div>
<div class="top"><div class="logo">ثغرة<i></i></div></div>
<div id="scenes"></div>
<div class="foot">@thaghra_ar</div>
<div id="flash"></div>
<script>
const TH = "__THEME__";
const S = __SLIDES__;
const ICONS = __ICONS__;
const CALM = (TH === 'aware' || TH === 'local');
const STAG = CALM ? .06 : .05, WDUR = CALM ? .25 : .2;
const LAT = /[A-Za-z][A-Za-z0-9+&_\-]*(?:[ .~][A-Za-z0-9][A-Za-z0-9+&_\-]*)*/g;
const esc = x => x.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const bidi = x => { let o = '', i = 0; for (const m of x.matchAll(LAT)) { o += esc(x.slice(i, m.index)) + '<span class="lt">' + esc(m[0].replace(/~/g, ' ')) + '</span>'; i = m.index + m[0].length; } return o + esc(x.slice(i)); };
const rnd = (a) => { const x = Math.sin(a * 91.7 + 13.3) * 43758.5453; return x - Math.floor(x); };
// background fx
const fx = document.getElementById('fx'); const rain = [], sparks = [];
if (TH === 'hack') for (let c = 0; c < 13; c++) { const d = document.createElement('div'); d.className = 'rain';
  let s = ''; for (let r = 0; r < 70; r++) s += (rnd(c * 100 + r) > .5 ? '1' : '0') + (rnd(c * 7 + r * 3) > .7 ? ' ' : '') + '\n';
  d.textContent = s; d.style.left = (c * 84 + 10) + 'px'; fx.appendChild(d); rain.push({el: d, sp: 90 + rnd(c) * 160, off: rnd(c + 50) * 2400}); }
if (TH === 'new' || TH === 'local' || TH === 'aware') for (let i = 0; i < 22; i++) { const d = document.createElement('div'); d.className = 'spark';
  fx.appendChild(d); sparks.push({el: d, x: rnd(i) * 1080, y: rnd(i + 30) * 1920, sp: 30 + rnd(i + 60) * 60, ph: rnd(i + 90) * 6}); }
const root = document.getElementById('scenes');
let t0 = 0; const EXTRA = [];
S.forEach((s, k) => {
  s.start = t0; t0 += s.dur;
  const el = document.createElement('div'); el.className = 'scene'; s.el = el;
  const big = s.kind !== 'point';
  if (s.kind === 'hook') { const ic = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); ic.setAttribute('viewBox', '0 0 24 24'); ic.setAttribute('class', 'icon');
    ic.innerHTML = ICONS[TH] || ICONS.aware; el.appendChild(ic); s.icon = ic; s.iconParts = [...ic.children]; }
  if (s.kind === 'hook' && s.kicker) { const k1 = document.createElement('div'); k1.className='kicker'; k1.textContent = s.kicker; el.appendChild(k1); s.kick = k1; }
  if (s.kind === 'hook' && s.claim) { const c = document.createElement('div'); c.className = 'claim'; c.textContent = s.claim;
    const st = document.createElement('s'); c.appendChild(st); el.appendChild(c); s.claimEl = c; s.strike = st; }
  if (s.kind === 'point' && s.num) { const n = document.createElement('div'); n.className='num'; n.textContent = s.num; el.appendChild(n); s.numEl = n; }
  const ti = document.createElement('div'); ti.className = 'title ' + (big ? 'big' : 'mid'); ti.style.position = 'relative';
  s.words = s.title.replace(LAT, m => m.replace(/ /g, '~')).split(' ').map((w, i, a) => { const sp = document.createElement('span'); sp.innerHTML = bidi(w + (i < a.length - 1 ? ' ' : '')); sp.dataset.w = sp.textContent; sp.dataset.h = sp.innerHTML; ti.appendChild(sp); return sp; });
  el.appendChild(ti);
  if (s.kind === 'hook' && TH === 'rumor') { const st = document.createElement('div'); st.className = 'stamp'; st.textContent = 'إشاعة'; el.appendChild(st); s.stamp = st; }
  s.lines = [];
  if (s.body) { const b = document.createElement('div'); b.className = 'body';
    s.body.split('\n').forEach(l => { const d = document.createElement('div'); d.innerHTML = bidi(l); b.appendChild(d); s.lines.push(d); });
    el.appendChild(b); }
  root.appendChild(el);
});
const TOTAL = t0;
const cl = x => Math.max(0, Math.min(1, x));
const ease = x => 1 - Math.pow(1 - cl(x), 3);
const back = x => { x = cl(x); const c = 1.7; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
const GL = '#$%&@<>/\\|01*+=';
function render(t) {
  const fr = Math.round(t * 30);
  document.getElementById('grid').style.transform = `translate(${(t*14)%60}px, ${(t*22)%60}px)`;
  document.getElementById('glow').style.transform = `translate(${Math.sin(t*.6)*90}px, ${Math.cos(t*.45)*140}px)`;
  document.getElementById('scan').style.top = (((t*(CALM?300:520)) % 2300) - 200) + 'px';
  document.querySelector('#bar b').style.width = (cl(t / TOTAL) * 100) + '%';
  const pulse = Math.pow(.5 + .5 * Math.sin(t * 2 * Math.PI * 1.4), 3);
  document.getElementById('vig').style.opacity = (TH === 'warn' || TH === 'rumor') ? (.25 + .55 * pulse) : 0;
  rain.forEach(r => { r.el.style.transform = `translateY(${((t * r.sp + r.off) % 2400) - 2400 + 1920}px)`; });
  sparks.forEach(p => { const y = ((p.y - t * p.sp) % 1920 + 1920) % 1920; p.el.style.transform = `translate(${p.x + Math.sin(t + p.ph) * 20}px, ${y}px)`;
    p.el.style.opacity = .25 + .6 * Math.pow(.5 + .5 * Math.sin(t * 2.2 + p.ph), 2); });
  let flash = 0;
  S.forEach((s, k) => {
    const lt0 = t - s.start, el = s.el;
    const lt = k === 0 ? lt0 + 1.6 : lt0;
    const vis = lt0 >= 0 && lt0 < s.dur;
    el.style.opacity = vis ? 1 : 0;
    if (!vis) return;
    const out = cl((lt0 - (s.dur - .3)) / .3);
    el.style.transform = `translateY(-50%) translateX(${-out*140}px) scale(${1 + lt0*.012})`;
    el.style.opacity = 1 - out;
    if (!CALM && lt0 < .18 && k > 0) flash = Math.max(flash, (.18 - lt0) / .18 * .35);
    let d = .15;
    if (s.icon) { const p = back((lt - .02) / .4); s.icon.style.transform = `scale(${p})`; s.icon.style.opacity = cl(lt / .12);
      s.iconParts.forEach((e, i) => { e.style.strokeDasharray = 1; e.style.strokeDashoffset = 1 - ease((lt - .1 - i * .15) / .55); });
      if (TH === 'warn') s.icon.style.transform += ` rotate(${Math.sin(lt * 40) * 6 * Math.exp(-lt * 2)}deg)`;
      d = .35; }
    if (s.kick) { const p = back((lt - d + .05) / .35); s.kick.style.transform = `scale(${p})`; s.kick.style.opacity = cl((lt - d + .1) / .1);
      s.kick.classList.toggle('rgb', !CALM && lt < .9 && Math.floor(lt * 20) % 3 === 0); d += .3; }
    if (s.claimEl) { const p = ease((lt - d) / .3); s.claimEl.style.opacity = p;
      s.strike.style.width = `calc(${ease((lt - d - .45) / .35) * 100}% + 20px)`; d += .85; }
    if (s.numEl) { const p = ease((lt - .05) / .4); s.numEl.style.transform = `translateX(${(1-p)*-220}px)`; s.numEl.style.opacity = p;
      s.numEl.classList.toggle('rgb', !CALM && lt < .5 && Math.floor(lt * 24) % 3 === 0); d = .35; }
    s.words.forEach((w, i) => { const st = d + i * STAG; const p = ease((lt - st) / WDUR);
      w.style.opacity = TH === 'hack' ? cl((lt - st) / .08) : p;
      let tx = 0; if (TH === 'warn') tx = Math.sin((lt - st) * 70) * 14 * (1 - p);
      w.style.transform = TH === 'hack' ? 'none' : `translate(${tx}px, ${(1-p)*(CALM?30:46)}px) scale(${.85 + .15*p})`;
      w.style.filter = TH === 'hack' ? 'none' : `blur(${(1-p)*(CALM?6:10)}px)`;
      if (TH === 'hack') { const real = w.dataset.w;
        if (lt - st < .45 && lt >= st) { let g = ''; for (let j = 0; j < real.trim().length; j++) g += GL[Math.floor(rnd(fr * 3.1 + i * 17 + j) * GL.length)]; w.textContent = g + (real.endsWith(' ') ? ' ' : ''); w.style.color = 'var(--a)'; }
        else { w.innerHTML = w.dataset.h; w.style.color = ''; } } });
    const ld = d + s.words.length * STAG + .25;
    if (s.stamp) { const sd = ld + .1; const p = cl((lt - sd) / .22);
      s.stamp.style.opacity = p; s.stamp.style.transform = `rotate(-12deg) scale(${2.6 - 1.6 * ease(p)})`; }
    s.lines.forEach((l, i) => { const p = ease((lt - ld - (s.stamp ? .5 : 0) - i * .35) / .4);
      l.style.opacity = p; l.style.transform = `translateX(${(1-p)*-60}px)`; });
  });
  document.getElementById('flash').style.opacity = flash;
  document.getElementById('slash').style.transform = `rotate(-8deg) translateX(${Math.sin(t*.8)*40}px)`;
}
// timing info for sfx
S.forEach(s => { let d = s.kind === 'hook' ? .35 : .15; if (s.kicker && s.kind === 'hook') d += .3; if (s.claim) { EXTRA.push(s.start + d + .45); d += .85; }
  if (s.kind === 'point' && s.num) d = .35; s.wd = d; if (TH === 'rumor' && s.kind === 'hook') EXTRA.push(s.start + d + s.title.split(' ').length * STAG + .35); });
window.TOTAL = TOTAL; window.render = render;
window.EVENTS = S.map((s, k) => ({start: s.start, kind: s.kind, words: s.words.length, hasKick: !!s.kick, hasNum: !!s.numEl, wd: s.wd, stag: STAG}));
window.EXTRA = EXTRA;
render(0);
</script></body></html>"""
def sfx(events, extra, total, out_wav, tmp):
    clips = []
    def gen(name, expr):
        p = os.path.join(tmp, name + ".wav")
        if not os.path.exists(p):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", expr, "-ac", "2", "-ar", "44100", p], check=True)
        return p
    hit = gen("hit", "aevalsrc='0.9*sin(2*PI*(52+40*exp(-12*t))*t)*exp(-5*t)':d=0.7")
    whoosh = gen("whoosh", "anoisesrc=d=0.45:c=pink:a=0.6,afade=t=in:d=0.2,afade=t=out:st=0.2:d=0.25,bandpass=f=1800:w=1600")
    tick = gen("tick", "aevalsrc='0.35*sin(2*PI*1600*t)*exp(-60*t)':d=0.08")
    glitch = gen("glitch", "anoisesrc=d=0.16:c=white:a=0.25,tremolo=f=40:d=0.9,highpass=f=2500")
    for k, e in enumerate(events):
        s = e["start"]
        if k == 0:
            clips += [(hit, s + 0.02), (glitch, s + 0.08)]
        else:
            clips += [(whoosh, s - 0.15), (glitch, s)]
        if e["hasNum"]:
            clips.append((hit, s + 0.05))
        for i in range(e["words"] if k > 0 else 0):
            clips.append((tick, s + e["wd"] + i * e["stag"]))
    for at in extra:
        clips.append((hit, at))
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for f, _ in clips:
        cmd += ["-i", f]
    parts = []
    for i, (_, at) in enumerate(clips):
        ms = max(0, int(at * 1000))
        parts.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(clips)))
    parts.append(f"{mix}amix=inputs={len(clips)}:normalize=0,volume=0.8,atrim=0:{total:.2f},apad=whole_dur={total:.2f}[out]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[out]", out_wav]
    subprocess.run(cmd, check=True)
def main(src, out):
    post = json.load(open(src, encoding="utf-8"))
    slug = post.get("slug", "post")
    theme = post.get("theme", "new")
    th = THEMES.get(theme, THEMES["new"])
    slides = [dict(s, dur=DUR.get(s.get("kind", "point"), 3.9), **({"num": f"{int(s['num']):02d}"} if str(s.get("num", "")).isdigit() else {})) for s in post["slides"]]
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp()
    page = (PAGE.replace("__ICONS__", JICONS).replace("__SLIDES__", json.dumps(slides, ensure_ascii=False)).replace("__THEME__", theme)
            .replace("__AG__", th["ag"]).replace("__A__", th["a"]))
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.set_content(page)
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        total = pg.evaluate("window.TOTAL")
        events = pg.evaluate("window.EVENTS")
        extra = pg.evaluate("window.EXTRA")
        n = int(total * FPS)
        for f in range(n):
            pg.evaluate(f"render({f / FPS})")
            pg.screenshot(path=os.path.join(tmp, f"f{f:05d}.jpg"), type="jpeg", quality=92)
        b.close()
    silent = os.path.join(out, f"{slug}_motion_silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "f%05d.jpg"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium", silent], check=True)
    wav = os.path.join(tmp, "sfx.wav")
    sfx(events, extra, total, wav, tmp)
    withsfx = os.path.join(out, f"{slug}_motion_sfx.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", withsfx], check=True)
    shutil.rmtree(tmp)
    print(silent, withsfx, f"{total:.1f}s", sep="\n")
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
