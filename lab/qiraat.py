# -*- coding: utf-8 -*-
"""طبقة القراءات: ثماني روايات من مجمع الملك فهد (KFGQPC)، منسوخة حرفيًا.

الرواية ← القارئ (الإسناد المعروف):
    حفص، شعبة   ← عاصم (الكوفة)
    ورش، قالون  ← نافع (المدينة)
    الدوري، السوسي ← أبو عمرو (البصرة)
    البزي، قنبل ← ابن كثير (مكة)
(ملاحظة: ملف README بمستودع المصدر بينسب البزي وقنبل لأبي عمرو؛ هاد غلط بالوصف، والنسبة الصحيحة لابن كثير.)

النص ما بيتعدّل على القرص. التطبيع (شيل رقم الآية، الشكل، علامات الوقف، أشكال الحروف
المغربية) بيصير وقت التشغيل بس.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quran  # noqa: E402

QDIR = os.path.join(quran.ROOT, "data", "qiraat")

NARRATIONS = {
    "hafs":   {"file": "hafsData_v18.json",   "ar": "حفص",    "qari": "عاصم",     "city": "الكوفة"},
    "shouba": {"file": "ShoubaData08.json",   "ar": "شعبة",   "qari": "عاصم",     "city": "الكوفة"},
    "warsh":  {"file": "warshData_v10.json",  "ar": "ورش",    "qari": "نافع",     "city": "المدينة"},
    "qaloon": {"file": "QaloonData_v10.json", "ar": "قالون",  "qari": "نافع",     "city": "المدينة"},
    "doori":  {"file": "DooriData_v09.json",  "ar": "الدوري", "qari": "أبو عمرو", "city": "البصرة"},
    "soosi":  {"file": "SoosiData09.json",    "ar": "السوسي", "qari": "أبو عمرو", "city": "البصرة"},
    "bazzi":  {"file": "BazziData_v07.json",  "ar": "البزي",  "qari": "ابن كثير", "city": "مكة"},
    "qumbul": {"file": "QumbulData_v07.json", "ar": "قنبل",   "qari": "ابن كثير", "city": "مكة"},
}

_NUM = re.compile(r"[٠-٩۰-۹]+\s*$")
_EXTRA = re.compile("[ ‌-‏۞۩࣓-ࣿ]")
_SHAPES = str.maketrans({"ڢ": "ف", "ڧ": "ق", "ں": "ن", "ی": "ي", "ے": "ي", "ٮ": "ب", "ک": "ك"})


def clean(text):
    """نص الآية بلا رقمها ولا علامة الحزب ولا المسافات غير المرئية."""
    return re.sub(r"\s+", " ", _NUM.sub("", _EXTRA.sub(" ", text))).strip()


def skeleton(text):
    """هيكل قابل للمقارنة بين الروايات (نفس quran.rasm + أشكال الحروف المغربية)."""
    return quran.rasm(clean(text).translate(_SHAPES))


class Narration:
    def __init__(self, key):
        meta = NARRATIONS[key]
        self.key, self.meta = key, meta
        rows = json.load(open(os.path.join(QDIR, meta["file"]), encoding="utf-8-sig"))
        self.verses = {}
        for r in rows:
            s = r.get("sura_no", r.get("sora"))
            self.verses[(int(s), int(r["aya_no"]))] = clean(r["aya_text"])

    def verse(self, s, a):
        return self.verses[(s, a)]

    def ayah_count(self, s=None):
        return len([k for k in self.verses if s is None or k[0] == s])

    def sura_words(self, s):
        """كل كلمات السورة بالترتيب، مع رقم الآية بهالرواية (العدّ بيختلف بين الروايات)."""
        out = []
        for (ss, a) in sorted(k for k in self.verses if k[0] == s):
            for w in self.verses[(ss, a)].split(" "):
                if quran.rasm(w):
                    out.append((a, w))
        return out


_CACHE = {}


def load(key):
    if key not in _CACHE:
        _CACHE[key] = Narration(key)
    return _CACHE[key]


def all_narrations():
    return [load(k) for k in NARRATIONS]
