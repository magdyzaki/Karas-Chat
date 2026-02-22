"""
برنامج متخصص للبحث عن مستوردي البصل والكراث المجفف من مصر
Specialized Program for Finding Importers of Dried Onion and Leek from Egypt
"""
import requests
import json
import re
import time
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


# قائمة المنصات والبنوك التي يجب استبعادها تماماً
EXCLUDED_PLATFORMS = [
    # منصات B2B
    "alibaba", "indiamart", "tradeindia", "europages", "kompass",
    "thomasnet", "globalsources", "ec21", "ecplaza", "made-in-china",
    "dhgate", "1688", "tradekey", "go4worldbusiness", "b2bfreezone",
    "bizvibe", "exportersindia", "yellowpages", "mfg", "supplychainconnect",
    "panjiva", "importgenius", "volza", "bizdirlib", "companylist",
    
    # بنوك ومؤسسات مالية
    "bank", "banks", "banking", "financial", "finance", "investment",
    "credit", "loan", "mortgage", "insurance", "capital", "wealth",
    "chase", "bank of america", "wells fargo", "citibank", "hsbc",
    "barclays", "deutsche bank", "jpmorgan", "goldman sachs", "morgan stanley",
    
    # منصات أخرى
    "amazon", "ebay", "etsy", "walmart", "target", "linkedin.com/in",
    "facebook", "twitter", "instagram", "youtube", "wikipedia", "google"
]

# كلمات تشير إلى منصات وليست شركات
PLATFORM_KEYWORDS = [
    "platform", "marketplace", "directory", "portal", "hub", "network",
    "exchange", "trading platform", "b2b platform", "online marketplace"
]

# كلمات تشير إلى بنوك ومؤسسات مالية
BANK_KEYWORDS = [
    "bank", "banking", "financial", "finance", "investment", "credit",
    "loan", "mortgage", "insurance", "capital", "wealth management",
    "asset management", "private equity", "hedge fund"
]


def build_search_queries(product_name: str = "", country: str = "USA") -> List[str]:
    """
    بناء استعلامات البحث بناءً على المنتج والبلد
    
    Args:
        product_name: اسم المنتج (اختياري)
        country: اسم البلد (اختياري)
    
    Returns:
        قائمة من استعلامات البحث
    """
    queries = []
    
    # المنتجات الافتراضية إذا لم يتم تحديد منتج
    default_products = ["dehydrated onion", "dried onion", "dehydrated leek", "dried leek", 
                       "dehydrated spinach", "dried spinach", "dehydrated vegetables"]
    
    # إذا تم تحديد منتج، استخدمه فقط
    if product_name and product_name.strip():
        products = [product_name.strip()]
        # إضافة أشكال مختلفة من المنتج
        product_lower = product_name.lower()
        if "dehydrated" not in product_lower and "dried" not in product_lower:
            products.append(f"dehydrated {product_name.strip()}")
            products.append(f"dried {product_name.strip()}")
    else:
        products = default_products
    
    # تحديد البلد
    country_code = country
    if country == "All Countries":
        country_code = ""
    elif country == "United Kingdom":
        country_code = "UK"
    elif country == "South Korea":
        country_code = "Korea"
    
    # بناء الاستعلامات
    for product in products:
        if country_code:
            # استعلامات مع بلد محدد
            queries.append(f'{product} importer company {country_code} (inc OR llc OR ltd)')
            queries.append(f'{product} buyer company {country_code} (inc OR llc OR ltd)')
            queries.append(f'{product} distributor company {country_code} (inc OR llc OR ltd)')
            queries.append(f'companies import {product} from Egypt {country_code} (inc OR llc OR ltd)')
        else:
            # استعلامات عامة (جميع البلدان)
            queries.append(f'{product} importer company (inc OR llc OR ltd) -egypt -egyptian -china -chinese -india -indian')
            queries.append(f'{product} buyer company (inc OR llc OR ltd) -egypt -egyptian -china -chinese -india -indian')
            queries.append(f'companies import {product} from Egypt (inc OR llc OR ltd) -china -chinese -india -indian')
    
    # إزالة التكرارات
    queries = list(dict.fromkeys(queries))
    
    return queries


