# -*- coding: utf-8 -*-
"""تجارب لؤلؤ العربية (لغة اللؤلؤ واللؤلؤة). كل تجربة حتمية (deterministic) وبتكتب نتيجتها في results/EXP-XX.json.

تشغيل:  python3 lab/experiments.py
كل تجربة بتحمل: السؤال، القاعدة، الناتج المتوقع، الناتج الفعلي، والأمثلة المضادة.
"""
import itertools
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qiraat  # noqa: E402
import quran  # noqa: E402
import sites as sites_mod  # noqa: E402

RESULTS = os.path.join(quran.ROOT, "results")
MADDA = "ٓ"  # علامة المدّ اللازم فوق حروف الافتتاح في الرسم العثماني عند تنزيل


def _sites():
    return json.load(open(sites_mod.OUTPUT, encoding="utf-8"))["sites"]


def _site_suras():
    return sorted({s["sura"] for s in _sites()})


def _share(q, suras, unit="ayah"):
    """حصّة مجموعة سور من النص كله (بالآيات)."""
    total = len(q.keys())
    part = sum(q.ayah_count(s) for s in suras)
    return part / total


# ---------------------------------------------------------------------------
# EXP-01  الطائرة والمغوصة: هل في قاعدة نصّية واحدة بتعيد إنتاج تصنيف المؤلف؟
# ---------------------------------------------------------------------------
def exp01():
    rows = []
    for s in _sites():
        u = s["units"][0]
        word = u["opening_as_written"]
        rows.append({
            "id": s["id"], "sura": s["sura"], "name": s["sura_name"], "letters": u["letters"],
            "class": s["author_class"],
            "standalone_ayah": u["standalone_ayah"],
            "single_letter": len(u["letters"]) == 1,
            "has_ra": "ر" in u["letters"],
            "last_letter_has_madd_sign": word.endswith(MADDA),
            "next_is_waw_oath": u["next_word"].startswith("و") and not u["standalone_ayah"],
        })
    classified = [r for r in rows if r["class"] in ("مغوصة", "طائرة")]

    rules = {
        "R1": ("مغوصة ⇔ الافتتاحية مش آية مستقلة (بتشارك آيتها كلام بعدها)",
               lambda r: not r["standalone_ayah"]),
        "R2": ("مغوصة ⇔ الافتتاحية فيها راء", lambda r: r["has_ra"]),
        "R3": ("مغوصة ⇔ آخر حرف مش عليه علامة مدّ في الرسم", lambda r: not r["last_letter_has_madd_sign"]),
        "R4": ("مغوصة ⇔ مش آية مستقلة، والكلمة اللي بعدها مش واو قسم",
               lambda r: (not r["standalone_ayah"]) and not r["next_is_waw_oath"]),
    }
    report = {}
    for key, (desc, pred) in rules.items():
        agree, counter = 0, []
        for r in classified:
            predicted = "مغوصة" if pred(r) else "طائرة"
            if predicted == r["class"]:
                agree += 1
            else:
                counter.append(f"{r['name']} ({r['letters']}): القاعدة بتقول {predicted}، والمؤلف بيقول {r['class']}")
        predictions = {f"{r['name']} ({r['letters']})": ("مغوصة" if pred(r) else "طائرة")
                       for r in rows if r["class"] == "غير محسوم"}
        report[key] = {"rule": desc, "agree": agree, "of": len(classified),
                       "counterexamples": counter, "predictions_for_unclassified": predictions}
    return {
        "id": "EXP-01",
        "question": "هل في خاصية نصية بسيطة بتفصل الحروف المغوصة عن الطائرة حسب تصنيف المؤلف الأولي؟",
        "data": rows,
        "rules": report,
        "finding": ("R1 بتطابق كل الحالات المغوصة (كلها جوّا آية أطول)، بس بتغلط في ق ون: هدول جوّا آية "
                    "والمؤلف بيعدّهم طائرة. ولا قاعدة من الأربع بتطابق التصنيف كاملًا."),
        "status": "COUNTEREXAMPLE FOUND",
    }


