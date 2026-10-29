"""English / हिन्दी / Hinglish. Every UI string is written in English in the code and wrapped in t();
this table holds (Hindi, Hinglish). A missing entry falls back to English.
Check coverage after adding UI text: python -m core.i18n"""
LANGS = {"en": "English", "hi": "हिन्दी", "hing": "Hinglish"}

T = {
    # app / login
    "dealership dashboard": ("डीलरशिप डैशबोर्ड", "dealership dashboard"),
    "Username": ("यूज़रनेम", "Username"),
    "Password": ("पासवर्ड", "Password"),
    "Sign in": ("लॉग इन करें", "Login karein"),
    "Sign out": ("लॉग आउट", "Logout"),
    "Wrong username or password": ("यूज़रनेम या पासवर्ड गलत है", "Username ya password galat hai"),
    "Demo logins (password **demo**): `admin`, `parts`, `sales`, `service`. Data is synthetic.":
        ("डेमो लॉगिन (पासवर्ड **demo**): `admin`, `parts`, `sales`, `service`. डेटा नकली है।",
         "Demo login (password **demo**): `admin`, `parts`, `sales`, `service`. Data nakli hai."),
    "This module is next on the roadmap. Parts came first because shortages hurt most.":
        ("यह मॉड्यूल अगले चरण में आएगा। पार्ट्स पहले बना क्योंकि कमी से सबसे ज़्यादा नुकसान होता है।",
         "Yeh module agle phase mein aayega. Parts pehle bana kyunki shortage se sabse zyada nuksaan hota hai."),
    # modules and roles
    "Parts": ("पार्ट्स", "Parts"), "Sales": ("सेल्स", "Sales"), "Service": ("सर्विस", "Service"),
    "Users": ("यूज़र्स", "Users"),
    "admin": ("एडमिन", "admin"), "parts": ("पार्ट्स", "parts"), "sales": ("सेल्स", "sales"),
    "service": ("सर्विस", "service"),
    # parts page header
    "Demand history up to {m} · {n} parts, {r} regular · forecast for {target} · refits whenever data changes":
        ("{m} तक की बिक्री · {n} पार्ट्स, {r} रेगुलर · {target} का अनुमान · नया डेटा आते ही अपडेट होता है",
         "{m} tak ki demand history · {n} parts, {r} regular · {target} ka forecast · naya data aate hi update hota hai"),
    "{n} regular parts are out of stock right now.":
        ("{n} रेगुलर पार्ट्स अभी स्टॉक में नहीं हैं।", "{n} regular parts abhi stock mein nahi hain."),
    "Note: latest HiRise export is {m}. Upload newer months for a better forecast.":
        ("ध्यान दें: आखिरी HiRise एक्सपोर्ट {m} का है। बेहतर अनुमान के लिए नए महीने अपलोड करें।",
         "Dhyan dein: last HiRise export {m} ka hai. Better forecast ke liye naye mahine upload karein."),
    # tabs
    "Order list": ("ऑर्डर लिस्ट", "Order list"), "Counter log": ("काउंटर रजिस्टर", "Counter log"),
    "Part trend": ("पार्ट ट्रेंड", "Part trend"), "Daily report": ("रोज़ की रिपोर्ट", "Daily report"),
    "Dead stock": ("डेड स्टॉक", "Dead stock"), "Upload HiRise": ("HiRise अपलोड", "HiRise upload"),
    "Accuracy": ("सटीकता", "Accuracy"),
    # order list
    "Lines to order": ("ऑर्डर करने वाले आइटम", "Order karne wale items"),
    "Order value": ("ऑर्डर की कीमत", "Order value"),
    "Out of stock / runs out in 7 days": ("स्टॉक खत्म / 7 दिन में खत्म", "Stock khatam / 7 din mein khatam"),
    "Lost sales logged (open)": ("छूटी बिक्री (इस महीने)", "Lost sales (is mahine)"),
    "Ordering settings": ("ऑर्डर सेटिंग्स", "Order settings"),
    "Days from order to delivery (Honda lead time)":
        ("ऑर्डर से डिलीवरी तक के दिन (Honda लीड टाइम)", "Order se delivery tak ke din (Honda lead time)"),
    "Days between orders": ("दो ऑर्डर के बीच के दिन", "Do order ke beech ke din"),
    "Safety level": ("सुरक्षा स्तर", "Safety level"),
    "Lean (84%)": ("कम (84%)", "Kam (84%)"), "Normal (90%)": ("सामान्य (90%)", "Normal (90%)"),
    "Safe (95%)": ("सुरक्षित (95%)", "Safe (95%)"), "Very safe (98%)": ("बहुत सुरक्षित (98%)", "Bahut safe (98%)"),
    "A part is 'regular' if it sells in at least this many of 12 months":
        ("पार्ट 'रेगुलर' है अगर वह 12 में से कम से कम इतने महीने बिके",
         "Part 'regular' hai agar 12 mein se kam se kam itne mahine bike"),
    "Regular parts are kept on the shelf. Others are ordered only when a customer asks.":
        ("रेगुलर पार्ट्स हमेशा स्टॉक में रखें। बाकी तभी मंगाएं जब ग्राहक मांगे।",
         "Regular parts hamesha stock mein rakhein. Baaki tabhi mangayein jab customer maange."),
    "Save settings": ("सेटिंग्स सेव करें", "Settings save karein"),
    "parts": ("पार्ट्स", "parts"),
    "Part no.": ("पार्ट नंबर", "Part no."), "Description": ("विवरण", "Description"), "Why": ("क्यों", "Kyun"),
    "regular": ("रेगुलर", "regular"), "customer asked": ("ग्राहक ने मांगा", "customer ne maanga"),
    "In stock": ("स्टॉक में", "Stock mein"), "Sells / month": ("बिक्री / महीना", "Bikri / mahina"),
    "Days left": ("बचे दिन", "Bache din"),
    "At the current sales pace": ("अभी की बिक्री की रफ़्तार से", "Abhi ki bikri ki speed se"),
    "Order qty": ("ऑर्डर मात्रा", "Order qty"), "Unit ₹": ("एक का ₹", "Ek ka ₹"), "Value ₹": ("कुल ₹", "Total ₹"),
    "Download order list (CSV)": ("ऑर्डर लिस्ट डाउनलोड करें (CSV)", "Order list download karein (CSV)"),
    # counter log
    "Say what happened at the counter. Hold your Wispr key and talk, or type.":
        ("काउंटर पर क्या हुआ, बोलें। Wispr का बटन दबाकर बोलें, या टाइप करें।",
         "Counter pe kya hua, bolein. Wispr key daba ke bolein, ya type karein."),
    "Example: customer wanted 2 brake shoes, we didn't have them":
        ("उदाहरण: ग्राहक को 2 ब्रेक शू चाहिए थे, हमारे पास नहीं थे",
         "Example: customer ko 2 brake shoe chahiye the, humare paas nahi the"),
    "Part": ("पार्ट", "Part"),
    "Best matches for what you said come first": ("आपने जो कहा, उससे मिलते पार्ट्स पहले दिखेंगे",
                                                  "Aapne jo bola, usse milte parts pehle dikhenge"),
    "Qty": ("मात्रा", "Qty"),
    "Lost sale (we didn't have it)": ("छूटी बिक्री (हमारे पास नहीं था)", "Lost sale (humare paas nahi tha)"),
    "Sold": ("बेचा", "Becha"), "Received from Honda": ("Honda से आया", "Honda se aaya"),
    "What happened": ("क्या हुआ", "Kya hua"), "Date": ("तारीख", "Date"), "Save": ("सेव करें", "Save karein"),
    "Saved: {what} · {qty} × {part}": ("सेव हुआ: {what} · {qty} × {part}", "Save hua: {what} · {qty} × {part}"),
    "Today": ("आज", "Aaj"),
    # part trend
    "Forecast / month": ("अनुमान / महीना", "Forecast / mahina"),
    "Typical swing (±)": ("आम उतार-चढ़ाव (±)", "Aam utaar-chadhaav (±)"),
    "Unit price": ("एक की कीमत", "Ek ki keemat"), "Regular?": ("रेगुलर?", "Regular?"),
    "Yes": ("हाँ", "Haan"), "No": ("नहीं", "Nahi"), "months": ("महीने", "mahine"),
    "Demand (sold + lost)": ("मांग (बिकी + छूटी)", "Demand (biki + chhooti)"),
    "Festive month": ("त्योहार का महीना", "Tyohaar ka mahina"),
    "units / month": ("नग / महीना", "nag / mahina"),
    "Blank months are ones where demand couldn't be seen (no stock at all, or COVID lockdown).":
        ("खाली महीनों में मांग नहीं दिख सकी (स्टॉक ही नहीं था, या कोविड लॉकडाउन)।",
         "Khaali mahino mein demand nahi dikh saki (stock hi nahi tha, ya COVID lockdown)."),
    # daily report
    "Report language": ("रिपोर्ट की भाषा", "Report ki bhasha"),
    "Generate report": ("रिपोर्ट बनाएं", "Report banayein"),
    "Copy and paste into WhatsApp, or send it by email.":
        ("कॉपी करके WhatsApp में भेजें, या ईमेल करें।", "Copy karke WhatsApp pe bhejein, ya email karein."),
    "Email is not set up yet. An admin adds SMTP settings and recipients on the Users page.":
        ("ईमेल अभी सेट नहीं है। एडमिन यूज़र्स पेज पर SMTP सेटिंग्स और ईमेल पते डालें।",
         "Email abhi set nahi hai. Admin Users page pe SMTP settings aur email IDs daalein."),
    "No recipients yet. An admin adds them on the Users page.":
        ("अभी कोई ईमेल पता नहीं है। एडमिन यूज़र्स पेज पर जोड़ें।", "Abhi koi email ID nahi hai. Admin Users page pe add karein."),
    "Send report": ("रिपोर्ट भेजें", "Report bhejein"),
    "Sent to {to}": ("भेजी गई: {to}", "Bhej di: {to}"),
    "Could not send: {err}": ("नहीं भेज पाए: {err}", "Bhej nahi paaye: {err}"),
    "Parts report": ("पार्ट्स रिपोर्ट", "Parts report"),
    "Lost sales today: {n}": ("आज छूटी बिक्री: {n}", "Aaj ki lost sales: {n}"),
    "Sold today (logged): {n}": ("आज बिका (दर्ज): {n}", "Aaj bika (log kiya): {n}"),
    "Order list: {n} lines, ₹{v}": ("ऑर्डर लिस्ट: {n} आइटम, ₹{v}", "Order list: {n} items, ₹{v}"),
    "Regular parts out of stock: {n} of {total}": ("स्टॉक में नहीं (रेगुलर पार्ट्स): {total} में से {n}",
                                                   "Stock khatam (regular parts): {total} mein se {n}"),
    "Running out within 7 days: {n}": ("7 दिन में खत्म होने वाले: {n}", "7 din mein khatam hone wale: {n}"),
    "stock": ("स्टॉक", "stock"),
    # dead stock / upload
    "Money stuck in parts that haven't sold in 12 months":
        ("12 महीने से न बिके पार्ट्स में फंसा पैसा", "12 mahine se na bike parts mein phansa paisa"),
    "Upload one or more **Month Wise Stock Report (Detailed)** exports. Re-uploading a month replaces it.":
        ("एक या ज़्यादा **Month Wise Stock Report (Detailed)** एक्सपोर्ट अपलोड करें। वही महीना दोबारा डालने पर पुराना बदल जाएगा।",
         "Ek ya zyada **Month Wise Stock Report (Detailed)** export upload karein. Wahi mahina dobara daalne pe purana replace hoga."),
    "HiRise exports": ("HiRise एक्सपोर्ट", "HiRise exports"),
    "Add to history": ("हिस्ट्री में जोड़ें", "History mein add karein"),
    "Added {months}. The model refit. Biggest changes in its forecast:":
        ("{months} जुड़ गया। मॉडल ने दोबारा सीखा। अनुमान में सबसे बड़े बदलाव:",
         "{months} add ho gaya. Model ne dobara seekha. Forecast mein sabse bade badlaav:"),
    "Before / month": ("पहले / महीना", "Pehle / mahina"), "Now / month": ("अब / महीना", "Ab / mahina"),
    # accuracy
    "Calendar effects (whole dealership)": ("कैलेंडर का असर (पूरी डीलरशिप)", "Calendar ka asar (poori dealership)"),
    "Annual growth": ("सालाना बढ़त", "Saalana growth"),
    "Festive month (Dhanteras–Diwali)": ("त्योहार का महीना (धनतेरस–दिवाली)", "Tyohaar ka mahina (Dhanteras–Diwali)"),
    "Months of history used": ("कितने महीनों का डेटा", "Kitne mahino ka data"),
    "Each effect switches on only with enough history: growth and month-of-year seasonality need 24 months, "
    "the festive effect needs 2 festive months. Until then it stays at 0%.":
        ("हर असर तभी चालू होता है जब काफ़ी डेटा हो: बढ़त और महीने के हिसाब से मौसम के लिए 24 महीने, त्योहार के असर के लिए "
         "2 त्योहार वाले महीने चाहिए। तब तक यह 0% रहता है।",
         "Har asar tabhi on hota hai jab kaafi data ho: growth aur season ke liye 24 mahine, festive asar ke liye "
         "2 tyohaar wale mahine chahiye. Tab tak yeh 0% rehta hai."),
    "% vs average month": ("% औसत महीने से", "% average mahine se"),
    "Use calendar effects": ("कैलेंडर का असर इस्तेमाल करें", "Calendar ka asar use karein"),
    "Replays the last 6 months: each month, forecast using only what was known then, and compare with what "
    "actually happened next. Scored on regular parts.":
        ("पिछले 6 महीने दोबारा चलाता है: हर महीने सिर्फ़ उस समय तक के डेटा से अनुमान, फिर असली बिक्री से तुलना। "
         "रेगुलर पार्ट्स पर जांच।",
         "Pichhle 6 mahine replay karta hai: har mahine sirf us time tak ke data se forecast, phir asli bikri se "
         "compare. Regular parts pe check."),
    "Run backtest": ("जांच चलाएं", "Backtest chalayein"), "Replaying…": ("चल रहा है…", "Chal raha hai…"),
    "This model": ("यह मॉडल", "Yeh model"), "Without calendar effects": ("कैलेंडर असर के बिना", "Calendar asar ke bina"),
    "'Same as last month'": ("'पिछले महीने जितना'", "'Pichhle mahine jitna'"),
    "6-month average": ("6 महीने का औसत", "6 mahine ka average"),
    "Error per part": ("हर पार्ट पर गलती", "Har part pe error"),
    "Error on total demand": ("कुल मांग पर गलती", "Total demand pe error"),
    "Regular-part stockouts flagged a month ahead": ("रेगुलर पार्ट्स जिनका स्टॉक खत्म होने से एक महीना पहले बताया",
                                                     "Regular parts jinka stock khatam hone se ek mahina pehle bataya"),
    "Months tested: {m}. Error per part is high for any method: a part selling 2 a month sells 0, 4, 1, 3… "
    "The order list protects against that with safety stock.":
        ("जांचे गए महीने: {m}। हर पार्ट की गलती किसी भी तरीके में ज़्यादा रहती है: जो पार्ट महीने में 2 बिकता है वो 0, 4, 1, 3… "
         "बिकता है। ऑर्डर लिस्ट सेफ्टी स्टॉक से इससे बचाती है।",
         "Check kiye mahine: {m}. Har part ka error kisi bhi method mein zyada rehta hai: jo part mahine mein 2 bikta "
         "hai woh 0, 4, 1, 3… bikta hai. Order list safety stock se isse bachati hai."),
    # admin
    "Name": ("नाम", "Naam"), "Role": ("भूमिका", "Role"),
    "User, email and dealership settings are read-only in the public demo.":
        ("पब्लिक डेमो में यूज़र, ईमेल और डीलरशिप सेटिंग्स बदली नहीं जा सकतीं।",
         "Public demo mein user, email aur dealership settings badal nahi sakte."),
    "Add or reset a user": ("यूज़र जोड़ें या पासवर्ड बदलें", "User add karein ya password badlein"),
    "Need a username and a password of at least 6 characters.":
        ("यूज़रनेम और कम से कम 6 अक्षर का पासवर्ड चाहिए।", "Username aur kam se kam 6 character ka password chahiye."),
    "Saved {name}": ("{name} सेव हुआ", "{name} save hua"), "Saved": ("सेव हुआ", "Save hua"),
    "Daily report by email": ("ईमेल से रोज़ की रिपोर्ट", "Email se daily report"),
    "Email login status: {status}": ("ईमेल लॉगिन: {status}", "Email login: {status}"),
    "ready": ("तैयार", "ready"), "not set up": ("सेट नहीं", "set nahi hai"),
    "Put these in .streamlit/secrets.toml on this computer (or in the app's Secrets on Streamlit Cloud).":
        ("इन्हें इस कंप्यूटर पर .streamlit/secrets.toml में डालें (या Streamlit Cloud पर ऐप के Secrets में)।",
         "Inhe is computer pe .streamlit/secrets.toml mein daalein (ya Streamlit Cloud pe app ke Secrets mein)."),
    "Send the report to (one email per line)": ("रिपोर्ट इन्हें भेजें (हर लाइन में एक ईमेल)",
                                               "Report inhe bhejein (har line mein ek email)"),
    "Save email settings": ("ईमेल सेटिंग्स सेव करें", "Email settings save karein"),
    "Not a valid email: {e}": ("सही ईमेल नहीं है: {e}", "Sahi email nahi hai: {e}"),
    "Dealership": ("डीलरशिप", "Dealership"), "Dealership name": ("डीलरशिप का नाम", "Dealership ka naam"),
    "Save name": ("नाम सेव करें", "Naam save karein"),
}