def is_real_company(company_name: str, website: str = "", snippet: str = "") -> bool:
    """
    التحقق من أن الاسم هو شركة حقيقية وليس منصة أو بنك أو شركة مصرية أو اسم منتج
    """
    if not company_name or len(company_name) < 5 or len(company_name) > 80:
        return False
    
    company_lower = company_name.lower()
    website_lower = website.lower() if website else ""
    snippet_lower = snippet.lower() if snippet else ""
    
    # 0. استبعاد الشركات المصرية والصينية والهندية (مهم جداً!)
    excluded_countries_keywords = {
        "egypt": ["egypt", "egyptian", "cairo", "alexandria", "giza"],
        "china": ["china", "chinese", "beijing", "shanghai", "guangzhou", "shenzhen"],
        "india": ["india", "indian", "mumbai", "delhi", "bangalore", "chennai"]
    }
    
    # استبعاد إذا كان الاسم يحتوي على أي من هذه الكلمات (ككلمات منفصلة)
    words = company_lower.split()
    for country, keywords in excluded_countries_keywords.items():
        # استبعاد إذا كانت الكلمة موجودة في اسم الشركة
        if any(keyword in words for keyword in keywords):
            return False
        # استبعاد إذا كان الموقع يحتوي على نطاق الدولة
        if f".{country}" in website_lower or f"{country}." in website_lower:
            return False
        # استبعاد إذا كان الموقع يحتوي على كلمات الدولة
        website_words = website_lower.replace('/', ' ').replace('.', ' ').split()
        if any(keyword in website_words for keyword in keywords):
            return False
    
    # 1. استبعاد أسماء المنتجات فقط (إذا كانت كل الكلمات منتجات)
    product_keywords = [
        # المنتجات الأساسية
        "onion", "onions", "leek", "leeks", "spinach", "garlic",
        # أشكال المنتجات
        "dehydrated", "dried", "freeze-dried", "freeze dried", "frozen",
        "flakes", "flake", "powder", "powdered", "granulated", "granules",
        "minced", "diced", "chopped", "sliced", "crispy", "organic",
        # أنواع المنتجات
        "vegetables", "vegetable", "spices", "spice", "herbs", "herb",
        "fruit", "fruits", "bulk", "pack", "packed", "oz", "ounce",
        # ألوان وصفات
        "white", "green", "yellow", "red", "spring", "fresh",
        "iqf", "individually quick frozen"
    ]
    company_indicators = ["inc", "llc", "ltd", "limited", "corp", "corporation", 
                        "company", "co", "group", "llp", "enterprises", "industries",
                        "foods", "food", "trading", "import", "export"]
    has_company_indicator = any(indicator in company_lower for indicator in company_indicators)
    
    # استبعاد فقط إذا كانت كل الكلمات تقريباً منتجات وليس هناك مؤشر شركة
    product_word_count = sum(1 for word in words if word in product_keywords)
    # تخفيف: استبعاد فقط إذا كانت 90%+ منتجات وليس هناك مؤشر شركة
    if len(words) > 0 and product_word_count >= len(words) * 0.9 and not has_company_indicator:
        return False
    
    # 2. استبعاد إذا كان اسم منصة
    if any(platform in company_lower for platform in EXCLUDED_PLATFORMS):
        return False
    
    if any(platform in website_lower for platform in EXCLUDED_PLATFORMS):
        return False
    
    # 3. استبعاد كلمات المنصات
    if any(keyword in company_lower for keyword in PLATFORM_KEYWORDS):
        return False
    
    # 4. استبعاد كلمات البنوك
    if any(keyword in company_lower for keyword in BANK_KEYWORDS):
        return False
    
    # 5. استبعاد أسماء البلدان (كأسماء شركات) - خاصة مصر والصين والهند
    excluded_country_names = ["egypt", "egyptian", "china", "chinese", "india", "indian"]
    if len(words) == 1 and words[0] in excluded_country_names:
        return False
    
    # 6. استبعاد العبارات العامة (لكن ليس كل شيء)
    generic_phrases = [
        "list of", "top ", "best ", "find ", "search", "directory",
        "click here", "read more", "learn more", "view all", "see all",
        "from china", "from chinese", "from egypt", "from egyptian",
        "from india", "from indian", "china manufacturers", "indian manufacturers",
        "egyptian manufacturers", "price 2025", "espaceagro"
    ]
    if any(phrase in company_lower for phrase in generic_phrases):
        return False
    
    # استبعاد إذا كان الاسم يبدأ بكلمات عامة فقط
    if company_lower.startswith(("importers", "buyers", "suppliers", "wholesale", "distributors")):
        if len(words) <= 3:  # عبارة قصيرة
            return False
    
    # 7. يجب أن يحتوي على حرف كبير واحد على الأقل (أو مؤشر شركة)
    if not any(c.isupper() for c in company_name[:15]) and not has_company_indicator:
        return False
    
    # 8. يجب أن يحتوي على حروف (ليس أرقام فقط)
    if not any(c.isalpha() for c in company_name):
        return False
    
    # 9. استبعاد الأسماء التي تبدو كعناوين صفحات
    if company_name.endswith(':') or company_name.endswith('...'):
        return False
    
    # 10. يجب أن يحتوي على كلمة حقيقية واحدة على الأقل (ليست عامة وليست منتج)
    generic_words = ["company", "corp", "inc", "ltd", "llc", "limited", "group"]
    has_real_word = False
    for word in words:
        word_lower = word.lower()
        # السماح بكلمات مثل "foods", "trading", "import", "export" ككلمات شركة
        business_words = ["foods", "food", "trading", "import", "export", "international", "global", 
                         "enterprises", "industries", "supply", "supplies", "distribution", "distributor"]
        # السماح بأي كلمة تبدأ بحرف كبير وطولها 3+ (اسم شركة محتمل)
        if (word_lower not in generic_words and 
            word_lower not in product_keywords and
            word_lower not in excluded_country_names and
            (word_lower in business_words or (len(word) >= 3 and word[0].isupper()))):
            has_real_word = True
            break
    
    # إذا لم يكن هناك كلمة حقيقية، لكن هناك مؤشر شركة، نسمح به
    if not has_real_word and has_company_indicator:
        has_real_word = True
    
    # تخفيف: السماح بأي اسم يحتوي على مؤشر شركة حتى لو لم يكن هناك كلمة حقيقية
    if not has_real_word and not has_company_indicator:
        return False
    
    # 11. استبعاد الأسماء التي تبدو كعناوين URLs
    if any(company_lower.startswith(prefix) for prefix in 
           ['http://', 'https://', 'www.']):
        return False
    
    # 12. استبعاد الأسماء التي تبدو كعبارات بحث (مثل "Import Export Onions")
    if "import export" in company_lower or "export import" in company_lower:
        # استبعاد فقط إذا كانت عبارة قصيرة وتحتوي على منتجات
        if len(words) <= 4 and any(word in product_keywords for word in words):
            return False
    
    return True