# ---------------------------------------------------------------------------
# EXP-02  هندسة ا ل م ر: الم، الر، المر، والكلمات القريبة
# ---------------------------------------------------------------------------
def is_subseq(a, b):
    it = iter(b)
    return all(c in it for c in a)


def damerau(a, b):
    d = {(i, -1): i + 1 for i in range(-1, len(a))}
    d.update({(-1, j): j + 1 for j in range(-1, len(b))})
    for i in range(len(a)):
        for j in range(len(b)):
            cost = 0 if a[i] == b[j] else 1
            d[(i, j)] = min(d[(i - 1, j)] + 1, d[(i, j - 1)] + 1, d[(i - 1, j - 1)] + cost)
            if i and j and a[i] == b[j - 1] and a[i - 1] == b[j]:
                d[(i, j)] = min(d[(i, j)], d[(i - 2, j - 2)] + 1)
    return d[(len(a) - 1, len(b) - 1)]


def shortest_common_supersequences(a, b):
    letters = sorted(set(a + b))
    for n in range(max(len(a), len(b)), len(a) + len(b) + 1):
        found = sorted("".join(p) for p in itertools.product(letters, repeat=n)
                       if is_subseq(a, "".join(p)) and is_subseq(b, "".join(p)))
        if found:
            return found
    return []


def exp02():
    q = quran.load()
    words = {"الم": "افتتاحية (٦ سور منها الروم)", "الر": "افتتاحية (٥ سور)",
             "المر": "افتتاحية الرعد", "المص": "افتتاحية الأعراف",
             "الروم": "٣٠:٢", "الامر": "هيكل «الأمر» (٣٠ موضع)", "ارم": "هيكل «إرم» ٨٩:٧"}
    keys = list(words)
    dist = {a: {b: damerau(a, b) for b in keys} for a in keys}
    subseq = [[a, b] for a in keys for b in keys if a != b and is_subseq(a, b)]
    scs = shortest_common_supersequences("الم", "الر")
    vocab = Counter(w for *_, w in q.words_rasm())
    openings = {"الم", "الر", "المر", "المص"}

    def one_insertion_supersets(core):
        return sorted(((w, n) for w, n in vocab.items()
                       if len(w) == len(core) + 1 and is_subseq(core, w)), key=lambda x: -x[1])

    scs_report = []
    for s in scs:
        sup = one_insertion_supersets(s)
        scs_report.append({
            "scs": s,
            "is_opening": s in openings,
            "occurs_as_word": vocab.get(s, 0),
            "words_one_letter_longer_containing_it": len(sup),
            "examples": sup[:15],
        })
    return {
        "id": "EXP-02",
        "question": "شو العلاقات الحرفية الدقيقة بين الم والر والمر وكلمات الروم والأمر وإرم؟",
        "operations": {"insert": "إضافة حرف", "delete": "حذف حرف", "substitute": "تبديل حرف بحرف",
                       "transpose": "تبديل موقع حرفين متجاورين"},
        "words": words,
        "distance_damerau": dist,
        "subsequence_pairs": subseq,
        "scs_of_alm_and_alr": scs_report,
        "finding": ("أقصر تراكيب بتحتوي الم والر مع بعض (shortest common supersequences) اثنين بالضبط: "
                    "المر والرم. الأولى افتتاحية الرعد، والثانية مش افتتاحية ولا كلمة بالقرآن. "
                    "المر قاعدة جوّا هيكل الامر (بإضافة ألف)، والرم قاعدة جوّا الروم (بإضافة واو)، "
                    "وارم هي الرم بلا لام. بس انتبه: الاحتواء لحاله ما بيميّز — "
                    + "، ".join(f"{r['scs']} + حرف: {' / '.join(w for w, _ in r['examples'])}" for r in scs_report)
                    + "."),
        "status": "FORMALIZED RULE",
    }


