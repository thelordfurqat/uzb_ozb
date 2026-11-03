import re

CYR_RUN = re.compile(r"[А-Яа-яЁёЎўҚқҒғҲҳЪъЬьЦц]+")
LAT_RUN = re.compile(r"[A-Za-zÖöĞğŞşÇç’‘`'ʼʻ]+")
CYR_VOWELS = set("аеёиоуўэюя")
APOSTROPHES = set("ʻ’‘`'ʼ")

CYR_BASE_NEW = {
    "а":"a","б":"b","в":"v","г":"g","д":"d","ж":"j","з":"z","и":"i","й":"y",
    "к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t",
    "у":"u","ф":"f","х":"x","ч":"ç","ш":"ş","ъ":"’","ь":"","э":"e","ю":"yu",
    "я":"ya","ё":"yo","ў":"ö","қ":"q","ғ":"ğ","ҳ":"h"
}
CYR_BASE_OLD = {
    "а":"a","б":"b","в":"v","г":"g","д":"d","ж":"j","з":"z","и":"i","й":"y",
    "к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t",
    "у":"u","ф":"f","х":"x","ч":"ch","ш":"sh","ъ":"’","ь":"","э":"e","ю":"yu",
    "я":"ya","ё":"yo","ў":"o‘","қ":"q","ғ":"g‘","ҳ":"h"
}

def has_case(ch):
    return ch.lower() != ch.upper()

def is_upper(ch):
    return has_case(ch) and ch == ch.upper()

def title_case(value):
    return value[:1].upper() + value[1:] if value else value

def cyr_word_to_latin(word, target):
    lower_word = word.lower()
    cased = [c for c in word if has_case(c)]
    all_upper = len(cased) > 1 and all(is_upper(c) for c in cased)
    base = CYR_BASE_OLD if target == "old" else CYR_BASE_NEW
    result = []

    for i, src in enumerate(word):
        low = lower_word[i]
        prev = lower_word[i-1] if i > 0 else ""
        nxt = lower_word[i+1] if i + 1 < len(lower_word) else ""

        if low == "е":
            value = "ye" if i == 0 or prev in CYR_VOWELS or prev in ("ъ", "ь") else "e"
        elif low == "ц":
            value = "s" if i == 0 else "ts"
        elif low == "ъ" and nxt in ("е", "ё", "ю", "я"):
            value = ""
        else:
            value = base.get(low, src)
            if target == "old" and low == "ҳ" and prev == "с":
                value = "’h"

        if is_upper(src):
            value = value.upper() if all_upper else title_case(value)
        result.append(value)

    return "".join(result)

def transliterate_cyr(text, target):
    return CYR_RUN.sub(lambda m: cyr_word_to_latin(m.group(0), target), str(text))

def old_latin_to_new(text):
    s = str(text)
    for pattern, replacement in [
        (r"O[ʻ’‘`'ʼ]", "Ö"), (r"o[ʻ’‘`'ʼ]", "ö"),
        (r"G[ʻ’‘`'ʼ]", "Ğ"), (r"g[ʻ’‘`'ʼ]", "ğ"),
        (r"SH", "Ş"), (r"Sh", "Ş"), (r"sh", "ş"),
        (r"CH", "Ç"), (r"Ch", "Ç"), (r"ch", "ç"),
    ]:
        s = re.sub(pattern, replacement, s)
    return s

def new_word_to_old(word):
    cased = [c for c in word if has_case(c)]
    all_upper = len(cased) > 1 and all(is_upper(c) for c in cased)
    out = []
    for ch in word:
        if ch == "Ö": out.append("O‘")
        elif ch == "ö": out.append("o‘")
        elif ch == "Ğ": out.append("G‘")
        elif ch == "ğ": out.append("g‘")
        elif ch == "Ş": out.append("SH" if all_upper else "Sh")
        elif ch == "ş": out.append("sh")
        elif ch == "Ç": out.append("CH" if all_upper else "Ch")
        elif ch == "ç": out.append("ch")
        else: out.append(ch)
    return "".join(out)

def new_latin_to_old(text):
    return re.sub(r"[A-Za-zÖöĞğŞşÇç]+", lambda m: new_word_to_old(m.group(0)), str(text))

LAT_TO_CYR = {
    "a":"а","b":"б","d":"д","e":"е","f":"ф","g":"г","h":"ҳ","i":"и","j":"ж",
    "k":"к","l":"л","m":"м","n":"н","o":"о","p":"п","q":"қ","r":"р","s":"с",
    "t":"т","u":"у","v":"в","x":"х","y":"й","z":"з","ö":"ў","ğ":"ғ","ş":"ш","ç":"ч"
}
INITIAL_C_WORDS = [
    "sirkulyats","sirkul","sirk","sement","sentner","senzur","sex","sikl",
    "sitrus","sistern","siferblat","silindr","sink"
]

def latin_word_to_cyr(word):
    normalized = old_latin_to_new(word)
    lower = normalized.lower()
    force_initial_c = any(lower.startswith(root) for root in INITIAL_C_WORDS)
    out = []
    i = 0
    digraphs = {"yo":"ё", "ya":"я", "yu":"ю", "ye":"е", "ts":"ц"}

    while i < len(normalized):
        ch = normalized[i]
        low = lower[i]
        pair = lower[i:i+2]
        pair_src = normalized[i:i+2]
        pair_upper = len(pair_src) == 2 and is_upper(pair_src[0])

        if i == 0 and force_initial_c and low == "s":
            out.append("Ц" if is_upper(ch) else "ц")
            i += 1
            continue

        if pair in digraphs:
            value = digraphs[pair].upper() if pair_upper else digraphs[pair]
            out.append(value)
            i += 2
            continue

        if low == "e":
            value = "э" if i == 0 else "е"
            out.append(value.upper() if is_upper(ch) else value)
            i += 1
            continue

        if ch in APOSTROPHES:
            if i > 0 and lower[i-1] == "s" and i+1 < len(lower) and lower[i+1] == "h":
                i += 1
                continue
            out.append("ъ")
            i += 1
            continue

        value = LAT_TO_CYR.get(low)
        if value:
            out.append(value.upper() if is_upper(ch) else value)
        else:
            out.append(ch)
        i += 1

    return "".join(out)

def latin_to_cyr(text):
    return LAT_RUN.sub(lambda m: latin_word_to_cyr(m.group(0)), str(text))

MODES = {
    "auto", "cyrToOld", "cyr", "old", "newToOld", "newToCyr", "oldToCyr"
}

def convert(text, mode="auto"):
    text = str(text)
    if mode == "cyrToOld":
        return transliterate_cyr(text, "old")
    if mode == "cyr":
        return transliterate_cyr(text, "new")
    if mode == "old":
        return old_latin_to_new(text)
    if mode == "newToOld":
        return new_latin_to_old(text)
    if mode == "newToCyr":
        return latin_to_cyr(text)
    if mode == "oldToCyr":
        return latin_to_cyr(old_latin_to_new(text))
    return old_latin_to_new(transliterate_cyr(text, "new"))
