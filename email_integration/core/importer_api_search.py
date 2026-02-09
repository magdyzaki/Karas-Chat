"""
البحث عن المستوردين بناءً على اسم الشركة المصدرة
Search for Importers based on Exporter Company Name
"""
import requests
import json
import re
import urllib.parse
import time
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


def search_importers_by_exporter(exporter_name: str, product_name: str = None, countries: List[str] = None, api_key: str = None) -> List[Dict]:
    """
    البحث عن المستوردين بناءً على اسم الشركة المصدرة واسم المنتج
    
    Args:
        exporter_name: اسم الشركة المصدرة
        product_name: اسم المنتج (اختياري)
        countries: قائمة الدول (اختياري)
        api_key: مفتاح API (اختياري)
    
    Returns:
        قائمة من المستوردين المحتملين
    """
    results = []
    
    print(f"DEBUG: بدء البحث - Exporter: {exporter_name}, Product: {product_name}, Countries: {countries}")
    
    # إذا كان هناك API key، استخدمه أولاً
    if api_key:
        print("DEBUG: محاولة البحث عبر SerpAPI...")
        try:
            api_results = search_api_importers(exporter_name, product_name, countries, api_key)
            results.extend(api_results)
            print(f"DEBUG: تم العثور على {len(api_results)} نتيجة من SerpAPI")
        except Exception as e:
            print(f"DEBUG: خطأ في SerpAPI: {e}")
    
    # إذا لم تكن هناك نتائج كافية، جرب Google scraping
    if len(results) < 5:
        print("DEBUG: محاولة البحث عبر Google...")
        try:
            google_results = search_google_importers(exporter_name, product_name, countries)
            results.extend(google_results)
            print(f"DEBUG: تم العثور على {len(google_results)} نتيجة من Google")
        except Exception as e:
            print(f"DEBUG: خطأ في Google: {e}")
    
    # فلترة قوية: إزالة التكرارات والنتائج غير الصحيحة
    unique_results = filter_valid_companies(results, exporter_name)
    
    print(f"DEBUG: إجمالي النتائج بعد الفلترة: {len(unique_results)}")
    return unique_results


