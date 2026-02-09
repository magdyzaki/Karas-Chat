# 🔍 برنامج البحث المتخصص - مستوردي البصل والكراث والسبانخ المجفف من مصر

## 📋 الوصف
برنامج متخصص للبحث عن شركات أجنبية حقيقية تستورد:
- بصل مجفف (Dehydrated/Dried Onion)
- كراث مجفف (Dehydrated/Dried Leek)
- سبانخ مجفف (Dehydrated/Dried Spinach)

من مصر فقط - بدون شركات مصرية أو صينية أو هندية.

## ✨ المميزات
- ✅ فلترة قوية لاستبعاد المنصات والبنوك
- ✅ استبعاد الشركات المصرية والصينية والهندية تماماً
- ✅ استبعاد أسماء المنتجات
- ✅ البحث عن شركات أجنبية فقط (USA, Europe)
- ✅ دعم 3 منتجات: بصل مجفف، كراث مجفف، سبانخ مجفف
- ✅ تصدير النتائج إلى Excel/CSV

## 📁 هيكل الملفات
```
specialized_search_tool/
├── core/
│   └── specialized_importer_search.py  # منطق البحث والفلترة
├── ui/
│   └── specialized_search_window.py    # واجهة المستخدم
└── README.md                           # هذا الملف
```

## 🔧 المتطلبات
- Python 3.7+
- PyQt5
- requests
- beautifulsoup4
- openpyxl (لتصدير Excel)
- مفتاح SerpAPI

## 🚀 الاستخدام

### 1. تثبيت المتطلبات
```bash
pip install PyQt5 requests beautifulsoup4 openpyxl
```

### 2. الحصول على مفتاح SerpAPI
- سجل في [SerpAPI](https://serpapi.com/)
- احصل على مفتاح API مجاني (100 استعلام/شهر)

### 3. تشغيل البرنامج
```python
from ui.specialized_search_window import SpecializedSearchWindow
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = SpecializedSearchWindow()
window.show()
sys.exit(app.exec_())
```

## 📝 ملاحظات
- البرنامج يستخدم SerpAPI للبحث
- الفلترة تستبعد الشركات المصرية والمنتجات والمنصات
- النتائج محدودة بـ 50 شركة كحد أقصى (قابل للتعديل)

## 🔍 الاستعلامات المستخدمة
- `dehydrated onion importer USA company (inc OR llc OR ltd) -egypt -egyptian -china -chinese -india -indian`
- `dehydrated leek importer USA company (inc OR llc OR ltd) -egypt -egyptian -china -chinese -india -indian`
- `dehydrated spinach importer USA company (inc OR llc OR ltd) -egypt -egyptian -china -chinese -india -indian`
- `companies import dehydrated onion from Egypt (inc OR llc OR ltd) -china -chinese -india -indian`
- وغيرها...

## 🚫 الدول المستبعدة
- ❌ مصر (Egypt, Egyptian)
- ❌ الصين (China, Chinese)
- ❌ الهند (India, Indian)

## 📧 الدعم
للمساعدة أو الإبلاغ عن مشاكل، يرجى التواصل مع المطور.