# ---------------------------------------------------------------------------
# EXP-03  «لله الأمر»: موضعين بس، بالرعد والروم. شو احتمال هيك صدفة؟
# ---------------------------------------------------------------------------
def exp03():
    q = quran.load()
    hits = q.find_rasm("لله الأمر")
    # خط الأساس: كل زوج كلمتين متتاليتين (bigram) ظهر مرتين بالضبط في سورتين مختلفتين.
    occ = defaultdict(list)
    for k in q.keys():
        w = quran.rasm(q.verse_simple(*k)).split(" ")
        for i in range(len(w) - 1):
            occ[w[i] + " " + w[i + 1]].append(k)
    twice = {g: v for g, v in occ.items() if len(v) == 2 and v[0][0] != v[1][0]}
    pair = {13, 30}
    same_pair = sorted(g for g, v in twice.items() if {v[0][0], v[1][0]} == pair)
    site = set(_site_suras())
    both_sites = sum(1 for v in twice.values() if v[0][0] in site and v[1][0] in site)
    return {
        "id": "EXP-03",
        "question": "عبارة «لله الأمر» وين بتظهر؟ وهل ظهورها بالرعد والروم بالذات نادر؟",
        "occurrences": [{"sura": s, "ayah": a, "text": q.verse(s, a)} for s, a in hits],
        "baseline": {
            "bigrams_exactly_twice_in_two_suras": len(twice),
            "of_which_in_pair_13_30": len(same_pair),
            "pair_13_30_bigrams": same_pair,
            "fraction_with_both_in_29_site_suras": round(both_sites / len(twice), 4),
            "share_of_ayahs_in_29_site_suras": round(_share(q, site), 4),
        },
        "finding": ("«لله الأمر» بالترتيب هاد بتظهر مرتين بس: الرعد ١٣:٣١ («بل لله الأمر جميعا») والروم ٣٠:٤ "
                    "(«لله الأمر من قبل ومن بعد»). يعني بالسورتين اللي بيدور حولهم سؤال المر/الم. "
                    "وخط الأساس طلّع إشي ما كنّا بندوّر عليه: الزوج ١٣/٣٠ بيتشارك كمان «يريكم البرق خوفا» "
                    "(الرعد ١٣:١٢ والروم ٣٠:٢٤) — البرق بسورة الرعد وبسورة الروم. "
                    "بس في تحذير: المؤلف كان عارف آية الرعد، واختيار الزوج ١٣/٣٠ صار بعد ما شفنا النتيجة، "
                    "فالرقم الأساسي هون للوصف مش برهان قصد."),
        "status": "OBSERVED STRUCTURE",
    }


# ---------------------------------------------------------------------------
# EXP-04  الصرح، وأسباب السماوات، وكوكبة حم
# ---------------------------------------------------------------------------
def exp04():
    q = quran.load()
    site = set(_site_suras())
    sarh = [(s, a, w) for s, a, i, w in q.words_rasm() if "صرح" in w]
    sarh_verses = sorted({(s, a) for s, a, _ in sarh})
    share = _share(q, site)
    ha_mim = [40, 41, 42, 43, 44, 45, 46]
    heavens = {}
    for s in ha_mim:
        heavens[q.name(s)] = sorted({a for ss, a, i, w in q.words_rasm() if ss == s and "سماوات" in w})
    seven = {p: q.find_rasm(p) for p in ["سبع سماوات", "السماوات السبع", "سبع طرائق", "سبعا شدادا"]}
    return {
        "id": "EXP-04",
        "question": "وين بيظهر «الصرح»؟ وشو اللي بيحيط بكلام فرعون عن أسباب السماوات في كوكبة حم؟",
        "sarh_words": sarh,
        "sarh_verses": [{"sura": s, "ayah": a, "name": q.name(s), "text": q.verse(s, a)} for s, a in sarh_verses],
        "all_sarh_suras_are_sites": all(s in site for s, _ in sarh_verses),
        "chance_if_independent_by_ayah_share": round(share ** len(sarh_verses), 4),
        "share_of_ayahs_in_29_site_suras": round(share, 4),
        "ghafir_36_37": [q.verse(40, 36), q.verse(40, 37)],
        "seven_heavens_phrases": seven,
        "ha_mim_chain": [{"sura": s, "name": q.name(s), "ayahs": q.ayah_count(s)} for s in ha_mim],
        "heavens_mentions_in_ha_mim": heavens,
        "finding": ("كلمة صرح بتظهر بثلاث آيات بس: النمل ٢٧:٤٤ (طس)، القصص ٢٨:٣٨ (طسم)، غافر ٤٠:٣٦ (حم) — "
                    "كلها سور من مواقع النجوم. ومباشرة بعد غافر، أول سورة بعدها بكوكبة حم (فصلت ٤١:١٢) "
                    "فيها «فقضاهن سبع سماوات في يومين». آية الصرح نفسها ما بتذكر سبعة؛ التجاور بين "
                    "السورتين هو الملاحظة، مش وصف للبرج."),
        "status": "OBSERVED STRUCTURE",
    }


