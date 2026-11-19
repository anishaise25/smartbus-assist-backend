"""Spoken-message templates in English (en), Kannada (kn) and Hindi (hi).
Have a native speaker review the kn/hi wording before the final demo."""

SUPPORTED = ("en", "kn", "hi")

MSG = {
    "en": {
        "take_first": "Take bus {bus} from {frm}.",
        "take_next": "Then take bus {bus} from {frm}.",
        "get_off": "Get off at {to} after {stops}.",
        "stops_one": "{n} stop", "stops_other": "{n} stops",
        "total_time": "Total travel time is about {m} minutes.",
        "direct_lead": "Bus {bus} goes directly from {frm} to {to}.",
        "change_lead": "No direct bus. The best option needs {changes}.",
        "changes_one": "{n} change", "changes_other": "{n} changes",
        "options_one": "{n} option found in total.", "options_other": "{n} options found in total.",
        "not_found": "Sorry, I could not find a bus from {frm} to {to}.",
        "arrived": "You have reached {dest}. Please get down.",
        "missed": "You have passed {dest}. Get off at the next stop and take a bus back.",
        "next_stop": "Next stop is {dest}. Get ready to get down.",
        "approaching": "{dest} is {n} stops away.",
        "on_route": "{n} stops to go until {dest}.",
        "ident": "This is bus {bus}, running between {a} and {b}.",
        "low_conf": " I am not fully sure. Please confirm.",
        "unreadable": "I could not read the bus number clearly. Please point the camera at the bus board again.",
        "not_go": " This bus does not go to {dest}.",
        "goes_board": " It goes to {dest}. You can board.",
        "opposite": " It goes to {dest} but runs in the opposite direction from here. Do not board.",
        "sos_sent": "Emergency alert sent to your contacts.",
        "sos_nocontacts": "Emergency alert ready, but you have no emergency contacts saved.",
        "sos_text": "EMERGENCY: I need help. I am {where}. My location: {link}",
        "sos_near": "near {stop} bus stop", "sos_unknown": "at an unknown location",
    },
    "kn": {
        "take_first": "{frm} ನಿಲ್ದಾಣದಿಂದ ಬಸ್ ಸಂಖ್ಯೆ {bus} ಹತ್ತಿ.",
        "take_next": "ನಂತರ {frm} ನಿಲ್ದಾಣದಿಂದ ಬಸ್ ಸಂಖ್ಯೆ {bus} ಹತ್ತಿ.",
        "get_off": "{stops} ನಂತರ {to} ನಲ್ಲಿ ಇಳಿಯಿರಿ.",
        "stops_one": "{n} ನಿಲ್ದಾಣದ", "stops_other": "{n} ನಿಲ್ದಾಣಗಳ",
        "total_time": "ಒಟ್ಟು ಪ್ರಯಾಣದ ಸಮಯ ಸುಮಾರು {m} ನಿಮಿಷ.",
        "direct_lead": "ಬಸ್ ಸಂಖ್ಯೆ {bus} {frm} ನಿಂದ {to} ಗೆ ನೇರವಾಗಿ ಹೋಗುತ್ತದೆ.",
        "change_lead": "ನೇರ ಬಸ್ ಇಲ್ಲ. ಉತ್ತಮ ಮಾರ್ಗಕ್ಕೆ {changes} ಬೇಕು.",
        "changes_one": "{n} ಬಸ್ ಬದಲಾವಣೆ", "changes_other": "{n} ಬಸ್ ಬದಲಾವಣೆಗಳು",
        "options_one": "ಒಟ್ಟು {n} ಆಯ್ಕೆ ಸಿಕ್ಕಿದೆ.", "options_other": "ಒಟ್ಟು {n} ಆಯ್ಕೆಗಳು ಸಿಕ್ಕಿವೆ.",
        "not_found": "ಕ್ಷಮಿಸಿ, {frm} ನಿಂದ {to} ಗೆ ಬಸ್ ಸಿಗಲಿಲ್ಲ.",
        "arrived": "ನೀವು {dest} ತಲುಪಿದ್ದೀರಿ. ದಯವಿಟ್ಟು ಇಳಿಯಿರಿ.",
        "missed": "ನೀವು {dest} ದಾಟಿ ಬಂದಿದ್ದೀರಿ. ಮುಂದಿನ ನಿಲ್ದಾಣದಲ್ಲಿ ಇಳಿದು ಹಿಂದಿರುಗುವ ಬಸ್ ಹತ್ತಿ.",
        "next_stop": "ಮುಂದಿನ ನಿಲ್ದಾಣ {dest}. ಇಳಿಯಲು ಸಿದ್ಧರಾಗಿ.",
        "approaching": "{dest} ಇನ್ನು {n} ನಿಲ್ದಾಣ ದೂರದಲ್ಲಿದೆ.",
        "on_route": "{dest} ತಲುಪಲು ಇನ್ನೂ {n} ನಿಲ್ದಾಣಗಳಿವೆ.",
        "ident": "ಇದು ಬಸ್ ಸಂಖ್ಯೆ {bus}, {a} ಮತ್ತು {b} ನಡುವೆ ಸಂಚರಿಸುತ್ತದೆ.",
        "low_conf": " ನನಗೆ ಪೂರ್ತಿ ಖಚಿತವಿಲ್ಲ. ದಯವಿಟ್ಟು ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ.",
        "unreadable": "ಬಸ್ ಸಂಖ್ಯೆ ಸ್ಪಷ್ಟವಾಗಿ ಓದಲಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಕ್ಯಾಮೆರಾವನ್ನು ಬಸ್ ಫಲಕದ ಕಡೆ ಮತ್ತೆ ತೋರಿಸಿ.",
        "not_go": " ಈ ಬಸ್ {dest} ಗೆ ಹೋಗುವುದಿಲ್ಲ.",
        "goes_board": " ಇದು {dest} ಗೆ ಹೋಗುತ್ತದೆ. ನೀವು ಹತ್ತಬಹುದು.",
        "opposite": " ಇದು {dest} ಗೆ ಹೋಗುತ್ತದೆ ಆದರೆ ಇಲ್ಲಿಂದ ವಿರುದ್ಧ ದಿಕ್ಕಿನಲ್ಲಿ ಹೋಗುತ್ತದೆ. ಹತ್ತಬೇಡಿ.",
        "sos_sent": "ತುರ್ತು ಸಂದೇಶವನ್ನು ನಿಮ್ಮ ಸಂಪರ್ಕಗಳಿಗೆ ಕಳುಹಿಸಲಾಗಿದೆ.",
        "sos_nocontacts": "ತುರ್ತು ಸಂದೇಶ ಸಿದ್ಧವಾಗಿದೆ, ಆದರೆ ನೀವು ಯಾವುದೇ ತುರ್ತು ಸಂಪರ್ಕಗಳನ್ನು ಉಳಿಸಿಲ್ಲ.",
        "sos_text": "ತುರ್ತು: ನನಗೆ ಸಹಾಯ ಬೇಕು. ನಾನು {where} ಇದ್ದೇನೆ. ನನ್ನ ಸ್ಥಳ: {link}",
        "sos_near": "{stop} ಬಸ್ ನಿಲ್ದಾಣದ ಹತ್ತಿರ", "sos_unknown": "ಅಜ್ಞಾತ ಸ್ಥಳದಲ್ಲಿ",
    },
    "hi": {
        "take_first": "{frm} से बस नंबर {bus} लें।",
        "take_next": "फिर {frm} से बस नंबर {bus} लें।",
        "get_off": "{stops} के बाद {to} पर उतरें।",
        "stops_one": "{n} स्टॉप", "stops_other": "{n} स्टॉप",
        "total_time": "कुल यात्रा का समय लगभग {m} मिनट है।",
        "direct_lead": "बस नंबर {bus} {frm} से {to} तक सीधी जाती है।",
        "change_lead": "कोई सीधी बस नहीं है। सबसे अच्छे रास्ते में {changes}।",
        "changes_one": "{n} बार बस बदलनी होगी", "changes_other": "{n} बार बस बदलनी होगी",
        "options_one": "कुल {n} विकल्प मिला।", "options_other": "कुल {n} विकल्प मिले।",
        "not_found": "माफ़ कीजिए, {frm} से {to} के लिए कोई बस नहीं मिली।",
        "arrived": "आप {dest} पहुँच गए हैं। कृपया उतरें।",
        "missed": "आप {dest} से आगे निकल गए हैं। अगले स्टॉप पर उतरकर वापसी की बस लें।",
        "next_stop": "अगला स्टॉप {dest} है। उतरने के लिए तैयार रहें।",
        "approaching": "{dest} अब {n} स्टॉप दूर है।",
        "on_route": "{dest} पहुँचने में अभी {n} स्टॉप बाकी हैं।",
        "ident": "यह बस नंबर {bus} है, जो {a} और {b} के बीच चलती है।",
        "low_conf": " मुझे पूरा यक़ीन नहीं है। कृपया पुष्टि करें।",
        "unreadable": "बस का नंबर साफ़ पढ़ा नहीं गया। कृपया कैमरा बस के बोर्ड की ओर फिर से करें।",
        "not_go": " यह बस {dest} नहीं जाती।",
        "goes_board": " यह {dest} जाती है। आप चढ़ सकते हैं।",
        "opposite": " यह {dest} जाती है, लेकिन यहाँ से उल्टी दिशा में। न चढ़ें।",
        "sos_sent": "आपातकालीन संदेश आपके संपर्कों को भेज दिया गया है।",
        "sos_nocontacts": "आपातकालीन संदेश तैयार है, लेकिन आपने कोई आपातकालीन संपर्क सेव नहीं किया है।",
        "sos_text": "आपातकाल: मुझे मदद चाहिए। मैं {where} हूँ। मेरी लोकेशन: {link}",
        "sos_near": "{stop} बस स्टॉप के पास", "sos_unknown": "किसी अज्ञात जगह पर",
    },
}

