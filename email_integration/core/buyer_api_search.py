"""
البحث عن المشترين عبر API خارجي
External API Search for Buyers
"""
import requests
import json
import re
import urllib.parse
import time
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


def search_buyers_via_api(product_name: str, countries: List[str], api_key: str = None, api_type: str = "serpapi") -> List[Dict]:
    """
    البحث عن المشترين عبر API خارجي
    
    Args:
        product_name: اسم المنتج
        countries: قائمة الدول
        api_key: مفتاح API (اختياري)
        api_type: نوع API ("serpapi", "custom", "google", "company_db", etc.)
    
    Returns:
        قائمة من المشترين (كل مشتري هو dict مع: company_name, country, email, etc.)
    """
    results = []
    
    if api_type == "serpapi":
        return search_serpapi(product_name, countries, api_key)
    elif api_type == "google":
        return search_google_places(product_name, countries, api_key)
    elif api_type == "company_db":
        return search_company_database(product_name, countries, api_key)
    else:
        return search_custom_api(product_name, countries, api_key)


def compute_result_score(result: Dict, product_name: str) -> int:
    """
    حساب نقاط النتيجة بناءً على جودة المعلومات المتاحة
    
    Args:
        result: نتيجة البحث (dict)
        product_name: اسم المنتج للبحث عن التطابق
    
    Returns:
        نقاط من 0 إلى 100
    """
    score = 0
    
    # البريد الإلكتروني (40 نقطة)
    if result.get("email"):
        email = result.get("email", "").lower()
        # نقاط إضافية إذا كان البريد من نطاق الشركة (ليس بريد شخصي)
        excluded_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
        if not any(domain in email for domain in excluded_domains):
            score += 40
        else:
            score += 20  # بريد شخصي لكن موجود
    
    # رقم الهاتف (25 نقطة)
    if result.get("phone"):
        phone = result.get("phone", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if len(phone) >= 7:
            score += 25
    
    # موقع إلكتروني (10 نقاط)
    if result.get("website"):
        score += 10
    
    # تطابق كلمات البحث (25 نقطة)
    company_name = result.get("company_name", "").lower()
    snippet = result.get("address", "").lower()
    product_lower = product_name.lower()
    
    keyword_matches = 0
    for word in product_lower.split():
        if word in company_name:
            keyword_matches += 1
        if word in snippet:
            keyword_matches += 1
    
    score += min(25, keyword_matches * 3)
    
    # طول الوصف (5 نقاط)
    if len(result.get("address", "")) > 200:
        score += 5
    
    # معلومات شخص الاتصال (5 نقاط)
    if result.get("contact_person"):
        score += 5
    
    return min(100, score)


def extract_obfuscated_emails(text: str) -> List[str]:
    """
    استخراج البريد الإلكتروني المشفر (مثل: info[at]company[dot]com)
    
    Args:
        text: النص للبحث فيه
    
    Returns:
        قائمة من عناوين البريد الإلكتروني
    """
    emails = []
    
    # نمط البريد المشفر
    obf_patterns = [
        r'([\w.\-]+)\s*(?:\[at\]|\(at\)| at |@)\s*([\w.\-]+)\s*(?:\[dot\]|\(dot\)| dot |\.)\s*([a-zA-Z]{2,})',
        r'([\w.\-]+)\s*\[at\]\s*([\w.\-]+)\s*\[dot\]\s*([a-zA-Z]{2,})',
        r'([\w.\-]+)\s*\(at\)\s*([\w.\-]+)\s*\(dot\)\s*([a-zA-Z]{2,})',
    ]
    
    for pattern in obf_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) == 3:
                email = f"{match[0]}@{match[1]}.{match[2]}"
                emails.append(email.lower())
    
    return emails


def extract_emails_enhanced(text: str) -> List[str]:
    """
    استخراج محسّن للبريد الإلكتروني (عادي + مشفر)
    
    Args:
        text: النص للبحث فيه
    
    Returns:
        قائمة من عناوين البريد الإلكتروني
    """
    emails = set()
    
    # البريد العادي
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    normal_emails = re.findall(email_pattern, text, re.IGNORECASE)
    emails.update([e.lower() for e in normal_emails])
    
    # البريد المشفر
    obf_emails = extract_obfuscated_emails(text)
    emails.update(obf_emails)
    
    return list(emails)