def search_dried_onion_leek_importers(api_key: str, max_results: int = 50, api_provider: str = "serpapi",
                                     product_name: str = "", country: str = "USA") -> List[Dict]:
    """
    البحث المتخصص عن مستوردي البصل والكراث والسبانخ المجفف من مصر
    
    Args:
        api_key: مفتاح API (SerpAPI أو Serper.dev)
        max_results: الحد الأقصى للنتائج
        api_provider: نوع API ("serpapi" أو "serper")
        product_name: اسم المنتج (اختياري)
        country: اسم البلد (اختياري)
    
    Returns:
        قائمة من الشركات المستوردة الحقيقية
    """
    if not api_key:
        return []
    
    api_key = api_key.strip()
    if api_key.startswith("serpapi-key "):
        api_key = api_key.replace("serpapi-key ", "").strip()
    if api_key.startswith("serper-key "):
        api_key = api_key.replace("serper-key ", "").strip()
    
    # تحديد نوع API
    api_provider_lower = api_provider.lower() if api_provider else "serper"
    if api_provider_lower == "serper" or "serper" in api_key.lower():
        try:
            return search_with_serper(api_key, max_results, product_name, country)
        except Exception as e:
            print(f"DEBUG: خطأ في Serper.dev: {e}")
            print(f"DEBUG: محاولة استخدام SerpAPI كبديل...")
            return search_with_serpapi(api_key, max_results, product_name, country)
    else:
        try:
            return search_with_serpapi(api_key, max_results, product_name, country)
        except Exception as e:
            print(f"DEBUG: خطأ في SerpAPI: {e}")
            return []