STOP_NAMES = {  # English -> (Kannada, Hindi) for the sample stops
    "Majestic": ("ಮೆಜೆಸ್ಟಿಕ್", "मेजेस्टिक"),
    "KR Market": ("ಕೆ.ಆರ್. ಮಾರುಕಟ್ಟೆ", "के.आर. मार्केट"),
    "Shivajinagar": ("ಶಿವಾಜಿನಗರ", "शिवाजीनगर"),
    "MG Road": ("ಎಂ.ಜಿ. ರಸ್ತೆ", "एम.जी. रोड"),
    "Indiranagar": ("ಇಂದಿರಾನಗರ", "इंदिरानगर"),
    "Domlur": ("ಡೊಮ್ಲೂರು", "डोमलूर"),
    "Marathahalli": ("ಮಾರತ್ತಹಳ್ಳಿ", "मराठाहल्ली"),
    "Whitefield": ("ವೈಟ್‌ಫೀಲ್ಡ್", "व्हाइटफ़ील्ड"),
    "Koramangala": ("ಕೋರಮಂಗಲ", "कोरमंगला"),
    "Silk Board": ("ಸಿಲ್ಕ್ ಬೋರ್ಡ್", "सिल्क बोर्ड"),
    "BTM Layout": ("ಬಿಟಿಎಂ ಲೇಔಟ್", "बीटीएम लेआउट"),
    "Jayanagar 4th Block": ("ಜಯನಗರ 4ನೇ ಬ್ಲಾಕ್", "जयनगर चौथा ब्लॉक"),
    "Banashankari": ("ಬನಶಂಕರಿ", "बनशंकरी"),
    "HSR Layout": ("ಎಚ್‌ಎಸ್‌ಆರ್ ಲೇಔಟ್", "एचएसआर लेआउट"),
    "Bellandur": ("ಬೆಳ್ಳಂದೂರು", "बेलंदूर"),
    "Electronic City": ("ಎಲೆಕ್ಟ್ರಾನಿಕ್ ಸಿಟಿ", "इलेक्ट्रॉनिक सिटी"),
    "Hebbal": ("ಹೆಬ್ಬಾಳ", "हेब्बाल"),
    "Mekhri Circle": ("ಮೇಖ್ರಿ ಸರ್ಕಲ್", "मेखरी सर्कल"),
    "Malleshwaram": ("ಮಲ್ಲೇಶ್ವರಂ", "मल्लेश्वरम"),
    "Yeshwanthpur": ("ಯಶವಂತಪುರ", "यशवंतपुर"),
    "Vijayanagar": ("ವಿಜಯನಗರ", "विजयनगर"),
    "Kengeri": ("ಕೆಂಗೇರಿ", "केंगेरी"),
    "Kempegowda Airport": ("ಕೆಂಪೇಗೌಡ ವಿಮಾನ ನಿಲ್ದಾಣ", "केम्पेगौड़ा हवाई अड्डा"),
}