def filter_valid_companies(results: List[Dict], exporter_name: str) -> List[Dict]:
    """فلترة قوية جداً لاستبعاد النتائج غير الصحيحة - فقط الشركات الحقيقية"""
    unique_results = []
    seen = set()
    exporter_name_lower = exporter_name.lower().strip()
    
    # قائمة أسماء البلدان (يجب استبعادها)
    country_names = [
        "usa", "united states", "america", "us", "uk", "united kingdom", "britain",
        "germany", "france", "italy", "spain", "netherlands", "belgium", "switzerland",
        "austria", "poland", "portugal", "greece", "sweden", "norway", "denmark",
        "finland", "ireland", "czech republic", "hungary", "romania", "bulgaria",
        "croatia", "slovakia", "slovenia", "lithuania", "latvia", "estonia",
        "cyprus", "malta", "luxembourg", "egypt", "saudi arabia", "uae", "emirates",
        "qatar", "kuwait", "bahrain", "oman", "jordan", "lebanon", "syria", "iraq",
        "iran", "turkey", "israel", "palestine", "china", "india", "japan", "korea",
        "thailand", "vietnam", "indonesia", "malaysia", "singapore", "philippines",
        "australia", "new zealand", "canada", "mexico", "brazil", "argentina",
        "chile", "south africa", "nigeria", "kenya", "morocco", "tunisia", "algeria"
    ]
    
    # كلمات تشير إلى صفحات وليست شركات (موسعة جداً)
    page_keywords = [
        "directory", "list", "listing", "catalog", "database", "registry",
        "find", "search", "browse", "top 10", "top 20", "top ", "best", "leading",
        "all", "complete", "full list", "companies", "suppliers",
        "importers", "buyers", "distributors", "wholesale", "how to",
        "what is", "which", "chart", "statistics", "data", "records",
        "list of", "directory of", "companies that", "who imports", "who buys",
        "import data", "trade data", "import statistics", "wholesale suppliers",
        "find importers", "search for", "browse companies", "leading importers",
        "major importers", "largest importers", "top importers", "best importers",
        "click here", "read more", "learn more", "view all", "see all",
        "show all", "more info", "more information", "details", "about us"
    ]
    
    # كلمات تعليمات/أزرار (يجب استبعادها)
    instruction_words = [
        "accept", "cookies", "cookie", "privacy", "policy", "terms", "conditions",
        "login", "sign in", "sign up", "register", "subscribe", "unsubscribe",
        "continue", "next", "previous", "back", "forward", "home", "menu",
        "contact", "about", "help", "support", "faq", "sitemap", "language",
        "english", "arabic", "french", "german", "spanish", "italian"
    ]
    
    # مواقع B2B العامة التي يجب استبعادها
    excluded_b2b_sites = [
        "alibaba", "indiamart", "tradeindia", "europages", "kompass",
        "thomasnet", "globalsources", "ec21", "ecplaza", "made-in-china",
        "dhgate", "1688", "tradekey", "go4worldbusiness", "b2bfreezone",
        "bizvibe", "exportersindia", "yellowpages", "mfg", "supplychainconnect"
    ]
    
    # كلمات عامة فقط (ليست أسماء شركات)
    generic_only_words = [
        "importers", "buyers", "distributors", "wholesale", "suppliers",
        "companies", "traders", "merchants", "trading", "logistics",
        "broker", "trade", "import", "export", "food", "products"
    ]
    
    for result in results:
        company_name = result.get("company_name", "").strip()
        if not company_name or len(company_name) < 3:
            continue
        
        company_name_lower = company_name.lower().strip()
        
        # 0. استبعاد الأسماء الفارغة أو قصيرة جداً
        if len(company_name_lower) < 4:
            continue
        
        # 1. استبعاد إذا كان نفس اسم الشركة المصدرة
        if (company_name_lower == exporter_name_lower or 
            exporter_name_lower in company_name_lower or
            company_name_lower in exporter_name_lower):
            continue
        
        # 2. استبعاد أسماء البلدان (مهم جداً!)
        if company_name_lower in country_names:
            continue
        # استبعاد إذا كان الاسم هو اسم بلد فقط
        if any(country in company_name_lower for country in country_names):
            # إذا كان الاسم يحتوي على اسم بلد فقط (بدون كلمات أخرى)
            words = company_name_lower.split()
            if len(words) == 1 and words[0] in country_names:
                continue
            # إذا كان الاسم يبدأ أو ينتهي باسم بلد فقط
            if (words[0] in country_names or words[-1] in country_names) and len(words) <= 2:
                continue
        
        # 3. استبعاد كلمات التعليمات/الأزرار (مهم جداً!)
        if any(instruction in company_name_lower for instruction in instruction_words):
            continue
        
        # 4. استبعاد إذا كان العنوان يبدو كصفحة (فلترة قوية)
        if any(keyword in company_name_lower for keyword in page_keywords):
            continue
        
        # 5. استبعاد إذا كان العنوان يبدأ بكلمات تشير إلى صفحات
        page_starters = [
            "list of", "top ", "best ", "find ", "search for", "how to", "what is",
            "directory of", "companies that", "who imports", "who buys",
            "import data", "trade data", "wholesale suppliers", "leading",
            "major", "largest", "complete list", "full list", "click", "read",
            "view", "see", "show", "more", "learn", "about", "contact"
        ]
        if any(company_name_lower.startswith(kw) for kw in page_starters):
            continue
        
        # 6. استبعاد الأسماء التي تنتهي بكلمات تشير إلى صفحات
        page_enders = ["directory", "list", "search", "results", "page", "article", "blog"]
        if any(company_name_lower.endswith(kw) for kw in page_enders):
            continue
        
        # 7. استبعاد إذا كان الموقع من مواقع B2B العامة
        website = result.get("website", "").lower()
        if any(site in website for site in excluded_b2b_sites):
            continue
        
        # 8. استبعاد الأسماء القصيرة جداً أو الطويلة جداً
        if len(company_name) < 5 or len(company_name) > 80:
            continue
        
        # 9. استبعاد الأسماء التي تحتوي على أرقام في البداية (مثل "10 Best...")
        if company_name and company_name[0].isdigit():
            continue
        
        # 10. استبعاد الأسماء التي تنتهي بـ ":" أو "..." (غالباً مقالات)
        if company_name.endswith(':') or company_name.endswith('...'):
            continue
        
        # 11. استبعاد الأسماء التي تحتوي على رموز خاصة كثيرة
        special_chars = sum(1 for c in company_name if c in "()[]{}|\\/<>")
        if special_chars > 1:  # أكثر صرامة
            continue
        
        # 12. استبعاد الأسماء التي تبدو كعناوين URLs
        if any(company_name_lower.startswith(prefix) for prefix in 
               ['http://', 'https://', 'www.', 'http', 'https']):
            continue
        
        # 13. التأكد من وجود حرف كبير واحد على الأقل (اسم شركة حقيقي)
        if not any(c.isupper() for c in company_name[:15]):
            continue
        
        # 14. استبعاد الأسماء التي كلها أحرف صغيرة (ليست أسماء شركات)
        if company_name.islower():
            continue
        
        # 15. استبعاد الأسماء التي كلها أحرف كبيرة (غالباً اختصارات أو عناوين)
        if company_name.isupper() and len(company_name) > 10:
            continue
        
        # 16. استبعاد الأسماء التي تحتوي على كلمات عامة فقط
        words = company_name.split()
        if len(words) <= 3:
            generic_count = sum(1 for word in words if word.lower() in generic_only_words)
            if generic_count >= len(words) - 1:  # كل الكلمات تقريباً عامة
                continue
        
        # 17. استبعاد الأسماء التي تبدو كعناوين صفحات
        page_indicators = ["page", "result", "search", "query", "found", "showing", 
                          "displaying", "article", "blog", "post", "news", "click",
                          "read", "view", "see", "more", "learn", "about"]
        if any(indicator in company_name_lower for indicator in page_indicators):
            continue
        
        # 18. التأكد من أن اسم الشركة يحتوي على كلمات حقيقية (ليس كل الكلمات عامة)
        company_words = company_name.split()
        if len(company_words) >= 2:
            business_words = ["company", "corp", "corporation", "inc", "ltd", "llc", 
                            "limited", "group", "enterprises", "industries", "trading",
                            "import", "export", "international", "global", "co"]
            non_business_words = [w for w in company_words if w.lower() not in business_words]
            if len(non_business_words) == 0:  # كل الكلمات عامة
                continue
        
        # 19. فلترة إضافية: استبعاد الأسماء التي تحتوي على "in" + دولة (مثل "Importers in USA")
        if " in " in company_name_lower and len(words) <= 5:
            # إذا كان الاسم قصير ويحتوي على "in" + دولة، غالباً عنوان صفحة
            continue
        
        # 20. استبعاد الأسماء التي تبدو كعبارات بحث (تحتوي على علامات استفهام أو تعجب)
        if "?" in company_name or "!" in company_name:
            continue
        
        # 21. استبعاد الأسماء التي تبدو كعناوين مقالات (تبدأ بكلمات مثل "The", "A", "An" فقط)
        if company_name_lower.startswith(("the ", "a ", "an ")) and len(words) <= 3:
            continue
        
        # 22. التأكد من أن الاسم يحتوي على حروف (ليس أرقام فقط)
        if not any(c.isalpha() for c in company_name):
            continue
        
        # 23. استبعاد الأسماء التي تبدو كعناوين صفحات (تحتوي على "/" أو "-" كثيرة)
        if company_name.count('/') > 1 or company_name.count('-') > 3:
            continue
        
        # 24. حساب نقاط الجودة (صارم جداً)
        quality_score = 0
        
        # نقاط أساسية: يجب أن يكون اسم الشركة يبدو حقيقياً
        # اسم الشركة يجب أن يحتوي على كلمة واحدة على الأقل ليست عامة
        has_real_word = False
        for word in words:
            word_lower = word.lower()
            if (word_lower not in generic_only_words and 
                word_lower not in page_keywords and 
                word_lower not in instruction_words and
                word_lower not in country_names and
                len(word) >= 3):
                has_real_word = True
                break
        
        if not has_real_word:
            continue  # استبعاد إذا لم يكن هناك كلمة حقيقية
        
        quality_score += 10  # نقاط أساسية لاسم شركة يبدو حقيقياً
        
        if result.get("email"):
            quality_score += 20
        if result.get("phone"):
            quality_score += 15
        if result.get("website") and not any(site in website for site in excluded_b2b_sites):
            quality_score += 10
        if result.get("country"):
            quality_score += 5
        
        # إذا كان المصدر من ImportKey مباشرة، إعطاء نقاط إضافية
        if result.get("source") == "ImportKey.com Direct":
            quality_score += 30  # ImportKey بيانات فعلية من الجمارك
        
        result["quality_score"] = quality_score
        
        # 25. إزالة التكرارات
        identifier = (company_name_lower, result.get("website", "").lower())
        if identifier not in seen:
            seen.add(identifier)
            unique_results.append(result)
    
    # ترتيب النتائج حسب نقاط الجودة (الأعلى أولاً)
    unique_results.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
    
    # إرجاع النتائج - فلترة صارمة جداً
    filtered_results = []
    for r in unique_results:
        score = r.get("quality_score", 0)
        source = r.get("source", "")
        company_name = r.get("company_name", "")
        
        # إذا كان من ImportKey مباشرة، إرجاعه فقط إذا كان يبدو كاسم شركة حقيقي
        if source == "ImportKey.com Direct":
            # فلترة إضافية: التأكد من أن الاسم يبدو حقيقياً
            if score >= 10:  # على الأقل النقاط الأساسية
                filtered_results.append(r)
        # وإلا، إرجاع فقط النتائج ذات الجودة الجيدة جداً (نقاط >= 20)
        elif score >= 20:
            filtered_results.append(r)
    
    print(f"DEBUG: بعد الفلترة الأساسية: {len(unique_results)}, بعد فلترة الجودة الصارمة: {len(filtered_results)}")
    
    # إذا كانت النتائج كثيرة جداً (أكثر من 100)، إرجاع فقط الأفضل
    if len(filtered_results) > 100:
        filtered_results = filtered_results[:100]
        print(f"DEBUG: تم تقليل النتائج إلى 100 نتيجة (الأفضل)")
    
    return filtered_results


