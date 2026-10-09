# -*- coding: utf-8 -*-
"""مواقع النجوم: المواقع التسعة والعشرون لحروف صُفْر، مع التحقق من النص.

المدخل: data/sites_input.json (قائمة المؤلف + التصنيف الأولي المقترح).
المخرج: data/sites.json (نفس القائمة بعد مطابقتها حرفيًا مع نص تنزيل).

أي اختلاف بين المتوقَّع والنص بيوقّف البناء: ما في «تصحيح صامت».
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quran  # noqa: E402

INPUT = os.path.join(quran.ROOT, "data", "sites_input.json")
OUTPUT = os.path.join(quran.ROOT, "data", "sites.json")


def _opening_units(q, sura, expected_units):
    """كل وحدة افتتاحية = (رقم الآية، الحروف المتوقعة). بنرجّع وصفًا متحقَّقًا لكل وحدة."""
    units = []
    for u in expected_units:
        aya, letters = u["ayah"], u["letters"]
        uth = q.verse(sura, aya)
        simple = q.verse_simple(sura, aya)
        first_word = quran.rasm(simple).split(" ")[0]
        if first_word != letters:
            raise ValueError(f"{sura}:{aya}: متوقَّع «{letters}» لكن أول كلمة «{first_word}»")
        rest = quran.rasm(simple).split(" ")[1:]
        standalone = len(rest) == 0
        units.append({
            "ayah": aya,
            "letters": letters,
            "uthmani_ayah_text": uth,
            "opening_as_written": uth.split(" ")[0],
            "standalone_ayah": standalone,
            "words_after_in_same_ayah": len(rest),
            "next_word": (rest[0] if rest else quran.rasm(q.verse_simple(sura, aya + 1)).split(" ")[0]),
        })
    return units


def build():
    q = quran.load()
    spec = json.load(open(INPUT, encoding="utf-8"))
    out = []
    for i, site in enumerate(spec["sites"], 1):
        s = site["sura"]
        if quran.rasm(q.name(s)) != quran.rasm(site["sura_name"]):
            raise ValueError(f"اسم السورة {s}: «{q.name(s)}» ≠ «{site['sura_name']}»")
        units = _opening_units(q, s, site["units"])
        out.append({
            "site": i,
            "id": f"STAR-{i:02d}",
            "sura": s,
            "sura_name": site["sura_name"],
            "sura_ayahs": q.ayah_count(s),
            "opening": " ".join(u["letters"] for u in units),
            "units": units,
            "letters_multiset": sorted("".join(u["letters"] for u in units)),
            "author_class": site.get("author_class", "غير محسوم"),
            "author_class_status": "AUTHOR'S READING" if site.get("author_class") else "OPEN QUESTION",
            "notes": site.get("notes", ""),
        })
    if len(out) != 29:
        raise ValueError(f"عدد المواقع {len(out)} مش ٢٩")
    data = {
        "description": "المواقع التسعة والعشرون (مواقع النجوم) متحقَّق منها حرفيًا من نص تنزيل العثماني، العدّ الكوفي (رواية حفص).",
        "text_source": "Tanzil Quran Text (Uthmani, Version 1.1), tanzil.net — CC BY 3.0, verbatim",
        "status": "VERIFIED TEXT",
        "sites": out,
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return data


if __name__ == "__main__":
    d = build()
    for s in d["sites"]:
        flags = " + ".join(f"{u['letters']}({'آية مستقلة' if u['standalone_ayah'] else 'داخل آية'})" for u in s["units"])
        print(f"{s['id']}  {s['sura']:>3} {s['sura_name']:<10} {flags:<40} {s['author_class']}")
