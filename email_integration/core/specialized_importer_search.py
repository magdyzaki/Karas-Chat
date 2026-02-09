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


def is_real_company(company_name: str, website: str = "", snippet: str = "") -> bool:
    """
    التحقق من أن الاسم هو شركة حقيقية وليس منصة أو بنك أو شركة مصرية أو اسم منتج
    """
    if not company_name or len(company_name) < 5 or len(company_name) > 80:
        return False
    
    company_lower = company_name.lower()
    website_lower = website.lower() if website else ""
    snippet_lower = snippet.lower() if snippet else ""
    
    # 0. استبعاد الشركات المصرية (مهم جداً!)
    egypt_keywords = ["egypt", "egyptian", "cairo", "alexandria", "giza"]
    # استبعاد فقط إذا كان الاسم يحتوي على مصر ككلمة كاملة (ليس جزء من كلمة أخرى)
    words = company_lower.split()
    if any(keyword in words for keyword in egypt_keywords):
        return False
    if any(keyword in website_lower.split('/') for keyword in egypt_keywords):
        return False
    
    # 1. استبعاد أسماء المنتجات فقط (إذا كانت كل الكلمات منتجات)
    product_keywords = [
        "onion", "leek", "garlic", "dehydrated", "dried", "freeze-dried",
        "flakes", "powder", "granulated", "minced", "crispy", "organic",
        "vegetables", "spices", "herbs", "fruit", "bulk", "pack", "oz",
        "white", "green", "spring", "iqf", "diced"
    ]
    company_indicators = ["inc", "llc", "ltd", "limited", "corp", "corporation", 
                        "company", "co", "group", "llp", "enterprises", "industries",
                        "foods", "food", "trading", "import", "export"]
    has_company_indicator = any(indicator in company_lower for indicator in company_indicators)
    
    # استبعاد فقط إذا كانت كل الكلمات تقريباً منتجات وليس هناك مؤشر شركة
    product_word_count = sum(1 for word in words if word in product_keywords)
    if len(words) > 0 and product_word_count >= len(words) * 0.8 and not has_company_indicator:
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
    
    # 5. استبعاد أسماء البلدان (كأسماء شركات)
    country_names = [
        "usa", "united states", "america", "us", "uk", "united kingdom",
        "germany", "france", "italy", "spain", "netherlands", "belgium",
        "egypt", "china", "india", "japan", "korea", "thailand", "vietnam"
    ]
    if len(words) == 1 and words[0] in country_names:
        return False
    
    # 6. استبعاد العبارات العامة (لكن ليس كل شيء)
    generic_phrases = [
        "list of", "top ", "best ", "find ", "search", "directory",
        "click here", "read more", "learn more", "view all", "see all",
        "from china manufacturers", "from egypt", "from india manufacturers",
        "price 2025", "espaceagro"
    ]
    if any(phrase in company_lower for phrase in generic_phrases):
        return False
    
    # استبعاد إذا كان الاسم يبدأ بكلمات عامة فقط
    if company_lower.startswith(("importers", "buyers", "suppliers", "wholesale", "distributors")):
        if len(words) <= 3:  # عبارة قصيرة
            return False
    
    # 7. يجب أن يحتوي على حرف كبير واحد على الأقل
    if not any(c.isupper() for c in company_name[:15]):
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
        business_words = ["foods", "food", "trading", "import", "export", "international", "global"]
        if (word_lower not in generic_words and 
            word_lower not in product_keywords and
            word_lower not in country_names and
            (word_lower in business_words or (len(word) >= 3 and word[0].isupper()))):
            has_real_word = True
            break
    
    if not has_real_word:
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


def search_dried_onion_leek_importers(api_key: str, max_results: int = 50) -> List[Dict]:
    """
    البحث المتخصص عن مستوردي البصل والكراث المجفف من مصر
    
    Args:
        api_key: مفتاح SerpAPI
        max_results: الحد الأقصى للنتائج
    
    Returns:
        قائمة من الشركات المستوردة الحقيقية
    """
    if not api_key:
        return []
    
    api_key = api_key.strip()
    if api_key.startswith("serpapi-key "):
        api_key = api_key.replace("serpapi-key ", "").strip()
    
    results = []
    seen_companies = set()
    
    # استعلامات بحث محددة - تركز على شركات أجنبية تستورد من مصر
    queries = [
        # استعلامات البصل المجفف - شركات أجنبية
        'dried onion importer USA company (inc OR llc OR ltd) -egypt -egyptian',
        'dried onion buyer USA company (inc OR llc OR ltd) -egypt -egyptian',
        'dried onion importer Europe company (inc OR ltd) -egypt -egyptian',
        'dried onion distributor company (inc OR llc OR ltd) -egypt -egyptian -china',
        
        # استعلامات الكراث المجفف - شركات أجنبية
        'dried leek importer USA company (inc OR llc OR ltd) -egypt -egyptian',
        'dried leek buyer USA company (inc OR llc OR ltd) -egypt -egyptian',
        'dried leek importer Europe company (inc OR ltd) -egypt -egyptian',
        
        # استعلامات عامة - شركات أجنبية
        'dehydrated vegetables importer USA company (inc OR llc OR ltd) -egypt -egyptian',
        'dehydrated vegetables buyer company (inc OR llc OR ltd) -egypt -egyptian -china',
        
        # استعلامات مع التركيز على الشركات الأجنبية التي تستورد من مصر
        'companies import dried onion from Egypt (inc OR llc OR ltd)',
        'companies import dried leek from Egypt (inc OR llc OR ltd)',
        'dried onion Egypt importer USA (inc OR llc OR ltd)',
        'dried leek Egypt importer USA (inc OR llc OR ltd)',
    ]
    
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
            
            for result in organic_results:
                try:
                    title = result.get("title", "").strip()
                    link = result.get("link", "")
                    snippet = result.get("snippet", "").strip()
                    
                    if not title or not link:
                        continue
                    
                    # تنظيف اسم الشركة من العنوان
                    company_name = title
                    for sep in [" - ", " | ", " – ", ":", "::"]:
                        if sep in company_name:
                            company_name = company_name.split(sep)[0].strip()
                    
                    # التحقق من أن الاسم شركة حقيقية
                    if not is_real_company(company_name, link, snippet):
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
                    
                    results.append({
                        "company_name": company_name,
                        "website": link,
                        "email": email,
                        "phone": phone,
                        "country": country or "Unknown",
                        "snippet": snippet[:200] if snippet else "",
                        "source": "SerpAPI Specialized"
                    })
                    
                    print(f"DEBUG: ✓ شركة حقيقية: {company_name}")
                    
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
    """استخراج اسم الدولة من النص"""
    if not text:
        return ""
    
    text_lower = text.lower()
    country_mappings = {
        "usa": "United States", "united states": "United States", "us": "United States",
        "uk": "United Kingdom", "united kingdom": "United Kingdom", "britain": "United Kingdom",
        "germany": "Germany", "france": "France", "italy": "Italy", "spain": "Spain",
        "netherlands": "Netherlands", "belgium": "Belgium", "switzerland": "Switzerland",
        "canada": "Canada", "australia": "Australia", "japan": "Japan", "china": "China",
        "india": "India", "south korea": "South Korea", "korea": "South Korea"
    }
    
    for key, value in country_mappings.items():
        if key in text_lower:
            return value
    
    return ""
