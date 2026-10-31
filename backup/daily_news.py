"""
ثغرة - نظام الأخبار الاحتياطي
يدور على خبر اليوم بـ Gemini (ببحث قوقل، ولو انرفض يجيب الأخبار من مصادر ثغرة بنفسه)، ويراجعه مراجع ثاني، ويسوي الصور والفيديو، ويرسلها لك على تليجرام.

المتغيرات المطلوبة (تنحط في GitHub Secrets):
  GEMINI_API_KEY      مفتاح Gemini من Google AI Studio
  TELEGRAM_BOT_TOKEN  توكن البوت من @BotFather
  TELEGRAM_CHAT_ID    رقم المحادثة حقك
اختياري:
  GEMINI_MODEL        اسم الموديل (الافتراضي gemini-3.8-flash)

تجربة بدون Gemini:  python3 backup/daily_news.py --from-file sample.json
"""
import json, os, re, sys, subprocess, datetime, urllib.request, urllib.parse, urllib.error, uuid, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "posted.json")
OUT = os.path.join(ROOT, "out")


def riyadh_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=3)


def load_log():
    try:
        return json.load(open(LOG, encoding="utf-8"))
    except Exception:
        return []


def save_log(items):
    json.dump(items[-60:], open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def http_json(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


FEEDS = [
    # أمنية
    "https://www.bleepingcomputer.com/feed/",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.securityweek.com/feed/",
    "https://therecord.media/feed",
    "https://krebsonsecurity.com/feed/",
    # تقنية عامة
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.engadget.com/rss.xml",
    "https://9to5mac.com/feed/",
    "https://www.androidauthority.com/feed/",
    "https://www.wired.com/feed/category/security/latest/rss",
    # رسمية
    "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    "https://telegram.org/blog/rss",
]

# أخبار قوقل: الجهات الرسمية السعودية، صفحات الشركات، Reuters و AP، ومنصات التحقق
GNEWS_AR = ["الهيئة الوطنية للأمن السيبراني", "هيئة الاتصالات والفضاء والتقنية", "البنك المركزي السعودي ساما احتيال",
            "واس الأمن السيبراني", "سدايا", "هيئة الحكومة الرقمية", "أبشر تحذير", "وزارة الداخلية احتيال",
            "stc تحذير احتيال", "موبايلي احتيال", "زين السعودية احتيال", "تحذير احتيال بنك السعودية",
            "مسبار تقنية", "فتبينوا تقنية", "واتساب ميزة جديدة", "تحديث آيفون أمني"]
GNEWS_EN = ["site:apple.com security", "Apple Security Releases", "Android Security Bulletin", "site:blog.google security",
            "Microsoft security update", "Samsung security update", "site:about.fb.com", "site:blog.whatsapp.com",
            "site:openai.com", "site:newsroom.tiktok.com", "site:newsroom.snap.com", "X Safety",
            "site:reuters.com cybersecurity", "site:apnews.com cybersecurity", "AFP Fact Check technology",
            "Reuters Fact Check technology"]


def gnews(q, ar):
    hl = "hl=ar&gl=SA&ceid=SA:ar" if ar else "hl=en-US&gl=US&ceid=US:en"
    return "https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:3d") + "&" + hl


def rss_news(days=3, per_feed=6):
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    out = []
    for f in FEEDS + [gnews(q, True) for q in GNEWS_AR] + [gnews(q, False) for q in GNEWS_EN]:
        try:
            req = urllib.request.Request(f, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
        except Exception:
            continue
        n = 0
        for it in root.iter():
            tag = it.tag.split("}")[-1]
            if tag not in ("item", "entry"):
                continue
            g = lambda name: next((c for c in it if c.tag.split("}")[-1] == name), None)
            title = (g("title").text or "").strip() if g("title") is not None else ""
            ln = g("link")
            link = (ln.get("href") or ln.text or "").strip() if ln is not None else ""
            d = g("pubDate") if g("pubDate") is not None else (g("published") if g("published") is not None else g("updated"))
            try:
                dt = parsedate_to_datetime(d.text) if d is not None and "," in d.text else datetime.datetime.fromisoformat(d.text.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                if dt < cutoff:
                    continue
                ds = dt.strftime("%Y-%m-%d")
            except Exception:
                ds = ""
            desc = g("description") if g("description") is not None else g("summary")
            dtext = re.sub(r"<[^>]+>|\s+", " ", (desc.text or "") if desc is not None else "").strip()[:400]
            out.append(f"- [{ds}] {title}\n  {link}\n  {dtext}")
            n += 1
            if n >= per_feed:
                break
    return "\n".join(out)


def ask_gemini(prompt):
    key = os.environ["GEMINI_API_KEY"]
    models = [m for m in [os.environ.get("GEMINI_MODEL"), "gemini-3.8-flash", "gemini-flash-latest", "gemini-flash-lite-latest"] if m]
    def body(text, search):
        b = {"contents": [{"role": "user", "parts": [{"text": text}]}],
             "generationConfig": {"temperature": 0.4}}
        if search:
            b["tools"] = [{"google_search": {}}]
        return b
    res, errs, rss = None, [], None
    # 1) بحث قوقل داخل Gemini، 2) لو رفض: أخبار RSS من المصادر الموثوقة بدون بحث
    for search in (True, False):
        if not search:
            rss = rss_news()
            if not rss:
                break
            text = prompt + "\n\n## ما عندك بحث ويب اليوم\nاختر الخبر من هالأخبار بس (من مصادر ثغرة الموثوقة)، واعتمد على كلامها فقط، وحط رابط الخبر في source_comment:\n" + rss
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            try:
                res = http_json(url, body(prompt if search else text, search))
                break
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="ignore")
                m = re.search(r'"message":\s*"([^"]{0,160})', msg)
                errs.append(f"{model}{' +بحث' if search else ''}: {e.code} {m.group(1) if m else msg[:160]}")
        if res is not None:
            break
    if res is None:
        raise RuntimeError("Gemini رفض الطلب:\n" + "\n".join(errs))
    cand = res["candidates"][0]
    text = "".join(p.get("text", "") for p in cand["content"]["parts"])
    links = []
    for ch in (cand.get("groundingMetadata") or {}).get("groundingChunks", []):
        w = ch.get("web") or {}
        if w.get("uri"):
            links.append(f'{w.get("title", "")}: {w["uri"]}')
    m = re.search(r"```json\s*(\{.*\})\s*```", text, re.S) or re.search(r"(\{.*\})", text, re.S)
    if not m:
        raise RuntimeError("Gemini ما رجّع JSON:\n" + text[:1500])
    return json.loads(m.group(1)), links


def gemini_plain(text):
    key = os.environ["GEMINI_API_KEY"]
    for model in [m for m in [os.environ.get("GEMINI_MODEL"), "gemini-3.8-flash", "gemini-flash-latest", "gemini-flash-lite-latest"] if m]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        try:
            res = http_json(url, {"contents": [{"role": "user", "parts": [{"text": text}]}], "generationConfig": {"temperature": 0.2}})
            return "".join(p.get("text", "") for p in res["candidates"][0]["content"]["parts"])
        except Exception:
            continue
    return ""


def page_text(url, limit=12000):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")
        raw = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", raw)
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw))
        return html_unescape(t)[:limit]
    except Exception:
        return ""


