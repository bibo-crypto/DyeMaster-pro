# Periodic Audit (فحص دوري)

الهدف: لما تقول “افحص البرنامج”، يكون فيه خطوات ثابتة ومخرجات تقرير.

## Run

من جذر المشروع:

`python tools/audit.py`

هيطلع تقرير في:

`audit_report.md`

## What it checks

- `compileall` على `main.py` + `app/` + `ui/`
- آثار كود ميت (ملفات `.pyc` يتيمة بدون `.py`)
- مؤشرات قابلية نقل ضعيفة (paths ثابتة)
- TODO/FIXME/HACK markers
- `except Exception: pass/return` اللي ممكن يخفي أخطاء
- تكرار تعليقات متتالية (مؤشر نسخ/لصق)

## Notes

- الفحص ده خفيف (بدون dependencies) ومش بديل لاختبارات تشغيل UI.
- لو محتاج فحص أعمق (lint/format/type-check)، نضيفه لاحقًا حسب رغبتك.