def generate_advanced_queries(product_name: str, country_term: str, exclude_terms: str) -> List[str]:
    """
    توليد استعلامات بحث متقدمة ومتنوعة
    
    Args:
        product_name: اسم المنتج
        country_term: مصطلح الدولة
        exclude_terms: مصطلحات الاستبعاد
    
    Returns:
        قائمة من استعلامات البحث
    """
    queries = []
    
    # استعلامات LinkedIn
    queries.append(f'site:linkedin.com/company "{product_name}" {country_term}')
    
    # استعلامات B2B directories (محدودة - بعضها قد يحتاج اشتراك)
    # queries.append(f'site:europages.com "{product_name}" {country_term} {exclude_terms}')
    
    # استعلامات صفحات الاتصال
    queries.append(f'"{product_name}" {country_term} "contact us" email {exclude_terms}')
    queries.append(f'"{product_name}" {country_term} "get quote" {exclude_terms}')
    queries.append(f'"{product_name}" {country_term} "request quote" {exclude_terms}')
    
    # استعلامات أساسية
    queries.append(f'"{product_name}" company {country_term} contact email {exclude_terms}')
    queries.append(f'"{product_name}" buyer {country_term} company email phone {exclude_terms}')
    queries.append(f'"{product_name}" importer {country_term} company contact {exclude_terms}')
    queries.append(f'"{product_name}" distributor {country_term} company email {exclude_terms}')
    queries.append(f'"{product_name}" trading company {country_term} contact {exclude_terms}')
    
    # استعلامات B2B متخصصة
    queries.append(f'"{product_name}" B2B {country_term} company {exclude_terms}')
    queries.append(f'"{product_name}" wholesale {country_term} buyer {exclude_terms}')
    
    # استعلامات صفحات About
    queries.append(f'"{product_name}" {country_term} "about us" company {exclude_terms}')
    
    return queries