# Spoken Hindi -> words that appear in HiRise part descriptions, for the counter log.
PART_WORDS = {
    "ब्रेक": "brake", "शू": "shoe", "शूज़": "shoe", "तेल": "oil", "ऑयल": "oil", "आयल": "oil", "इंजन": "engine",
    "क्लच": "clutch", "केबल": "cable", "चेन": "chain", "चैन": "chain", "टायर": "tyre", "ट्यूब": "tube",
    "बैटरी": "battery", "प्लग": "plug", "स्पार्क": "spark", "फिल्टर": "filter", "बल्ब": "bulb", "शीशा": "mirror",
    "मिरर": "mirror", "सीट": "seat", "पिस्टन": "piston", "गैस्केट": "gasket", "बेयरिंग": "bearing",
    "हैंडल": "handle", "लीवर": "lever", "स्प्रॉकेट": "sprocket", "किट": "kit", "पैड": "pad", "डिस्क": "disc",
    "हॉर्न": "horn", "इंडिकेटर": "indicator", "लाइट": "light", "हेडलाइट": "headlight", "साइलेंसर": "silencer",
    "कार्बोरेटर": "carburetor", "एयर": "air", "फ्यूल": "fuel", "टंकी": "tank", "टैंक": "tank", "गार्ड": "guard",
    "कवर": "cover", "बेल्ट": "belt", "वाल्व": "valve", "रिंग": "ring", "पंप": "pump", "मीटर": "meter",
    "स्विच": "switch", "लॉक": "lock", "एक्टिवा": "activa", "शाइन": "shine", "ड्रीम": "dream",
    "यूनिकॉर्न": "unicorn", "डियो": "dio", "tel": "oil", "shisha": "mirror", "tanki": "tank",
}
NUMBER_WORDS = {"एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "छः": 6, "सात": 7,
                "आठ": 8, "नौ": 9, "दस": 10}
