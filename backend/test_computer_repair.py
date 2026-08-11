"""
Computer Repair Shop - 1000 Question Test Suite
Tests customer and shop owner interactions across all scenarios
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from services.free_ai import get_fallback_reply, detect_language

# Computer Repair Shop Inventory
REPAIR_SHOP = [
    # Services
    {'name': 'Laptop Repair', 'price': 500, 'stock': 10, 'unit': 'slots', 'category': 'Repair', 'item_type': 'service', 'duration_minutes': 60},
    {'name': 'Screen Replacement', 'price': 1500, 'stock': 5, 'unit': 'slots', 'category': 'Repair', 'item_type': 'service', 'duration_minutes': 45},
    {'name': 'Virus Removal', 'price': 300, 'stock': 10, 'unit': 'slots', 'category': 'Repair', 'item_type': 'service', 'duration_minutes': 30},
    {'name': 'Data Recovery', 'price': 800, 'stock': 5, 'unit': 'slots', 'category': 'Repair', 'item_type': 'service', 'duration_minutes': 120},
    {'name': 'OS Installation', 'price': 400, 'stock': 10, 'unit': 'slots', 'category': 'Repair', 'item_type': 'service', 'duration_minutes': 60},
    {'name': 'Printer Repair', 'price': 350, 'stock': 5, 'unit': 'slots', 'category': 'Repair', 'item_type': 'service', 'duration_minutes': 45},
    {'name': 'Motherboard Repair', 'price': 2000, 'stock': 3, 'unit': 'slots', 'category': 'Repair', 'item_type': 'service', 'duration_minutes': 180},
    {'name': 'Keyboard Replacement', 'price': 800, 'stock': 8, 'unit': 'slots', 'category': 'Repair', 'item_type': 'service', 'duration_minutes': 30},
    {'name': 'Battery Replacement', 'price': 1200, 'stock': 6, 'unit': 'slots', 'category': 'Repair', 'item_type': 'service', 'duration_minutes': 30},
    {'name': 'WiFi Fix', 'price': 250, 'stock': 10, 'unit': 'slots', 'category': 'Repair', 'item_type': 'service', 'duration_minutes': 30},
    # Products
    {'name': 'SSD 256GB', 'price': 2500, 'stock': 8, 'unit': 'pcs', 'category': 'Storage', 'item_type': 'product'},
    {'name': 'SSD 512GB', 'price': 4500, 'stock': 5, 'unit': 'pcs', 'category': 'Storage', 'item_type': 'product'},
    {'name': 'RAM 8GB DDR4', 'price': 1800, 'stock': 12, 'unit': 'pcs', 'category': 'Memory', 'item_type': 'product'},
    {'name': 'RAM 16GB DDR4', 'price': 3200, 'stock': 8, 'unit': 'pcs', 'category': 'Memory', 'item_type': 'product'},
    {'name': 'Laptop Charger Universal', 'price': 800, 'stock': 20, 'unit': 'pcs', 'category': 'Accessories', 'item_type': 'product'},
    {'name': 'Laptop Battery', 'price': 2500, 'stock': 6, 'unit': 'pcs', 'category': 'Parts', 'item_type': 'product'},
    {'name': 'Keyboard USB', 'price': 500, 'stock': 15, 'unit': 'pcs', 'category': 'Accessories', 'item_type': 'product'},
    {'name': 'Mouse USB', 'price': 350, 'stock': 20, 'unit': 'pcs', 'category': 'Accessories', 'item_type': 'product'},
    {'name': 'HDMI Cable', 'price': 200, 'stock': 25, 'unit': 'pcs', 'category': 'Cables', 'item_type': 'product'},
    {'name': 'USB Hub 4-Port', 'price': 450, 'stock': 10, 'unit': 'pcs', 'category': 'Accessories', 'item_type': 'product'},
    {'name': 'Thermal Paste', 'price': 150, 'stock': 30, 'unit': 'pcs', 'category': 'Repair', 'item_type': 'product'},
    {'name': 'Laptop Screen 15.6 inch', 'price': 3500, 'stock': 4, 'unit': 'pcs', 'category': 'Parts', 'item_type': 'product'},
    {'name': 'Laptop Screen 14 inch', 'price': 3000, 'stock': 3, 'unit': 'pcs', 'category': 'Parts', 'item_type': 'product'},
    {'name': 'Webcam HD', 'price': 1200, 'stock': 10, 'unit': 'pcs', 'category': 'Accessories', 'item_type': 'product'},
    {'name': 'Headphone USB', 'price': 800, 'stock': 12, 'unit': 'pcs', 'category': 'Accessories', 'item_type': 'product'},
]

# ======== 1000 TEST SCENARIOS ========
TESTS = {
    # ──────────────────────────────────────────────
    # 1. GREETINGS (30 tests)
    # ──────────────────────────────────────────────
    "GREETING": [
        ("Hello", "Rahul"), ("Hi", "Amit"), ("Hey", "Priya"), ("Namaste", "Rahul"),
        ("Good morning", "Amit"), ("Good evening", "Priya"), ("Good afternoon", "Rahul"),
        ("hii", "Amit"), ("hello bhai", "Priya"), ("namaskar", "Rahul"),
        ("helo", "Amit"), ("hiii", "Priya"), ("gud morning", "Rahul"),
        ("pranam", "Amit"), ("ram ram", "Priya"), ("sat sri akal", "Rahul"),
        ("jai hind", "Amit"), ("kaise ho", "Priya"), ("kya haal hai", "Rahul"),
        ("how are you", "Amit"), ("what's up", "Priya"), ("yo", "Rahul"),
        ("sup", "Amit"), ("hola", "Priya"), ("bonjour", "Rahul"),
        ("hi there", "Amit"), ("hello sir", "Priya"), ("namaste ji", "Rahul"),
        ("good night", "Amit"), ("subah ho gayi", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 2. SERVICE QUERIES - Laptop Issues (80 tests)
    # ──────────────────────────────────────────────
    "LAPTOP_ISSUES": [
        ("Mera laptop kharab hai", "Rahul"), ("Laptop repair karwana hai", "Amit"),
        ("Laptop band ho gaya", "Priya"), ("Laptop on nahi ho raha", "Rahul"),
        ("Laptop hang ho raha hai", "Amit"), ("Laptop slow hai", "Priya"),
        ("Laptop garam ho raha hai", "Rahul"), ("Laptop mein se awaaz aa rahi hai", "Amit"),
        ("Laptop ki fan kharab hai", "Priya"), ("Laptop freeze ho raha hai", "Rahul"),
        ("Laptop restart ho raha hai", "Amit"), ("Laptop blue screen aa raha hai", "Priya"),
        ("Laptop boot nahi ho raha", "Rahul"), ("Laptop mein virus hai", "Amit"),
        ("Laptop mein malware hai", "Priya"), ("Laptop bahut slow hai", "Rahul"),
        ("Laptop kaam nahi kar raha", "Amit"), ("Laptop chalu nahi ho raha", "Priya"),
        ("Laptop dead ho gaya", "Rahul"), ("Laptop mein kuch nahi ho raha", "Amit"),
        ("Laptop ki performance kharab hai", "Priya"), ("Laptop overheating hai", "Rahul"),
        ("Laptop ka processor slow hai", "Amit"), ("Laptop ki RAM kam hai", "Priya"),
        ("Laptop ki storage full hai", "Rahul"), ("Laptop ki battery phool gayi hai", "Amit"),
        ("Laptop ka hinge toot gaya", "Priya"), ("Laptop ki body toot gayi", "Rahul"),
        ("Laptop mein paani gir gaya", "Amit"), ("Laptop paani mein gir gaya", "Priya"),
        ("Laptop drop ho gaya", "Rahul"), ("Laptop gir gaya", "Amit"),
        ("Laptop ka charger kaam nahi kar raha", "Priya"), ("Laptop charging nahi ho rahi", "Rahul"),
        ("Laptop ka port kharab hai", "Amit"), ("Laptop ki screen flicker kar rahi hai", "Priya"),
        ("Screen pe lines aa rahe hain", "Rahul"), ("Screen black hai", "Amit"),
        ("Screen pe spots hain", "Priya"), ("Laptop ki screen dim hai", "Rahul"),
        ("Laptop ki screen tut gayi", "Amit"), ("Screen crack ho gaya", "Priya"),
        ("Laptop ka display nahi aa raha", "Rahul"), ("Laptop ki screen white hai", "Amit"),
        ("Keyboard kaam nahi kar raha", "Priya"), ("Keyboard ke kharab ho gaye", "Rahul"),
        ("Keyboard ke keys nahi dab rahe", "Amit"), ("Keyboard mein paani gir gaya", "Priya"),
        ("Touchpad kaam nahi kar raha", "Rahul"), ("Mouse kaam nahi kar raha", "Amit"),
        ("Touchpad cursor nahi move ho raha", "Priya"), ("WiFi connect nahi ho raha", "Rahul"),
        ("WiFi kaam nahi kar raha", "Amit"), ("Internet nahi chal raha", "Priya"),
        ("Bluetooth kaam nahi kar raha", "Rahul"), ("Sound nahi aa raha", "Amit"),
        ("Speaker kharab hai", "Priya"), ("Camera kaam nahi kar raha", "Rahul"),
        ("Webcam kaam nahi kar raha", "Amit"), ("Mic kaam nahi kar raha", "Priya"),
        ("USB port kaam nahi kar raha", "Rahul"), ("HDMI port kaam nahi kar raha", "Amit"),
        ("Laptop ka fan noise bahut hai", "Priya"), ("Laptop se smell aa rahi hai", "Rahul"),
        ("Laptop ka processor kharab hai", "Amit"), ("Laptop ki motherboard kharab hai", "Priya"),
        ("Laptop ka GPU kharab hai", "Rahul"), ("Laptop ki battery drain ho rahi hai", "Amit"),
        ("Battery backup nahi hai", "Priya"), ("Laptop ka hinge loose hai", "Rahul"),
        ("Laptop ki body crack hai", "Amit"), ("Laptop ka CD drive kaam nahi kar raha", "Priya"),
        ("Laptop ka audio jack kaam nahi kar raha", "Rahul"), ("Laptop ka ethernet port kharab hai", "Amit"),
        ("Laptop ka power button kaam nahi kar raha", "Priya"), ("Laptop ka volume button kharab hai", "Rahul"),
        ("Laptop ka brightness control kaam nahi kar raha", "Amit"), ("Laptop ka keyboard light nahi aa rahi", "Priya"),
        ("Laptop ka fan nahi chal raha", "Rahul"), ("Laptop ki battery swelling hai", "Amit"),
        ("Laptop ka charger pin kharab hai", "Priya"), ("Laptop ka charger wire cut gayi", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 3. SERVICE QUERIES - Screen Issues (30 tests)
    # ──────────────────────────────────────────────
    "SCREEN_ISSUES": [
        ("Screen tod gaya hai", "Rahul"), ("Laptop ka screen tut gaya", "Amit"),
        ("Screen flicker kar rahi hai", "Priya"), ("Screen pe lines aa rahe hain", "Rahul"),
        ("Screen black hai", "Amit"), ("Screen pe spots hain", "Priya"),
        ("Screen dim hai", "Rahul"), ("Screen white ho gayi", "Amit"),
        ("Screen pe dead pixels hain", "Priya"), ("Screen ka color galat aa raha", "Rahul"),
        ("Screen ka touch kaam nahi kar raha", "Amit"), ("Screen pe crack hai", "Priya"),
        ("Screen replacement karwana hai", "Rahul"), ("Naya screen chahiye", "Amit"),
        ("Screen ka size kya hai?", "Priya"), ("15.6 inch screen hai?", "Rahul"),
        ("14 inch screen chahiye", "Amit"), ("Screen ka rate kya hai?", "Priya"),
        ("Screen kitne ka milega?", "Rahul"), ("Screen ki warranty hai?", "Amit"),
        ("Screen replacement mein kitna time lagega?", "Priya"), ("Screen replacement ka charge?", "Rahul"),
        ("Original screen milega?", "Amit"), ("Compatible screen hai?", "Priya"),
        ("Screen ki quality kaisi hai?", "Rahul"), ("Screen pe guard milega?", "Amit"),
        ("Screen protector hai?", "Priya"), ("Screen cleaning karwani hai", "Rahul"),
        ("Screen pe scratch hai", "Amit"), ("Screen ka backlight kharab hai", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 4. SERVICE QUERIES - Data/Software (30 tests)
    # ──────────────────────────────────────────────
    "DATA_SOFTWARE": [
        ("Data recover karna hai", "Rahul"), ("Hard disk se data nikalna hai", "Amit"),
        ("Data loss ho gaya", "Priya"), ("Files delete ho gayi", "Rahul"),
        ("Photos recover karne hain", "Amit"), ("Documents recover karne hain", "Priya"),
        ("Hard disk kharab hai", "Rahul"), ("SSD kharab hai", "Amit"),
        ("Pen drive se data nikalna hai", "Priya"), ("Memory card se data nikalna hai", "Rahul"),
        ("Windows install karna hai", "Amit"), ("Format karna hai laptop", "Priya"),
        ("Windows 11 install karna hai", "Rahul"), ("Windows 10 install karna hai", "Amit"),
        ("Linux install karna hai", "Priya"), ("Dual boot karna hai", "Rahul"),
        ("Software install karna hai", "Amit"), ("Driver install karna hai", "Priya"),
        ("Antivirus install karna hai", "Rahul"), ("Office install karna hai", "Amit"),
        ("Virus removal karwana hai", "Priya"), ("Malware hatana hai", "Rahul"),
        ("System restore karna hai", "Amit"), ("Backup lena hai", "Priya"),
        ("Cloning karna hai", "Rahul"), ("Migration karna hai", "Amit"),
        ("Partition karna hai", "Priya"), ("Disk cleanup karna hai", "Rahul"),
        ("BIOS update karna hai", "Amit"), ("Driver update karna hai", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 5. SERVICE QUERIES - Printer (20 tests)
    # ──────────────────────────────────────────────
    "PRINTER_ISSUES": [
        ("Printer kaam nahi kar raha", "Rahul"), ("Printer repair karwana hai", "Amit"),
        ("Printer print nahi de raha", "Priya"), ("Printer ka paper jam ho gaya", "Rahul"),
        ("Printer ki ink khatam ho gayi", "Amit"), ("Printer ka cartridge change karna hai", "Priya"),
        ("Printer ka driver install karna hai", "Rahul"), ("Printer connect nahi ho raha", "Amit"),
        ("Printer WiFi se connect nahi ho raha", "Priya"), ("Printer ki quality kharab hai", "Rahul"),
        ("Printer se streaks aa rahe hain", "Amit"), ("Printer ka drum change karna hai", "Priya"),
        ("Printer ka maintenance karwana hai", "Rahul"), ("Printer ka head clean karna hai", "Amit"),
        ("Printer ka roller change karna hai", "Priya"), ("Printer ka belt change karna hai", "Rahul"),
        ("Printer ka fuser change karna hai", "Amit"), ("Printer ka toner change karna hai", "Priya"),
        ("Printer ka paper tray kharab hai", "Rahul"), ("Printer ka power supply kharab hai", "Amit"),
    ],

    # ──────────────────────────────────────────────
    # 6. PRODUCT QUERIES (60 tests)
    # ──────────────────────────────────────────────
    "PRODUCT_QUERIES": [
        ("SSD hai kya?", "Rahul"), ("SSD 256GB chahiye", "Amit"), ("SSD 512GB hai?", "Priya"),
        ("RAM chahiye 8GB", "Rahul"), ("RAM 16GB hai?", "Amit"), ("DDR4 RAM hai?", "Priya"),
        ("Laptop charger hai?", "Rahul"), ("Charger chahiye universal", "Amit"), ("Charger milega?", "Priya"),
        ("Laptop battery hai?", "Rahul"), ("Battery chahiye", "Amit"), ("Battery milegi?", "Priya"),
        ("Keyboard chahiye", "Rahul"), ("USB keyboard hai?", "Amit"), ("Keyboard milega?", "Priya"),
        ("Mouse hai?", "Rahul"), ("USB mouse chahiye", "Amit"), ("Wireless mouse hai?", "Priya"),
        ("HDMI cable hai?", "Rahul"), ("HDMI cable chahiye", "Amit"), ("HDMI cable kitni lambi?", "Priya"),
        ("USB hub hai?", "Rahul"), ("USB hub chahiye", "Amit"), ("4 port USB hub hai?", "Priya"),
        ("Thermal paste hai?", "Rahul"), ("Thermal paste chahiye", "Amit"), ("Thermal paste kitne ka?", "Priya"),
        ("Laptop screen hai?", "Rahul"), ("Screen 15.6 inch chahiye", "Amit"), ("14 inch screen hai?", "Priya"),
        ("Webcam hai?", "Rahul"), ("HD webcam chahiye", "Amit"), ("Webcam kitne ka hai?", "Priya"),
        ("Headphone hai?", "Rahul"), ("USB headphone chahiye", "Amit"), ("Headphone kitne ka?", "Priya"),
        ("Pen drive hai?", "Rahul"), ("External hard disk hai?", "Amit"), ("Laptop bag hai?", "Priya"),
        ("Laptop stand hai?", "Rahul"), ("Screen guard hai?", "Amit"), ("Keyboard cover hai?", "Priya"),
        ("Mouse pad hai?", "Rahul"), ("USB cable hai?", "Amit"), ("Type C cable hai?", "Priya"),
        ("Power bank hai?", "Rahul"), ("Surge protector hai?", "Amit"), ("Extension board hai?", "Priya"),
        ("SSD enclosure hai?", "Rahul"), ("RAM slot hai?", "Amit"), ("Laptop skin hai?", "Priya"),
        ("Cleaning kit hai?", "Rahul"), ("Compressed air hai?", "Amit"), ("Screwdriver set hai?", "Priya"),
        ("Soldering iron hai?", "Rahul"), ("Multimeter hai?", "Amit"), ("Toolkit hai?", "Priya"),
        ("SSD ka price?", "Rahul"), ("RAM ka rate?", "Amit"), ("Charger ka cost?", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 7. PRICING QUERIES (40 tests)
    # ──────────────────────────────────────────────
    "PRICING_QUERIES": [
        ("Laptop repair ka kitna charge hai?", "Rahul"), ("Screen replacement ka rate?", "Amit"),
        ("Virus removal ka price?", "Priya"), ("Data recovery kitne ka hai?", "Rahul"),
        ("OS installation ka charge?", "Amit"), ("Printer repair ka kitna lagega?", "Priya"),
        ("Motherboard repair ka cost?", "Rahul"), ("Keyboard replacement ka rate?", "Amit"),
        ("Battery replacement ka price?", "Priya"), ("WiFi fix ka charge?", "Rahul"),
        ("Kitna lagega repair mein?", "Amit"), ("Total kitna hoga?", "Priya"),
        ("Price kitna hai?", "Rahul"), ("Rate kya hai?", "Amit"), ("Cost kitna aayega?", "Priya"),
        ("Charge kitna hai?", "Rahul"), ("Kitne paise lagenge?", "Amit"), ("Kitna kharcha hoga?", "Priya"),
        ("Sasta hoga kya?", "Rahul"), ("Discount milega kya?", "Amit"), ("Kya price hai laptop repair ka?", "Priya"),
        ("Screen replacement ka kitna lagega?", "Rahul"), ("Data recovery ka charge kitna hai?", "Amit"),
        ("Virus removal ka rate kya hai?", "Priya"), ("OS installation ka price batao", "Rahul"),
        ("Printer repair ka cost kitna hai?", "Amit"), ("Motherboard repair ka rate batao", "Priya"),
        ("Keyboard replacement ka charge kitna?", "Rahul"), ("Battery replacement ka cost batao", "Amit"),
        ("WiFi fix ka price kitna hai?", "Priya"), ("SSD ka rate kya hai?", "Rahul"),
        ("RAM ka price batao", "Amit"), ("Charger ka cost kitna?", "Priya"),
        ("Mouse ka rate kya hai?", "Rahul"), ("Keyboard ka price?", "Amit"),
        ("HDMI cable ka rate?", "Priya"), ("USB hub ka price?", "Rahul"),
        ("Thermal paste ka rate?", "Amit"), ("Webcam ka price?", "Priya"),
        ("Headphone ka rate?", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 8. BOOKING/APPOINTMENT (40 tests)
    # ──────────────────────────────────────────────
    "BOOKING_QUERIES": [
        ("Laptop repair book karna hai", "Rahul"), ("Screen replacement ke liye appointment chahiye", "Amit"),
        ("Kal ka slot hai?", "Priya"), ("Monday ko aa sakta hoon?", "Rahul"),
        ("Subah ka slot chahiye", "Amit"), ("Shaam ko aa sakta hoon?", "Priya"),
        ("Timing kya hai?", "Rahul"), ("Kab aa sakta hoon?", "Amit"),
        ("Aaj ka slot hai?", "Priya"), ("Tuesday 2pm ko", "Rahul"),
        ("Wednesday subah 10 baje", "Amit"), ("Thursday shaam 5 baje", "Priya"),
        ("Friday ko 3 baje", "Rahul"), ("Saturday ko subah", "Amit"),
        ("Sunday ko bhi khula hai?", "Priya"), ("Weekend pe aa sakta hoon?", "Rahul"),
        ("Laptop repair ke liye kab aaun?", "Amit"), ("Screen replacement ka time kitna lagega?", "Priya"),
        ("Kitne din lagega repair mein?", "Rahul"), ("Aaj hi ho jayega?", "Amit"),
        ("Emergency repair hai", "Priya"), ("Jaldi se jaldi chahiye", "Rahul"),
        ("2 din mein ho jayega?", "Amit"), ("1 hafte mein ho jayega?", "Priya"),
        ("Subah 9 baje aa sakta hoon?", "Rahul"), ("Shaam 6 baje aa sakta hoon?", "Amit"),
        ("Dopahar ko aa sakta hoon?", "Priya"), ("Raat ko bhi khula hai?", "Rahul"),
        ("Holiday pe khula hai?", "Amit"), ("Sunday ko band hai?", "Priya"),
        ("Monday ko band hai?", "Rahul"), ("Slot book karna hai", "Amit"),
        ("Appointment lena hai", "Priya"), ("Walk-in aa sakta hoon?", "Rahul"),
        ("Online booking hai?", "Amit"), ("Phone pe booking hogi?", "Priya"),
        ("WhatsApp pe booking hogi?", "Rahul"), ("Kitne baje aana hai?", "Amit"),
        ("Time batao", "Priya"), ("Schedule kya hai?", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 9. ORDER/DELIVERY (50 tests)
    # ──────────────────────────────────────────────
    "ORDER_DELIVERY": [
        ("SSD order karna hai", "Rahul"), ("RAM chahiye 2 piece", "Amit"),
        ("Mouse order karna hai", "Priya"), ("Keyboard chahiye 1 piece", "Rahul"),
        ("Charger chahiye urgent", "Amit"), ("Order kaise karun?", "Priya"),
        ("Delivery hogi kya?", "Rahul"), ("Ghar pe delivery ho jayegi?", "Amit"),
        ("Store se pickup kar sakta hoon?", "Priya"), ("Delivery charge kitna hai?", "Rahul"),
        ("Free delivery hai?", "Amit"), ("Kitne din mein delivery hogi?", "Priya"),
        ("Same day delivery hai?", "Rahul"), ("Order track kaise karun?", "Amit"),
        ("Mera order kab aayega?", "Priya"), ("Order cancel karna hai", "Rahul"),
        ("Order return karna hai", "Amit"), ("Exchange ho jayega?", "Priya"),
        ("2 piece SSD chahiye", "Rahul"), ("3 mouse order karna hai", "Amit"),
        ("5 keyboard chahiye", "Priya"), ("10 USB hub chahiye", "Rahul"),
        ("Bulk order karna hai", "Amit"), ("Wholesale milega?", "Priya"),
        ("Party order hai", "Rahul"), ("Office ke liye order karna hai", "Amit"),
        ("Delivery address dena hai", "Priya"), ("Address change karna hai", "Rahul"),
        ("Order modify karna hai", "Amit"), ("Quantity badhani hai", "Priya"),
        ("Order confirm ho gaya?", "Rahul"), ("Order processing hai?", "Amit"),
        ("Order shipped ho gaya?", "Priya"), ("Order delivered ho gaya?", "Rahul"),
        ("Order ID kya hai?", "Amit"), ("Tracking number kya hai?", "Priya"),
        ("Delivery boy ka number?", "Rahul"), ("Delivery time kya hai?", "Amit"),
        ("Morning delivery hogi?", "Priya"), ("Evening delivery hogi?", "Rahul"),
        ("Night delivery hogi?", "Amit"), ("Express delivery hai?", "Priya"),
        ("Next day delivery hai?", "Rahul"), ("2 day delivery hai?", "Amit"),
        ("COD available hai?", "Priya"), ("Prepaid order karna hai", "Rahul"),
        ("Gift wrap kar doge?", "Amit"), ("Packing achhi hogi?", "Priya"),
        ("Fragile item hai", "Rahul"), ("Insurance milega?", "Amit"),
    ],

    # ──────────────────────────────────────────────
    # 10. PAYMENT (40 tests)
    # ──────────────────────────────────────────────
    "PAYMENT_QUERIES": [
        ("Payment kaise karun?", "Rahul"), ("UPI se payment ho jayegi?", "Amit"),
        ("Cash de sakta hoon?", "Priya"), ("Card se payment ho jayegi?", "Rahul"),
        ("PhonePe se pay kar sakta hoon?", "Amit"), ("Google Pay chalega?", "Priya"),
        ("Paytm se payment?", "Rahul"), ("EMI available hai?", "Amit"),
        ("Installment mein payment?", "Priya"), ("Advance dena padega?", "Rahul"),
        ("Kitna advance dena hoga?", "Amit"), ("Baad mein payment kar sakta hoon?", "Priya"),
        ("Bill dena", "Rahul"), ("Invoice chahiye", "Amit"), ("Receipt dena", "Priya"),
        ("GST bill milega?", "Rahul"), ("GST number kya hai?", "Amit"),
        ("Payment link bhejo", "Rahul"), ("QR code bhejo", "Amit"),
        ("UPI ID kya hai?", "Priya"), ("Bank account hai?", "Rahul"),
        ("Cheque se payment?", "Amit"), ("NEFT se payment?", "Priya"),
        ("RTGS se payment?", "Rahul"), ("Online payment hai?", "Amit"),
        ("Payment gateway hai?", "Priya"), ("Payment secure hai?", "Rahul"),
        ("Payment refund kab milega?", "Amit"), ("Payment failed ho gaya", "Priya"),
        ("Payment pending hai", "Rahul"), ("Payment confirmed hai?", "Amit"),
        ("Payment receipt bhejo", "Priya"), ("Payment history dekhni hai", "Rahul"),
        ("Payment due hai?", "Amit"), ("Payment overdue hai?", "Priya"),
        ("Payment extension milegi?", "Rahul"), ("Payment plan hai?", "Amit"),
        ("Financing available hai?", "Priya"), ("Loan pe milega?", "Rahul"),
        ("Credit card se EMI?", "Amit"),
    ],

    # ──────────────────────────────────────────────
    # 11. WARRANTY/GUARANTEE (30 tests)
    # ──────────────────────────────────────────────
    "WARRANTY_QUERIES": [
        ("Warranty hai kya?", "Rahul"), ("Guarantee kitne din ki hai?", "Amit"),
        ("Warranty period kitna hai?", "Priya"), ("Repair pe warranty milegi?", "Rahul"),
        ("SSD pe warranty hai?", "Amit"), ("RAM pe guarantee hai?", "Priya"),
        ("Warranty card milega?", "Rahul"), ("Warranty claim kaise karun?", "Amit"),
        ("Warranty expire ho gayi", "Priya"), ("Extended warranty hai?", "Rahul"),
        ("Warranty mein free repair hoga?", "Amit"), ("Warranty terms kya hain?", "Priya"),
        ("Warranty register kaise karun?", "Rahul"), ("Warranty check kaise karun?", "Amit"),
        ("Warranty number kya hai?", "Priya"), ("Warranty center kahan hai?", "Rahul"),
        ("Warranty mein replacement hoga?", "Amit"), ("Warranty mein refund hoga?", "Priya"),
        ("Warranty transfer ho sakti hai?", "Rahul"), ("Warranty international hai?", "Amit"),
        ("Warranty online check hogi?", "Priya"), ("Warranty document chahiye", "Rahul"),
        ("Warranty receipt chahiye", "Amit"), ("Warranty certificate chahiye", "Priya"),
        ("Warranty policy kya hai?", "Rahul"), ("Warranty exclude kya hai?", "Amit"),
        ("Warranty mein accidental damage?", "Priya"), ("Warranty mein liquid damage?", "Rahul"),
        ("Warranty mein physical damage?", "Amit"), ("Warranty mein software issue?", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 12. STATUS/TRACKING (20 tests)
    # ──────────────────────────────────────────────
    "STATUS_QUERIES": [
        ("Mera laptop repair ho gaya?", "Rahul"), ("Laptop kab milega?", "Amit"),
        ("Repair ka status kya hai?", "Priya"), ("Data recovery ho gayi?", "Rahul"),
        ("Screen replacement ho gaya?", "Amit"), ("Status check karna hai", "Priya"),
        ("Kaam ho gaya kya?", "Rahul"), ("Kab tak milega laptop?", "Amit"),
        ("Aaj milega kya?", "Priya"), ("Kal milega kya?", "Rahul"),
        ("2 din ho gaye", "Amit"), ("1 hafte ho gaya", "Priya"),
        ("Jaldi karo na", "Rahul"), ("Kitna time aur lagega?", "Amit"),
        ("Progress kya hai?", "Priya"), ("Update do", "Rahul"),
        ("Status batao", "Amit"), ("Kaam chal raha hai?", "Priya"),
        ("Kaam start hua?", "Rahul"), ("Kaam complete hua?", "Amit"),
    ],

    # ──────────────────────────────────────────────
    # 13. COMPLAINT/REFUND (25 tests)
    # ──────────────────────────────────────────────
    "COMPLAINT_REFUND": [
        ("Repair sahi nahi hua", "Rahul"), ("Problem phir se aa gayi", "Amit"),
        ("Kaam achha nahi hua", "Priya"), ("Complaint karna hai", "Rahul"),
        ("Paisa waste ho gaya", "Amit"), ("Dubse repair karna padega", "Priya"),
        ("Kharab kaam hua hai", "Rahul"), ("Manager se baat karni hai", "Amit"),
        ("Refund chahiye", "Priya"), ("Paise wapas chahiye", "Rahul"),
        ("Consumer court mein jaunga", "Amit"), ("Social media pe daalunga", "Priya"),
        ("Review likhna hai", "Rahul"), ("1 star dunga", "Amit"),
        ("Service kharab hai", "Priya"), ("Technician achha nahi tha", "Rahul"),
        ("Part duplicate lagaya", "Amit"), ("Original part nahi lagaya", "Priya"),
        ("Charge zyada liya", "Rahul"), ("Overcharge kiya", "Amit"),
        ("Time pe nahi hua", "Priya"), ("Deadline miss ho gayi", "Rahul"),
        ("Promise nahi nibhaya", "Amit"), ("Guarantee nahi mili", "Priya"),
        ("Warranty nahi mili", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 14. NON-BUSINESS (25 tests)
    # ──────────────────────────────────────────────
    "NON_BUSINESS": [
        ("Joke sunao", "Rahul"), ("Gaana gao", "Amit"), ("Mausam kaisa hai?", "Priya"),
        ("Cricket score kya hai?", "Rahul"), ("News kya hai?", "Amit"),
        ("Translate karo", "Priya"), ("Shayari sunao", "Rahul"), ("Kahani sunao", "Amit"),
        ("Movie recommend karo", "Priya"), ("Game khelte ho?", "Rahul"),
        ("Instagram pe ho?", "Amit"), ("Facebook pe ho?", "Priya"),
        ("Twitter pe ho?", "Rahul"), ("YouTube channel hai?", "Amit"),
        ("TikTok pe ho?", "Priya"), ("Snapchat pe ho?", "Rahul"),
        ("WhatsApp pe ho?", "Amit"), ("Telegram pe ho?", "Priya"),
        ("Dating app use karte ho?", "Rahul"), ("Relationship advice do", "Amit"),
        ("Health tips do", "Priya"), ("Diet plan batao", "Rahul"),
        ("Exercise batao", "Amit"), ("Yoga batao", "Priya"),
        ("Astrology batao", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 15. THANKS (15 tests)
    # ──────────────────────────────────────────────
    "THANKS": [
        ("Thank you", "Rahul"), ("Shukriya", "Amit"), ("Thanks bhai", "Priya"),
        ("Dhanyavaad", "Rahul"), ("Bahut shukriya", "Amit"), ("Thanks a lot", "Priya"),
        ("Thank you so much", "Rahul"), ("Bohot bohot shukriya", "Amit"),
        ("Thanks ji", "Priya"), ("Thank you sir", "Rahul"),
        ("Thanks for help", "Amit"), ("Thanks for support", "Priya"),
        ("Appreciate it", "Rahul"), ("Great service", "Amit"),
        ("Bahut achha kaam kiya", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 16. EDGE CASES (40 tests)
    # ──────────────────────────────────────────────
    "EDGE_CASES": [
        ("?", "Rahul"), ("kya", "Amit"), ("hai", "Priya"), ("hello", "Rahul"),
        ("ok", "Amit"), ("hmm", "Priya"), ("theek hai", "Rahul"), ("achha", "Amit"),
        ("haan", "Priya"), ("nahi", "Rahul"), ("bye", "Amit"), ("good night", "Priya"),
        ("tata", "Rahul"), ("chal bye", "Amit"), ("ok bye", "Priya"),
        ("...", "Rahul"), ("??? ", "Amit"), ("!!!", "Priya"), ("huh", "Rahul"),
        ("what", "Amit"), ("why", "Priya"), ("how", "Rahul"), ("when", "Amit"),
        ("where", "Priya"), ("who", "Rahul"), ("which", "Amit"), ("ok ok", "Priya"),
        ("hmm hmm", "Rahul"), ("achha achha", "Amit"), ("haan haan", "Priya"),
        ("theek theek", "Rahul"), ("ok ok ok", "Amit"), ("hmm hmm hmm", "Priya"),
        ("123", "Rahul"), ("abc", "Amit"), ("xyz", "Priya"), ("test", "Rahul"),
        ("testing", "Amit"), ("check", "Priya"), ("ping", "Rahul"),
    ],

    # ──────────────────────────────────────────────
    # 17. MULTI-LANGUAGE - Hindi (30 tests)
    # ──────────────────────────────────────────────
    "HINDI_QUERIES": [
        ("Mera laptop kharab ho gaya hai", "Rahul"), ("Laptop theek karwana hai", "Amit"),
        ("Screen toot gayi hai", "Priya"), ("Data recover karna hai", "Rahul"),
        ("Windows install karna hai", "Amit"), ("Virus hatana hai", "Priya"),
        ("Printer kaam nahi kar raha", "Rahul"), ("SSD chahiye", "Amit"),
        ("RAM chahiye 8GB", "Priya"), ("Charger chahiye", "Rahul"),
        ("Kitna charge lagega?", "Amit"), ("Price kya hai?", "Priya"),
        ("Warranty hai?", "Rahul"), ("Delivery hogi?", "Amit"),
        ("Payment kaise karun?", "Priya"), ("Order karna hai", "Rahul"),
        ("Booking karni hai", "Amit"), ("Slot chahiye", "Priya"),
        ("Timing kya hai?", "Rahul"), ("Kab aa sakta hoon?", "Amit"),
        ("Kitne din lagega?", "Priya"), ("Jaldi karo", "Rahul"),
        ("Status batao", "Amit"), ("Complaint karni hai", "Priya"),
        ("Refund chahiye", "Rahul"), ("Exchange hoga?", "Amit"),
        ("Return kar sakta hoon?", "Priya"), ("Cancel karna hai", "Rahul"),
        ("Track kaise karun?", "Amit"), ("Bill dena", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 18. MULTI-LANGUAGE - English (30 tests)
    # ──────────────────────────────────────────────
    "ENGLISH_QUERIES": [
        ("My laptop is not working", "John"), ("I need laptop repair", "Sarah"),
        ("Screen is broken", "Mike"), ("I want to recover data", "John"),
        ("Install Windows please", "Sarah"), ("Remove virus from laptop", "Mike"),
        ("Printer is not working", "John"), ("Do you have SSD?", "Sarah"),
        ("I need 8GB RAM", "Mike"), ("Where can I get a charger?", "John"),
        ("How much does it cost?", "Sarah"), ("What is the price?", "Mike"),
        ("Is there warranty?", "John"), ("Do you deliver?", "Sarah"),
        ("How to make payment?", "Mike"), ("I want to order", "John"),
        ("I want to book appointment", "Sarah"), ("What slots are available?", "Mike"),
        ("What are your timings?", "John"), ("When can I come?", "Sarah"),
        ("How long will it take?", "Mike"), ("Please hurry", "John"),
        ("What is the status?", "Sarah"), ("I want to complain", "Mike"),
        ("I need refund", "John"), ("Can I exchange?", "Sarah"),
        ("Can I return?", "Mike"), ("Cancel my order", "John"),
        ("How to track?", "Sarah"), ("Give me bill", "Mike"),
    ],

    # ──────────────────────────────────────────────
    # 19. MULTI-LANGUAGE - Marathi (20 tests)
    # ──────────────────────────────────────────────
    "MARATHI_QUERIES": [
        ("Maza laptop bigadla aahe", "Rahul"), ("Laptop theek karaycha aahe", "Amit"),
        ("Screen todli aahe", "Priya"), ("Data recover karaycha aahe", "Rahul"),
        ("Windows install karaycha aahe", "Amit"), ("Virus kadhyaycha aahe", "Priya"),
        ("Printer kaam nahi karto", "Rahul"), ("SSD pahije", "Amit"),
        ("RAM pahije 8GB", "Priya"), ("Charger pahije", "Rahul"),
        ("Kiti charge lagel?", "Amit"), ("Kimmat kiti?", "Priya"),
        ("Warranty aahe?", "Rahul"), ("Delivery hoil?", "Amit"),
        ("Payment kasa karu?", "Priya"), ("Order karaycha aahe", "Rahul"),
        ("Booking karaychi aahe", "Amit"), ("Slot pahije", "Rahul"),
        ("Timing kiti?", "Amit"), ("Kadhi yeu shakto?", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 20. MULTI-LANGUAGE - Gujarati (20 tests)
    # ──────────────────────────────────────────────
    "GUJARATI_QUERIES": [
        ("Maro laptop bigadi gayo chhe", "Rahul"), ("Laptop theek karvano chhe", "Amit"),
        ("Screen todi gayi chhe", "Priya"), ("Data recover karvano chhe", "Rahul"),
        ("Windows install karvano chhe", "Amit"), ("Virus kadhvano chhe", "Priya"),
        ("Printer kaam nathi karto", "Rahul"), ("SSD joie chhe", "Amit"),
        ("RAM joie chhe 8GB", "Priya"), ("Charger joie chhe", "Rahul"),
        ("Kitla charge thase?", "Amit"), ("Bhav kiti chhe?", "Priya"),
        ("Warranty chhe?", "Rahul"), ("Delivery thase?", "Amit"),
        ("Payment kavi karish?", "Priya"), ("Order karvano chhe", "Rahul"),
        ("Booking karvi chhe", "Amit"), ("Slot joie chhe", "Rahul"),
        ("Timing kiti chhe?", "Amit"), ("Kyaare aavi shaku?", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 21. COMPLEX SCENARIOS (50 tests)
    # ──────────────────────────────────────────────
    "COMPLEX_SCENARIOS": [
        ("Mera laptop kharab hai aur mujhe urgent data recover karna hai", "Rahul"),
        ("Screen toot gayi hai aur warranty bhi expire ho gayi hai", "Amit"),
        ("Laptop slow hai aur virus bhi hai", "Priya"),
        ("SSD chahiye aur installation bhi karwani hai", "Rahul"),
        ("RAM upgrade karna hai aur SSD bhi dalwana hai", "Amit"),
        ("Printer repair karwana hai aur cartridge bhi change karna hai", "Priya"),
        ("Laptop ka hinge toot gaya hai aur screen bhi flicker kar rahi hai", "Rahul"),
        ("Battery drain ho rahi hai aur charger bhi kaam nahi kar raha", "Amit"),
        ("WiFi kaam nahi kar raha aur Bluetooth bhi connect nahi ho raha", "Priya"),
        ("Keyboard kharab hai aur touchpad bhi kaam nahi kar raha", "Rahul"),
        ("Data recovery karwani hai aur phir Windows bhi install karna hai", "Amit"),
        ("Screen replacement karwani hai aur phir keyboard bhi change karna hai", "Priya"),
        ("Laptop repair karwana hai aur SSD bhi dalwana hai", "Rahul"),
        ("Virus removal karwana hai aur phir antivirus bhi install karna hai", "Amit"),
        ("Motherboard repair karwana hai aur RAM bhi upgrade karna hai", "Priya"),
        ("Mera budget 5000 hai, kya kya ho sakta hai?", "Rahul"),
        ("Mera budget 10000 hai, full repair ho jayega?", "Amit"),
        ("Mera budget 2000 hai, sirf zaruri kaam karo", "Priya"),
        ("Pehle data recover karo, phir Windows install karo", "Rahul"),
        ("Pehle screen change karo, phir keyboard change karo", "Amit"),
        ("Aaj hi chahiye, kal kaam pe jaana hai", "Rahul"),
        ("Emergency hai, 2 ghante mein chahiye", "Amit"),
        ("Kal subah tak chahiye, presentation hai", "Priya"),
        ("Monday tak chahiye, client meeting hai", "Rahul"),
        ("1 hafte mein chahiye, koi jaldi nahi", "Amit"),
        ("Mujhe 2 laptops repair karwane hain", "Priya"),
        ("Mere poore office ke laptops repair karwane hain", "Rahul"),
        ("School ke liye 10 laptops repair karwane hain", "Amit"),
        ("Mera purana laptop hai, kya karein?", "Priya"),
        ("Naya laptop hai, warranty mein hai", "Rahul"),
        ("Refurbished laptop hai, kya repair hoga?", "Amit"),
        ("Gaming laptop hai, special repair chahiye?", "Priya"),
        ("MacBook hai, repair kar sakte ho?", "Rahul"),
        ("Chromebook hai, repair kar sakte ho?", "Amit"),
        ("Desktop PC hai, repair kar sakte ho?", "Priya"),
        ("All-in-one PC hai, repair kar sakte ho?", "Rahul"),
        ("Server hai, repair kar sakte ho?", "Amit"),
        ("Network issue hai, repair kar sakte ho?", "Priya"),
        ("CCTV camera hai, repair kar sakte ho?", "Rahul"),
        ("Projector hai, repair kar sakte ho?", "Amit"),
        ("Scanner hai, repair kar sakte ho?", "Priya"),
        ("UPS hai, repair kar sakte ho?", "Rahul"),
        ("Inverter hai, repair kar sakte ho?", "Amit"),
        ("Mobile phone hai, repair kar sakte ho?", "Priya"),
        ("Tablet hai, repair kar sakte ho?", "Rahul"),
        ("Smartwatch hai, repair kar sakte ho?", "Amit"),
        ("Headphone repair kar sakte ho?", "Priya"),
        ("Speaker repair kar sakte ho?", "Rahul"),
        ("TV repair kar sakte ho?", "Amit"),
        ("AC repair kar sakte ho?", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 22. SHOP OWNER QUERIES (30 tests)
    # ──────────────────────────────────────────────
    "SHOP_OWNER": [
        ("Aaj kitne orders aaye?", "Rahul"), ("Total revenue kitna hai?", "Amit"),
        ("Kitne customers aaye?", "Priya"), ("Stock check karo", "Rahul"),
        ("SSD ka stock kitna hai?", "Amit"), ("RAM ka stock kitna hai?", "Priya"),
        ("Low stock alert hai?", "Rahul"), ("Restock karna hai", "Amit"),
        ("New product add karna hai", "Priya"), ("Price update karna hai", "Rahul"),
        ("Discount laga do", "Amit"), ("Sale lagao", "Priya"),
        ("Report banao", "Rahul"), ("Analytics dikhao", "Amit"),
        ("Customer list dikhao", "Priya"), ("Order history dikhao", "Rahul"),
        ("Payment history dikhao", "Amit"), ("Expense report dikhao", "Priya"),
        ("Profit kitna hai?", "Rahul"), ("Loss kitna hai?", "Amit"),
        ("GST return file karna hai", "Priya"), ("Tax calculation karo", "Rahul"),
        ("Invoice generate karo", "Amit"), ("Receipt generate karo", "Priya"),
        ("Customer feedback dikhao", "Rahul"), ("Rating kya hai?", "Amit"),
        ("Review check karo", "Priya"), ("Complaint list dikhao", "Rahul"),
        ("Pending orders dikhao", "Amit"), ("Completed orders dikhao", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 23. TRICKY QUESTIONS (30 tests)
    # ──────────────────────────────────────────────
    "TRICKY_QUESTIONS": [
        ("Kya tum sach mein AI ho?", "Rahul"), ("Tumhara naam kya hai?", "Amit"),
        ("Tum kahan se ho?", "Priya"), ("Tumhari age kya hai?", "Rahul"),
        ("Tumhe kisne banaya?", "Amit"), ("Tum kya kar sakte ho?", "Priya"),
        ("Tumhare paas kya kya hai?", "Rahul"), ("Sabse sasta kya hai?", "Amit"),
        ("Sabse mehenga kya hai?", "Priya"), ("Best product kya hai?", "Rahul"),
        ("Worst product kya hai?", "Amit"), ("Sabse popular kya hai?", "Priya"),
        ("Naya kya hai?", "Rahul"), ("Purana kya hai?", "Amit"),
        ("Sale mein kya hai?", "Priya"), ("Offer kya hai?", "Rahul"),
        ("Deal kya hai?", "Amit"), ("Combo hai?", "Priya"),
        ("Bundle hai?", "Rahul"), ("Pack hai?", "Amit"),
        ("Set hai?", "Priya"), ("Kit?", "Rahul"),
        ("Accessories hai?", "Amit"), ("Spare parts hai?", "Priya"),
        ("Original parts?", "Rahul"), ("Compatible parts?", "Amit"),
        ("Local parts?", "Priya"), ("OEM parts?", "Rahul"),
        ("Aftermarket parts?", "Amit"), ("Genuine parts?", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 24. EMERGENCY SCENARIOS (20 tests)
    # ──────────────────────────────────────────────
    "EMERGENCY": [
        ("Bahut urgent hai, aaj hi chahiye", "Rahul"), ("Emergency repair hai", "Amit"),
        ("Client meeting hai 2 ghante mein", "Priya"), ("Presentation deni hai kal", "Rahul"),
        ("Exam hai kal, laptop chahiye", "Amit"), ("Office ka kaam atak gaya hai", "Priya"),
        ("Deadline hai aaj", "Rahul"), ("Boss ne daanta", "Amit"),
        ("Project submit karna hai", "Priya"), ("Assignment deni hai", "Rahul"),
        ("Interview hai kal", "Amit"), ("Exam hai 2 din mein", "Priya"),
        ("Wedding photos recover karne hain", "Rahul"), ("Business presentation hai", "Amit"),
        ("Client ka order process karna hai", "Priya"), ("Online class hai", "Rahul"),
        ("Video call hai", "Amit"), ("Webinar hai", "Priya"),
        ("Live stream karna hai", "Rahul"), ("YouTube video upload karna hai", "Amit"),
    ],

    # ──────────────────────────────────────────────
    # 25. BUDGET QUERIES (20 tests)
    # ──────────────────────────────────────────────
    "BUDGET_QUERIES": [
        ("Mera budget 1000 hai", "Rahul"), ("Mera budget 2000 hai", "Amit"),
        ("Mera budget 5000 hai", "Priya"), ("Mera budget 10000 hai", "Rahul"),
        ("Sasta option batao", "Amit"), ("Mehenga option batao", "Priya"),
        ("Budget friendly option?", "Rahul"), ("Cheap mein ho jayega?", "Amit"),
        ("Premium service hai?", "Priya"), ("Basic package kya hai?", "Rahul"),
        ("Standard package kya hai?", "Amit"), ("Advanced package kya hai?", "Priya"),
        ("5000 mein full repair?", "Rahul"), ("2000 mein screen change?", "Amit"),
        ("1000 mein virus removal?", "Priya"), ("500 mein data recovery?", "Rahul"),
        ("EMI pe ho jayega?", "Amit"), ("Installment mein?", "Priya"),
        ("Part payment kar sakta hoon?", "Rahul"), ("Half now half later?", "Amit"),
    ],

    # ──────────────────────────────────────────────
    # 26. COMPARISON QUERIES (20 tests)
    # ──────────────────────────────────────────────
    "COMPARISON_QUERIES": [
        ("SSD ya HDD, kya better hai?", "Rahul"), ("8GB ya 16GB RAM?", "Amit"),
        ("Original ya compatible screen?", "Priya"), ("Branded ya local charger?", "Rahul"),
        ("Wired ya wireless mouse?", "Amit"), ("Mechanical ya normal keyboard?", "Priya"),
        ("Data recovery kaunsi company se?", "Rahul"), ("Screen replacement kaunsi company se?", "Amit"),
        ("SSD kaunsa brand achha hai?", "Priya"), ("RAM kaunsa brand achha hai?", "Rahul"),
        ("Charger kaunsa brand achha hai?", "Amit"), ("Mouse kaunsa brand achha hai?", "Priya"),
        ("Keyboard kaunsa brand achha hai?", "Rahul"), ("Webcam kaunsa brand achha hai?", "Amit"),
        ("Headphone kaunsa brand achha hai?", "Priya"), ("HDMI cable kaunsi achhi hai?", "Rahul"),
        ("USB hub kaunsa achha hai?", "Amit"), ("Thermal paste kaunsa achha hai?", "Priya"),
        ("Laptop repair ya new laptop?", "Rahul"), ("Repair ya replace?", "Amit"),
    ],

    # ──────────────────────────────────────────────
    # 27. TAMIL QUERIES (20 tests)
    # ──────────────────────────────────────────────
    "TAMIL_QUERIES": [
        ("En laptop seri illai", "Rahul"), ("Laptop repair pannanum", "Amit"),
        ("Screen udhirinju pochu", "Priya"), ("Data recover pannanum", "Rahul"),
        ("Windows install pannanum", "Amit"), ("Virus edukkanum", "Priya"),
        ("Printer velaikaravillai", "Rahul"), ("SSD venum", "Amit"),
        ("RAM venum 8GB", "Priya"), ("Charger venum", "Rahul"),
        ("Evvalavu charge aagum?", "Amit"), ("Vilai evvalavu?", "Priya"),
        ("Warranty irukka?", "Rahul"), ("Delivery aaguma?", "Amit"),
        ("Payment eppadi pannuvathu?", "Priya"), ("Order pannanum", "Rahul"),
        ("Booking pannanum", "Amit"), ("Slot venum", "Rahul"),
        ("Timing enna?", "Amit"), ("Eppo varalam?", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 28. TELUGU QUERIES (20 tests)
    # ──────────────────────────────────────────────
    "TELUGU_QUERIES": [
        ("Naa laptop pani cheyatledu", "Rahul"), ("Laptop repair cheyali", "Amit"),
        ("Screen pagilipoyindi", "Priya"), ("Data recover cheyali", "Rahul"),
        ("Windows install cheyali", "Amit"), ("Virus teeseyali", "Priya"),
        ("Printer pani cheyatledu", "Rahul"), ("SSD kavali", "Amit"),
        ("RAM kavali 8GB", "Priya"), ("Charger kavali", "Rahul"),
        ("Entha charge avutundi?", "Amit"), ("Dhara entha?", "Priya"),
        ("Warranty unda?", "Rahul"), ("Delivery avutunda?", "Amit"),
        ("Payment ela cheyyali?", "Priya"), ("Order cheyyali", "Rahul"),
        ("Booking cheyyali", "Amit"), ("Slot kavali", "Rahul"),
        ("Timing enti?", "Amit"), ("Eppudu ravalisindi?", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 29. BENGALI QUERIES (20 tests)
    # ──────────────────────────────────────────────
    "BENGALI_QUERIES": [
        ("Amar laptop kharap hoye geche", "Rahul"), ("Laptop repair korte hobe", "Amit"),
        ("Screen bhenge geche", "Priya"), ("Data recover korte hobe", "Rahul"),
        ("Windows install korte hobe", "Amit"), ("Virus kete hobe", "Priya"),
        ("Printer kaj korchhe na", "Rahul"), ("SSD dorkar", "Amit"),
        ("RAM dorkar 8GB", "Priya"), ("Charger dorkar", "Rahul"),
        ("Koto charge hobe?", "Amit"), ("Dam koto?", "Priya"),
        ("Warranty ache?", "Rahul"), ("Delivery hobe?", "Amit"),
        ("Payment kemon korbo?", "Priya"), ("Order korte hobe", "Rahul"),
        ("Booking korte hobe", "Amit"), ("Slot dorkar", "Rahul"),
        ("Timing koto?", "Amit"), ("Kobe ashte parbo?", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 30. MORE EDGE CASES (30 tests)
    # ──────────────────────────────────────────────
    "MORE_EDGE_CASES": [
        ("A", "Rahul"), ("B", "Amit"), ("Z", "Priya"), ("1", "Rahul"),
        ("2", "Amit"), ("100", "Priya"), ("0", "Rahul"), ("-1", "Amit"),
        ("aaa", "Priya"), ("zzz", "Rahul"), ("111", "Amit"), ("999", "Priya"),
        ("!!", "Rahul"), ("??", "Amit"), ("???", "Priya"), ("...", "Rahul"),
        ("---", "Amit"), ("+++", "Priya"), ("***", "Rahul"), ("###", "Amit"),
        ("@@@", "Priya"), ("$$$", "Rahul"), ("%%%", "Amit"), ("&&&", "Priya"),
        ("|||", "Rahul"), ("~~~", "Amit"), ("^^^", "Priya"), ("```", "Rahul"),
        ("aaa bbb", "Amit"), ("xxx yyy", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 31. MORE COMPLEX SCENARIOS (30 tests)
    # ──────────────────────────────────────────────
    "MORE_COMPLEX": [
        ("Mera laptop 5 saal purana hai, kya repair karwana chahiye?", "Rahul"),
        ("Mera laptop 2 saal purana hai, warranty expire ho gayi hai", "Amit"),
        ("Mera laptop gaming hai, special repair chahiye?", "Priya"),
        ("Mera laptop business hai, data bahut important hai", "Rahul"),
        ("Mera laptop student hai, budget kam hai", "Amit"),
        ("Mera laptop designer hai, color accuracy important hai", "Priya"),
        ("Mera laptop programmer hai, bahut slow hai", "Rahul"),
        ("Mera laptop photographer hai, storage full hai", "Amit"),
        ("Mera laptop video editor hai, RAM kam hai", "Priya"),
        ("Mera laptop music producer hai, audio issue hai", "Rahul"),
        ("Mera laptop trader hai, 24/7 chalna chahiye", "Amit"),
        ("Mera laptop doctor hai, patient data hai", "Priya"),
        ("Mera laptop lawyer hai, confidential files hain", "Rahul"),
        ("Mera laptop teacher hai, online classes leni hain", "Amit"),
        ("Mera laptop engineer hai, CAD software chalana hai", "Priya"),
        ("Mera laptop accountant hai, Tally chalana hai", "Rahul"),
        ("Mera laptop journalist hai, article likhna hai", "Amit"),
        ("Mera laptop blogger hai, content create karna hai", "Priya"),
        ("Mera laptop YouTuber hai, video edit karna hai", "Rahul"),
        ("Mera laptop gamer hai, FPS drop ho raha hai", "Amit"),
        ("Mera laptop streamer hai, OBS crash ho raha hai", "Priya"),
        ("Mera laptop designer hai, Photoshop hang ho raha hai", "Rahul"),
        ("Mera laptop developer hai, Docker nahi chal raha", "Amit"),
        ("Mera laptop data scientist hai, Python slow chal raha", "Priya"),
        ("Mera laptop AI engineer hai, GPU kharab hai", "Rahul"),
        ("Mera laptop security expert hai, VPN nahi chal raha", "Amit"),
        ("Mera laptop network admin hai, WiFi issue hai", "Priya"),
        ("Mera laptop database admin hai, SQL crash ho raha", "Rahul"),
        ("Mera laptop web developer hai, localhost nahi chal raha", "Amit"),
        ("Mera laptop mobile developer hai, emulator nahi chal raha", "Priya"),
    ],

    # ──────────────────────────────────────────────
    # 32. MORE SHOP OWNER (20 tests)
    # ──────────────────────────────────────────────
    "MORE_SHOP_OWNER": [
        ("Aaj ka collection kitna hai?", "Rahul"), ("This week ka revenue?", "Amit"),
        ("Monthly report dikhao", "Priya"), ("Yearly summary dikhao", "Rahul"),
        ("Top selling products kaunse hain?", "Amit"), ("Slow moving products kaunse hain?", "Priya"),
        ("Customer retention rate kya hai?", "Rahul"), ("New customers kitne aaye?", "Amit"),
        ("Repeat customers kitne hain?", "Priya"), ("Average order value kya hai?", "Rahul"),
        ("Profit margin kitna hai?", "Amit"), ("Expense kitna hua?", "Priya"),
        ("Salary kitna diya?", "Rahul"), ("Rent kitna hai?", "Amit"),
        ("Electricity bill kitna hai?", "Priya"), ("Internet bill kitna hai?", "Rahul"),
        ("Maintenance cost kitna hai?", "Amit"), ("Marketing budget kitna hai?", "Priya"),
        ("Advertising karna hai?", "Rahul"), ("Social media pe post karna hai?", "Amit"),
    ],

    # ──────────────────────────────────────────────
    # 33. MORE TRICKY (20 tests)
    # ──────────────────────────────────────────────
    "MORE_TRICKY": [
        ("Kya tum mujhe chutiya bana rahe ho?", "Rahul"), ("Tumhara boss kaun hai?", "Amit"),
        ("Tumhe kitni salary milti hai?", "Priya"), ("Tum kahan kaam karte ho?", "Rahul"),
        ("Tumhara address kya hai?", "Amit"), ("Tumhara phone number kya hai?", "Priya"),
        ("Tumse baat karke achha laga", "Rahul"), ("Tum bahut helpful ho", "Amit"),
        ("Tum best ho", "Priya"), ("Tumhari service achhi hai", "Rahul"),
        ("Tumhe 5 star dunga", "Amit"), ("Tumhare baare mein bolunga", "Priya"),
        ("Tumhe recommend karunga", "Rahul"), ("Tumhara review likhna hai", "Amit"),
        ("Tumhari tareef karni hai", "Priya"), ("Tumhe gift dena hai", "Rahul"),
        ("Tumhe party deni hai", "Amit"), ("Tumhara birthday kab hai?", "Priya"),
        ("Tumhara favorite color kya hai?", "Rahul"), ("Tumhara favorite food kya hai?", "Amit"),
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
                reply = get_fallback_reply(msg, name, REPAIR_SHOP)
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