def norm_lang(lang):
    lang = (lang or "en").lower()[:2]
    return lang if lang in SUPPORTED else "en"


def tr(lang, key, **kw):
    return MSG[norm_lang(lang)][key].format(**kw)


def plural(lang, base, n):
    return tr(lang, f"{base}_one" if n == 1 else f"{base}_other", n=n)

MSG["en"]["didnt_understand"] = "Sorry, I did not understand. You can say a place name, or say SOS in an emergency."
MSG["kn"]["didnt_understand"] = "ಕ್ಷಮಿಸಿ, ನನಗೆ ಅರ್ಥವಾಗಲಿಲ್ಲ. ನೀವು ಸ್ಥಳದ ಹೆಸರು ಹೇಳಬಹುದು, ಅಥವಾ ತುರ್ತು ಸಂದರ್ಭದಲ್ಲಿ ಎಸ್‌ಒಎಸ್ ಎಂದು ಹೇಳಿ."
MSG["hi"]["didnt_understand"] = "माफ़ कीजिए, मैं समझ नहीं पाया। आप किसी जगह का नाम बोल सकते हैं, या आपातकाल में एसओएस कहें।"

MSG["en"]["help"] = "You can say a place name to find a bus, say where am I, say repeat, or say SOS in an emergency."
MSG["kn"]["help"] = "ಬಸ್ ಹುಡುಕಲು ಸ್ಥಳದ ಹೆಸರು ಹೇಳಿ, ನಾನು ಎಲ್ಲಿದ್ದೇನೆ ಎಂದು ಕೇಳಿ, ಮತ್ತೆ ಹೇಳಿ ಎನ್ನಿ, ಅಥವಾ ತುರ್ತು ಸಂದರ್ಭದಲ್ಲಿ ಎಸ್‌ಒಎಸ್ ಎಂದು ಹೇಳಿ."
MSG["hi"]["help"] = "बस खोजने के लिए जगह का नाम बोलिए, कहाँ हूँ पूछिए, दोबारा कहिए, या आपातकाल में एसओएस कहिए।"
