نظام ثغرة الاحتياطي — كيف تشغّله (مرة وحدة بس)
==================================================
يشتغل كل يوم الساعة 5:47 العصر لحاله على GitHub، ويرسل لك المنشور (الفيديو والصور والكابشن) على تليجرام.
مجاني: GitHub Actions + المستوى المجاني من Gemini API + بوت تليجرام.

1) مفتاح Gemini
   - افتح aistudio.google.com وسجل بحساب قوقل
   - افتح aistudio.google.com/apikey ← Create API key ← Create project ← Create key وانسخه (لا تختار أي شي فيه billing أو paid)

2) بوت تليجرام
   - في تليجرام كلّم @BotFather واكتب /newbot وسمّه، وانسخ التوكن اللي يعطيك
   - افتح البوت حقك واكتب له أي رسالة (مثلاً: hi)
   - افتح في المتصفح: https://api.telegram.org/bot<التوكن>/getUpdates
     ودوّر على "chat":{"id": رقم ... انسخ الرقم، هذا TELEGRAM_CHAT_ID

3) حط المفاتيح في GitHub
   - افتح المستودع thaghra-kit ← Settings ← Secrets and variables ← Actions ← New repository secret
   - سوّ 3 أسرار بهالأسماء بالضبط:
       GEMINI_API_KEY
       TELEGRAM_BOT_TOKEN
       TELEGRAM_CHAT_ID
   - (اختياري) GEMINI_MODEL لو تبي موديل غير gemini-3.8-flash

4) جرّبه
   - في المستودع افتح تبويب Actions ← "ثغرة - الأخبار الاحتياطية" ← Run workflow
   - بعد 5 إلى 10 دقايق يوصلك المنشور على تليجرام

ملاحظات
- لو المفاتيح مو موجودة، النظام ما يسوي شي ولا يرسل شي.
- لو تبي توقفه: Actions ← الـ workflow ← (...) ← Disable workflow
- راجع المنشور دايماً قبل النشر، لأن Gemini ممكن يغلط.
- الملفات: backup/daily_news.py (الكود)، backup/news_prompt.txt (القواعد)، backup/posted.json (سجل عشان ما يكرر)،
  .github/workflows/thaghra_backup.yml (الجدولة).