def html_unescape(t):
    import html
    return html.unescape(t)


def review(data, rules):
    """المراجع الثاني: يصحح مخالفات القواعد بدون ما يضيف معلومات."""
    src = ""
    for u in re.findall(r"https?://\S+", str(data.get("source_url", "")) + " " + str(data.get("source_comment", "")))[:2]:
        if "news.google.com" not in u:
            src += page_text(u.rstrip(").,،")) + "\n"
    srcpart = ("\n\n## نص المصدر\nقارن كل جملة في الشرائح والكابشن بهالنص، وأي رقم أو اسم أو تاريخ أو معلومة مو مكتوبة فيه صراحة احذفها أو عدّلها:\n" + src) if src.strip() else ""
    ask = ("أنت المراجع الثاني لقناة ثغرة. هذي قواعد الكتابة:\n" + rules + srcpart +
           "\n\nراجع المنشور التالي سطر سطر كأنك مشاهد عادي أول مرة يسمع بالخبر، وصحح بس اللي يخالف القواعد: "
           "الكلمات الرسمية الممنوعة، أسماء الشركات والمنتجات المكتوبة بحروف عربية (رجعها إنجليزي مثل OpenAI)، "
           "الجمل الناقصة أو اللي ما تنفهم لحالها، الخطاف المبالغ أو اللي يوحي إن الخطر مستمر وهو انحل، "
           "والكابشن اللي يقول شي مو في الشرائح. لا تضيف أي معلومة أو رقم أو اسم مو موجود. "
           "رجّع نفس JSON بنفس الشكل والمفاتيح داخل ```json ... ``` بدون أي كلام ثاني.\n\n```json\n"
           + json.dumps(data, ensure_ascii=False) + "\n```")
    text = gemini_plain(ask)
    m = re.search(r"```json\s*(\{.*\})\s*```", text, re.S) or re.search(r"(\{.*\})", text, re.S)
    try:
        new = json.loads(m.group(1))
        if new.get("post", {}).get("slides") and new.get("caption"):
            return new, True
    except Exception:
        pass
    return data, False