def is_directory_page(title: str, link: str, snippet: str) -> bool:
    """التحقق من أن الصفحة هي صفحة directory أو list وليست صفحة شركة"""
    title_lower = title.lower()
    link_lower = link.lower()
    snippet_lower = (snippet or "").lower()
    
    # كلمات تشير إلى صفحات directories
    directory_keywords = [
        "directory", "list", "listing", "catalog", "database", "registry",
        "find", "search", "browse", "companies", "suppliers", "importers",
        "buyers", "distributors", "wholesale", "top 10", "top 20",
        "best", "leading", "major", "all", "complete list", "full list"
    ]
    
    # إذا كان العنوان يحتوي على كلمات directory
    if any(keyword in title_lower for keyword in directory_keywords):
        return True
    
    # إذا كان العنوان يبدأ بكلمات تشير إلى صفحات
    if any(title_lower.startswith(kw) for kw in ["list of", "top ", "best ", "find ", "search for"]):
        return True
    
    # إذا كان الموقع يحتوي على كلمات directory في الرابط
    directory_domains = ["directory", "list", "catalog", "database", "registry"]
    if any(dd in link_lower for dd in directory_domains):
        return True
    
    return False


def extract_companies_from_page(url: str, exporter_name: str, countries: List[str] = None) -> List[Dict]:
    """استخراج أسماء الشركات من صفحة directory أو list"""
    results = []
    
    try:
        print(f"DEBUG: استخراج الشركات من: {url[:80]}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        if response.status_code != 200:
            return results
        
        soup = BeautifulSoup(response.text, 'html.parser')
        exporter_name_lower = exporter_name.lower()
        
        # استراتيجية 1: البحث عن عناصر <li> أو <div> تحتوي على أسماء شركات
        # البحث عن عناصر تحتوي على كلمات مثل "Inc", "LLC", "Ltd", "Company"
        company_indicators = ["inc", "llc", "ltd", "limited", "corporation", "corp", "company", "co"]
        
        # البحث في جميع العناصر
        all_elements = soup.find_all(['li', 'div', 'p', 'td', 'span', 'a'])
        seen_companies = set()
        
        for elem in all_elements:
            text = elem.get_text().strip()
            
            # فلترة: يجب أن يكون النص مناسباً لاسم شركة
            if not text or len(text) < 5 or len(text) > 100:
                continue
            
            text_lower = text.lower()
            
            # استبعاد إذا كان نفس اسم الشركة المصدرة
            if exporter_name_lower in text_lower or text_lower in exporter_name_lower:
                continue
            
            # استبعاد النصوص التي تبدو كعناوين صفحات
            if any(kw in text_lower for kw in ["directory", "list", "page", "search", "find", "click here", "more info"]):
                continue
            
            # البحث عن مؤشرات شركة
            has_company_indicator = any(indicator in text_lower for indicator in company_indicators)
            
            # أو البحث عن نمط اسم شركة (يبدأ بحرف كبير، يحتوي على كلمات)
            words = text.split()
            if len(words) >= 2 and len(words) <= 6:
                # يجب أن تبدأ كلمة واحدة على الأقل بحرف كبير
                has_capital = any(w and w[0].isupper() for w in words[:3])
                
                if (has_company_indicator or has_capital) and text_lower not in seen_companies:
                    # تنظيف النص
                    company_name = text
                    for sep in [" - ", " | ", " – ", ":", "::"]:
                        if sep in company_name:
                            company_name = company_name.split(sep)[0].strip()
                    
                    if len(company_name) >= 3 and len(company_name) <= 80:
                        seen_companies.add(text_lower)
                        
                        # محاولة استخراج معلومات إضافية
                        parent = elem.find_parent()
                        full_text = parent.get_text() if parent else text
                        
                        results.append({
                            "company_name": company_name,
                            "country": extract_country_from_text(full_text, countries) or "",
                            "email": extract_email_from_text(full_text) or "",
                            "website": "",
                            "phone": extract_phone_from_text(full_text) or "",
                            "contact_person": "",
                            "address": full_text[:200] if full_text else "",
                            "source": f"Extracted from {url[:50]}"
                        })
        
        # استراتيجية 2: البحث في جداول
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # أول عمود عادة يكون اسم الشركة
                    first_cell_text = cells[0].get_text().strip()
                    if (first_cell_text and 5 <= len(first_cell_text) <= 80 and
                        first_cell_text.lower() not in seen_companies and
                        exporter_name_lower not in first_cell_text.lower()):
                        
                        seen_companies.add(first_cell_text.lower())
                        
                        # البحث عن معلومات في باقي الخلايا
                        full_row_text = " ".join([c.get_text() for c in cells])
                        
                        results.append({
                            "company_name": first_cell_text,
                            "country": extract_country_from_text(full_row_text, countries) or "",
                            "email": extract_email_from_text(full_row_text) or "",
                            "website": "",
                            "phone": extract_phone_from_text(full_row_text) or "",
                            "contact_person": "",
                            "address": full_row_text[:200] if full_row_text else "",
                            "source": f"Extracted from {url[:50]}"
                        })
        
        print(f"DEBUG: تم استخراج {len(results)} شركة من الصفحة")
        
    except Exception as e:
        print(f"DEBUG: خطأ في استخراج الشركات من {url}: {e}")
    
    return results


def search_google_importers(exporter_name: str, product_name: str = None, countries: List[str] = None) -> List[Dict]:
    """البحث عن المستوردين عبر Google - محسّن للبحث عن الشركات التي استوردت من مصدر محدد"""
    results = []
    
    try:
        # بناء استعلامات البحث المحسّنة - تستهدف الشركات التي استوردت فعلياً
        queries = []
        
        # استعلامات أساسية: الشركات التي استوردت من المصدر
        queries.append(f'companies imported from "{exporter_name}"')
        queries.append(f'importers from "{exporter_name}"')
        queries.append(f'buyers from "{exporter_name}"')
        queries.append(f'"{exporter_name}" importers buyers')
        queries.append(f'customs data "{exporter_name}" importers')
        
        # إذا كان هناك منتج محدد
        if product_name:
            queries.append(f'"{product_name}" importers from "{exporter_name}"')
            queries.append(f'companies imported "{product_name}" from "{exporter_name}"')
            queries.append(f'"{exporter_name}" "{product_name}" importers')
        
        # استعلامات مع الدول
        if countries:
            for country in countries[:3]:
                queries.append(f'companies imported from "{exporter_name}" {country}')
                queries.append(f'"{exporter_name}" importers {country}')
                if product_name:
                    queries.append(f'"{product_name}" importers from "{exporter_name}" {country}')
        
        # استعلامات ImportKey style
        queries.append(f'site:importkey.com "{exporter_name}"')
        queries.append(f'importkey "{exporter_name}" importers')
        
        print(f"DEBUG: Google - عدد الاستعلامات: {len(queries)}")
        
        for idx, query in enumerate(queries[:10], 1):
            try:
                print(f"DEBUG: Google [{idx}/{len(queries[:5])}] - استعلام: {query[:60]}...")
                
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                
                response = requests.get(search_url, headers=headers, timeout=15)
                print(f"DEBUG: Google [{idx}] - حالة الاستجابة: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # البحث عن النتائج
                    result_divs = soup.find_all('div', class_='g')
                    if not result_divs:
                        result_divs = soup.find_all('div', {'class': ['tF2Cxc', 'g']})
                    
                    print(f"DEBUG: Google [{idx}] - تم العثور على {len(result_divs)} div")
                    
                    for result_div in result_divs[:10]:
                        try:
                            title_elem = result_div.find('h3')
                            link_elem = result_div.find('a', href=True)
                            
                            if title_elem and link_elem:
                                title = title_elem.get_text().strip()
                                website = link_elem.get('href', '')
                                
                                # تنظيف الرابط
                                if website.startswith('/url?'):
                                    try:
                                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(website).query)
                                        if 'q' in parsed:
                                            website = parsed['q'][0]
                                    except:
                                        pass
                                
                                snippet = result_div.find('span', class_='aCOpRe')
                                snippet_text = snippet.get_text() if snippet else ""
                                
                                # التحقق من أن الصفحة ليست directory
                                if is_directory_page(title, website, snippet_text):
                                    print(f"DEBUG: اكتشاف صفحة directory: {title[:50]}...")
                                    # محاولة استخراج الشركات من داخل الصفحة
                                    if website and ('http' in website or 'www' in website):
                                        extracted = extract_companies_from_page(website, exporter_name, countries)
                                        results.extend(extracted)
                                else:
                                    # صفحة شركة عادية
                                    if title and len(title) > 2:
                                        results.append({
                                            "company_name": title,
                                            "country": extract_country_from_text(snippet_text, countries) or "",
                                            "email": extract_email_from_text(snippet_text) or "",
                                            "website": website or "",
                                            "phone": extract_phone_from_text(snippet_text) or "",
                                            "contact_person": "",
                                            "address": snippet_text[:200] if snippet_text else "",
                                            "source": "Google Search"
                                        })
                        except:
                            continue
                
                time.sleep(1)
                
            except Exception as e:
                print(f"DEBUG: Google [{idx}] - خطأ: {e}")
                continue
        
    except Exception as e:
        print(f"DEBUG: خطأ عام في Google: {e}")
    
    return results


def search_api_importers(exporter_name: str, product_name: str = None, countries: List[str] = None, api_key: str = None) -> List[Dict]:
    """البحث عن المستوردين عبر SerpAPI - محسّن للبحث عن الشركات التي استوردت من مصدر محدد"""
    results = []
    
    if not api_key:
        return results
    
    print(f"DEBUG: SerpAPI - بدء البحث")
    
    try:
        api_key = api_key.strip()
        base_url = "https://serpapi.com/search"
        
        # بناء استعلامات البحث المحسّنة - تستهدف الشركات التي استوردت فعلياً
        queries = []
        
        # استعلامات أساسية: الشركات التي استوردت من المصدر
        queries.append(f'companies imported from "{exporter_name}" (inc OR llc OR company OR ltd)')
        queries.append(f'importers from "{exporter_name}" (inc OR llc OR company)')
        queries.append(f'buyers from "{exporter_name}" (inc OR llc OR company)')
        queries.append(f'"{exporter_name}" importers buyers (inc OR llc OR company)')
        queries.append(f'customs data "{exporter_name}" importers')
        
        # استعلامات ImportKey style
        queries.append(f'site:importkey.com "{exporter_name}"')
        queries.append(f'importkey "{exporter_name}" importers')
        
        # إذا كان هناك منتج محدد
        if product_name:
            queries.append(f'"{product_name}" importers from "{exporter_name}" (inc OR llc OR company)')
            queries.append(f'companies imported "{product_name}" from "{exporter_name}"')
        
        # استعلامات مع الدول
        if countries:
            for country in countries[:3]:
                queries.append(f'companies imported from "{exporter_name}" "{country}" (inc OR llc OR company)')
                queries.append(f'"{exporter_name}" importers "{country}" (inc OR llc OR company)')
                if product_name:
                    queries.append(f'"{product_name}" importers from "{exporter_name}" "{country}"')
        
        print(f"DEBUG: SerpAPI - عدد الاستعلامات: {len(queries)}")
        
        for idx, query in enumerate(queries[:8], 1):
            try:
                print(f"DEBUG: SerpAPI [{idx}/{len(queries[:3])}] - استعلام: {query[:60]}...")
                
                gl_code = "us"
                if countries:
                    country_mapping = {
                        "United States": "us", "USA": "us",
                        "Germany": "de", "France": "fr", "United Kingdom": "uk", "UK": "uk",
                        "Italy": "it", "Spain": "es", "Netherlands": "nl", "Belgium": "be",
                    }
                    gl_code = country_mapping.get(countries[0], "us")
                
                params = {
                    "q": query,
                    "api_key": api_key,
                    "engine": "google",
                    "num": 20,
                    "hl": "en",
                    "gl": gl_code
                }
                
                response = requests.get(base_url, params=params, timeout=30)
                print(f"DEBUG: SerpAPI [{idx}] - حالة الاستجابة: {response.status_code}")
                
                if response.status_code == 401:
                    print("DEBUG: SerpAPI - ⚠️ مفتاح API غير صحيح (401)")
                    break
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except:
                        continue
                    
                    if "error" in data:
                        print(f"DEBUG: SerpAPI [{idx}] - خطأ: {data.get('error')}")
                        continue
                    
                    organic_results = data.get("organic_results", [])
                    print(f"DEBUG: SerpAPI [{idx}] - عدد النتائج: {len(organic_results)}")
                    
                    for result in organic_results:
                        try:
                            title = result.get("title", "").strip()
                            link = result.get("link", "")
                            snippet = result.get("snippet", "").strip()
                            
                            if not title or not link:
                                continue
                            
                            link_lower = link.lower()
                            
                            # استبعاد المواقع غير المرغوبة
                            excluded = ["amazon", "alibaba", "ebay", "facebook", "twitter", "wikipedia", "google"]
                            if any(domain in link_lower for domain in excluded):
                                continue
                            
                            # التحقق من أن الصفحة ليست directory
                            if is_directory_page(title, link, snippet):
                                print(f"DEBUG: SerpAPI - اكتشاف صفحة directory: {title[:50]}...")
                                # محاولة استخراج الشركات من داخل الصفحة
                                extracted = extract_companies_from_page(link, exporter_name, countries)
                                results.extend(extracted)
                            else:
                                # صفحة شركة عادية
                                company_name = title
                                for sep in [" - ", " | ", " – "]:
                                    if sep in company_name:
                                        company_name = company_name.split(sep)[0].strip()
                                
                                if company_name and len(company_name) > 3:
                                    results.append({
                                        "company_name": company_name,
                                        "country": extract_country_from_text(snippet, countries) or (countries[0] if countries else ""),
                                        "email": extract_email_from_text(snippet) or "",
                                        "website": link,
                                        "phone": extract_phone_from_text(snippet) or "",
                                        "contact_person": "",
                                        "address": snippet[:200] if snippet else "",
                                        "source": "SerpAPI"
                                    })
                        except:
                            continue
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"DEBUG: SerpAPI [{idx}] - خطأ: {e}")
                continue
        
    except Exception as e:
        print(f"DEBUG: SerpAPI - خطأ عام: {e}")
    
    print(f"DEBUG: SerpAPI - إجمالي النتائج: {len(results)}")
    return results