# ---------------------------------------------------------------------------
# EXP-05  «إن في ذلك لآيات»: التوزيع وعنقود الروم
# ---------------------------------------------------------------------------
def exp05():
    q = quran.load()
    plural = q.find_rasm("في ذلك لآيات")
    singular = q.find_rasm("إن في ذلك لآية")
    by_sura = Counter(s for s, _ in plural)
    total = len(plural)
    expected_30 = total * q.ayah_count(30) / len(q.keys())
    return {
        "id": "EXP-05",
        "question": "عبارة «في ذلك لآيات» كيف بتتوزّع؟ وليش الروم؟",
        "plural_occurrences": [{"sura": s, "ayah": a, "name": q.name(s)} for s, a in plural],
        "plural_by_sura": {q.name(s): n for s, n in by_sura.most_common()},
        "singular_occurrences_count": len(singular),
        "rum_observed": by_sura[30],
        "rum_expected_by_length": round(expected_30, 3),
        "rum_consecutive_run": [a for s, a in plural if s == 30],
        "finding": (f"الجمع «لآيات» ظهر {total} مرة. الروم لحالها فيها {by_sura[30]} (أكثر سورة)، "
                    "منها أربع متتالية ٣٠:٢١–٢٤، وبينها «منامكم بالليل والنهار» (٣٠:٢٣). "
                    f"لو التوزيع حسب الطول بس كان المتوقع ≈ {expected_30:.2f}."),
        "status": "OBSERVED STRUCTURE",
    }


# ---------------------------------------------------------------------------
# EXP-06  العمد والعماد وإرم
# ---------------------------------------------------------------------------
def exp06():
    q = quran.load()
    hits = [(s, a, w) for s, a, i, w in q.words_rasm() if w in ("عمد", "العماد")]
    return {
        "id": "EXP-06",
        "question": "إرم ذات العماد (٨٩:٧) و«بغير عمد» — وين بتلتقي؟",
        "occurrences": [{"sura": s, "ayah": a, "word": w, "name": q.name(s), "text": q.verse(s, a)} for s, a, w in hits],
        "finding": ("«عَمَد» (أعمدة) بتظهر بالرعد ١٣:٢ (المر) ولقمان ٣١:١٠ (الم) بصيغة «بغير عمد ترونها»، "
                    "وبالهمزة ١٠٤:٩. و«العماد» مرة وحدة مع إرم. يعني صورة الأعمدة/اللاأعمدة بتمرّ بسورتين من "
                    "عيلة ا ل م ر. هاد تجاور معجمي، مش عملية حرفية."),
        "status": "OBSERVED STRUCTURE",
    }


# ---------------------------------------------------------------------------
# EXP-07  الدخول والسكن في سورة النمل
# ---------------------------------------------------------------------------
def exp07():
    q = quran.load()
    enter = [(a, w) for s, a, i, w in q.words_rasm() if s == 27 and w.startswith(("ادخل", "وادخل", "فادخل"))]
    return {
        "id": "EXP-07",
        "question": "في سورة النمل، شو اللي بيندخل، ومين بيدخل؟",
        "enter_words_in_naml": enter,
        "verses": {str(a): q.verse(27, a) for a in sorted({a for a, _ in enter} | {18, 20, 44})},
        "finding": ("بالنمل: النملة بتقول «ادخلوا مساكنكم» (٢٧:١٨)، وبعدها بآيتين «وتفقد الطير ... أم كان من الغائبين» "
                    "(٢٧:٢٠)، وبالآخر «قيل لها ادخلي الصرح» (٢٧:٤٤). دخول للمسكن، تفقّد للغائب، دخول للصرح."),
        "status": "OBSERVED STRUCTURE",
    }


