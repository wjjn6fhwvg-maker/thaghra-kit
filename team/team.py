"""
فريق تطوير ثغرة (مجاني: GitHub Actions + Gemini)
- كل يوم: 3 موظفين (المراجع، الباحث، المطوّر) يكتبون ملاحظاتهم في team/log.md
- يوم الأحد: تقرير الأسبوع يوصلك على تليجرام، ويتحفظ في team/weekly/
- ما يعدّل أي شي في القناة أبداً. كل شي اقتراحات تنتظر موافقتك.

التشغيل:  python team/team.py daily   أو   python team/team.py weekly
"""
import os, sys, json, glob, base64, datetime, re, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "backup"))
import daily_news as dn  # نستخدم نفس دوال Gemini والأخبار وتليجرام

LOG = os.path.join(HERE, "log.md")
DECISIONS = os.path.join(HERE, "decisions.md")
WEEKLY = os.path.join(HERE, "weekly")


def read(p, limit=None):
    try:
        t = open(p, encoding="utf-8").read()
    except Exception:
        return ""
    return t[-limit:] if limit else t


def gemini(parts):
    """طلب لـ Gemini بنص وصور (لو فيه)."""
    key = os.environ["GEMINI_API_KEY"]
    models = [m for m in [os.environ.get("GEMINI_MODEL"), "gemini-3.8-flash", "gemini-flash-latest", "gemini-flash-lite-latest"] if m]
    errs = []
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        try:
            res = dn.http_json(url, {"contents": [{"role": "user", "parts": parts}], "generationConfig": {"temperature": 0.5}})
            return "".join(p.get("text", "") for p in res["candidates"][0]["content"]["parts"]).strip()
        except Exception as e:
            errs.append(f"{model}: {str(e)[:120]}")
    raise RuntimeError("Gemini رفض الطلب:\n" + "\n".join(errs))


