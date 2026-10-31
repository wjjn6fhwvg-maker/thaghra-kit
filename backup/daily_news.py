"""
ثغرة - نظام الأخبار الاحتياطي
يدور على خبر اليوم بـ Gemini (مع بحث قوقل)، ويسوي الصور والفيديو، ويرسلها لك على تليجرام.

المتغيرات المطلوبة (تنحط في GitHub Secrets):
  GEMINI_API_KEY      مفتاح Gemini من Google AI Studio
  TELEGRAM_BOT_TOKEN  توكن البوت من @BotFather
  TELEGRAM_CHAT_ID    رقم المحادثة حقك
اختياري:
  GEMINI_MODEL        اسم الموديل (الافتراضي gemini-2.5-flash)

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


def ask_gemini(prompt):
    key = os.environ["GEMINI_API_KEY"]
    models = [m for m in [os.environ.get("GEMINI_MODEL"), "gemini-flash-latest", "gemini-2.5-flash"] if m]
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {"temperature": 0.4}}
    res, errs = None, []
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        try:
            res = http_json(url, body)
            break
        except urllib.error.HTTPError as e:
            errs.append(f"{model}: {e.code} {e.read().decode()[:300]}")
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
    else:
        recent = "، ".join(x["title"] for x in log[-20:]) or "ما فيه"
        prompt = open(os.path.join(HERE, "news_prompt.txt"), encoding="utf-8").read()
        prompt = prompt.replace("{TODAY}", now.strftime("%Y-%m-%d")).replace("{WEEKDAY}", days[now.weekday()]).replace("{RECENT}", recent)
        data, links = ask_gemini(prompt)

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
           f"⚠️ راجع الكلام والمصادر قبل النشر\n\n"
           f"🗞 {data.get('summary', '')}\n📅 تاريخ الخبر: {data.get('news_date', '')}\n\n"
           f"📋 الكابشن:\n{data.get('caption', '')}\n\n"
           f"💬 تعليق المصدر:\n{data.get('source_comment', '')}\n")
    if links:
        msg += "\n🔗 الروابط اللي بحث فيها:\n" + "\n".join(links[:8])

    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        chat = os.environ["TELEGRAM_CHAT_ID"]
        send_text(msg)
        tg("sendVideo", {"chat_id": chat, "caption": title[:1000]}, {"video": os.path.join(OUT, f"{slug}_motion_sfx.mp4")})
        tg("sendDocument", {"chat_id": chat}, {"document": os.path.join(OUT, f"{slug}_cover.png")})
        for f in sorted(glob.glob(os.path.join(OUT, f"{slug}_carousel_*.png"))):
            tg("sendDocument", {"chat_id": chat}, {"document": f})
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
