"""
تحليل نتائج التصدير وفحص جودة البيانات
Analyze Export Results and Check Data Quality
"""
import os
import csv
from typing import List, Dict, Tuple
from collections import Counter

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


def analyze_export_file(file_path: str, exporter_name: str) -> Dict:
    """
    تحليل ملف Excel أو CSV وفحص جودة النتائج
    
    Args:
        file_path: مسار الملف
        exporter_name: اسم الشركة المصدرة للتحقق من التكرارات
    
    Returns:
        Dict يحتوي على:
        - total_companies: إجمالي الشركات
        - real_companies: عدد الشركات الحقيقية
        - fake_companies: عدد الشركات المزيفة
        - duplicates: عدد التكرارات
        - exporter_matches: عدد التكرارات مع اسم الشركة المصدرة
        - countries: توزيع الدول
        - analysis: تحليل مفصل
    """
    results = {
        "total_companies": 0,
        "real_companies": 0,
        "fake_companies": 0,
        "duplicates": 0,
        "exporter_matches": 0,
        "countries": {},
        "analysis": []
    }
    
    if not os.path.exists(file_path):
        results["analysis"].append(f"❌ الملف غير موجود: {file_path}")
        return results
    
    companies = []
    
    try:
        if file_path.endswith('.xlsx') and EXCEL_AVAILABLE:
            # قراءة Excel
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
            
            # قراءة البيانات (تخطي الرأس)
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and len(row) >= 2:
                    company_name = str(row[1]).strip() if row[1] else ""
                    country = str(row[2]).strip() if len(row) > 2 and row[2] else ""
                    
                    if company_name and company_name.lower() != "company name":
                        companies.append({
                            "company_name": company_name,
                            "country": country
                        })
        
        elif file_path.endswith('.csv'):
            # قراءة CSV
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                headers = next(reader, None)  # تخطي الرأس
                
                for row in reader:
                    if row and len(row) >= 2:
                        company_name = row[1].strip() if len(row) > 1 else ""
                        country = row[2].strip() if len(row) > 2 else ""
                        
                        if company_name and company_name.lower() != "company name":
                            companies.append({
                                "company_name": company_name,
                                "country": country
                            })
        
        results["total_companies"] = len(companies)
        
        # تحليل الشركات
        exporter_name_lower = exporter_name.lower().strip()
        seen_companies = set()
        real_companies_list = []
        fake_companies_list = []
        
        # كلمات تشير إلى صفحات وليست شركات
        page_indicators = [
            "import data", "importers list", "buyers list", "importers data",
            "wholesale suppliers", "find importers", "search for importers",
            "list of", "top 10", "best wholesale", "how to", "chart:",
            "who imports", "importing food", "agricultural imports",
            "import assistance", "import guide", "importers directory",
            "wholesale directory", "distributors directory", "buyers directory",
            "import statistics", "trade data", "import records",
            "national association", "international wholesale", "wholesale central",
            "global distributors", "finding top", "variety distributors",
            "allied importers", "largest importers", "known importers",
            "most important", "faces record", "how much", "what in the world",
            "charting the essentials", "which countries", "attachment",
            "starting a business", "welcome by", "home", "company logistics",
            "dedicated to", "export of", "chemical distribution", "canned food"
        ]
        
        for company in companies:
            company_name = company.get("company_name", "").strip()
            company_lower = company_name.lower()
            
            if not company_name:
                continue
            
            # فحص التكرارات
            if company_lower in seen_companies:
                results["duplicates"] += 1
                continue
            seen_companies.add(company_lower)
            
            # فحص إذا كان مطابق لاسم الشركة المصدرة
            if exporter_name_lower in company_lower or company_lower in exporter_name_lower:
                results["exporter_matches"] += 1
                fake_companies_list.append(company_name)
                continue
            
            # فحص إذا كان عنوان صفحة
            is_fake = False
            for indicator in page_indicators:
                if indicator in company_lower:
                    is_fake = True
                    break
            
            # فحص إذا كان يبدأ بكلمات عامة
            page_starters = [
                "find ", "search for ", "list of ", "top ", "best ",
                "how to ", "how much ", "what ", "which ", "chart:",
                "importing ", "agricultural ", "u.s. ", "us ",
                "all ", "allied ", "global ", "international ",
                "national ", "variety ", "finding ", "wholesale ",
                "starting a", "welcome by", "dedicated to", "export of"
            ]
            
            if not is_fake:
                for starter in page_starters:
                    if company_lower.startswith(starter):
                        is_fake = True
                        break
            
            # فحص إذا كان يحتوي على أرقام في البداية
            if company_name and company_name[0].isdigit():
                is_fake = True
            
            # فحص إذا كان قصير جداً أو طويل جداً
            if len(company_name) < 3 or len(company_name) > 100:
                is_fake = True
            
            # فحص إذا كان يحتوي على كلمات عامة فقط
            generic_words = ["importers", "buyers", "distributors", "wholesale", 
                           "suppliers", "companies", "traders", "merchants", "distribution"]
            words = company_name.split()
            generic_count = sum(1 for word in words if word.lower() in generic_words)
            if generic_count >= 2 and len(words) <= 4:
                is_fake = True
            
            if is_fake:
                results["fake_companies"] += 1
                fake_companies_list.append(company_name)
            else:
                results["real_companies"] += 1
                real_companies_list.append(company_name)
                
                # إحصاء الدول
                country = company.get("country", "").strip()
                if country:
                    results["countries"][country] = results["countries"].get(country, 0) + 1
        
        # تحليل مفصل
        results["analysis"].append(f"✅ إجمالي الشركات: {results['total_companies']}")
        results["analysis"].append(f"✅ شركات حقيقية: {results['real_companies']}")
        results["analysis"].append(f"❌ شركات مزيفة: {results['fake_companies']}")
        results["analysis"].append(f"🔄 تكرارات: {results['duplicates']}")
        results["analysis"].append(f"⚠️ مطابقة مع الشركة المصدرة: {results['exporter_matches']}")
        
        if results["countries"]:
            results["analysis"].append(f"\n🌍 توزيع الدول:")
            for country, count in sorted(results["countries"].items(), key=lambda x: x[1], reverse=True):
                results["analysis"].append(f"   - {country}: {count}")
        
        if real_companies_list:
            results["analysis"].append(f"\n✅ قائمة الشركات الحقيقية ({len(real_companies_list)}):")
            for i, company in enumerate(real_companies_list[:20], 1):  # أول 20 شركة
                results["analysis"].append(f"   {i}. {company}")
            if len(real_companies_list) > 20:
                results["analysis"].append(f"   ... و {len(real_companies_list) - 20} شركة أخرى")
        
        if fake_companies_list:
            results["analysis"].append(f"\n❌ أمثلة على الشركات المزيفة ({len(fake_companies_list)}):")
            for i, company in enumerate(fake_companies_list[:10], 1):  # أول 10 أمثلة
                results["analysis"].append(f"   {i}. {company}")
        
    except Exception as e:
        results["analysis"].append(f"❌ خطأ في قراءة الملف: {str(e)}")
        import traceback
        results["analysis"].append(traceback.format_exc())
    
    return results
