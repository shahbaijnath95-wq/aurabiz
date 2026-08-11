"""
Multi-Language Service — Hinglish, Hindi, English, Marathi, Gujarati, Bengali, Tamil, Telugu
Language detection + translation + locale-aware responses for WhatsApp bot.
"""

import re
from typing import Optional


# Language detection patterns — common words mapped to language codes
LANG_PATTERNS = {
    "hi": [
        r"\b(namaste|namaskar|kaise|hain|hai|kya|aap|tum|hum|main|mera|mere|mein|ko|ka|ki|ke|se|pe|"
        r"nahi|haan|ji|bilkul|zaroor|theek|accha|shukriya|samajh|madad|chahiye|batao|"
        r"karo|karna|ho|raha|rahe|hain|bhi|abhi|kal|aaj|wala|wali|bohot|bahut|thoda|zyada|"
        r"sab|kuch|koi|ye|wo|yahan|wahan|idhar|udhar|kab|kaise|kyun|matlab|yaar|dost|bhai|"
        r"behen|mataji|pitaji|uncle|aunty|didi|bhaiya)\b"
    ],
    "mr": [
        r"\b(namaskar|kaise|ahe|aahet|kay|tumhi|amhi|mazya|mhyat|la|che|chi|ni|nahi|hoi|"
        r"thik|chhan|dhanyavaad|madat|pahije|sanga|sangha|kara|karayla|hot|hoty|ahet|pan|"
        r"khup|thoda|jast|sagla|kahi|he|te|ikde|tikde|kadhi|kashi|kas|mhanje|barobar|"
        r"kiti|kitla|chha|aahe|karaycha|pahije|aara|ahe|ho|nahi|mi|tu|amhi|tumhi)\b"
    ],
    "gu": [
        r"\b(namaskar|kemcho|hoi|chhe|shu|tame|hu |maru|mari|ne|no|na|nathi|ha|"
        r"barabar|saru|dhanyavaad|maddat|joie|kaho|karo|karvu|hatu|hati|chhe|"
        r"khub|thodu|vadhare|badhu|kai|aa|te|ahyetya|tya|kyaare|kem|matlab)\b"
    ],
    "bn": [
        r"\b(namaskar|kemon|achen|ki|apni|amar|amake|te|tar|e|o|na|haan|"
        r"bhalo|dhonnobad|sahajjo|jonno|bollo|koro|korte|chilo|chilen|ache|"
        r"khub|ektu|beshi|shob|kono|eta|ota|ekhane|khane|kokhon|kivabe| mane)\b"
    ],
    "ta": [
        r"\b(vanakkam|epdi|irukkeenga|enna|neenga|naan|en|ukku|ukka|illai|"
        r"nandraam|nandri|udhavi|sollunga|panunga|panrathu|irundhadhu|irukkirathu|"
        r"romba|konjam|adhigam|ellam|ethu|adhu|ingu|angui|eppadi|epdi|avlo)\b"
    ],
    "te": [
        r"\b(namaskaram|ela|unnaru|enti|meeru|nenu|na|ku|ki|ledu|haa|"
        r"bagundi|dhanyavaadmadat|cheppandi|cheyandi|undedi|undi|"
        r"chala|koncham|ekkuva|anni|adi|idhi|ikada|akada|eppudu|ela|alage)\b"
    ],
    "en": [
        r"\b(hello|hi|hey|thanks|thank you|please|yes|no|okay|ok|good|great|"
        r"price|order|delivery|payment|help|support|product|available|"
        r"stock|service|how|what|when|where|why|can|could|would|should|"
        r"want|need|like|love|best|worst|very|much|really|sure|fine)\b"
    ],
}

# Romanized Hindi/Marathi/etc. detected as "hi" (default Indian business language)
DEFAULT_LANG = "hi"


