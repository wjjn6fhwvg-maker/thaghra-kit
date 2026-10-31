ملف ثغرة الكامل — كل اللي سويناه
=====================================

1_prompts (تعليمات المهام، تقدر تنسخها لأي منصة ذكاء اصطناعي)
- daily_news_prompt.txt : مهمة الأخبار اليومية (كانت تشتغل 5:47 العصر). فيها كل قواعد اختيار الخبر والمصادر والتحقق وكتابة الشرائح والكابشن والنشر.
- urgent_alert_prompt.txt : مهمة التنبيهات العاجلة (11:47 الصبح، 2:47 الظهر، 9:47 الليل).
- weekly_report_prompt.txt : التقرير الأسبوعي (كل جمعة 12:47) من أرقام Metricool.
ملاحظة: الأجزاء اللي فيها Claude Docs و Metricool و add_repo خاصة بـ Claude. في منصة ثانية خذ القواعد (المصادر، التحقق، هيكل القصة، الوضوح، الكلمات الرسمية، اختبار القارئ، الكابشن) واترك أجزاء الأدوات.

2_code (برامج تصميم الصور والفيديو، Python)
- render.py : يسوي صور الكاروسيل 1080x1350 وصورة الغلاف.
- animate.py : يسوي الفيديو 1080x1920 بالحركات والمؤثرات الصوتية (السرعة والصوت الأصلي).
- setup.sh : تثبيت الخطوط.
التشغيل:
  pip install playwright && playwright install chromium   (ويحتاج ffmpeg)
  ثبّت خط Readex Pro و IBM Plex Mono
  python3 render.py post.json out
  python3 animate.py post.json out
شكل post.json:
  {"slug": "name", "theme": "warn|hack|new|rumor|aware|local",
   "slides": [
     {"kind": "hook", "kicker": "تحذير", "title": "...", "body": "..."},
     {"kind": "point", "num": 1, "title": "وش صار؟", "body": "سطر\nسطر"},
     {"kind": "cta", "title": "وش تسوي الحين؟", "body": "..."}
   ]}

3_backgrounds (خلفيات CapCut جاهزة)
- new = جديد/تقنية (تركوازي #2DD4BF)
- warn = تحذير/احتيال (برتقالي #F97316)
- hack = ثغرة/اختراق (بنفسجي #A78BFA)
- aware = توعية/نصيحة (أزرق #38BDF8)
- rumor = إشاعة (أحمر #EF4444)

هوية ثغرة
- الخلفية #0B1220، العنوان #F1F5F9، الشرح #CBD5E1
- الخط: Readex Pro (أو القاهرة Cairo في CapCut)
- المقاسات (فيديو 1080x1920): الشعار 62، عنوان أول/آخر شريحة 96، عنوان الشرائح 76، الشرح 48، الرقم 170، الكلمة الملونة 40
- المدة: الأولى 4.2 ث، الوسط 3.9 ث، الأخيرة 4 ث

روابط مهمة
- المستودع: github.com/wjjn6fhwvg-maker/thaghra-kit (فيه الكود ومجلد media)
- سجل المنشورات: https://claude.ai/artifact/H9RNmbRvG8o6sZRmgS8oMk
- Metricool: brandId 7671375 (انستقرام + تيك توك)