def extract_email_from_text(text: str) -> str:
    """استخراج البريد الإلكتروني من النص"""
    if not text:
        return ""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else ""


def extract_country_from_text(text: str, countries: List[str] = None) -> str:
    """استخراج اسم الدولة من النص"""
    if not text:
        return ""
    
    text_lower = text.lower()
    
    if countries:
        for country in countries:
            if country.lower() in text_lower:
                return country
    
    country_mappings = {
        "usa": "United States", "united states": "United States", "us": "United States",
        "uk": "United Kingdom", "united kingdom": "United Kingdom",
        "germany": "Germany", "france": "France", "italy": "Italy", "spain": "Spain",
    }
    
    for key, value in country_mappings.items():
        if key in text_lower:
            return value
    
    return ""


def extract_phone_from_text(text: str) -> str:
    """استخراج رقم الهاتف من النص"""
    if not text:
        return ""
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        r'\+?\d{10,15}',
    ]
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        if matches:
            digits = re.sub(r'\D', '', matches[0])
            if len(digits) >= 7:
                return matches[0]
    return ""


def search_importkey_direct(exporter_name: str, product_name: str = None, countries: List[str] = None) -> List[Dict]:
    """البحث المباشر في ImportKey.com - محاولة استخراج بيانات الشحنات الفعلية"""
    results = []
    
    try:
        print(f"DEBUG: ImportKey - محاولة البحث في ImportKey مباشرة...")
        
        # بناء رابط البحث في ImportKey
        search_query = exporter_name.replace(" ", "+")
        importkey_url = f"https://www.importkey.com/search?q={urllib.parse.quote(search_query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.importkey.com/',
        }
        
        response = requests.get(importkey_url, headers=headers, timeout=15, allow_redirects=True)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # حفظ HTML للفحص (للتطوير)
            debug_file = f"importkey_debug_{exporter_name.replace(' ', '_')[:30]}.html"
            try:
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"DEBUG: تم حفظ HTML في {debug_file} للفحص")
            except:
                pass
            
            # البحث عن أسماء الشركات المستوردة في الصفحة
            # ImportKey يعرض عادة أسماء الشركات في جداول أو divs معينة
            exporter_name_lower = exporter_name.lower()
            seen_companies = set()
            
            # استراتيجية 1: البحث في جميع النصوص التي تبدو كأسماء شركات
            all_text_elements = soup.find_all(['div', 'span', 'td', 'a', 'p', 'li'])
            
            for elem in all_text_elements:
                text = elem.get_text().strip()
                
                # فلترة: يجب أن يكون النص مناسباً لاسم شركة
                if not text or len(text) < 5 or len(text) > 80:
                    continue
                
                text_lower = text.lower()
                
                # استبعاد إذا كان نفس اسم الشركة المصدرة
                if exporter_name_lower in text_lower or text_lower in exporter_name_lower:
                    continue
                
                # استبعاد النصوص التي تبدو كعناوين صفحات
                if any(kw in text_lower for kw in ["search", "results", "importkey", "page", "next", "previous", "showing"]):
                    continue
                
                # البحث عن نمط اسم شركة (يبدأ بحرف كبير، يحتوي على كلمات)
                words = text.split()
                if len(words) >= 2 and len(words) <= 6:
                    # يجب أن تبدأ كلمة واحدة على الأقل بحرف كبير
                    has_capital = any(w and w[0].isupper() for w in words[:3])
                    
                    # مؤشرات شركة
                    company_indicators = ["inc", "llc", "ltd", "limited", "corporation", "corp", "company", "co", "llp"]
                    has_company_indicator = any(indicator in text_lower for indicator in company_indicators)
                    
                    if (has_capital or has_company_indicator) and text_lower not in seen_companies:
                        # تنظيف النص
                        company_name = text
                        for sep in [" - ", " | ", " – ", ":", "::", "\n", "\t"]:
                            if sep in company_name:
                                company_name = company_name.split(sep)[0].strip()
                        
                        if len(company_name) >= 3 and len(company_name) <= 80:
                            seen_companies.add(text_lower)
                            
                            # محاولة استخراج معلومات إضافية من العنصر الأب
                            parent = elem.find_parent()
                            full_text = parent.get_text() if parent else text
                            
                            results.append({
                                "company_name": company_name,
                                "country": extract_country_from_text(full_text, countries) or "",
                                "email": extract_email_from_text(full_text) or "",
                                "website": "",
                                "phone": extract_phone_from_text(full_text) or "",
                                "contact_person": "",
                                "address": full_text[:200] if full_text else "",
                                "source": "ImportKey.com Direct"
                            })
            
            # استراتيجية 2: البحث في جداول (ImportKey يستخدم جداول لعرض البيانات)
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # أول عمود عادة يكون اسم الشركة المستوردة
                        first_cell_text = cells[0].get_text().strip()
                        if (first_cell_text and 5 <= len(first_cell_text) <= 80 and
                            first_cell_text.lower() not in seen_companies and
                            exporter_name_lower not in first_cell_text.lower()):
                            
                            seen_companies.add(first_cell_text.lower())
                            
                            # البحث عن معلومات في باقي الخلايا
                            full_row_text = " ".join([c.get_text() for c in cells])
                            
                            results.append({
                                "company_name": first_cell_text,
                                "country": extract_country_from_text(full_row_text, countries) or "",
                                "email": extract_email_from_text(full_row_text) or "",
                                "website": "",
                                "phone": extract_phone_from_text(full_row_text) or "",
                                "contact_person": "",
                                "address": full_row_text[:200] if full_row_text else "",
                                "source": "ImportKey.com Direct"
                            })
            
            print(f"DEBUG: تم العثور على {len(results)} شركة من ImportKey")
        else:
            print(f"DEBUG: ImportKey - حالة الاستجابة: {response.status_code}")
    
    except Exception as e:
        print(f"DEBUG: ImportKey - خطأ في البحث المباشر: {e}")
    
    return results