# ---------------------------------------------------------------------------
# EXP-08  هيكل اللؤلؤ: كلمة وحدة بالرسم، أكثر من قراءة
# ---------------------------------------------------------------------------
def exp08():
    q = quran.load()
    occ = []
    for s, a, i, w in q.words_rasm():
        core = w[1:] if w.startswith("و") else w
        core = core[2:] if core.startswith("ال") else core
        if core.startswith("لولو"):
            uth = q.verse(s, a).split(" ")[i - 1]
            occ.append({"sura": s, "ayah": a, "name": q.name(s), "word_index": i,
                        "skeleton": w, "uthmani": uth, "uthmani_skeleton": quran.rasm(uth),
                        "enter_in_ayah": any("دخل" in x for x in quran.rasm(q.verse_simple(s, a)).split(" ")),
                        "text": q.verse(s, a)})
    readings = defaultdict(list)
    for o in occ:
        readings["لُؤْلُؤ" if "ؤ" in o["uthmani"] else "لَوَلَّوْا"].append(f"{o['sura']}:{o['ayah']}")
    return {
        "id": "EXP-08",
        "question": "كم مرة بيظهر هيكل «لولو» بالقرآن، وكم قراءة إله؟",
        "occurrences": occ,
        "same_skeleton_in_both_editions": all("لولو" in o["uthmani_skeleton"] for o in occ),
        "readings": dict(readings),
        "enter_cooccurrence": [f"{o['sura']}:{o['ayah']}" for o in occ if o["enter_in_ayah"]],
        "finding": (f"هيكل «لولو» بيظهر بـ{len(occ)} آيات، وهو نفس الكلمة بالرسم بكل المواضع. "
                    f"بطبقة القراءة بينقرا قراءتين: «لُؤْلُؤ» ({len(readings['لُؤْلُؤ'])} مواضع) "
                    f"و«لَوَلَّوْا» ({len(readings['لَوَلَّوْا'])}: التوبة ٩:٥٧ والفتح ٤٨:٢٢). "
                    "يعني الرسم الواحد بيحمل حالتين، والقراءة هي اللي بتحسم. "
                    f"وفعل الدخول (دخل) بيظهر بـ{sum(o['enter_in_ayah'] for o in occ)} من الآيات: "
                    "٩:٥٧ (مدّخلا)، ٢٢:٢٣ (يدخل)، ٣٥:٣٣ (يدخلونها)."),
        "status": "VERIFIED TEXT",
    }


# ---------------------------------------------------------------------------
# EXP-09  تأمنّا: علامة الإشمام/الرَّوْم الوحيدة بالمصحف، والنون اللي غاصت بالرسم
# ---------------------------------------------------------------------------
RAWM_MARK = "\u06EB"  # ARABIC EMPTY CENTRE HIGH STOP — علامة الإشمام/الروم بمصحف المدينة عند تنزيل