def search_serpapi(product_name: str, countries: List[str], api_key: str = None) -> List[Dict]:
    """
    البحث باستخدام SerpAPI (Google Search API)
    """
    results = []
    
    if not api_key:
        return results
    
    try:
        # تنظيف مفتاح API (إزالة "serpapi-key" إذا كان موجوداً)
        api_key = api_key.strip()
        if api_key.startswith("serpapi-key "):
            api_key = api_key.replace("serpapi-key ", "").strip()
        
        base_url = "https://serpapi.com/search"
        
        # قائمة المواقع التجارية العامة والمواقع التي تحتاج اشتراكات - قائمة شاملة
        excluded_domains = [
            # مواقع تجارية عامة
            "amazon", "alibaba", "ebay", "etsy", "walmart", "target",
            "aliexpress", "made-in-china", "indiamart", "tradeindia",
            "ec21", "ecplaza", "globalsources", "thomasnet", "yellowpages",
            # مواقع التواصل الاجتماعي
            "facebook", "twitter", "instagram", "youtube", "pinterest",
            "reddit", "quora", "medium", "tumblr", "snapchat", "tiktok",
            # محركات البحث
            "google", "bing", "yahoo", "duckduckgo",
            # موسوعات
            "wikipedia", "wikimedia",
            # مواقع تحتاج اشتراكات أو دلائل تجارية
            "volza", "europages", "kompass", "panjiva", "importgenius",
            "tradekey", "go4worldbusiness", "b2bfreezone", "bizvibe",
            "exportersindia", "tradeindia", "indiamart", "alibaba",
            "made-in-china", "dhgate", "1688", "globalsources",
            "thomasnet", "mfg", "supplychainconnect", "bizdirlib",
            "bizvibe", "companylist", "company-directory", "companieshouse",
            "zoominfo", "clearbit", "crunchbase", "linkedin.com/in",  # LinkedIn profiles (ليس company pages)
            # مواقع أخرى
            "fiverr", "upwork", "freelancer", "guru", "peopleperhour"
        ]
        
        # البحث في كل دولة
        for country in countries[:5]:  # زيادة إلى 5 دول
            # استعلامات محسنة للبحث عن شركات حقيقية فقط من الدولة المحددة
            # إضافة استبعادات قوية للمواقع العامة
            exclude_terms = "-amazon -alibaba -ebay -etsy -marketplace -directory -yellowpages -thomasnet -volza -europages -kompass -panjiva -indiamart -tradeindia -ec21 -ecplaza -globalsources -facebook -twitter -instagram"
            
            # استعلامات محددة للدولة
            country_code = country.lower()[:2] if len(country) >= 2 else "us"
            country_specific_queries = {
                "germany": ["deutschland", "germany", ".de"],
                "france": ["france", ".fr"],
                "united kingdom": ["uk", "united kingdom", "britain", ".co.uk"],
                "united states": ["usa", "united states", "america", ".us"],
                "italy": ["italy", "italia", ".it"],
                "spain": ["spain", "espana", ".es"],
                "netherlands": ["netherlands", "holland", ".nl"]
            }
            
            country_terms = country_specific_queries.get(country.lower(), [country.lower()])
            country_term = country_terms[0] if country_terms else country.lower()
            
            # استخدام استعلامات متقدمة
            queries = generate_advanced_queries(product_name, country_term, exclude_terms)
            
            # إضافة استعلامات إضافية حسب الدولة
            queries.append(f'site:{country_code} "{product_name}" company buyer {exclude_terms}')
            
            for query in queries:
                params = {
                    "q": query,
                    "api_key": api_key,
                    "engine": "google",
                    "num": 10,  # عدد النتائج لكل query
                    "hl": "en",
                    "gl": country.lower()[:2] if len(country) >= 2 else "us"
                }
                
                try:
                    response = requests.get(base_url, params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # استخراج النتائج العضوية
                        organic_results = data.get("organic_results")
                        if not organic_results:
                            continue
                        for result in organic_results:
                            title = result.get("title") or ""
                            link = (result.get("link") or "").lower()
                            snippet = (result.get("snippet") or "").lower()
                            
                            # التأكد من أن title و link و snippet ليست None
                            if not title or not link:
                                continue
                            
                            # استبعاد المواقع التجارية العامة والمواقع التي تحتاج اشتراكات
                            if not link or not excluded_domains:
                                continue
                            is_excluded = any(domain in link for domain in excluded_domains)
                            if is_excluded:
                                continue
                            
                            # استبعاد LinkedIn profiles (ليس company pages)
                            if "linkedin.com/in" in link or "linkedin.com/pub" in link:
                                continue
                            
                            # السماح فقط بـ LinkedIn company pages
                            if "linkedin.com/company" not in link:
                                # استبعاد إذا كان العنوان يحتوي على كلمات تشير إلى موقع عام
                                generic_title_keywords = [
                                    "directory", "marketplace", "yellow pages", "business directory",
                                    "company directory", "supplier directory", "buyer directory",
                                    "trade directory", "wholesale directory", "b2b marketplace",
                                    "online marketplace", "trading platform", "export directory"
                                ]
                                if title and any(keyword in title.lower() for keyword in generic_title_keywords):
                                    continue
                            
                            # التحقق من أن النتيجة من الدولة المحددة
                            # البحث عن اسم الدولة في العنوان أو النص
                            country_lower = country.lower()
                            country_in_result = (
                                country_lower in title.lower() or
                                country_lower in snippet or
                                country_lower in link or
                                # أسماء الدول بالعربية/مختصرة
                                (country == "Germany" and ("germany" in title.lower() or "germany" in snippet or "deutschland" in snippet or ".de" in link)) or
                                (country == "France" and ("france" in title.lower() or "france" in snippet or ".fr" in link)) or
                                (country == "United Kingdom" and ("uk" in title.lower() or "united kingdom" in title.lower() or "britain" in snippet or ".co.uk" in link or ".uk" in link)) or
                                (country == "United States" and ("usa" in title.lower() or "united states" in title.lower() or "america" in snippet or ".us" in link)) or
                                (country == "Italy" and ("italy" in title.lower() or "italia" in snippet or ".it" in link)) or
                                (country == "Spain" and ("spain" in title.lower() or "espana" in snippet or ".es" in link)) or
                                (country == "Netherlands" and ("netherlands" in title.lower() or "holland" in snippet or ".nl" in link))
                            )
                            
                            # استبعاد إذا لم تكن النتيجة من الدولة المحددة
                            if not country_in_result:
                                # استثناء: السماح بـ LinkedIn company pages إذا كان اسم الشركة واضح
                                if "linkedin.com/company" not in link:
                                    continue
                            
                            # استبعاد النتائج التي تحتوي على كلمات تشير إلى مواقع عامة في العنوان
                            excluded_title_patterns = [
                                "suppliers directory", "buyers directory", "manufacturers directory",
                                "wholesale directory", "trade directory", "company directory",
                                "b2b marketplace", "online marketplace", "trading platform",
                                "export directory", "import directory", "business directory"
                            ]
                            if any(pattern in title.lower() for pattern in excluded_title_patterns):
                                continue
                            
                                # فلترة النتائج التي تحتوي على كلمات البحث العامة
                            title_lower = title.lower()
                            snippet_lower = snippet.lower()
                            link_lower = link
                            
                            # كلمات عامة للاستبعاد في بداية العنوان
                            title_starts_with_generic = any(title_lower.startswith(word) for word in [
                                "global", "worldwide", "leading", "top", "best", "verified",
                                "premium", "wholesale", "bulk"
                            ])
                            
                            # كلمات عامة للاستبعاد
                            generic_keywords_in_title = [
                                "manufacturer", "manufacturers", "supplier", "suppliers",
                                "directory", "marketplace", "yellow pages", "yellowpages",
                                "wholesale directory", "trade directory", "buyer directory"
                            ]
                            
                            # استبعاد العناوين التي تبدأ بكلمات عامة + اسم المنتج + supplier/manufacturer
                            product_words = product_name.lower().split()
                            if title_starts_with_generic:
                                # إذا بدأ العنوان بكلمة عامة
                                if any(word in title_lower for word in ["supplier", "manufacturer", "suppliers", "manufacturers"]):
                                    # استبعاد إلا إذا كان LinkedIn
                                    if "linkedin.com/company" not in link_lower:
                                        continue
                            
                            # استبعاد العناوين التي تحتوي على اسم المنتج + supplier/manufacturer فقط (بدون اسم شركة)
                            # مثل "Dehydrated Onion Suppliers" أو "Onion Manufacturers in France"
                            if any(word in title_lower for word in product_words):
                                # إذا كان العنوان يحتوي على اسم المنتج
                                has_supplier_words = any(word in title_lower for word in ["supplier", "manufacturer", "suppliers", "manufacturers"])
                                # إذا كان العنوان قصير جداً (أقل من 40 حرف) ويحتوي على supplier/manufacturer
                                if has_supplier_words and len(title) < 40:
                                    # السماح فقط إذا كان LinkedIn أو يحتوي على معلومات اتصال
                                    if "linkedin.com/company" not in link_lower and \
                                       ("contact" not in snippet_lower and "email" not in snippet_lower):
                                        continue
                            
                            # استبعاد العناوين العامة الأخرى
                            if any(keyword in title_lower for keyword in generic_keywords_in_title):
                                # السماح فقط إذا كان LinkedIn أو موقع شركة واضح
                                if "linkedin.com/company" not in link_lower and \
                                   "company" not in title_lower and \
                                   "contact" not in snippet_lower:
                                    continue
                            
                            # استخراج اسم الشركة من العنوان - تحسين
                            company_name = title.strip()
                            
                            # إزالة معلومات إضافية من العنوان (LinkedIn, etc.)
                            for pattern in [
                                r'\s*-\s*LinkedIn',
                                r'\s*\|\s*LinkedIn',
                                r'\s*on\s+LinkedIn',
                                r'\s*-\s*.*?Company',
                                r'\s*::\s*.*',
                                r'\s*\|\s*.*',
                            ]:
                                company_name = re.sub(pattern, '', company_name, flags=re.IGNORECASE).strip()
                            
                            # إزالة الفواصل والرموز
                            for separator in [" - ", " | ", " – ", " — ", " :: ", " | ", " | ", " • "]:
                                if separator in company_name:
                                    company_name = company_name.split(separator)[0].strip()
                                    break
                            
                            # إزالة الكلمات العامة من اسم الشركة (من البداية والنهاية)
                            generic_words = ["manufacturer", "supplier", "distributor", "importer", "buyer", 
                                           "wholesale", "trading", "company", "ltd", "limited", "inc", 
                                           "corporation", "corp", "llc", "gmbh", "srl", "spa"]
                            
                            # إزالة من النهاية
                            for word in generic_words:
                                pattern = rf'\s*{re.escape(word)}\s*$'
                                company_name = re.sub(pattern, '', company_name, flags=re.IGNORECASE).strip()
                            
                            # إزالة من البداية (مثل "Leading Supplier of...")
                            for prefix in ["leading", "top", "best", "premium", "global", "worldwide"]:
                                if company_name.lower().startswith(prefix):
                                    company_name = re.sub(rf'^{re.escape(prefix)}\s+', '', company_name, flags=re.IGNORECASE).strip()
                            
                            # إذا كان الاسم قصير جداً أو غير واضح، استخرجه من الرابط
                            if not company_name or len(company_name) < 3:
                                try:
                                    parsed_url = urllib.parse.urlparse(result.get("link", ""))
                                    domain = parsed_url.netloc.replace("www.", "").lower()
                                    
                                    # استخراج اسم الشركة من النطاق
                                    if "linkedin.com" in domain:
                                        # من LinkedIn: linkedin.com/company/company-name
                                        path_parts = parsed_url.path.split('/')
                                        if 'company' in path_parts:
                                            idx = path_parts.index('company')
                                            if idx + 1 < len(path_parts):
                                                company_name = path_parts[idx + 1].replace('-', ' ').title()
                                    elif "." in domain:
                                        domain_parts = domain.split(".")
                                        if len(domain_parts) >= 2:
                                            # أخذ الجزء قبل .com/.co.uk/etc
                                            main_part = domain_parts[0]
                                            # إزالة كلمات عامة
                                            for word in ["www", "mail", "shop", "store", "buy", "sell"]:
                                                main_part = main_part.replace(word, "")
                                            if main_part:
                                                company_name = main_part.replace("-", " ").title()
                                except:
                                    pass
                            
                            # تنظيف إضافي: إزالة الأرقام والرموز في البداية
                            company_name = re.sub(r'^[\d\s\-_\.]+', '', company_name).strip()
                            
                            # إزالة مسافات زائدة
                            company_name = ' '.join(company_name.split())
                            
                            # تخطي إذا كان الاسم غير واضح أو قصير جداً
                            if not company_name or len(company_name) < 2:
                                continue
                            
                            # تخطي إذا كان اسم الشركة هو نفس كلمات البحث
                            if company_name.lower() in product_name.lower() or product_name.lower() in company_name.lower():
                                continue
                            
                            # التأكد من أن اسم الشركة يحتوي على كلمات حقيقية (ليس فقط كلمات البحث)
                            company_words = set(company_name.lower().split())
                            product_words_set = set(product_name.lower().split())
                            generic_words_set = {"supplier", "manufacturer", "buyer", "importer", "distributor", 
                                                "wholesale", "trading", "company", "ltd", "limited", "inc", 
                                                "corp", "gmbh", "srl", "spa", "llc", "co", "the", "of", "in", "and"}
                            
                            # إذا كان اسم الشركة يحتوي فقط على كلمات المنتج + كلمات عامة، استبعده
                            meaningful_words = company_words - product_words_set - generic_words_set
                            if len(meaningful_words) < 2 and len(company_words) > 3:
                                # إذا كان الاسم طويلاً ولكن لا يحتوي على كلمات ذات معنى
                                continue
                            
                            # استبعاد إذا كان العنوان مطابق تماماً أو قريب جداً من كلمات البحث
                            # مثل "Dehydrated Onion Suppliers" أو "Onion Manufacturers in France"
                            title_clean = re.sub(r'[^\w\s]', ' ', title_lower)  # إزالة الرموز
                            title_words = set(title_clean.split())
                            product_words_set = set(product_name.lower().split())
                            
                            # إذا كان العنوان يحتوي على معظم كلمات المنتج + كلمات عامة فقط
                            common_words = title_words & product_words_set
                            generic_words_in_title = {"supplier", "manufacturer", "suppliers", "manufacturers", 
                                                      "global", "worldwide", "leading", "top", "best", 
                                                      "wholesale", "bulk", "in", "the"}
                            remaining_words = title_words - product_words_set - generic_words_in_title
                            
                            # إذا كان العنوان يحتوي على كلمات المنتج ولكن القليل جداً من الكلمات الأخرى
                            if len(common_words) >= 1 and len(remaining_words) < 2:
                                # السماح فقط إذا كان LinkedIn أو يحتوي على معلومات اتصال
                                if "linkedin.com/company" not in link_lower and \
                                   "contact" not in snippet_lower and "email" not in snippet_lower:
                                    continue
                            
                            # استخراج البريد الإلكتروني - محسّن (يدعم المشفر)
                            link_url = result.get("link") or ""
                            search_text = f"{title or ''} {snippet or ''} {link_url}"
                            
                            # استخراج جميع أنواع البريد (عادي + مشفر)
                            all_emails = extract_emails_enhanced(search_text) if search_text else []
                            
                            # فلترة البريد الإلكتروني (استبعاد البريد العام)
                            filtered_emails = []
                            excluded_domains = ["example.com", "gmail.com", "yahoo.com", "hotmail.com", 
                                              "outlook.com", "email.com", "test.com", "domain.com"]
                            
                            for em in all_emails:
                                domain = em.split('@')[1].lower() if '@' in em else ""
                                # قبول البريد إذا كان من نطاق الشركة (ليس بريد شخصي عام)
                                if domain and domain not in excluded_domains:
                                    # إذا كان النطاق يحتوي على اسم الشركة أو كلمات تجارية
                                    if any(word in domain for word in ["company", "corp", "ltd", "inc", "com", "co", "net", "org"]):
                                        filtered_emails.append(em)
                                elif domain and len(domain.split('.')) >= 2:
                                    # قبول النطاقات التجارية الأخرى
                                    filtered_emails.append(em)
                            
                            email = filtered_emails[0] if filtered_emails else (all_emails[0] if all_emails else "")
                            
                            # استخراج رقم الهاتف - تحسين
                            phone_patterns = [
                                r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}',  # دولي
                                r'[\+]?[0-9]{1,4}[\s\-]?[0-9]{1,4}[\s\-]?[0-9]{1,4}[\s\-]?[0-9]{1,9}',  # بدون أقواس
                                r'Tel[:\s]+([\+\d\s\-\(\)]+)',  # Tel: +123...
                                r'Phone[:\s]+([\+\d\s\-\(\)]+)',  # Phone: +123...
                                r'Call[:\s]+([\+\d\s\-\(\)]+)',  # Call: +123...
                            ]
                            
                            phone = ""
                            for pattern in phone_patterns:
                                phones = re.findall(pattern, snippet + " " + title, re.IGNORECASE)
                                if phones:
                                    phone = phones[0].strip() if isinstance(phones[0], str) else str(phones[0]).strip()
                                    # تنظيف رقم الهاتف
                                    phone = re.sub(r'[^\d\+\-\(\)\s]', '', phone)
                                    if len(phone.replace('+', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')) >= 7:
                                        break
                            
                            # إضافة النتيجة فقط إذا لم تكن مكررة
                            is_duplicate = any(
                                (email and existing.get("email") == email) or 
                                (company_name.lower() == existing.get("company_name", "").lower())
                                for existing in results
                            )
                            
                            if not is_duplicate and company_name and len(company_name) >= 2:
                                # استخراج معلومات إضافية من snippet
                                contact_person = ""
                                # محاولة استخراج اسم شخص من snippet
                                person_patterns = [
                                    r'Contact[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                                    r'Manager[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                                    r'Director[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                                ]
                                for pattern in person_patterns:
                                    matches = re.findall(pattern, snippet, re.IGNORECASE)
                                    if matches:
                                        contact_person = matches[0]
                                        break
                                
                                # تنظيف الموقع الإلكتروني
                                website = result.get("link", "")
                                # إزالة معاملات URL
                                if website:
                                    try:
                                        parsed = urllib.parse.urlparse(website)
                                        website = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                                        if not website.startswith("http"):
                                            website = f"https://{website}"
                                    except:
                                        pass
                                
                                # إنشاء النتيجة
                                result_dict = {
                                    "company_name": company_name[:100].strip(),
                                    "country": country,
                                    "contact_person": contact_person,
                                    "email": email.strip() if email else "",
                                    "phone": phone.strip() if phone else "",
                                    "website": website,
                                    "address": snippet[:200].strip() if snippet else "",
                                    "source": "SerpAPI"
                                }
                                
                                # حساب نقاط الجودة
                                score = compute_result_score(result_dict, product_name)
                                result_dict["score"] = score
                                
                                results.append(result_dict)
                    
                    elif response.status_code == 401:
                        print(f"SerpAPI: مفتاح API غير صحيح")
                        break
                    elif response.status_code == 429:
                        print(f"SerpAPI: تم تجاوز حد الاستخدام")
                        break
                        
                    # إيقاف مؤقت بين الطلبات (تقليل لتسريع البحث)
                    time.sleep(0.3)
                        
                except requests.exceptions.Timeout:
                    print(f"SerpAPI: انتهى الوقت للبحث في {country}")
                    continue
                except Exception as e:
                    print(f"SerpAPI: خطأ في البحث عن {country}: {e}")
                    continue
                
    except Exception as e:
        print(f"SerpAPI: خطأ عام: {e}")
    
    # إزالة التكرارات النهائية بناءً على اسم الشركة أو البريد الإلكتروني
    unique_results = []
    seen_companies = set()
    seen_emails = set()
    
    for result in results:
        company_lower = result.get("company_name", "").lower().strip()
        email_lower = result.get("email", "").lower().strip()
        
        # استخدام اسم الشركة أو البريد كمعرف فريد
        identifier = email_lower if email_lower else company_lower
        
        if identifier and identifier not in seen_companies and identifier not in seen_emails:
            seen_companies.add(company_lower if company_lower else "")
            seen_emails.add(email_lower if email_lower else "")
            unique_results.append(result)
    
    # ترتيب النتائج حسب النقاط (الأعلى أولاً)
    unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return unique_results


def search_custom_api(product_name: str, countries: List[str], api_key: str = None) -> List[Dict]:
    """
    بحث مخصص - يمكن إضافة أي API هنا
    """
    results = []
    
    # مثال: البحث في API مخصص
    # يمكن استبدال هذا بـ API الحقيقي
    if api_key:
        try:
            # مثال على استخدام API
            # url = f"https://api.example.com/search"
            # params = {
            #     "product": product_name,
            #     "countries": ",".join(countries),
            #     "api_key": api_key
            # }
            # response = requests.get(url, params=params, timeout=10)
            # data = response.json()
            # results = parse_api_response(data)
            pass
        except Exception as e:
            print(f"خطأ في البحث عبر API: {e}")
    
    return results


def search_google_places(product_name: str, countries: List[str], api_key: str) -> List[Dict]:
    """
    البحث في Google Places API (مثال)
    """
    results = []
    
    if not api_key:
        return results
    
    try:
        # مثال على استخدام Google Places API
        # يمكن التعديل حسب الحاجة
        base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        
        for country in countries[:5]:  # حد أقصى 5 دول في كل مرة
            query = f"{product_name} buyers {country}"
            params = {
                "query": query,
                "key": api_key,
                "type": "establishment"
            }
            
            try:
                response = requests.get(base_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "OK":
                        for place in data.get("results", []):
                            results.append({
                                "company_name": place.get("name", ""),
                                "country": country,
                                "address": place.get("formatted_address", ""),
                                "website": place.get("website", ""),
                                "phone": place.get("formatted_phone_number", ""),
                                "source": "Google Places"
                            })
            except Exception as e:
                print(f"خطأ في البحث عن {country}: {e}")
                continue
                
    except Exception as e:
        print(f"خطأ في Google Places API: {e}")
    
    return results


def search_company_database(product_name: str, countries: List[str], api_key: str) -> List[Dict]:
    """
    البحث في قاعدة بيانات الشركات (مثال)
    """
    results = []
    
    # يمكن إضافة APIs أخرى مثل Clearbit, ZoomInfo, etc.
    # مثال:
    # if api_key:
    #     url = "https://api.clearbit.com/v2/companies/search"
    #     headers = {"Authorization": f"Bearer {api_key}"}
    #     params = {"query": f"{product_name} {countries[0]}"}
    #     response = requests.get(url, headers=headers, params=params)
    #     ...
    
    return results


def parse_api_response(data: Dict) -> List[Dict]:
    """
    تحليل استجابة API وتحويلها إلى تنسيق موحد
    """
    results = []
    
    # يمكن تخصيص هذا حسب تنسيق API
    if isinstance(data, list):
        for item in data:
            results.append({
                "company_name": item.get("name") or item.get("company_name", ""),
                "country": item.get("country", ""),
                "email": item.get("email", ""),
                "phone": item.get("phone", ""),
                "website": item.get("website", ""),
                "address": item.get("address", ""),
                "source": item.get("source", "API")
            })
    elif isinstance(data, dict):
        items = data.get("results") or data.get("data") or data.get("companies", [])
        for item in items:
            results.append({
                "company_name": item.get("name") or item.get("company_name", ""),
                "country": item.get("country", ""),
                "email": item.get("email", ""),
                "phone": item.get("phone", ""),
                "website": item.get("website", ""),
                "address": item.get("address", ""),
                "source": item.get("source", "API")
            })
    
    return results