def search_importkey_style(exporter_name: str, countries: List[str] = None, api_key: str = None, product_name: str = None) -> List[Dict]:
    """البحث بنمط ImportKey - محسّن للعثور على الشركات التي استوردت فعلياً"""
    print(f"DEBUG: ===== بدء البحث بنمط ImportKey =====")
    results = []
    
    # محاولة 1: البحث المباشر في ImportKey.com
    print("DEBUG: ImportKey - محاولة البحث في ImportKey مباشرة...")
    try:
        direct_results = search_importkey_direct(exporter_name, product_name, countries)
        results.extend(direct_results)
        print(f"DEBUG: ✓ تم العثور على {len(direct_results)} نتيجة من ImportKey")
    except Exception as e:
        print(f"DEBUG: ✗ خطأ في ImportKey المباشر: {e}")
    
    # محاولة 2: SerpAPI (مع استعلامات محسّنة)
    if api_key and len(results) < 10:
        print("DEBUG: ImportKey - محاولة البحث عبر SerpAPI...")
        try:
            api_results = search_api_importers(exporter_name, product_name, countries, api_key)
            results.extend(api_results)
            print(f"DEBUG: ✓ تم العثور على {len(api_results)} نتيجة من SerpAPI")
        except Exception as e:
            print(f"DEBUG: ✗ خطأ في SerpAPI: {e}")
    
    # محاولة 3: Google (مع استعلامات محسّنة)
    if len(results) < 10:
        print("DEBUG: ImportKey - محاولة البحث عبر Google...")
        try:
            google_results = search_google_importers(exporter_name, product_name, countries)
            results.extend(google_results)
            print(f"DEBUG: ✓ تم العثور على {len(google_results)} نتيجة من Google")
        except Exception as e:
            print(f"DEBUG: ✗ خطأ في Google: {e}")
    
    # محاولة 4: البحث القياسي (كحل احتياطي)
    if len(results) == 0:
        print("DEBUG: ImportKey - محاولة البحث القياسي...")
        try:
            standard_results = search_importers_by_exporter(exporter_name, product_name, countries, api_key)
            results.extend(standard_results)
            print(f"DEBUG: ✓ تم العثور على {len(standard_results)} نتيجة من البحث القياسي")
        except Exception as e:
            print(f"DEBUG: ✗ خطأ في البحث القياسي: {e}")
    
    print(f"DEBUG: ImportKey - إجمالي النتائج: {len(results)}")
    return results