# What happened, checked in this order. Single words match whole words; phrases match anywhere.
KIND_WORDS = {
    "lost": ["didn't", "did not", "not available", "out of stock", "wanted", "nahi", "nahin", "khatam",
             "chahiye", "नहीं", "खत्म", "चाहिए"],
    "received": ["received", "arrived", "aaya", "aaye", "mila", "aagaya", "आया", "आए", "मिला"],
    "sale": [],
}


def t(text, lang="en", **kw):
    if lang != "en" and text in T:
        text = T[text][0 if lang == "hi" else 1]
    return text.format(**kw) if kw else text


def kind_of(sentence):
    low = sentence.lower()
    tokens = set(split_words(low))
    for kind, ws in KIND_WORDS.items():
        if any((w in low) if (" " in w) else (w in tokens) for w in ws):
            return kind
    return "sale"


def split_words(text):
    """Split on spaces/punctuation only: regex \\w drops Hindi vowel signs and breaks the words."""
    import re
    return [w for w in re.split(r"[\s,.!?।;:()\"]+", text) if w]


if __name__ == "__main__":
    import ast
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parent.parent
    used = {"Order list", "Counter log", "Part trend", "Daily report", "Dead stock", "Upload HiRise", "Accuracy",
            "Sales", "Service", "Users", "Parts", "admin", "parts", "sales", "service", "regular", "customer asked",
            "Lean (84%)", "Normal (90%)", "Safe (95%)", "Very safe (98%)"}
    for f in ["app.py", "modules/parts.py", "modules/admin.py", "core/report.py"]:
        for n in ast.walk(ast.parse((root / f).read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "t" and n.args \
                    and isinstance(n.args[0], ast.Constant):
                used.add(n.args[0].value)
    missing = sorted(used - T.keys())
    assert not missing, f"untranslated: {missing}"
    ph = lambda s: set(re.findall(r"{\w+}", s))  # noqa: E731
    bad = [k for k, (hi, hing) in T.items() if not (ph(k) == ph(hi) == ph(hing))]
    assert not bad, f"placeholders differ: {bad}"
    assert t("Sent to {to}", "hi", to="a@b.c") == "भेजी गई: a@b.c"
    assert kind_of("customer wanted 2 brake shoes, we didn't have them") == "lost"
    assert kind_of("ग्राहक को दो ब्रेक शू चाहिए थे") == "lost"
    assert kind_of("Honda se 5 chain aaya") == "received" and kind_of("2 oil becha gaya") == "sale"
    print(f"i18n ok: {len(used)} strings translated")
