"""
Salon & Beauty Shop - 1000 Question Test Suite
Tests customer and shop owner interactions
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from services.free_ai import get_fallback_reply, detect_language

# Salon Inventory
SALON = [
    # Services - Hair
    {'name': 'Hair Cut', 'price': 200, 'stock': 20, 'unit': 'slots', 'category': 'Hair', 'item_type': 'service', 'duration_minutes': 30},
    {'name': 'Hair Color', 'price': 500, 'stock': 10, 'unit': 'slots', 'category': 'Hair', 'item_type': 'service', 'duration_minutes': 60},
    {'name': 'Hair Spa', 'price': 400, 'stock': 10, 'unit': 'slots', 'category': 'Hair', 'item_type': 'service', 'duration_minutes': 45},
    {'name': 'Hair Straightening', 'price': 1500, 'stock': 5, 'unit': 'slots', 'category': 'Hair', 'item_type': 'service', 'duration_minutes': 120},
    {'name': 'Hair Smoothing', 'price': 1200, 'stock': 5, 'unit': 'slots', 'category': 'Hair', 'item_type': 'service', 'duration_minutes': 90},
    {'name': 'Hair Highlights', 'price': 800, 'stock': 8, 'unit': 'slots', 'category': 'Hair', 'item_type': 'service', 'duration_minutes': 90},
    {'name': 'Keratin Treatment', 'price': 2000, 'stock': 5, 'unit': 'slots', 'category': 'Hair', 'item_type': 'service', 'duration_minutes': 120},
    {'name': 'Hair Wash', 'price': 100, 'stock': 20, 'unit': 'slots', 'category': 'Hair', 'item_type': 'service', 'duration_minutes': 15},
    {'name': 'Blow Dry', 'price': 150, 'stock': 15, 'unit': 'slots', 'category': 'Hair', 'item_type': 'service', 'duration_minutes': 20},
    {'name': 'Hair Oil Massage', 'price': 250, 'stock': 15, 'unit': 'slots', 'category': 'Hair', 'item_type': 'service', 'duration_minutes': 30},
    # Services - Skin
    {'name': 'Facial', 'price': 500, 'stock': 15, 'unit': 'slots', 'category': 'Skin', 'item_type': 'service', 'duration_minutes': 45},
    {'name': 'Gold Facial', 'price': 800, 'stock': 10, 'unit': 'slots', 'category': 'Skin', 'item_type': 'service', 'duration_minutes': 60},
    {'name': 'Diamond Facial', 'price': 1200, 'stock': 5, 'unit': 'slots', 'category': 'Skin', 'item_type': 'service', 'duration_minutes': 75},
    {'name': 'Clean Up', 'price': 300, 'stock': 15, 'unit': 'slots', 'category': 'Skin', 'item_type': 'service', 'duration_minutes': 30},
    {'name': 'Bleach', 'price': 250, 'stock': 15, 'unit': 'slots', 'category': 'Skin', 'item_type': 'service', 'duration_minutes': 30},
    {'name': 'Face Pack', 'price': 200, 'stock': 20, 'unit': 'slots', 'category': 'Skin', 'item_type': 'service', 'duration_minutes': 20},
    {'name': 'Skin Whitening', 'price': 600, 'stock': 10, 'unit': 'slots', 'category': 'Skin', 'item_type': 'service', 'duration_minutes': 45},
    {'name': 'Anti Aging Treatment', 'price': 1000, 'stock': 5, 'unit': 'slots', 'category': 'Skin', 'item_type': 'service', 'duration_minutes': 60},
    {'name': 'Acne Treatment', 'price': 400, 'stock': 10, 'unit': 'slots', 'category': 'Skin', 'item_type': 'service', 'duration_minutes': 30},
    {'name': 'Pigmentation Treatment', 'price': 500, 'stock': 8, 'unit': 'slots', 'category': 'Skin', 'item_type': 'service', 'duration_minutes': 45},
    # Services - Makeup
    {'name': 'Bridal Makeup', 'price': 5000, 'stock': 3, 'unit': 'slots', 'category': 'Makeup', 'item_type': 'service', 'duration_minutes': 120},
    {'name': 'Party Makeup', 'price': 2000, 'stock': 5, 'unit': 'slots', 'category': 'Makeup', 'item_type': 'service', 'duration_minutes': 60},
    {'name': 'Engagement Makeup', 'price': 3000, 'stock': 3, 'unit': 'slots', 'category': 'Makeup', 'item_type': 'service', 'duration_minutes': 90},
    {'name': 'Reception Makeup', 'price': 4000, 'stock': 3, 'unit': 'slots', 'category': 'Makeup', 'item_type': 'service', 'duration_minutes': 90},
    {'name': 'Sangeet Makeup', 'price': 2500, 'stock': 5, 'unit': 'slots', 'category': 'Makeup', 'item_type': 'service', 'duration_minutes': 75},
    {'name': 'Mehndi Makeup', 'price': 1500, 'stock': 5, 'unit': 'slots', 'category': 'Makeup', 'item_type': 'service', 'duration_minutes': 60},
    {'name': 'HD Makeup', 'price': 3500, 'stock': 3, 'unit': 'slots', 'category': 'Makeup', 'item_type': 'service', 'duration_minutes': 90},
    {'name': 'Airbrush Makeup', 'price': 4500, 'stock': 3, 'unit': 'slots', 'category': 'Makeup', 'item_type': 'service', 'duration_minutes': 90},
    # Services - Threading & Waxing
    {'name': 'Eyebrow Threading', 'price': 50, 'stock': 30, 'unit': 'slots', 'category': 'Threading', 'item_type': 'service', 'duration_minutes': 10},
    {'name': 'Upper Lip Threading', 'price': 30, 'stock': 30, 'unit': 'slots', 'category': 'Threading', 'item_type': 'service', 'duration_minutes': 5},
    {'name': 'Full Face Threading', 'price': 150, 'stock': 20, 'unit': 'slots', 'category': 'Threading', 'item_type': 'service', 'duration_minutes': 20},
    {'name': 'Full Arms Waxing', 'price': 300, 'stock': 15, 'unit': 'slots', 'category': 'Waxing', 'item_type': 'service', 'duration_minutes': 30},
    {'name': 'Full Legs Waxing', 'price': 400, 'stock': 15, 'unit': 'slots', 'category': 'Waxing', 'item_type': 'service', 'duration_minutes': 45},
    {'name': 'Full Body Waxing', 'price': 1000, 'stock': 10, 'unit': 'slots', 'category': 'Waxing', 'item_type': 'service', 'duration_minutes': 90},
    {'name': 'Under Arms Waxing', 'price': 100, 'stock': 20, 'unit': 'slots', 'category': 'Waxing', 'item_type': 'service', 'duration_minutes': 10},
    {'name': 'Bikini Waxing', 'price': 500, 'stock': 10, 'unit': 'slots', 'category': 'Waxing', 'item_type': 'service', 'duration_minutes': 30},
    # Services - Manicure & Pedicure
    {'name': 'Manicure', 'price': 200, 'stock': 15, 'unit': 'slots', 'category': 'Nails', 'item_type': 'service', 'duration_minutes': 30},
    {'name': 'Pedicure', 'price': 300, 'stock': 15, 'unit': 'slots', 'category': 'Nails', 'item_type': 'service', 'duration_minutes': 45},
    {'name': 'Nail Art', 'price': 400, 'stock': 10, 'unit': 'slots', 'category': 'Nails', 'item_type': 'service', 'duration_minutes': 45},
    {'name': 'Nail Extension', 'price': 600, 'stock': 8, 'unit': 'slots', 'category': 'Nails', 'item_type': 'service', 'duration_minutes': 60},
    {'name': 'Gel Nails', 'price': 500, 'stock': 8, 'unit': 'slots', 'category': 'Nails', 'item_type': 'service', 'duration_minutes': 45},
    {'name': 'Acrylic Nails', 'price': 700, 'stock': 5, 'unit': 'slots', 'category': 'Nails', 'item_type': 'service', 'duration_minutes': 60},
    # Services - Mehndi
    {'name': 'Bridal Mehndi', 'price': 1500, 'stock': 3, 'unit': 'slots', 'category': 'Mehndi', 'item_type': 'service', 'duration_minutes': 120},
    {'name': 'Simple Mehndi', 'price': 300, 'stock': 10, 'unit': 'slots', 'category': 'Mehndi', 'item_type': 'service', 'duration_minutes': 30},
    {'name': 'Arabic Mehndi', 'price': 500, 'stock': 8, 'unit': 'slots', 'category': 'Mehndi', 'item_type': 'service', 'duration_minutes': 45},
    {'name': 'Full Hand Mehndi', 'price': 800, 'stock': 5, 'unit': 'slots', 'category': 'Mehndi', 'item_type': 'service', 'duration_minutes': 60},
    # Products
    {'name': 'Shampoo', 'price': 150, 'stock': 30, 'unit': 'pcs', 'category': 'Hair Care', 'item_type': 'product'},
    {'name': 'Conditioner', 'price': 180, 'stock': 25, 'unit': 'pcs', 'category': 'Hair Care', 'item_type': 'product'},
    {'name': 'Hair Oil', 'price': 120, 'stock': 20, 'unit': 'bottles', 'category': 'Hair Care', 'item_type': 'product'},
    {'name': 'Hair Serum', 'price': 250, 'stock': 15, 'unit': 'pcs', 'category': 'Hair Care', 'item_type': 'product'},
    {'name': 'Face Wash', 'price': 100, 'stock': 25, 'unit': 'pcs', 'category': 'Skin Care', 'item_type': 'product'},
    {'name': 'Moisturizer', 'price': 200, 'stock': 20, 'unit': 'pcs', 'category': 'Skin Care', 'item_type': 'product'},
    {'name': 'Sunscreen', 'price': 250, 'stock': 15, 'unit': 'pcs', 'category': 'Skin Care', 'item_type': 'product'},
    {'name': 'Face Pack', 'price': 150, 'stock': 20, 'unit': 'pcs', 'category': 'Skin Care', 'item_type': 'product'},
    {'name': 'Nail Polish', 'price': 80, 'stock': 30, 'unit': 'pcs', 'category': 'Nails', 'item_type': 'product'},
    {'name': 'Nail Remover', 'price': 50, 'stock': 20, 'unit': 'pcs', 'category': 'Nails', 'item_type': 'product'},
    {'name': 'Mehndi Cone', 'price': 30, 'stock': 50, 'unit': 'pcs', 'category': 'Mehndi', 'item_type': 'product'},
    {'name': 'Hair Clip', 'price': 50, 'stock': 40, 'unit': 'pcs', 'category': 'Accessories', 'item_type': 'product'},
    {'name': 'Hair Band', 'price': 30, 'stock': 50, 'unit': 'pcs', 'category': 'Accessories', 'item_type': 'product'},
    {'name': 'Comb Set', 'price': 100, 'stock': 20, 'unit': 'sets', 'category': 'Accessories', 'item_type': 'product'},
    {'name': 'Scissors', 'price': 300, 'stock': 10, 'unit': 'pcs', 'category': 'Tools', 'item_type': 'product'},
]

# ======== 1000 TEST SCENARIOS ========
TESTS = {
    # ──────────────────────────────────────────────
    # 1. GREETINGS (30 tests)
    # ──────────────────────────────────────────────
    "GREETING": [
        ("Hello", "Priya"), ("Hi", "Rahul"), ("Hey", "Anita"), ("Namaste", "Priya"),
        ("Good morning", "Rahul"), ("Good evening", "Anita"), ("Good afternoon", "Priya"),
        ("hii", "Rahul"), ("hello didi", "Anita"), ("namaskar", "Priya"),
        ("helo", "Rahul"), ("hiii", "Anita"), ("gud morning", "Priya"),
        ("pranam", "Rahul"), ("ram ram", "Anita"), ("sat sri akal", "Priya"),
        ("jai hind", "Rahul"), ("kaise ho", "Anita"), ("kya haal hai", "Priya"),
        ("how are you", "Rahul"), ("what's up", "Anita"), ("yo", "Priya"),
        ("sup", "Rahul"), ("hola", "Anita"), ("bonjour", "Priya"),
        ("hi there", "Rahul"), ("hello ma'am", "Anita"), ("namaste ji", "Priya"),
        ("good night", "Rahul"), ("subah ho gayi", "Anita"),
    ],

    # ──────────────────────────────────────────────
    # 2. HAIR SERVICES (80 tests)
    # ──────────────────────────────────────────────
    "HAIR_SERVICES": [
        ("Hair cut karwana hai", "Priya"), ("Baalon ki cutting karwani hai", "Rahul"),
        ("Trimming karwani hai", "Anita"), ("Layer cut karwana hai", "Priya"),
        ("Step cut karwana hai", "Rahul"), ("Bob cut karwana hai", "Anita"),
        ("Pixie cut karwana hai", "Priya"), ("Undercut karwana hai", "Rahul"),
        ("Fade cut karwana hai", "Anita"), ("Buzz cut karwana hai", "Priya"),
        ("Hair color karwana hai", "Rahul"), ("Baalon ko rang karwana hai", "Anita"),
        ("Hair dye karwana hai", "Priya"), ("Black color karwana hai", "Rahul"),
        ("Brown color karwana hai", "Anita"), ("Red color karwana hai", "Priya"),
        ("Highlights karwane hain", "Rahul"), ("Streaks karwani hain", "Anita"),
        ("Balayage karwana hai", "Priya"), ("Ombre karwana hai", "Rahul"),
        ("Hair spa karwana hai", "Anita"), ("Spa treatment chahiye", "Priya"),
        ("Deep conditioning karwani hai", "Rahul"), ("Hair mask lagwana hai", "Anita"),
        ("Hair treatment karwana hai", "Priya"), ("Hair repair karwana hai", "Rahul"),
        ("Straightening karwani hai", "Anita"), ("Baalon ko straight karwana hai", "Priya"),
        ("Rebonding karwani hai", "Rahul"), ("Smoothing karwani hai", "Anita"),
        ("Keratin treatment karwana hai", "Priya"), ("Cysteine treatment karwana hai", "Rahul"),
        ("Hair wash karwana hai", "Anita"), ("Head wash karwana hai", "Priya"),
        ("Blow dry karwana hai", "Rahul"), ("Dryer se set karwana hai", "Anita"),
        ("Hair set karwana hai", "Priya"), ("Hair styling karwani hai", "Rahul"),
        ("Curling karwani hai", "Anita"), ("Ironing karwani hai", "Priya"),
        ("Hair oil massage karwani hai", "Rahul"), ("Champi karwani hai", "Anita"),
        ("Head massage karwani hai", "Priya"), ("Scalp treatment karwana hai", "Rahul"),
        ("Dandruff treatment karwana hai", "Anita"), ("Hair fall treatment karwana hai", "Priya"),
        ("Hair growth treatment karwana hai", "Rahul"), ("Baldness treatment hai?", "Anita"),
        ("Hair transplant karwate ho?", "Priya"), ("Wig milta hai?", "Rahul"),
        ("Hair extension karwana hai", "Anita"), ("Hair bonding karwana hai", "Priya"),
        ("Hair fixing karwana hai", "Rahul"), ("Patching karwana hai", "Anita"),
        ("Hair cutting ka rate kya hai?", "Priya"), ("Hair color ka price?", "Rahul"),
        ("Hair spa kitne ka hai?", "Anita"), ("Straightening ka charge?", "Priya"),
        ("Smoothing ka rate?", "Rahul"), ("Keratin ka price?", "Anita"),
        ("Blow dry ka charge?", "Priya"), ("Hair wash ka rate?", "Rahul"),
        ("Oil massage ka price?", "Anita"), ("Cutting mein kitna time lagega?", "Priya"),
        ("Color mein kitna time lagega?", "Rahul"), ("Spa mein kitna time lagega?", "Anita"),
        ("Straightening mein kitna time?", "Priya"), ("Keratin mein kitna time?", "Rahul"),
        ("Aaj slot hai hair cut ke liye?", "Anita"), ("Kal ka slot hai color ke liye?", "Priya"),
        ("Monday ko aa sakta hoon?", "Rahul"), ("Subah ka slot chahiye", "Anita"),
        ("Shaam ko aa sakta hoon?", "Priya"), ("Weekend pe aa sakta hoon?", "Rahul"),
        ("Baal bahut jhad rahe hain", "Anita"), ("Baal toot rahe hain", "Priya"),
        ("Baal sukh rahe hain", "Rahul"), ("Baal white ho rahe hain", "Anita"),
        ("Dandruff bahut hai", "Priya"), ("Scalp mein itching hai", "Rahul"),
        ("Baal dry ho gaye hain", "Anita"), ("Baal damage ho gaye hain", "Priya"),
        ("Baal bahut oily hain", "Rahul"), ("Baal bahut rough hain", "Anita"),
    ],

    # ──────────────────────────────────────────────
    # 3. SKIN SERVICES (60 tests)
    # ──────────────────────────────────────────────
    "SKIN_SERVICES": [
        ("Facial karwana hai", "Priya"), ("Gold facial karwana hai", "Rahul"),
        ("Diamond facial karwana hai", "Anita"), ("Pearl facial karwana hai", "Priya"),
        ("Fruit facial karwana hai", "Rahul"), ("Herbal facial karwana hai", "Anita"),
        ("Anti aging facial karwana hai", "Priya"), ("Whitening facial karwana hai", "Rahul"),
        ("Bleach karwani hai", "Anita"), ("Face bleach karwani hai", "Priya"),
        ("Full body bleach karwani hai", "Rahul"), ("Clean up karwana hai", "Anita"),
        ("Face clean up karwana hai", "Priya"), ("Deep clean up karwana hai", "Rahul"),
        ("Face pack lagwana hai", "Anita"), ("Multani mitti pack", "Priya"),
        ("Aloe vera pack", "Rahul"), ("Skin whitening treatment", "Anita"),
        ("Skin glow treatment", "Priya"), ("Skin tightening treatment", "Rahul"),
        ("Acne treatment karwana hai", "Anita"), ("Pimple treatment", "Priya"),
        ("Pigmentation treatment", "Rahul"), ("Dark circles treatment", "Anita"),
        ("Tan removal karwana hai", "Priya"), ("Sun tan hatana hai", "Rahul"),
        ("Scar removal treatment", "Anita"), ("Stretch marks treatment", "Priya"),
        ("Botox karwate ho?", "Rahul"), ("Fillers karwate ho?", "Anita"),
        ("Chemical peel karwate ho?", "Priya"), ("Microdermabrasion karwate ho?", "Rahul"),
        ("Laser treatment karwate ho?", "Anita"), ("PRP treatment karwate ho?", "Priya"),
        ("Facial ka rate kya hai?", "Rahul"), ("Gold facial ka price?", "Anita"),
        ("Diamond facial ka charge?", "Priya"), ("Bleach ka rate?", "Rahul"),
        ("Clean up ka price?", "Anita"), ("Face pack ka charge?", "Priya"),
        ("Facial mein kitna time lagega?", "Rahul"), ("Gold facial mein kitna time?", "Anita"),
        ("Aaj slot hai facial ke liye?", "Priya"), ("Kal facial karwa sakti hoon?", "Rahul"),
        ("Skin bahut dry hai", "Anita"), ("Skin oily hai", "Priya"),
        ("Skin pe dark spots hain", "Rahul"), ("Skin pe pimples hain", "Anita"),
        ("Skin dull hai", "Priya"), ("Skin pe wrinkles aa rahe hain", "Rahul"),
        ("Skin pe tan ho gaya hai", "Anita"), ("Skin pe redness hai", "Priya"),
        ("Skin pe allergy hai", "Rahul"), ("Skin pe itching hai", "Anita"),
        ("Skin pe rash hai", "Priya"), ("Skin pe eczema hai", "Rahul"),
        ("Skin pe psoriasis hai", "Anita"), ("Skin pe pigmentation hai", "Priya"),
        ("Skin pe freckles hain", "Rahul"), ("Skin pe moles hain", "Anita"),
    ],

    # ──────────────────────────────────────────────
    # 4. MAKEUP SERVICES (50 tests)
    # ──────────────────────────────────────────────
    "MAKEUP_SERVICES": [
        ("Bridal makeup karwana hai", "Priya"), ("Dulhan ka makeup chahiye", "Rahul"),
        ("Wedding makeup karwana hai", "Anita"), ("Shaadi ka makeup chahiye", "Priya"),
        ("Party makeup karwana hai", "Rahul"), ("Reception makeup chahiye", "Anita"),
        ("Engagement makeup chahiye", "Priya"), ("Sangeet makeup chahiye", "Rahul"),
        ("Mehndi makeup chahiye", "Anita"), ("Haldi makeup chahiye", "Priya"),
        ("HD makeup karwana hai", "Rahul"), ("Airbrush makeup chahiye", "Anita"),
        ("Matte makeup chahiye", "Priya"), ("Dewy makeup chahiye", "Rahul"),
        ("Natural makeup chahiye", "Anita"), ("Glam makeup chahiye", "Priya"),
        ("Smokey eyes karwane hain", "Rahul"), ("Eye makeup karwana hai", "Anita"),
        ("Lip makeup karwana hai", "Priya"), ("Contouring karwani hai", "Rahul"),
        ("Highlighting karwani hai", "Anita"), ("Blush lagwana hai", "Priya"),
        ("Foundation lagwana hai", "Rahul"), ("Concealer lagwana hai", "Anita"),
        ("Primer lagwana hai", "Priya"), ("Setting spray lagwana hai", "Rahul"),
        ("Makeup trial karwana hai", "Anita"), ("Demo makeup chahiye", "Priya"),
        ("Makeup ka rate kya hai?", "Rahul"), ("Bridal makeup ka price?", "Anita"),
        ("Party makeup ka charge?", "Priya"), ("HD makeup ka rate?", "Rahul"),
        ("Airbrush makeup ka price?", "Anita"), ("Makeup mein kitna time?", "Priya"),
        ("Bridal makeup mein kitna time?", "Rahul"), ("Party makeup mein kitna time?", "Anita"),
        ("Makeup kaun karega?", "Priya"), ("Senior artist chahiye", "Rahul"),
        ("Best artist kaun hai?", "Anita"), ("Portfolio dikhao", "Priya"),
        ("Previous work dikhao", "Rahul"), ("Reviews kya hain?", "Anita"),
        ("Makeup products kaunse hain?", "Priya"), ("MAC use karte ho?", "Rahul"),
        ("Huda Beauty use karte ho?", "Anita"), ("Charlotte Tilbury use karte ho?", "Priya"),
        ("Makeup trial free hai?", "Rahul"), ("Trial ke liye aa sakti hoon?", "Anita"),
        ("Makeup ghar pe kar doge?", "Priya"), ("Home service hai?", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 5. THREADING & WAXING (50 tests)
    # ──────────────────────────────────────────────
    "THREADING_WAXING": [
        ("Eyebrow karwani hai", "Priya"), ("Eyebrow threading karwani hai", "Rahul"),
        ("Upper lip karwani hai", "Anita"), ("Lower lip karwani hai", "Priya"),
        ("Full face threading karwani hai", "Rahul"), ("Chin threading karwani hai", "Anita"),
        ("Forehead threading karwani hai", "Priya"), ("Side locks karwani hain", "Rahul"),
        ("Threading ka rate kya hai?", "Anita"), ("Eyebrow ka price?", "Priya"),
        ("Upper lip ka charge?", "Rahul"), ("Full face ka rate?", "Anita"),
        ("Waxing karwani hai", "Priya"), ("Full arms waxing karwani hai", "Rahul"),
        ("Full legs waxing karwani hai", "Anita"), ("Under arms waxing", "Priya"),
        ("Full body waxing karwani hai", "Rahul"), ("Half arms waxing", "Anita"),
        ("Half legs waxing", "Priya"), ("Bikini waxing karwani hai", "Rahul"),
        ("Brazilian waxing karwani hai", "Anita"), ("Hot wax karwana hai", "Priya"),
        ("Cold wax karwana hai", "Rahul"), ("Rica wax karwana hai", "Anita"),
        ("Chocolate wax karwana hai", "Priya"), ("Fruit wax karwana hai", "Rahul"),
        ("Honey wax karwana hai", "Anita"), ("Waxing ka rate kya hai?", "Priya"),
        ("Full arms ka price?", "Rahul"), ("Full legs ka charge?", "Anita"),
        ("Full body ka rate?", "Priya"), ("Waxing mein kitna time?", "Rahul"),
        ("Waxing painful hai kya?", "Anita"), ("Waxing se allergy hoti hai?", "Priya"),
        ("Sensitive skin ke liye wax?", "Rahul"), ("Waxing ke baad kya karein?", "Anita"),
        ("Waxing ke baad redness hoti hai?", "Priya"), ("Waxing ke baad bumps aate hain?", "Rahul"),
        ("Waxing ke baad skin dry ho gayi", "Anita"), ("Waxing ke baad itching hoti hai", "Priya"),
        ("Aaj waxing karwa sakti hoon?", "Rahul"), ("Kal slot hai waxing ke liye?", "Anita"),
        ("Threading ya waxing, kya better hai?", "Priya"), ("Waxing se baal nahi aate?", "Rahul"),
        ("Waxing se baal patle hote hain?", "Anita"), ("Waxing kitne din chalti hai?", "Priya"),
        ("Waxing ke baad moisturizer lagana hai?", "Rahul"), ("Waxing ke baad sunscreen lagana hai?", "Anita"),
        ("Waxing ke baad scrub karna hai?", "Priya"), ("Waxing ke baad exfoliate karna hai?", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 6. MANICURE & PEDICURE (40 tests)
    # ──────────────────────────────────────────────
    "NAILS_SERVICES": [
        ("Manicure karwana hai", "Priya"), ("Pedicure karwana hai", "Rahul"),
        ("Nail art karwana hai", "Anita"), ("Nail extension karwani hai", "Priya"),
        ("Gel nails karwani hain", "Rahul"), ("Acrylic nails karwani hain", "Anita"),
        ("French nails karwani hain", "Priya"), ("Ombre nails karwani hain", "Rahul"),
        ("Chrome nails karwani hain", "Anita"), ("Glitter nails karwani hain", "Priya"),
        ("Matte nails karwani hain", "Rahul"), ("Metallic nails karwani hain", "Anita"),
        ("Nail polish lagwani hai", "Priya"), ("Nail paint lagwana hai", "Rahul"),
        ("Nail remover se utarna hai", "Anita"), ("Nail repair karwani hai", "Priya"),
        ("Nail cutting karwani hai", "Rahul"), ("Nail filing karwani hai", "Anita"),
        ("Cuticle treatment", "Priya"), ("Hand spa karwana hai", "Rahul"),
        ("Foot spa karwana hai", "Anita"), ("Hand massage karwana hai", "Priya"),
        ("Foot massage karwana hai", "Rahul"), ("Manicure ka rate kya hai?", "Anita"),
        ("Pedicure ka price?", "Priya"), ("Nail art ka charge?", "Rahul"),
        ("Nail extension ka rate?", "Anita"), ("Gel nails ka price?", "Priya"),
        ("Acrylic nails ka charge?", "Rahul"), ("Manicure mein kitna time?", "Anita"),
        ("Pedicure mein kitna time?", "Priya"), ("Nail art mein kitna time?", "Rahul"),
        ("Aaj slot hai manicure ke liye?", "Anita"), ("Kal pedicure karwa sakti hoon?", "Priya"),
        ("Nails bahut toot rahe hain", "Rahul"), ("Nails weak hain", "Anita"),
        ("Nails pe white spots hain", "Priya"), ("Nails yellow ho gaye hain", "Rahul"),
        ("Nails pe fungus hai", "Anita"), ("Nails ka shape kharab hai", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 7. MEHNDI SERVICES (30 tests)
    # ──────────────────────────────────────────────
    "MEHNDI_SERVICES": [
        ("Mehndi lagwani hai", "Priya"), ("Bridal mehndi lagwani hai", "Rahul"),
        ("Full hand mehndi lagwani hai", "Anita"), ("Arabic mehndi lagwani hai", "Priya"),
        ("Simple mehndi lagwani hai", "Rahul"), ("Indian mehndi lagwani hai", "Anita"),
        ("Indo-Arabic mehndi lagwani hai", "Priya"), ("Moroccan mehndi lagwani hai", "Rahul"),
        ("Western mehndi lagwani hai", "Anita"), ("Tattoo mehndi lagwani hai", "Priya"),
        ("Mehndi ka rate kya hai?", "Rahul"), ("Bridal mehndi ka price?", "Anita"),
        ("Simple mehndi ka charge?", "Priya"), ("Arabic mehndi ka rate?", "Rahul"),
        ("Full hand ka price?", "Anita"), ("Mehndi mein kitna time?", "Priya"),
        ("Bridal mehndi mein kitna time?", "Rahul"), ("Mehndi ka design dikhao", "Anita"),
        ("Catalog dikhao", "Priya"), ("Latest design dikhao", "Rahul"),
        ("Mehndi ka color dark aata hai?", "Anita"), ("Mehndi kitne din rehti hai?", "Priya"),
        ("Mehndi ka cone milta hai?", "Rahul"), ("Mehndi ka paste milta hai?", "Anita"),
        ("Aaj mehndi lagwa sakti hoon?", "Priya"), ("Kal slot hai mehndi ke liye?", "Rahul"),
        ("Mehndi bahut light aa rahi hai", "Anita"), ("Mehndi ka color nahi aa raha", "Priya"),
        ("Mehndi jhad rahi hai", "Rahul"), ("Mehndi ka design kharab ho gaya", "Anita"),
    ],

    # ──────────────────────────────────────────────
    # 8. PRODUCT QUERIES (60 tests)
    # ──────────────────────────────────────────────
    "PRODUCT_QUERIES": [
        ("Shampoo hai kya?", "Priya"), ("Shampoo chahiye", "Rahul"),
        ("Conditioner hai?", "Anita"), ("Conditioner chahiye", "Priya"),
        ("Hair oil hai?", "Rahul"), ("Hair oil chahiye", "Anita"),
        ("Hair serum hai?", "Priya"), ("Hair serum chahiye", "Rahul"),
        ("Face wash hai?", "Anita"), ("Face wash chahiye", "Priya"),
        ("Moisturizer hai?", "Rahul"), ("Moisturizer chahiye", "Anita"),
        ("Sunscreen hai?", "Priya"), ("Sunscreen chahiye", "Rahul"),
        ("Face pack hai?", "Anita"), ("Face pack chahiye", "Priya"),
        ("Nail polish hai?", "Rahul"), ("Nail polish chahiye", "Anita"),
        ("Nail remover hai?", "Priya"), ("Nail remover chahiye", "Rahul"),
        ("Mehndi cone hai?", "Anita"), ("Mehndi cone chahiye", "Priya"),
        ("Hair clip hai?", "Rahul"), ("Hair clip chahiye", "Anita"),
        ("Hair band hai?", "Priya"), ("Hair band chahiye", "Rahul"),
        ("Comb set hai?", "Anita"), ("Comb set chahiye", "Priya"),
        ("Scissors hai?", "Rahul"), ("Scissors chahiye", "Anita"),
        ("Shampoo ka price?", "Priya"), ("Conditioner ka rate?", "Rahul"),
        ("Hair oil ka cost?", "Anita"), ("Hair serum ka price?", "Priya"),
        ("Face wash ka rate?", "Rahul"), ("Moisturizer ka price?", "Anita"),
        ("Sunscreen ka cost?", "Priya"), ("Face pack ka rate?", "Rahul"),
        ("Nail polish ka price?", "Anita"), ("Mehndi cone ka rate?", "Priya"),
        ("Hair clip ka price?", "Rahul"), ("Hair band ka cost?", "Anita"),
        ("Comb set ka rate?", "Priya"), ("Scissors ka price?", "Rahul"),
        ("Shampoo available hai?", "Anita"), ("Conditioner stock mein hai?", "Priya"),
        ("Hair oil milega?", "Rahul"), ("Face wash mil jayega?", "Anita"),
        ("Sunscreen hai kya aapke paas?", "Priya"), ("Nail polish hai kya?", "Rahul"),
        ("Mehndi cone milega?", "Anita"), ("Hair clip milega?", "Priya"),
        ("Best shampoo kaunsa hai?", "Rahul"), ("Best conditioner kaunsa hai?", "Anita"),
        ("Best hair oil kaunsa hai?", "Priya"), ("Best face wash kaunsa hai?", "Rahul"),
        ("Best moisturizer kaunsa hai?", "Anita"), ("Best sunscreen kaunsa hai?", "Priya"),
        ("2 shampoo chahiye", "Rahul"), ("3 conditioner chahiye", "Anita"),
        ("5 mehndi cone chahiye", "Priya"), ("10 hair clip chahiye", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 9. PRICING QUERIES (40 tests)
    # ──────────────────────────────────────────────
    "PRICING_QUERIES": [
        ("Hair cut ka kitna charge hai?", "Priya"), ("Facial ka rate?", "Rahul"),
        ("Bridal makeup ka price?", "Anita"), ("Waxing ka charge?", "Priya"),
        ("Manicure ka rate?", "Rahul"), ("Pedicure ka price?", "Anita"),
        ("Mehndi ka charge?", "Priya"), ("Threading ka rate?", "Rahul"),
        ("Hair color ka price?", "Anita"), ("Hair spa ka charge?", "Priya"),
        ("Straightening ka rate?", "Rahul"), ("Smoothing ka price?", "Anita"),
        ("Keratin ka charge?", "Priya"), ("Bleach ka rate?", "Rahul"),
        ("Clean up ka price?", "Anita"), ("Nail art ka charge?", "Priya"),
        ("Kitna lagega total?", "Rahul"), ("Total kitna hoga?", "Anita"),
        ("Price kitna hai?", "Priya"), ("Rate kya hai?", "Rahul"),
        ("Cost kitna aayega?", "Anita"), ("Charge kitna hai?", "Priya"),
        ("Kitne paise lagenge?", "Rahul"), ("Kitna kharcha hoga?", "Anita"),
        ("Sasta hoga kya?", "Priya"), ("Discount milega kya?", "Rahul"),
        ("Package deal hai?", "Anita"), ("Combo offer hai?", "Priya"),
        ("Membership hai?", "Rahul"), ("Loyalty program hai?", "Anita"),
        ("Regular customer discount?", "Priya"), ("First time discount?", "Rahul"),
        ("Student discount?", "Anita"), ("Senior citizen discount?", "Priya"),
        ("Group discount?", "Rahul"), ("Bulk booking discount?", "Anita"),
        ("Festival offer hai?", "Priya"), ("Seasonal offer hai?", "Rahul"),
        ("Sale chal rahi hai?", "Anita"), ("Special offer hai?", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 10. BOOKING/APPOINTMENT (50 tests)
    # ──────────────────────────────────────────────
    "BOOKING_QUERIES": [
        ("Hair cut book karna hai", "Priya"), ("Facial ke liye appointment chahiye", "Rahul"),
        ("Bridal makeup book karna hai", "Anita"), ("Kal ka slot hai?", "Priya"),
        ("Monday ko aa sakti hoon?", "Rahul"), ("Subah ka slot chahiye", "Anita"),
        ("Shaam ko aa sakti hoon?", "Priya"), ("Timing kya hai?", "Rahul"),
        ("Kab aa sakti hoon?", "Anita"), ("Aaj ka slot hai?", "Priya"),
        ("Tuesday 2pm ko", "Rahul"), ("Wednesday subah 10 baje", "Anita"),
        ("Thursday shaam 5 baje", "Priya"), ("Friday ko 3 baje", "Rahul"),
        ("Saturday ko subah", "Anita"), ("Sunday ko bhi khula hai?", "Priya"),
        ("Weekend pe aa sakti hoon?", "Rahul"), ("Hair cut ke liye kab aaun?", "Anita"),
        ("Facial ka time kitna lagega?", "Priya"), ("Makeup mein kitna time?", "Rahul"),
        ("Aaj hi ho jayega?", "Anita"), ("Emergency hai", "Priya"),
        ("Jaldi se jaldi chahiye", "Rahul"), ("2 din mein ho jayega?", "Anita"),
        ("1 hafte mein ho jayega?", "Priya"), ("Subah 9 baje aa sakti hoon?", "Rahul"),
        ("Shaam 6 baje aa sakti hoon?", "Anita"), ("Dopahar ko aa sakti hoon?", "Priya"),
        ("Raat ko bhi khula hai?", "Rahul"), ("Holiday pe khula hai?", "Anita"),
        ("Sunday ko band hai?", "Priya"), ("Monday ko band hai?", "Rahul"),
        ("Slot book karna hai", "Anita"), ("Appointment lena hai", "Priya"),
        ("Walk-in aa sakti hoon?", "Rahul"), ("Online booking hai?", "Anita"),
        ("Phone pe booking hogi?", "Priya"), ("WhatsApp pe booking hogi?", "Rahul"),
        ("Kitne baje aana hai?", "Anita"), ("Time batao", "Priya"),
        ("Schedule kya hai?", "Rahul"), ("Open kab hota hai?", "Anita"),
        ("Band kab hota hai?", "Priya"), ("Lunch time kya hai?", "Rahul"),
        ("Last client kab tak?", "Anita"), ("Early morning slot hai?", "Priya"),
        ("Late night slot hai?", "Rahul"), ("Flexible timing hai?", "Anita"),
        ("Same day booking hogi?", "Priya"), ("Advance booking karni padegi?", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 11. ORDER/DELIVERY (40 tests)
    # ──────────────────────────────────────────────
    "ORDER_DELIVERY": [
        ("Shampoo order karna hai", "Priya"), ("Conditioner chahiye 2 piece", "Rahul"),
        ("Hair oil order karna hai", "Anita"), ("Face wash chahiye 1 piece", "Priya"),
        ("Order kaise karun?", "Rahul"), ("Delivery hogi kya?", "Anita"),
        ("Ghar pe delivery ho jayegi?", "Priya"), ("Store se pickup kar sakti hoon?", "Rahul"),
        ("Delivery charge kitna hai?", "Anita"), ("Free delivery hai?", "Priya"),
        ("Kitne din mein delivery hogi?", "Rahul"), ("Same day delivery hai?", "Anita"),
        ("Order track kaise karun?", "Priya"), ("Mera order kab aayega?", "Rahul"),
        ("Order cancel karna hai", "Anita"), ("Order return karna hai", "Priya"),
        ("Exchange ho jayega?", "Rahul"), ("2 shampoo chahiye", "Anita"),
        ("3 conditioner chahiye", "Priya"), ("5 mehndi cone chahiye", "Rahul"),
        ("Bulk order karna hai", "Anita"), ("Wholesale milega?", "Priya"),
        ("Delivery address dena hai", "Rahul"), ("Address change karna hai", "Anita"),
        ("Order modify karna hai", "Priya"), ("Quantity badhani hai", "Rahul"),
        ("Order confirm ho gaya?", "Anita"), ("Order processing hai?", "Priya"),
        ("Order shipped ho gaya?", "Rahul"), ("Order delivered ho gaya?", "Anita"),
        ("Order ID kya hai?", "Priya"), ("Tracking number kya hai?", "Rahul"),
        ("Delivery boy ka number?", "Anita"), ("Delivery time kya hai?", "Priya"),
        ("Morning delivery hogi?", "Rahul"), ("Evening delivery hogi?", "Anita"),
        ("COD available hai?", "Priya"), ("Prepaid order karna hai", "Rahul"),
        ("Gift wrap kar doge?", "Anita"), ("Packing achhi hogi?", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 12. PAYMENT (30 tests)
    # ──────────────────────────────────────────────
    "PAYMENT_QUERIES": [
        ("Payment kaise karun?", "Priya"), ("UPI se payment ho jayegi?", "Rahul"),
        ("Cash de sakti hoon?", "Anita"), ("Card se payment ho jayegi?", "Priya"),
        ("PhonePe se pay kar sakti hoon?", "Rahul"), ("Google Pay chalega?", "Anita"),
        ("Paytm se payment?", "Priya"), ("EMI available hai?", "Rahul"),
        ("Installment mein payment?", "Anita"), ("Advance dena padega?", "Priya"),
        ("Kitna advance dena hoga?", "Rahul"), ("Baad mein payment kar sakti hoon?", "Anita"),
        ("Bill dena", "Priya"), ("Invoice chahiye", "Rahul"), ("Receipt dena", "Anita"),
        ("GST bill milega?", "Priya"), ("GST number kya hai?", "Rahul"),
        ("Payment link bhejo", "Anita"), ("QR code bhejo", "Priya"),
        ("UPI ID kya hai?", "Rahul"), ("Payment secure hai?", "Anita"),
        ("Payment refund kab milega?", "Priya"), ("Payment failed ho gaya", "Rahul"),
        ("Payment pending hai", "Anita"), ("Payment confirmed hai?", "Priya"),
        ("Payment receipt bhejo", "Rahul"), ("Payment history dekhni hai", "Anita"),
        ("Payment due hai?", "Priya"), ("Payment extension milegi?", "Rahul"),
        ("Payment plan hai?", "Anita"),
    ],

    # ──────────────────────────────────────────────
    # 13. WARRANTY/GUARANTEE (20 tests)
    # ──────────────────────────────────────────────
    "WARRANTY_QUERIES": [
        ("Warranty hai kya?", "Priya"), ("Guarantee kitne din ki hai?", "Rahul"),
        ("Service pe warranty milegi?", "Anita"), ("Product pe warranty hai?", "Priya"),
        ("Warranty card milega?", "Rahul"), ("Warranty claim kaise karun?", "Anita"),
        ("Warranty expire ho gayi", "Priya"), ("Extended warranty hai?", "Rahul"),
        ("Warranty mein free service hogi?", "Anita"), ("Warranty terms kya hain?", "Priya"),
        ("Warranty register kaise karun?", "Rahul"), ("Warranty check kaise karun?", "Anita"),
        ("Warranty number kya hai?", "Priya"), ("Warranty center kahan hai?", "Rahul"),
        ("Warranty mein replacement hoga?", "Anita"), ("Warranty mein refund hoga?", "Priya"),
        ("Warranty transfer ho sakti hai?", "Rahul"), ("Warranty online check hogi?", "Anita"),
        ("Warranty document chahiye", "Priya"), ("Warranty policy kya hai?", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 14. STATUS/TRACKING (20 tests)
    # ──────────────────────────────────────────────
    "STATUS_QUERIES": [
        ("Mera facial ho gaya?", "Priya"), ("Makeup kab hoga?", "Rahul"),
        ("Service ka status kya hai?", "Anita"), ("Mehndi lag gayi?", "Priya"),
        ("Nails ho gaye?", "Rahul"), ("Status check karna hai", "Anita"),
        ("Kaam ho gaya kya?", "Priya"), ("Kab tak hoga?", "Rahul"),
        ("Aaj hoga kya?", "Anita"), ("Kal hoga kya?", "Priya"),
        ("2 din ho gaye", "Rahul"), ("1 hafte ho gaya", "Anita"),
        ("Jaldi karo na", "Priya"), ("Kitna time aur lagega?", "Rahul"),
        ("Progress kya hai?", "Anita"), ("Update do", "Priya"),
        ("Status batao", "Rahul"), ("Kaam chal raha hai?", "Anita"),
        ("Kaam start hua?", "Priya"), ("Kaam complete hua?", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 15. COMPLAINT/REFUND (25 tests)
    # ──────────────────────────────────────────────
    "COMPLAINT_REFUND": [
        ("Service achhi nahi thi", "Priya"), ("Makeup kharab ho gaya", "Rahul"),
        ("Facial se allergy ho gayi", "Anita"), ("Waxing se jalan ho rahi hai", "Priya"),
        ("Hair cut galat ho gaya", "Rahul"), ("Color galat aa gaya", "Anita"),
        ("Complaint karna hai", "Priya"), ("Manager se baat karni hai", "Rahul"),
        ("Refund chahiye", "Anita"), ("Paise wapas chahiye", "Priya"),
        ("Consumer court mein jaungi", "Rahul"), ("Social media pe daalungi", "Anita"),
        ("Review likhna hai", "Priya"), ("1 star dungi", "Rahul"),
        ("Service kharab hai", "Anita"), ("Staff achha nahi tha", "Priya"),
        ("Product duplicate lagaya", "Rahul"), ("Original product nahi lagaya", "Anita"),
        ("Charge zyada liya", "Priya"), ("Overcharge kiya", "Rahul"),
        ("Time pe nahi hua", "Anita"), ("Deadline miss ho gayi", "Priya"),
        ("Promise nahi nibhaya", "Rahul"), ("Guarantee nahi mili", "Anita"),
        ("Warranty nahi mili", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 16. NON-BUSINESS (20 tests)
    # ──────────────────────────────────────────────
    "NON_BUSINESS": [
        ("Joke sunao", "Priya"), ("Gaana gao", "Rahul"), ("Mausam kaisa hai?", "Anita"),
        ("Cricket score kya hai?", "Priya"), ("News kya hai?", "Rahul"),
        ("Translate karo", "Anita"), ("Shayari sunao", "Priya"), ("Kahani sunao", "Rahul"),
        ("Movie recommend karo", "Anita"), ("Game khelte ho?", "Priya"),
        ("Instagram pe ho?", "Rahul"), ("Facebook pe ho?", "Anita"),
        ("Twitter pe ho?", "Priya"), ("YouTube channel hai?", "Rahul"),
        ("TikTok pe ho?", "Anita"), ("Snapchat pe ho?", "Priya"),
        ("WhatsApp pe ho?", "Rahul"), ("Telegram pe ho?", "Anita"),
        ("Dating app use karte ho?", "Priya"), ("Relationship advice do", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 17. THANKS (15 tests)
    # ──────────────────────────────────────────────
    "THANKS": [
        ("Thank you", "Priya"), ("Shukriya", "Rahul"), ("Thanks didi", "Anita"),
        ("Dhanyavaad", "Priya"), ("Bahut shukriya", "Rahul"), ("Thanks a lot", "Anita"),
        ("Thank you so much", "Priya"), ("Bohot bohot shukriya", "Rahul"),
        ("Thanks ji", "Anita"), ("Thank you ma'am", "Priya"),
        ("Thanks for help", "Rahul"), ("Thanks for service", "Anita"),
        ("Appreciate it", "Priya"), ("Great service", "Rahul"),
        ("Bahut achha kaam kiya", "Anita"),
    ],

    # ──────────────────────────────────────────────
    # 18. EDGE CASES (30 tests)
    # ──────────────────────────────────────────────
    "EDGE_CASES": [
        ("?", "Priya"), ("kya", "Rahul"), ("hai", "Anita"), ("hello", "Priya"),
        ("ok", "Rahul"), ("hmm", "Anita"), ("theek hai", "Priya"), ("achha", "Rahul"),
        ("haan", "Anita"), ("nahi", "Priya"), ("bye", "Rahul"), ("good night", "Anita"),
        ("tata", "Priya"), ("chal bye", "Rahul"), ("ok bye", "Anita"),
        ("...", "Priya"), ("??? ", "Rahul"), ("!!!", "Anita"), ("huh", "Priya"),
        ("what", "Rahul"), ("why", "Anita"), ("how", "Priya"), ("when", "Rahul"),
        ("where", "Anita"), ("who", "Priya"), ("which", "Rahul"), ("ok ok", "Anita"),
        ("hmm hmm", "Priya"), ("achha achha", "Rahul"), ("haan haan", "Anita"),
    ],

    # ──────────────────────────────────────────────
    # 19. MULTI-LANGUAGE (60 tests)
    # ──────────────────────────────────────────────
    "MULTI_LANGUAGE": [
        # Hindi
        ("Mujhe facial karwana hai", "Priya"), ("Hair cut ka rate kya hai?", "Rahul"),
        ("Bridal makeup book karna hai", "Anita"), ("Waxing karwani hai", "Priya"),
        ("Threading karwani hai", "Rahul"), ("Manicure karwana hai", "Anita"),
        ("Pedicure karwana hai", "Priya"), ("Nail art karwana hai", "Rahul"),
        ("Mehndi lagwani hai", "Anita"), ("Shampoo chahiye", "Priya"),
        # English
        ("I want facial", "Sarah"), ("What is the price of hair cut?", "Mike"),
        ("I want to book bridal makeup", "Sarah"), ("I need waxing", "Mike"),
        ("I want threading", "Sarah"), ("Manicure please", "Mike"),
        ("Pedicure please", "Sarah"), ("I want nail art", "Mike"),
        ("I want mehndi", "Sarah"), ("I need shampoo", "Mike"),
        # Marathi
        ("Mala facial karaycha aahe", "Priya"), ("Hair cut cha kimmat kiti?", "Rahul"),
        ("Bridal makeup book karaycha aahe", "Anita"), ("Waxing karaychi aahe", "Priya"),
        ("Threading karaychi aahe", "Rahul"), ("Manicure karaycha aahe", "Anita"),
        # Gujarati
        ("Mane facial karvano chhe", "Priya"), ("Hair cut no bhav kiti chhe?", "Rahul"),
        ("Bridal makeup book karvano chhe", "Anita"), ("Waxing karvi chhe", "Priya"),
        ("Threading karvi chhe", "Rahul"), ("Manicure karvano chhe", "Anita"),
        # Tamil
        ("Enakku facial pannanum", "Priya"), ("Hair cut vilai evvalavu?", "Rahul"),
        ("Bridal makeup book pannanum", "Anita"), ("Waxing pannanum", "Priya"),
        # Telugu
        ("Naku facial cheyali", "Priya"), ("Hair cut dhara entha?", "Rahul"),
        ("Bridal makeup book cheyali", "Anita"), ("Waxing cheyali", "Priya"),
        # Bengali
        ("Amake facial korte hobe", "Priya"), ("Hair cut dam koto?", "Rahul"),
        ("Bridal makeup book korte hobe", "Anita"), ("Waxing korte hobe", "Priya"),
        # More Hindi
        ("Facial ka rate batao", "Rahul"), ("Hair color karwana hai", "Anita"),
        ("Hair spa karwana hai", "Priya"), ("Straightening karwani hai", "Rahul"),
        ("Smoothing karwani hai", "Anita"), ("Keratin treatment chahiye", "Priya"),
        ("Bleach karwani hai", "Rahul"), ("Clean up karwana hai", "Anita"),
        ("Face pack lagwana hai", "Priya"), ("Skin whitening treatment", "Rahul"),
        ("Anti aging treatment", "Anita"), ("Acne treatment chahiye", "Priya"),
        ("Party makeup chahiye", "Rahul"), ("Reception makeup chahiye", "Anita"),
        ("Sangeet makeup chahiye", "Priya"), ("HD makeup chahiye", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 20. COMPLEX SCENARIOS (50 tests)
    # ──────────────────────────────────────────────
    "COMPLEX_SCENARIOS": [
        ("Mujhe bridal makeup karwana hai aur mehndi bhi lagwani hai", "Priya"),
        ("Hair cut karwana hai aur color bhi karwana hai", "Rahul"),
        ("Facial karwana hai aur waxing bhi karwani hai", "Anita"),
        ("Manicure karwana hai aur pedicure bhi karwana hai", "Priya"),
        ("Hair spa karwana hai aur oil massage bhi", "Rahul"),
        ("Threading karwani hai aur facial bhi karwana hai", "Anita"),
        ("Full body waxing karwani hai aur facial bhi", "Priya"),
        ("Nail art karwana hai aur manicure bhi", "Rahul"),
        ("Mehndi lagwani hai aur makeup bhi karwana hai", "Anita"),
        ("Hair straightening karwani hai aur color bhi", "Priya"),
        ("Mera budget 2000 hai, kya kya ho sakta hai?", "Rahul"),
        ("Mera budget 5000 hai, full package hoga?", "Anita"),
        ("Mera budget 10000 hai, bridal package chahiye", "Priya"),
        ("Mera budget 500 hai, sirf zaruri kaam karo", "Rahul"),
        ("Pehle hair cut karo, phir facial karo", "Anita"),
        ("Pehle waxing karo, phir threading karo", "Priya"),
        ("Aaj hi chahiye, kal shaadi hai", "Rahul"),
        ("Emergency hai, 2 ghante mein chahiye", "Anita"),
        ("Kal subah tak chahiye, function hai", "Priya"),
        ("Monday tak chahiye, wedding hai", "Rahul"),
        ("1 hafte mein chahiye, koi jaldi nahi", "Anita"),
        ("Mujhe 2 facial karwane hain", "Priya"),
        ("Mere poore group ke liye booking hai", "Rahul"),
        ("Family ke liye package chahiye", "Anita"),
        ("Mera wedding hai, full package chahiye", "Priya"),
        ("Engagement hai, makeup chahiye", "Rahul"),
        ("Reception hai, makeup chahiye", "Anita"),
        ("Sangeet hai, makeup chahiye", "Priya"),
        ("Haldi hai, makeup chahiye", "Rahul"),
        ("Mehndi hai, mehndi lagwani hai", "Anita"),
        ("Birthday party hai, makeup chahiye", "Priya"),
        ("Anniversary hai, special treatment chahiye", "Rahul"),
        ("Date night hai, makeup chahiye", "Anita"),
        ("Interview hai, grooming chahiye", "Priya"),
        ("Photoshoot hai, makeup chahiye", "Rahul"),
        ("Video shoot hai, makeup chahiye", "Anita"),
        ("College event hai, makeup chahiye", "Priya"),
        ("Office party hai, grooming chahiye", "Rahul"),
        ("Festival hai, special treatment chahiye", "Anita"),
        ("Karva Chauth ke liye makeup chahiye", "Priya"),
        ("Diwali ke liye facial karwana hai", "Rahul"),
        ("Christmas ke liye grooming chahiye", "Anita"),
        ("New Year ke liye makeup chahiye", "Priya"),
        ("Valentine's Day ke liye special treatment", "Rahul"),
        ("Rakhi ke liye grooming chahiye", "Anita"),
        ("Eid ke liye makeup chahiye", "Priya"),
        ("Navratri ke liye special treatment", "Rahul"),
        ("Durga Puja ke liye makeup chahiye", "Anita"),
        ("Ganesh Chaturthi ke liye grooming", "Priya"),
        ("Pongal ke liye special treatment", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 21. SHOP OWNER (30 tests)
    # ──────────────────────────────────────────────
    "SHOP_OWNER": [
        ("Aaj kitne clients aaye?", "Priya"), ("Total revenue kitna hai?", "Rahul"),
        ("Kitne appointments hain?", "Anita"), ("Stock check karo", "Priya"),
        ("Shampoo ka stock kitna hai?", "Rahul"), ("Conditioner ka stock kitna hai?", "Anita"),
        ("Low stock alert hai?", "Priya"), ("Restock karna hai", "Rahul"),
        ("New product add karna hai", "Anita"), ("Price update karna hai", "Priya"),
        ("Discount laga do", "Rahul"), ("Sale lagao", "Anita"),
        ("Report banao", "Priya"), ("Analytics dikhao", "Rahul"),
        ("Client list dikhao", "Anita"), ("Appointment history dikhao", "Priya"),
        ("Payment history dikhao", "Rahul"), ("Expense report dikhao", "Anita"),
        ("Profit kitna hai?", "Priya"), ("Loss kitna hai?", "Rahul"),
        ("GST return file karna hai", "Anita"), ("Tax calculation karo", "Priya"),
        ("Invoice generate karo", "Rahul"), ("Receipt generate karo", "Anita"),
        ("Client feedback dikhao", "Priya"), ("Rating kya hai?", "Rahul"),
        ("Review check karo", "Anita"), ("Complaint list dikhao", "Priya"),
        ("Pending appointments dikhao", "Rahul"), ("Completed services dikhao", "Anita"),
    ],

    # ──────────────────────────────────────────────
    # 22. TRICKY QUESTIONS (30 tests)
    # ──────────────────────────────────────────────
    "TRICKY_QUESTIONS": [
        ("Kya tum sach mein AI ho?", "Priya"), ("Tumhara naam kya hai?", "Rahul"),
        ("Tum kahan se ho?", "Anita"), ("Tumhari age kya hai?", "Priya"),
        ("Tumhe kisne banaya?", "Rahul"), ("Tum kya kar sakte ho?", "Anita"),
        ("Tumhare paas kya kya hai?", "Priya"), ("Sabse sasta kya hai?", "Rahul"),
        ("Sabse mehenga kya hai?", "Anita"), ("Best service kya hai?", "Priya"),
        ("Worst service kya hai?", "Rahul"), ("Sabse popular kya hai?", "Anita"),
        ("Naya kya hai?", "Priya"), ("Purana kya hai?", "Rahul"),
        ("Sale mein kya hai?", "Anita"), ("Offer kya hai?", "Priya"),
        ("Deal kya hai?", "Rahul"), ("Combo hai?", "Anita"),
        ("Package hai?", "Priya"), ("Membership hai?", "Rahul"),
        ("Loyalty program hai?", "Anita"), ("Reward points hain?", "Priya"),
        ("Referral bonus hai?", "Rahul"), ("First visit discount?", "Anita"),
        ("Birthday discount?", "Priya"), ("Anniversary discount?", "Rahul"),
        ("Coupons hain?", "Anita"), ("Vouchers hain?", "Priya"),
        ("Gift cards hain?", "Rahul"), ("Cashback hai?", "Anita"),
    ],

    # ──────────────────────────────────────────────
    # 23. EMERGENCY (20 tests)
    # ──────────────────────────────────────────────
    "EMERGENCY": [
        ("Bahut urgent hai, aaj hi chahiye", "Priya"), ("Emergency hai", "Rahul"),
        ("Kal shaadi hai, makeup chahiye", "Anita"), ("Aaj engagement hai", "Priya"),
        ("Kal reception hai", "Rahul"), ("Aaj sangeet hai", "Anita"),
        ("Kal mehndi hai", "Priya"), ("Aaj haldi hai", "Rahul"),
        ("Kal birthday party hai", "Anita"), ("Aaj anniversary hai", "Priya"),
        ("Kal interview hai", "Rahul"), ("Aaj photoshoot hai", "Anita"),
        ("Kal video shoot hai", "Priya"), ("Aaj college event hai", "Rahul"),
        ("Kal office party hai", "Anita"), ("Aaj date night hai", "Priya"),
        ("Kal festival hai", "Rahul"), ("Aaj function hai", "Anita"),
        ("Kal guest aa rahe hain", "Priya"), ("Aaj special occasion hai", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 24. BUDGET QUERIES (20 tests)
    # ──────────────────────────────────────────────
    "BUDGET_QUERIES": [
        ("Mera budget 500 hai", "Priya"), ("Mera budget 1000 hai", "Rahul"),
        ("Mera budget 2000 hai", "Anita"), ("Mera budget 5000 hai", "Priya"),
        ("Mera budget 10000 hai", "Rahul"), ("Sasta option batao", "Anita"),
        ("Mehenga option batao", "Priya"), ("Budget friendly option?", "Rahul"),
        ("Cheap mein ho jayega?", "Anita"), ("Premium service hai?", "Priya"),
        ("Basic package kya hai?", "Rahul"), ("Standard package kya hai?", "Anita"),
        ("Advanced package kya hai?", "Priya"), ("5000 mein bridal package?", "Rahul"),
        ("2000 mein facial waxing?", "Anita"), ("1000 mein hair cut color?", "Priya"),
        ("500 mein threading facial?", "Rahul"), ("EMI pe ho jayega?", "Anita"),
        ("Installment mein?", "Priya"), ("Part payment kar sakti hoon?", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 25. COMPARISON QUERIES (20 tests)
    # ──────────────────────────────────────────────
    "COMPARISON_QUERIES": [
        ("Facial ya cleanup, kya better hai?", "Priya"), ("Gold facial ya diamond facial?", "Rahul"),
        ("Waxing ya threading?", "Anita"), ("Hot wax ya cold wax?", "Priya"),
        ("Gel nails ya acrylic nails?", "Rahul"), ("Manicure ya pedicure pehle?", "Anita"),
        ("Hair cut ya hair spa pehle?", "Priya"), ("Hair color ya highlights?", "Rahul"),
        ("Straightening ya smoothing?", "Anita"), ("Keratin ya cysteine?", "Priya"),
        ("HD makeup ya airbrush makeup?", "Rahul"), ("Bridal makeup ya party makeup?", "Anita"),
        ("Indian mehndi ya Arabic mehndi?", "Priya"), ("Full hand ya half hand?", "Rahul"),
        ("Shampoo kaunsa brand achha hai?", "Anita"), ("Conditioner kaunsa brand?", "Priya"),
        ("Hair oil kaunsa brand?", "Rahul"), ("Face wash kaunsa brand?", "Anita"),
        ("Sunscreen kaunsa brand?", "Priya"), ("Moisturizer kaunsa brand?", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 26. OCCASION QUERIES (30 tests)
    # ──────────────────────────────────────────────
    "OCCASION_QUERIES": [
        ("Wedding ke liye kya karwana chahiye?", "Priya"), ("Engagement ke liye kya?", "Rahul"),
        ("Reception ke liye kya?", "Anita"), ("Sangeet ke liye kya?", "Priya"),
        ("Mehndi ke liye kya?", "Rahul"), ("Haldi ke liye kya?", "Anita"),
        ("Birthday ke liye kya?", "Priya"), ("Anniversary ke liye kya?", "Rahul"),
        ("Date night ke liye kya?", "Anita"), ("Interview ke liye kya?", "Priya"),
        ("Photoshoot ke liye kya?", "Rahul"), ("Video shoot ke liye kya?", "Anita"),
        ("College event ke liye kya?", "Priya"), ("Office party ke liye kya?", "Rahul"),
        ("Festival ke liye kya?", "Anita"), ("Karva Chauth ke liye kya?", "Priya"),
        ("Diwali ke liye kya?", "Rahul"), ("Christmas ke liye kya?", "Anita"),
        ("New Year ke liye kya?", "Priya"), ("Valentine's Day ke liye kya?", "Rahul"),
        ("Rakhi ke liye kya?", "Anita"), ("Eid ke liye kya?", "Priya"),
        ("Navratri ke liye kya?", "Rahul"), ("Durga Puja ke liye kya?", "Anita"),
        ("Ganesh Chaturthi ke liye kya?", "Priya"), ("Pongal ke liye kya?", "Rahul"),
        ("Onam ke liye kya?", "Anita"), ("Baisakhi ke liye kya?", "Priya"),
        ("Lohri ke liye kya?", "Rahul"), ("Holi ke liye kya?", "Anita"),
    ],

    # ──────────────────────────────────────────────
    # 27. HAIR PROBLEMS (25 tests)
    # ──────────────────────────────────────────────
    "HAIR_PROBLEMS": [
        ("Baal bahut jhad rahe hain", "Priya"), ("Hair fall ho raha hai", "Rahul"),
        ("Baal toot rahe hain", "Anita"), ("Baal sukh rahe hain", "Priya"),
        ("Baal dry ho gaye hain", "Rahul"), ("Baal damage ho gaye hain", "Anita"),
        ("Baal bahut oily hain", "Priya"), ("Baal bahut rough hain", "Rahul"),
        ("Dandruff bahut hai", "Anita"), ("Scalp mein itching hai", "Priya"),
        ("Baal white ho rahe hain", "Rahul"), ("Baal grey ho rahe hain", "Anita"),
        ("Baal patle ho rahe hain", "Priya"), ("Ganjapan aa raha hai", "Rahul"),
        ("Baal nahi badh rahe", "Anita"), ("Baal ki growth slow hai", "Priya"),
        ("Baal bahut curly hain", "Rahul"), ("Baal bahut frizzy hain", "Anita"),
        ("Baal mein lice ho gaye", "Priya"), ("Baal mein fungus ho gaya", "Rahul"),
        ("Baal mein infection ho gaya", "Anita"), ("Baal ka colour galat aa gaya", "Priya"),
        ("Baal ka colour jaldi fade ho gaya", "Rahul"), ("Baal ka colour uneven aa gaya", "Anita"),
        ("Baal ka colour dark chahiye tha", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 28. SKIN PROBLEMS (25 tests)
    # ──────────────────────────────────────────────
    "SKIN_PROBLEMS": [
        ("Skin bahut dry hai", "Priya"), ("Skin oily hai", "Rahul"),
        ("Skin pe dark spots hain", "Anita"), ("Skin pe pimples hain", "Priya"),
        ("Skin dull hai", "Rahul"), ("Skin pe wrinkles aa rahe hain", "Anita"),
        ("Skin pe tan ho gaya hai", "Priya"), ("Skin pe redness hai", "Rahul"),
        ("Skin pe allergy hai", "Anita"), ("Skin pe itching hai", "Priya"),
        ("Skin pe rash hai", "Rahul"), ("Skin pe eczema hai", "Anita"),
        ("Skin pe psoriasis hai", "Priya"), ("Skin pe pigmentation hai", "Rahul"),
        ("Skin pe freckles hain", "Anita"), ("Skin pe moles hain", "Priya"),
        ("Skin pe blackheads hain", "Rahul"), ("Skin pe whiteheads hain", "Anita"),
        ("Skin pe open pores hain", "Priya"), ("Skin pe scars hain", "Rahul"),
        ("Skin pe stretch marks hain", "Anita"), ("Skin pe sunburn hai", "Priya"),
        ("Skin pe dark circles hain", "Rahul"), ("Skin pe puffiness hai", "Anita"),
        ("Skin pe sagging ho rahi hai", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 29. SALON AMBIENCE (20 tests)
    # ──────────────────────────────────────────────
    "SALON_AMBIENCE": [
        ("Salon kahan hai?", "Priya"), ("Address kya hai?", "Rahul"),
        ("Location bhejo", "Anita"), ("Google Maps pe hai?", "Priya"),
        ("Parking hai?", "Rahul"), ("AC hai salon mein?", "Anita"),
        ("WiFi hai?", "Priya"), ("Music bajta hai?", "Rahul"),
        ("Cleanliness kaisi hai?", "Anita"), ("Hygiene maintain karte ho?", "Priya"),
        ("Sanitization karte ho?", "Rahul"), ("Tools sanitize karte ho?", "Anita"),
        ("Fresh towels milte hain?", "Priya"), ("Disposable items use karte ho?", "Rahul"),
        ("Waiting area hai?", "Anita"), ("Refreshments milte hain?", "Priya"),
        ("Magazines hain?", "Rahul"), ("TV hai?", "Anita"),
        ("Kids area hai?", "Priya"), ("Couples area hai?", "Rahul"),
    ],
}

def run_tests():
    total = 0
    passed = 0
    failed = 0
    failures = []
    
    for category, tests in TESTS.items():
        print(f"\n{'='*60}")
        print(f"  {category} ({len(tests)} tests)")
        print(f"{'='*60}")
        
        for msg, name in tests:
            total += 1
            try:
                reply = get_fallback_reply(msg, name, SALON)
                if not reply or len(reply) < 5:
                    failed += 1
                    failures.append((category, msg, name, "Empty/too short reply"))
                    print(f"  FAIL: [{name}] {msg} -> EMPTY REPLY")
                elif reply.startswith("Traceback") or reply.startswith("Error"):
                    failed += 1
                    failures.append((category, msg, name, "Error in reply"))
                    print(f"  FAIL: [{name}] {msg} -> ERROR")
                else:
                    passed += 1
                    print(f"  OK: [{name}] {msg} -> {reply[:80]}...")
            except Exception as e:
                failed += 1
                failures.append((category, msg, name, str(e)))
                print(f"  ERROR: [{name}] {msg} -> {e}")
    
    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}")
    
    if failures:
        print(f"\n  FAILURES ({len(failures)}):")
        for cat, msg, name, err in failures[:20]:
            print(f"    [{cat}] {name}: {msg} -> {err}")
        if len(failures) > 20:
            print(f"    ... and {len(failures) - 20} more")
    
    return passed, failed, total

if __name__ == "__main__":
    run_tests()