def exp09():
    q = quran.load()
    sites = {s["sura"]: s for s in _sites()}
    marked = [(s, a) for (s, a), v in sorted(q.uthmani.items()) if RAWM_MARK in v["text"]]
    words = [(s, a, w) for s, a in marked for w in q.verse(s, a).split(" ") if RAWM_MARK in w]
    s, a, w = words[0]
    skel = quran.rasm(w)
    morph = "تامننا"  # تَأْمَنُنَا: الفعل تأمنُ + نا — نونين بالبنية
    return {
        "id": "EXP-09",
        "question": "وين بتظهر علامة الإشمام/الرَّوْم بالمصحف؟ وشو بيصير للنون بـ«تأمنّا»؟",
        "mark": "U+06EB",
        "verses_with_mark": [{"sura": s_, "ayah": a_, "name": q.name(s_), "text": q.verse(s_, a_)} for s_, a_ in marked],
        "marked_words": [x[2] for x in words],
        "sura_is_star_site": s in sites,
        "sura_opening": sites[s]["opening"] if s in sites else None,
        "sura_author_class": sites[s]["author_class"] if s in sites else None,
        "rasm_skeleton": skel,
        "morphological_skeleton": morph,
        "rasm_is_morph_minus_one_nun": len(morph) == len(skel) + 1 and is_subseq(skel, morph) and damerau(skel, morph) == 1,
        "skeleton_alrum_eq_alrawm": quran.rasm("ٱلرُّومُ") == quran.rasm("الرَّوْم"),
        "duration_model": {"حركة كاملة": 1, "اختلاس (عند من يسمّيه)": "≈ ٢/٣", "الرَّوْم": "≈ ١/٣", "الإشمام": "٠ صوت (إشارة شفتين بتنشاف)", "السكون المحض": 0},
        "finding": (f"العلامة U+06EB بتظهر بآية وحدة بس بالمصحف كله: {q.name(s)} {s}:{a}، على كلمة «{w}». "
                    f"وسورة {q.name(s)} من مواقع النجوم (افتتاحيتها {sites[s]['opening']}، وتصنيفها عند المؤلف "
                    f"«{sites[s]['author_class']}»). الرسم «{skel}» = البنية «{morph}» ناقص نون: نون غاصت بالكتابة، "
                    "والرَّوْم بيرجّع أثرها بالصوت (ثلث الحركة)، والإشمام بيرجّعه إشارة بتنشاف وما بتنسمع. "
                    "وهيكل «الروم» (السورة) هو نفسه هيكل «الرَّوْم» (المصطلح)."),
        "status": "VERIFIED TEXT",
    }


# ---------------------------------------------------------------------------
# EXP-10  حروف صُفْر عبر ثماني روايات: هل الافتتاحية آية لحالها؟ (العدّ بيختلف)
# ---------------------------------------------------------------------------
def exp10():
    rows = []
    for st in _sites():
        s = st["sura"]
        row = {"id": st["id"], "sura": s, "name": st["sura_name"], "opening": st["opening"],
               "author_class": st["author_class"], "narrations": {}}
        for n in qiraat.all_narrations():
            first = n.verse(s, 1)
            words = [w for w in first.split(" ") if quran.rasm(w)]
            row["narrations"][n.meta["ar"]] = {
                "verse_1": first,
                "standalone": len(words) == 1,
                "words_in_verse_1": len(words),
                "ayahs_in_sura": n.ayah_count(s),
            }
        rows.append(row)
    names = [n.meta["ar"] for n in qiraat.all_narrations()]
    standalone_count = {nm: sum(r["narrations"][nm]["standalone"] for r in rows) for nm in names}
    rum_basri = rows[[r["sura"] for r in rows].index(30)]["narrations"]["الدوري"]["verse_1"]
    # R1 من EXP-01 (مغوص ⇔ مش آية مستقلة) تحت كل عدّ
    r1 = {}
    for nm in names:
        ok = sum(1 for r in rows if r["author_class"] in ("مغوصة", "طائرة")
                 and (("مغوصة" if not r["narrations"][nm]["standalone"] else "طائرة") == r["author_class"]))
        r1[nm] = ok
    return {
        "id": "EXP-10",
        "question": "هل «الافتتاحية آية مستقلة» خاصية للنص ولا للعدّ؟ وكيف بتظهر حروف صُفْر بكل رواية؟",
        "narration_totals": {n.meta["ar"]: n.ayah_count() for n in qiraat.all_narrations()},
        "standalone_openings_per_narration": standalone_count,
        "rule_R1_agreement_per_count": r1,
        "rum_1_in_basri_count": rum_basri,
        "data": rows,
        "finding": ("كون الافتتاحية آية لحالها خاصية للعدّ الكوفي (حفص وشعبة: "
                    f"{standalone_count['حفص']} موقع). بباقي الروايات المطبوعة هون ولا افتتاحية من التسعة والعشرين آية "
                    f"لحالها ({standalone_count['ورش']} بورش، {standalone_count['الدوري']} بالدوري، {standalone_count['البزي']} بالبزي). "
                    f"وبعدّ الدوري/السوسي، الروم ٣٠:١ هي بالضبط «{rum_basri}»: «الم غلبت الروم» آية وحدة. "
                    f"يعني قاعدة R1 بتطابق تصنيف المؤلف {r1['حفص']}/١٩ بالعدّ الكوفي بس، وبتنهار لـ{r1['ورش']}/١٩ "
                    "بالأعداد التانية: تصنيف «الطائرة/المغوصة» إذا كان مربوط بحدود الآية، فهو مربوط بالعدّ الكوفي."),
        "status": "VERIFIED RECITATIONAL FACT",
    }