def detect_language(text: str) -> str:
    """
    Detect language from text. Returns ISO 639-1 code.
    Works for Romanized Hindi, Marathi, Gujarati, etc.
    """
    if not text or not text.strip():
        return DEFAULT_LANG

    text_lower = text.lower().strip()
    scores = {}

    for lang, patterns in LANG_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            score += len(matches)
        scores[lang] = score

    if not scores or max(scores.values()) == 0:
        # No Indic-language keyword matched. If the text is predominantly
        # Latin script, treat it as English rather than defaulting to Hindi —
        # this keeps pure-English messages (e.g. "Do you have a mouse?") in English.
        latin = sum(1 for c in text if "a" <= c.lower() <= "z")
        if text.strip() and latin / len(text.strip()) > 0.6:
            return "en"
        return DEFAULT_LANG

    # Return language with highest score, default to hi for ties
    best_lang = max(scores, key=scores.get)
    if scores[best_lang] == 0:
        return DEFAULT_LANG

    return best_lang


# Translation mappings for common business phrases
TRANSLATIONS = {
    "hello": {
        "hi": "Namaste {name}! 🙏",
        "en": "Hello {name}!",
        "mr": "नमस्कार {name}! 🙏",
        "gu": "નમસ્કાર {name}! 🙏",
        "bn": "নমস্কার {name}! 🙏",
        "ta": "வணக்கம் {name}! 🙏",
        "te": "నమస్కారం {name}! 🙏",
    },
    "welcome": {
        "hi": "{business} mein aapka swagat hai! Hum kaise help kar sakte hain?",
        "en": "Welcome to {business}! How can we help you?",
        "mr": "{business} मध्ये आपले स्वागत आहे! आम्ही कशी मदत करू शकतो?",
        "gu": "{business} मा आपनुं स्वागत छे! अमे कई रीते मदत करी शकीએ?",
        "bn": "{business}-এ স্বাগতম! আমরা কিভাবে সাহায্য করতে পারি?",
        "ta": "{business}-க்கு வரவேற்கிறோம்! நாங்கள் எப்படி உதவ முடியும்?",
        "te": "{business}-కు స్వాగతం! మేము ఎలా సహాయం చేయగలం?",
    },
    "out_of_stock": {
        "hi": "{product} abhi out of stock hai 😔 Koi aur product dekhna ho toh batao!",
        "en": "{product} is currently out of stock 😔 Let me know if you'd like to see something else!",
        "mr": "{product} सध्या out of stock आहे 😔 काहीतरी वेगळं पाहायचं असल्यास सांगा!",
        "gu": "{product} હાલ out of stock છે 😔 બીજું કંઈ જોવું હોય તો કહો!",
        "bn": "{product} এখন স্টকে নেই 😔 অন্য কিছু দেখতে চাইলে জানাবেন!",
        "ta": "{product} தற்போது ஸ்டாக் இல்லை 😔 வேறு ஏதாவது பார்க்க விரும்பினால் சொல்லுங்கள்!",
        "te": "{product} ప్రస్తుతం స్టాక్ లేదు 😔 వేరేదైనా చూడాలనుకుంటే చెప్పండి!",
    },
    "in_stock": {
        "hi": "{product} hamare paas hai! 🎉\n💰 Price: ₹{price}\n📦 Stock: {stock} {unit} bache hain\n\nOrder karna ho toh batao!",
        "en": "{product} is available! 🎉\n💰 Price: ₹{price}\n📦 Stock: {stock} {unit} left\n\nLet me know if you'd like to order!",
        "mr": "{product} आमच्याकडे आहे! 🎉\n💰 किंमत: ₹{price}\n📦 स्टॉक: {stock} {unit} शेल्ल\n\nऑर्डर करायचं असल्यास सांगा!",
        "gu": "{product} अमारे पास छे! 🎉\n💰 भाव: ₹{price}\n📦 स्टॉक: {stock} {unit} बाकी\n\nऑर्डर करवुं होय तो कहो!",
        "bn": "{product} আমাদের কাছে আছে! 🎉\n💰 দাম: ₹{price}\n📦 স্টক: {stock} {unit} বাকি\n\nঅর্ডার করতে চাইলে জানাবেন!",
        "ta": "{product} எங்களிடம் உள்ளது! 🎉\n💰 விலை: ₹{price}\n📦 ஸ்டாக்: {stock} {unit} மீதம்\n\nஆர்டர் செய்ய விரும்பினால் சொல்லுங்கள்!",
        "te": "{product} మా వద్ద ఉంది! 🎉\n💰 ధర: ₹{price}\n📦 స్టాక్: {stock} {unit} మిగిలి ఉంది\n\nఆర్డర్ చేయాలనుకుంటే చెప్పండి!",
    },
    "how_much": {
        "hi": "{product} ki price ₹{price} hai! 💰",
        "en": "{product} costs ₹{price}! 💰",
        "mr": "{product} ची किंमत ₹{price} आहे! 💰",
        "gu": "{product} નો ભાવ ₹{price} છે! 💰",
        "bn": "{product}-এর দাম ₹{price}! 💰",
        "ta": "{product} விலை ₹{price}! 💰",
        "te": "{product} ధర ₹{price}! 💰",
    },
    "order_placed": {
        "hi": "Aapka order confirm ho gaya! 🎉\n📦 Order #{order_id}\n💰 Total: ₹{amount}\n\nPayment karne ke liye neeche click karo!",
        "en": "Your order is confirmed! 🎉\n📦 Order #{order_id}\n💰 Total: ₹{amount}\n\nClick below to pay!",
        "mr": "तुमचा order confirm झाला! 🎉\n📦 Order #{order_id}\n💰 एकूण: ₹{amount}\n\nPayment करायसाठी खाली click करा!",
        "gu": "तमारो order confirm थयो! 🎉\n📦 Order #{order_id}\n💰 कुल: ₹{amount}\n\nPayment करवा माटे खाले click करो!",
        "bn": "আপনার অর্ডার কনফার্ম হয়েছে! 🎉\n📦 Order #{order_id}\n💰 মোট: ₹{amount}\n\nপেমেন্ট করতে নিচে ক্লিক করুন!",
        "ta": "உங்கள் ஆர்டர் உறுதிசெய்யப்பட்டது! 🎉\n📦 Order #{order_id}\n💰 மொத்தம்: ₹{amount}\n\nபணம் செலுத்த கீழே கிளிக் செய்யுங்கள்!",
        "te": "మీ ఆర్డర్ కన్ఫర్మ్ అయింది! 🎉\n📦 Order #{order_id}\n💰 మొత్తం: ₹{amount}\n\nపేమెంట్ చేయడానికి కింద క్లిక్ చేయండి!",
    },
    "payment_pending": {
        "hi": "Aapka payment pending hai! 💰\nAmount: ₹{amount}\n\nUPI se aasani se pay kar sakte hain!",
        "en": "Your payment is pending! 💰\nAmount: ₹{amount}\n\nYou can easily pay via UPI!",
        "mr": "तुमचा payment pending आहे! 💰\nAmount: ₹{amount}\n\nUPI ने सहज payment करू शकता!",
        "gu": "तमारो payment pending छे! 💰\nAmount: ₹{amount}\n\nUPI थी सरलताथे pay करी शको!",
        "bn": "আপনার পেমেন্ট pending! 💰\nAmount: ₹{amount}\n\nUPI দিয়ে সহজেই পেমেন্ট করতে পারবেন!",
        "ta": "உங்கள் பேமெண்ட் pending! 💰\nAmount: ₹{amount}\n\nUPI மூலம் எளிதாக செலுத்தலாம்!",
        "te": "మీ పేమెంట్ pending! 💰\nAmount: ₹{amount}\n\nUPI ద్వారా సులభంగా చెల్లించవచ్చు!",
    },
    "thank_you": {
        "hi": "Shukriya {name}! 🙏 Aapka din shubh ho!",
        "en": "Thank you {name}! 🙏 Have a great day!",
        "mr": "धन्यवाद {name}! 🙏 तुमचा दिवस चांगला राहो!",
        "gu": "धन्यवाद {name}! 🙏 તમારો દિવસ સારો રહે!",
        "bn": "ধন্যবাদ {name}! 🙏 আপনার দিন শুভ হোক!",
        "ta": "நன்றி {name}! 🙏 உங்கள் நாள் நல்லதாக இருக்கட்டும்!",
        "te": "ధన్యవాదాలు {name}! 🙏 మీ రోజు మంచిగా ఉండాలి!",
    },
    "ask_catalog": {
        "hi": "Kya aapko hamare products dekhne hain? 🛍️ Bolo kya chahiye!",
        "en": "Would you like to see our products? 🛍️ Tell me what you need!",
        "mr": "तुम्हाला आमचे products पाहायचे आहेत? 🛍️ सांगा काय पाहिजे!",
        "gu": "તમને અમારા products જોવા છે? 🛍️ કહો શું જોઈએ!",
        "bn": "আপনি আমাদের পণ্য দেখতে চান? 🛍️ বলুন কী লাগবে!",
        "ta": "எங்கள் தயாரிப்புகளைப் பார்க்க விரும்புகிறீர்களா? 🛍️ என்ன வேண்டும் சொல்லுங்கள்!",
        "te": "మా ప్రోడక్ట్స్ చూడాలనుకుంటున్నారా? 🛍️ ఏమి కావాలో చెప్పండి!",
    },
    "track_order": {
        "hi": "Aapka order track karne ke liye order number batao! 📦",
        "en": "Please share your order number to track! 📦",
        "mr": "Order track करायसाठी order number सांगा! 📦",
        "gu": "Order track करवा order number कहो! 📦",
        "bn": "অর্ডার ট্র্যাক করতে অর্ডার নম্বর দিন! 📦",
        "ta": "ஆர்டரை ட்ராக் செய்ய ஆர்டர் எண்ணைச் சொல்லுங்கள்! 📦",
        "te": "ఆర్డర్ ట్రాక్ చేయడానికి ఆర్డర్ నంబర్ చెప్పండి! 📦",
    },
}