def recent_posts(days=7):
    """منشورات آخر أسبوع: منشورات Claude (صورة الغلاف من media) ومنشورات تليجرام (النص كامل من history)."""
    cutoff = (dn.riyadh_now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    texts, images = [], []
    for f in sorted(glob.glob(os.path.join(ROOT, "backup", "history", "*.json"))):
        if os.path.basename(f)[:10] >= cutoff:
            d = json.load(open(f, encoding="utf-8"))
            slides = "\n".join(f"  - {s.get('title','')}: {s.get('body','')}" for s in d.get("post", {}).get("slides", []))
            texts.append(f"[{d.get('date')}] (تليجرام/{d.get('mode')})\n{slides}\nالكابشن: {d.get('caption','')}\nالمصدر: {d.get('source_comment','')}")
    latest = {}  # آخر نسخة بس من كل منشور (v2، v3...)
    for d in sorted(glob.glob(os.path.join(ROOT, "media", "*"))):
        latest[re.sub(r"_v\d+$", "", os.path.basename(d))] = d
    for d in latest.values():
        name = os.path.basename(d)
        if name[:10] >= cutoff:
            cov = os.path.join(d, "cover.jpg")
            texts.append(f"[{name[:10]}] (Claude) {name[11:]}" + (" ← صورة الغلاف مرفقة" if os.path.exists(cov) else ""))
            if os.path.exists(cov):
                images.append(open(cov, "rb").read())
    return "\n\n".join(texts) or "ما فيه منشورات هالأسبوع", images[-8:]


COMMON = """أنت موظف في «فريق تطوير ثغرة». ثغرة قناة عربية بلهجة سعودية (@thaghra_ar على انستقرام وتيك توك) توعية في الأمن السيبراني والتقنية للناس العاديين.
قوانين الفريق:
- أنت تقترح بس، وما تعدّل أي شي. صاحب القناة يقرر يوم الأحد.
- لا تكرر اقتراح رفضه صاحب القناة (شوف القرارات تحت)، ولا تكرر اقتراح كتبه الفريق قبل إلا لو عندك سبب جديد.
- كل اقتراح: المشكلة ← الحل ← النتيجة المتوقعة، بسطر أو سطرين، وبلهجة سعودية بسيطة.
- ما عندكم أرقام مشاهدات، فلا تخترع أرقام أداء. اعتمد على المحتوى نفسه.
- ممنوع: سياسة، دين، اتهام أشخاص، شرح طرق اختراق، أو أي شي يكشف هوية صاحب القناة.

قواعد القناة الحالية:
{rules}

قرارات صاحب القناة السابقة:
{decisions}

آخر ملاحظات الفريق (عشان تتعلم منها وما تكرر):
{history}
"""

ROLES = {
    "المراجع": "دورك: راجع منشورات الأسبوع تحت (النصوص وصور الأغلفة) كأنك مشاهد عادي. طلّع أهم 3 مشاكل بس: خطاف ضعيف، كلمة رسمية، جملة ما تنفهم، تكرار مواضيع، تصميم مزحوم، كابشن ما يطابق الشرائح. لكل مشكلة اذكر المنشور وتاريخه.",
    "الباحث": "دورك: من أخبار الأسبوع تحت، طلّع وش المواضيع المهمة اللي فاتت القناة (ما نزلت في منشورات الأسبوع) وتهم الشخص العادي، واقترح نوعين أو ثلاث من المنشورات الجديدة (مثلاً: سلسلة، سؤال وجواب، مقارنة) تناسب القناة. بحد أقصى 4 نقاط.",
    "المطوّر": "دورك: بناءً على ملاحظات المراجع والباحث اليوم، اقترح بحد أقصى 3 تحسينات عملية على القواعد أو التصميم أو الكابشن أو الهاشتاقات أو أوقات النشر. ولكل واحد اكتب: «وش نخلي / وش نغيّر / وش نبني»، والنص المقترح بالضبط لو هو تعديل على القواعد.",
}


def daily():
    now = dn.riyadh_now()
    rules = read(os.path.join(ROOT, "backup", "news_prompt.txt"))
    rules = rules[rules.find("## المصادر"):rules.find("## المخرج")]
    ctx = COMMON.format(rules=rules, decisions=read(DECISIONS) or "ما فيه قرارات للحين", history=read(LOG, 6000) or "ما فيه")
    posts, images = recent_posts()
    news = dn.rss_news(days=7, per_feed=3)[:15000]
    out = {}
    img_parts = [{"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(b).decode()}} for b in images]
    out["المراجع"] = gemini([{"text": ctx + "\n\n" + ROLES["المراجع"] + "\n\n## منشورات الأسبوع\n" + posts}] + img_parts)
    out["الباحث"] = gemini([{"text": ctx + "\n\n" + ROLES["الباحث"] + "\n\n## منشورات الأسبوع\n" + posts + "\n\n## أخبار الأسبوع من مصادرنا\n" + news}])
    out["المطوّر"] = gemini([{"text": ctx + "\n\n" + ROLES["المطوّر"] + "\n\n## ملاحظات المراجع\n" + out["المراجع"] + "\n\n## ملاحظات الباحث\n" + out["الباحث"]}])
    entry = f"\n\n## {now.strftime('%Y-%m-%d')}\n" + "".join(f"\n### {k}\n{v}\n" for k, v in out.items())
    if not os.path.exists(LOG):
        open(LOG, "w", encoding="utf-8").write("# سجل فريق تطوير ثغرة\nكل يوم الساعة 2 الفجر. اقتراحات بس، ولا شي يتطبق إلا بموافقة صاحب القناة يوم الأحد.\n")
    open(LOG, "a", encoding="utf-8").write(entry)
    print(entry)


def weekly():
    now = dn.riyadh_now()
    log = read(LOG)
    start = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    week = "\n".join(b for b in re.split(r"\n(?=## \d{4}-\d{2}-\d{2})", log) if b.startswith("## ") and b[3:13] >= start)
    if not week.strip():
        week = "ما اشتغل الفريق هالأسبوع."
    ask = ("أنت مدير «فريق تطوير ثغرة». هذي ملاحظات الفريق اليومية للأسبوع. اكتب تقرير الأحد لصاحب القناة بلهجة سعودية بسيطة ومختصرة، بهالترتيب بالضبط:\n"
           "📊 تقرير فريق التطوير (من–إلى)\n"
           "1) ✅ أهم 5 اقتراحات مرتبة حسب الأهمية، وكل واحد برقم، وتحته: المشكلة ← الحل ← النتيجة المتوقعة\n"
           "2) ⚠️ المشاكل اللي تكررت هالأسبوع\n"
           "3) 💡 أفكار منشورات جديدة (بحد أقصى 3)\n"
           "4) 🧱 وش نخلي زي ما هو (اللي ماشي صح)\n"
           "وفي الآخر سطر: «قل لـ Claude: اعتمد 1 و 3 (مثلاً) وهو يطبقها».\n"
           "لا تخترع أرقام أداء. لا تكرر نفس الاقتراح بصيغتين. بدون مقدمات.\n\n"
           "قرارات صاحب القناة السابقة:\n" + (read(DECISIONS) or "ما فيه") + "\n\nملاحظات الأسبوع:\n" + week[-30000:])
    report = gemini([{"text": ask}])
    os.makedirs(WEEKLY, exist_ok=True)
    open(os.path.join(WEEKLY, f"{now.strftime('%Y-%m-%d')}.md"), "w", encoding="utf-8").write(report)
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        dn.send_text("🛠 " + report)
    print(report)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    try:
        weekly() if mode == "weekly" else daily()
    except Exception as e:
        if os.environ.get("TELEGRAM_BOT_TOKEN"):
            try:
                dn.send_text(f"❌ فريق تطوير ثغرة ما قدر يشتغل ({mode}):\n{e}")
            except Exception:
                pass
        raise