def tg(method, data, files=None):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = f"https://api.telegram.org/bot{token}/{method}"
    if not files:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
    else:
        b = uuid.uuid4().hex
        parts = []
        for k, v in data.items():
            parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        for k, path in files.items():
            parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{os.path.basename(path)}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode())
            parts.append(open(path, "rb").read())
            parts.append(b"\r\n")
        parts.append(f"--{b}--\r\n".encode())
        req = urllib.request.Request(url, data=b"".join(parts), headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


def send_text(text):
    chat = os.environ["TELEGRAM_CHAT_ID"]
    for i in range(0, len(text), 4000):
        tg("sendMessage", {"chat_id": chat, "text": text[i:i + 4000], "disable_web_page_preview": "true"})


def main():
    now = riyadh_now()
    days = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    log = load_log()

    if "--from-file" in sys.argv:
        data = json.load(open(sys.argv[sys.argv.index("--from-file") + 1], encoding="utf-8"))
        links = []
        reviewed = False
    else:
        recent = "، ".join(x["title"] for x in log[-20:]) or "ما فيه"
        prompt = open(os.path.join(HERE, "news_prompt.txt"), encoding="utf-8").read()
        prompt = prompt.replace("{TODAY}", now.strftime("%Y-%m-%d")).replace("{WEEKDAY}", days[now.weekday()]).replace("{RECENT}", recent)
        data, links = ask_gemini(prompt)
        data, reviewed = review(data, prompt[prompt.find("## الشرائح"):prompt.find("## المخرج")])

    post = data["post"]
    post["slug"] = re.sub(r"[^a-z0-9_]", "_", post.get("slug", "post").lower())[:40] or "post"
    os.makedirs(OUT, exist_ok=True)
    pj = os.path.join(OUT, "post.json")
    json.dump(post, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    subprocess.run([sys.executable, "render.py", pj, OUT], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "animate.py", pj, OUT], cwd=ROOT, check=True)

    slug = post["slug"]
    title = post["slides"][0]["title"]
    msg = (f"📰 منشور ثغرة لليوم (النظام الاحتياطي) — {now.strftime('%Y-%m-%d')}\n"
           f"⚠️ راجع الكلام والمصادر قبل النشر{' (راجعه مراجع ثاني ✅)' if reviewed else ''}\n\n"
           f"🗞 {data.get('summary', '')}\n📅 تاريخ الخبر: {data.get('news_date', '')}\n\n"
           f"📋 الكابشن:\n{data.get('caption', '')}\n\n"
           f"💬 تعليق المصدر:\n{data.get('source_comment', '')}\n"
           f"🔗 رابط الخبر: {data.get('source_url', '')}\n")
    if links:
        msg += "\n🔗 الروابط اللي بحث فيها:\n" + "\n".join(links[:8])

    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        chat = os.environ["TELEGRAM_CHAT_ID"]
        send_text(msg)
        tg("sendVideo", {"chat_id": chat, "caption": title[:1000]}, {"video": os.path.join(OUT, f"{slug}_motion_sfx.mp4")})
        imgs = [os.path.join(OUT, f"{slug}_cover.png")] + sorted(glob.glob(os.path.join(OUT, f"{slug}_carousel_*.png")))
        for i in range(0, len(imgs), 10):
            part = imgs[i:i + 10]
            media = [{"type": "document", "media": f"attach://f{j}"} for j in range(len(part))]
            tg("sendMediaGroup", {"chat_id": chat, "media": json.dumps(media)}, {f"f{j}": f for j, f in enumerate(part)})
    else:
        print(msg)

    log.append({"date": now.strftime("%Y-%m-%d"), "title": title})
    save_log(log)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if os.environ.get("TELEGRAM_BOT_TOKEN"):
            try:
                send_text(f"❌ النظام الاحتياطي لثغرة ما قدر يسوي منشور اليوم:\n{e}")
            except Exception:
                pass
        raise