def translate(text: str, target_lang: str, **kwargs) -> str:
    """
    Translate common business phrases to target language.
    Falls back to Hinglish if translation not found.
    """
    if target_lang == "hi":
        return text  # Default is already Hinglish

    # Check if we have a translation for this key
    for key, translations in TRANSLATIONS.items():
        if target_lang in translations:
            # Simple template replacement
            translated = translations[target_lang]
            for k, v in kwargs.items():
                translated = translated.replace("{" + k + "}", str(v))
            return translated

    return text  # Fallback to original


def get_greeting(name: str, lang: str = "hi") -> str:
    """Get greeting in detected language."""
    template = TRANSLATIONS["hello"].get(lang, TRANSLATIONS["hello"]["hi"])
    return template.format(name=name)


def get_welcome(business_name: str, lang: str = "hi") -> str:
    """Get welcome message in detected language."""
    template = TRANSLATIONS["welcome"].get(lang, TRANSLATIONS["welcome"]["hi"])
    return template.format(business=business_name)


def get_stock_message(product_name: str, price: float, stock: int, unit: str, lang: str = "hi") -> str:
    """Get in-stock message in detected language."""
    template = TRANSLATIONS["in_stock"].get(lang, TRANSLATIONS["in_stock"]["hi"])
    return template.format(product=product_name, price=price, stock=stock, unit=unit)