# ---------------------------------------------------------------------------
# EXP-11  الفرش على مستوى الرسم: وين بتختلف الروايات بالهيكل نفسه؟
# ---------------------------------------------------------------------------
def exp11():
    import difflib
    base = qiraat.load("hafs")
    out = {}
    watch = {(22, 23), (35, 33), (77, 33), (12, 11), (30, 2), (30, 4), (13, 31), (13, 1)}
    for n in qiraat.all_narrations():
        if n.key == "hafs":
            continue
        skel_diff, marks_only, examples, watched = 0, 0, [], []
        for s in range(1, 115):
            A = base.sura_words(s)
            B = n.sura_words(s)
            ka = [qiraat.skeleton(w) for _, w in A]
            kb = [qiraat.skeleton(w) for _, w in B]
            sm = difflib.SequenceMatcher(a=ka, b=kb, autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == "equal":
                    for i, j in zip(range(i1, i2), range(j1, j2)):
                        if quran.strip_marks(qiraat.clean(A[i][1])) != quran.strip_marks(qiraat.clean(B[j][1])) or A[i][1] != B[j][1]:
                            marks_only += 1
                            if (s, A[i][0]) in watch:
                                watched.append({"ref": f"{s}:{A[i][0]}", "hafs": A[i][1], n.meta["ar"]: B[j][1], "kind": "ضبط/أداء"})
                else:
                    skel_diff += 1
                    if len(examples) < 12:
                        examples.append({"sura": s, "ayah_hafs": A[i1][0] if i1 < len(A) else None,
                                         "hafs": " ".join(w for _, w in A[i1:i2]), n.meta["ar"]: " ".join(w for _, w in B[j1:j2])})
                    if i1 < len(A) and (s, A[i1][0]) in watch:
                        watched.append({"ref": f"{s}:{A[i1][0]}", "hafs": " ".join(w for _, w in A[i1:i2]),
                                        n.meta["ar"]: " ".join(w for _, w in B[j1:j2]), "kind": "رسم"})
        out[n.meta["ar"]] = {"skeleton_diff_spans": skel_diff, "words_same_skeleton_diff_marks": marks_only,
                             "examples": examples, "watched_verses": watched}
    return {
        "id": "EXP-11",
        "question": "قدّيش من خلاف الروايات بيمسّ الهيكل (الرسم)، وقدّيش بيضل فوق الهيكل (ضبط وأداء)؟",
        "baseline": "حفص",
        "per_narration": out,
        "finding": ("الأغلبية الساحقة من الخلاف بين الروايات بتصير فوق نفس الهيكل: نفس الرسم، ضبط وأداء مختلف. "
                    "الخلاف اللي بيغيّر الهيكل نفسه قليل نسبيًا. هاد هو ركن «موافقة الرسم ولو احتمالًا»: "
                    "الرسم لوح مشترك، والقراءات حالات عليه — نفس فكرة «لغة اللؤلؤ» (P-025)."),
        "status": "OBSERVED STRUCTURE",
    }


# ---------------------------------------------------------------------------
# EXP-12  حروف صُفْر بالأداء: الإمالة/التقليل والإدغام عبر الروايات
# ---------------------------------------------------------------------------
IMALA_MARKS = {"\u06EA": "إمالة/تقليل (نقطة خالية تحت)", "\u065C": "إمالة (نقطة تحت)", "\u06ED": "إمالة (ميم صغيرة تحت)"}
HAYY_TAHIR = set("حيطهر")   # أسماؤها على حرفين آخرها ألف: حا يا طا ها را
NAQS_ASALKAM = set("نقصعسلكم")  # أسماؤها ثلاثة أحرف: مدّ لازم


def exp12():
    rows, seen = [], set()
    for st in _sites():
        for u in st["units"]:
            key = u["letters"]
            if key in seen:
                continue
            seen.add(key)
            per = {}
            for n in qiraat.all_narrations():
                words = [w for w in n.verse(st["sura"], u["ayah"] if n.key in ("hafs", "shouba") else 1).split(" ")
                         if qiraat.skeleton(w) == key]
                w = words[0] if words else n.verse(st["sura"], 1).split(" ")[0]
                inclined = []
                for i, c in enumerate(w):
                    if c in IMALA_MARKS:
                        j = i - 1
                        while j >= 0 and not ("\u0621" <= w[j] <= "\u064A" or w[j] == "\u0671"):
                            j -= 1
                        inclined.append(w[j] if j >= 0 else "?")
                per[n.meta["ar"]] = {"written": w, "inclined_letters": inclined,
                                     "shadda_on_last": w.rstrip("\u06D6\u06D7\u06DA\u06D8\u0653").endswith("\u0651")
                                     or "\u0651\u0653" in w[-4:] or "\u0651" in w[-3:]}
            all_inclined = {c for v in per.values() for c in v["inclined_letters"]}
            rows.append({"letters": key, "author_class": st["author_class"], "per_narration": per,
                         "inclined_anywhere": sorted(all_inclined),
                         "inclined_subset_of_hayy_tahir": all_inclined <= HAYY_TAHIR})
    noon = rows[[r["letters"] for r in rows].index("ن")]["per_narration"]
    return {
        "id": "EXP-12",
        "question": "حروف صُفْر نفسها: شو بيتغيّر بأدائها من رواية لرواية؟",
        "groups": {"حي طهر": "أسماؤها حرفين آخرها ألف (مدّ طبيعي)، وهي اللي بتقبل الإمالة/التقليل",
                   "نقص عسلكم": "أسماؤها ثلاث أحرف (مدّ لازم)", "ا": "ألف: ما فيها مدّ"},
        "data": rows,
        "all_inclined_letters_in_hayy_tahir": all(r["inclined_subset_of_hayy_tahir"] for r in rows),
        "noon_68_1": {k: v["written"] for k, v in noon.items()},
        "finding": ("كل حرف من حروف صُفْر انمال أو تقلّل بأي رواية من الثمانية هو من مجموعة «حي طهر» "
                    "(أسماء على حرفين آخرها ألف). الراء في الر والمر بتنمال/بتتقلّل عند شعبة وورش والدوري والسوسي، "
                    "وبتضل مفتوحة عند حفص وقالون والبزي وقنبل. وورش بيكتب «نُّٓ» بالقلم ٦٨:١ بشدّة: النون بتدغم "
                    "بواو «والقلم»، وحفص بيظهرها. يعني بالأداء، ن بتغوص عند ورش."),
        "status": "VERIFIED RECITATIONAL FACT",
    }


EXPERIMENTS = [exp01, exp02, exp03, exp04, exp05, exp06, exp07, exp08, exp09, exp10, exp11, exp12]


def run_all():
    os.makedirs(RESULTS, exist_ok=True)
    sites_mod.build()
    out = []
    for fn in EXPERIMENTS:
        r = fn()
        with open(os.path.join(RESULTS, r["id"] + ".json"), "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
        out.append(r)
    return out


if __name__ == "__main__":
    for r in run_all():
        print(f"{r['id']}  [{r['status']}]  {r['finding']}\n")