def search_with_serper(api_key: str, max_results: int = 50, product_name: str = "", country: str = "USA") -> List[Dict]:
    """البحث باستخدام Serper.dev API"""
    results = []
    seen_companies = set()
    
    # بناء الاستعلامات بناءً على المنتج والبلد
    queries = build_search_queries(product_name, country)
    
    base_url = "https://google.serper.dev/search"
    
    print(f"DEBUG: بدء البحث باستخدام Serper.dev - عدد الاستعلامات: {len(queries)}")
    
    for idx, query in enumerate(queries, 1):
        try:
            print(f"DEBUG: [{idx}/{len(queries)}] استعلام: {query[:60]}...")
            
            headers = {
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": 20,
                "gl": "us",
                "hl": "en"
            }
            
            response = requests.post(base_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 401:
                print(f"DEBUG: ⚠️ مفتاح API غير صحيح (401)")
                break
            
            if response.status_code != 200:
                print(f"DEBUG: خطأ في الاستجابة: {response.status_code}")
                continue
            
            try:
                data = response.json()
            except:
                print(f"DEBUG: خطأ في تحليل JSON")
                continue
            
            if "error" in data:
                print(f"DEBUG: خطأ من Serper.dev: {data.get('error')}")
                continue
            
            organic_results = data.get("organic", [])
            print(f"DEBUG: تم العثور على {len(organic_results)} نتيجة من Serper.dev")
            
            if len(organic_results) == 0:
                print(f"DEBUG: ⚠️ لا توجد نتائج من Serper.dev للاستعلام: {query[:50]}...")
                continue
            
            processed_count = 0
            for result in organic_results:
                try:
                    title = result.get("title", "").strip()
                    link = result.get("link", "")
                    snippet = result.get("snippet", "").strip()
                    
                    if not title or not link:
                        continue
                    
                    processed_count += 1
                    print(f"DEBUG: معالجة النتيجة [{processed_count}]: {title[:60]}...")
                    
                    # تنظيف اسم الشركة من العنوان
                    company_name = title
                    for sep in [" - ", " | ", " – ", ":", "::"]:
                        if sep in company_name:
                            company_name = company_name.split(sep)[0].strip()
                    
                    # التحقق من أن الاسم شركة حقيقية
                    if not is_real_company(company_name, link, snippet):
                        print(f"DEBUG: ✗ تم استبعاد: {company_name[:50]}...")
                        continue
                    
                    # إزالة التكرارات
                    company_lower = company_name.lower()
                    if company_lower in seen_companies:
                        continue
                    seen_companies.add(company_lower)
                    
                    # استخراج معلومات إضافية
                    email = extract_email(snippet)
                    phone = extract_phone(snippet)
                    country = extract_country(snippet)
                    
                    # استبعاد إذا كانت الدولة مصر أو الصين أو الهند
                    if country and country.lower() in ["egypt", "china", "india"]:
                        print(f"DEBUG: ✗ تم استبعاد شركة من {country}: {company_name}")
                        continue
                    
                    results.append({
                        "company_name": company_name,
                        "website": link,
                        "email": email,
                        "phone": phone,
                        "country": country or "Unknown",
                        "snippet": snippet[:200] if snippet else "",
                        "source": "Serper.dev"
                    })
                    
                    print(f"DEBUG: ✓ شركة حقيقية: {company_name} ({country or 'Unknown'})")
                    
                    # إيقاف إذا وصلنا للحد الأقصى
                    if len(results) >= max_results:
                        break
                
                except Exception as e:
                    print(f"DEBUG: خطأ في معالجة نتيجة: {e}")
                    continue
            
            # إيقاف إذا وصلنا للحد الأقصى
            if len(results) >= max_results:
                break
            
            time.sleep(0.3)  # Serper.dev أسرع، نحتاج delay أقل
        
        except Exception as e:
            print(f"DEBUG: خطأ في الاستعلام [{idx}]: {e}")
            continue
    
    print(f"DEBUG: إجمالي الشركات الحقيقية: {len(results)}")
    return results


def search_with_serpapi(api_key: str, max_results: int = 50, product_name: str = "", country: str = "USA") -> List[Dict]:
    """البحث باستخدام SerpAPI"""
    results = []
    seen_companies = set()
    
    # بناء الاستعلامات بناءً على المنتج والبلد
    queries = build_search_queries(product_name, country)
    
    base_url = "https://serpapi.com/search"
    
    print(f"DEBUG: بدء البحث المتخصص - عدد الاستعلامات: {len(queries)}")
    
    for idx, query in enumerate(queries, 1):
        try:
            print(f"DEBUG: [{idx}/{len(queries)}] استعلام: {query[:60]}...")
            
            params = {
                "q": query,
                "api_key": api_key,
                "engine": "google",
                "num": 20,
                "hl": "en",
                "gl": "us"
            }
            
            response = requests.get(base_url, params=params, timeout=30)
            
            if response.status_code == 401:
                print(f"DEBUG: ⚠️ مفتاح API غير صحيح (401)")
                break
            
            if response.status_code != 200:
                print(f"DEBUG: خطأ في الاستجابة: {response.status_code}")
                continue
            
            try:
                data = response.json()
            except:
                print(f"DEBUG: خطأ في تحليل JSON")
                continue
            
            if "error" in data:
                print(f"DEBUG: خطأ من SerpAPI: {data.get('error')}")
                continue
            
            organic_results = data.get("organic_results", [])
            print(f"DEBUG: تم العثور على {len(organic_results)} نتيجة من SerpAPI")
            
            if len(organic_results) == 0:
                print(f"DEBUG: ⚠️ لا توجد نتائج من SerpAPI للاستعلام: {query[:50]}...")
                continue
            
            processed_count = 0
            for result in organic_results:
                try:
                    title = result.get("title", "").strip()
                    link = result.get("link", "")
                    snippet = result.get("snippet", "").strip()
                    
                    if not title or not link:
                        continue
                    
                    processed_count += 1
                    print(f"DEBUG: معالجة النتيجة [{processed_count}]: {title[:60]}...")
                    
                    # تنظيف اسم الشركة من العنوان
                    company_name = title
                    for sep in [" - ", " | ", " – ", ":", "::"]:
                        if sep in company_name:
                            company_name = company_name.split(sep)[0].strip()
                    
                    # التحقق من أن الاسم شركة حقيقية
                    if not is_real_company(company_name, link, snippet):
                        print(f"DEBUG: ✗ تم استبعاد: {company_name[:50]}...")
                        continue
                    
                    # إزالة التكرارات
                    company_lower = company_name.lower()
                    if company_lower in seen_companies:
                        continue
                    seen_companies.add(company_lower)
                    
                    # استخراج معلومات إضافية
                    email = extract_email(snippet)
                    phone = extract_phone(snippet)
                    country = extract_country(snippet)
                    
                    # استبعاد إذا كانت الدولة مصر أو الصين أو الهند
                    if country and country.lower() in ["egypt", "china", "india"]:
                        print(f"DEBUG: ✗ تم استبعاد شركة من {country}: {company_name}")
                        continue
                    
                    results.append({
                        "company_name": company_name,
                        "website": link,
                        "email": email,
                        "phone": phone,
                        "country": country or "Unknown",
                        "snippet": snippet[:200] if snippet else "",
                        "source": "SerpAPI Specialized"
                    })
                    
                    print(f"DEBUG: ✓ شركة حقيقية: {company_name} ({country or 'Unknown'})")
                    
                    # إيقاف إذا وصلنا للحد الأقصى
                    if len(results) >= max_results:
                        break
                
                except Exception as e:
                    print(f"DEBUG: خطأ في معالجة نتيجة: {e}")
                    continue
            
            # إيقاف إذا وصلنا للحد الأقصى
            if len(results) >= max_results:
                break
            
            time.sleep(0.5)  # تجنب rate limiting
        
        except Exception as e:
            print(f"DEBUG: خطأ في الاستعلام [{idx}]: {e}")
            continue
    
    print(f"DEBUG: إجمالي الشركات الحقيقية: {len(results)}")
    return results


def extract_email(text: str) -> str:
    """استخراج البريد الإلكتروني من النص"""
    if not text:
        return ""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else ""


def extract_phone(text: str) -> str:
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


def extract_country(text: str) -> str:
    """استخراج اسم الدولة من النص - استبعاد مصر والصين والهند"""
    if not text:
        return ""
    
    text_lower = text.lower()
    
    # استبعاد مصر والصين والهند
    excluded_countries = ["egypt", "egyptian", "china", "chinese", "india", "indian"]
    if any(country in text_lower for country in excluded_countries):
        return ""  # لا نعيد دولة مستبعدة
    
    country_mappings = {
        "usa": "United States", "united states": "United States", "us": "United States",
        "uk": "United Kingdom", "united kingdom": "United Kingdom", "britain": "United Kingdom",
        "germany": "Germany", "france": "France", "italy": "Italy", "spain": "Spain",
        "netherlands": "Netherlands", "belgium": "Belgium", "switzerland": "Switzerland",
        "canada": "Canada", "australia": "Australia", "japan": "Japan",
        "south korea": "South Korea", "korea": "South Korea"
    }
    
    for key, value in country_mappings.items():
        if key in text_lower:
            return value
    
    return ""