def get_out_of_stock_message(product_name: str, lang: str = "hi") -> str:
    """Get out-of-stock message in detected language."""
    template = TRANSLATIONS["out_of_stock"].get(lang, TRANSLATIONS["out_of_stock"]["hi"])
    return template.format(product=product_name)


def get_price_message(product_name: str, price: float, lang: str = "hi") -> str:
    """Get price message in detected language."""
    template = TRANSLATIONS["how_much"].get(lang, TRANSLATIONS["how_much"]["hi"])
    return template.format(product=product_name, price=price)


def get_order_confirmation(order_id: str, amount: float, lang: str = "hi") -> str:
    """Get order confirmation in detected language."""
    template = TRANSLATIONS["order_placed"].get(lang, TRANSLATIONS["order_placed"]["hi"])
    return template.format(order_id=order_id, amount=amount)


def get_payment_pending(amount: float, lang: str = "hi") -> str:
    """Get payment pending in detected language."""
    template = TRANSLATIONS["payment_pending"].get(lang, TRANSLATIONS["payment_pending"]["hi"])
    return template.format(amount=amount)


def get_thank_you(name: str, lang: str = "hi") -> str:
    """Get thank you message in detected language."""
    template = TRANSLATIONS["thank_you"].get(lang, TRANSLATIONS["thank_you"]["hi"])
    return template.format(name=name)


def get_catalog_prompt(lang: str = "hi") -> str:
    """Get catalog browsing prompt in detected language."""
    return TRANSLATIONS["ask_catalog"].get(lang, TRANSLATIONS["ask_catalog"]["hi"])


def get_track_order_prompt(lang: str = "hi") -> str:
    """Get track order prompt in detected language."""
    return TRANSLATIONS["track_order"].get(lang, TRANSLATIONS["track_order"]["hi"])


def format_product_catalog(products: list, lang: str = "hi") -> str:
    """
    Format product list as a WhatsApp-friendly catalog message.
    """
    if not products:
        if lang == "en":
            return "Sorry, no products found! Try searching for something else."
        elif lang == "mr":
            return "माफ करा, कोणतेही products सापडले नाहीत! काहीतरी वेगळं शोधून पहा."
        elif lang == "gu":
            return "માફ કરો, કોઈ products મળ્યા નથી! બીજું કંઈ શોધો."
        elif lang == "bn":
            return "দুঃখিত, কোনো পণ্য পাওয়া যায়নি! অন্য কিছু খুঁজুন।"
        elif lang == "ta":
            return "மன்னிக்கவும், தயாரிப்புகள் எதுவும் இல்லை! வேறு ஏதாவது தேடுங்கள்."
        elif lang == "te":
            return "క్షమించండి, ప్రోడక్ట్స్ ఏవీ కనిపించలేదు! వేరేదైనా వెతకండి."
        return "Maaf kijiye, koi products nahi mile! Kuch aur dhoondh ke dekho."

    lines = ["*Hamare Products:* 🛍️\n"]
    for i, p in enumerate(products, 1):
        stock_status = "✅" if p.get("stock", 0) > 0 else "❌"
        price_str = f"₹{p['price']}"
        name = p.get("name", "Product")
        unit = p.get("unit", "pc")
        stock = p.get("stock", 0)
        cat = p.get("category", "")

        lines.append(f"{i}. {stock_status} *{name}* — {price_str}/{unit}")
        if cat:
            lines.append(f"   📂 {cat}")
        if stock > 0:
            lines.append(f"   📦 {stock} available")
        lines.append("")

    lines.append("Kya lena hai? Number ya naam batao! 🛒")
    return "\n".join(lines)


def format_product_card(product: dict, lang: str = "hi") -> str:
    """
    Format a single product as a detailed card with image URL support.
    Returns tuple: (text, image_url)
    """
    name = product.get("name", "Product")
    price = product.get("price", 0)
    stock = product.get("stock", 0)
    unit = product.get("unit", "pc")
    desc = product.get("description", "")
    category = product.get("category", "")
    image_url = product.get("image_url")
    specs = product.get("specs", {})
    brand = product.get("brand", "")

    lines = [f"*{name}*"]
    if brand:
        lines.append(f"🏷️ Brand: {brand}")
    lines.append(f"💰 Price: ₹{price}/{unit}")
    if desc:
        lines.append(f"\n{desc}")
    if category:
        lines.append(f"\n📂 Category: {category}")
    if specs:
        lines.append("\n📋 Specs:")
        for k, v in specs.items():
            lines.append(f"  • {k}: {v}")

    if stock > 0:
        lines.append(f"\n📦 Stock: {stock} {unit} available")
        lines.append("\nOrder karna ho toh number ya 'buy {name}' bolo! 🛒")
    else:
        lines.append("\n❌ Out of stock")

    return "\n".join(lines), image_url
