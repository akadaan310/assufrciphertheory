# -*- coding: utf-8 -*-
"""طبقة النص: تحميل نص تنزيل الحرفي (بدون أي تعديل على الملف) والوصول إليه.

القاعدة: ملفات data/quran/*.txt منسوخة حرفيًا من مشروع تنزيل (tanzil.net)
وممنوع تعديلها حسب شروط الترخيص. أي معالجة (فصل البسملة، تجريد التشكيل)
بتصير هون وقت التشغيل، ومش بتنكتب على الملف.
"""
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QDIR = os.path.join(ROOT, "data", "quran")
UTHMANI = os.path.join(QDIR, "tanzil-uthmani.txt")
SIMPLE = os.path.join(QDIR, "tanzil-simple-clean.txt")
SURAHS = os.path.join(QDIR, "surahs.json")

# ملف txt-2 من تنزيل بيلصق البسملة في أول الآية ١ من كل سورة (غير الفاتحة والتوبة).
# البسملة مش جزء من رقم الآية ١ في العدّ الكوفي لهالسور، فبنفصلها وقت التحميل.
# نص البسملة بناخذه من الفاتحة ١ في نفس الملف، وبنقارنه بلا تشكيل.

# التشكيل وعلامات الضبط والوقف القرآنية (U+0610–U+061A, U+064B–U+065F,
# U+0670, U+06D6–U+06ED) والتطويل.
_MARKS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_SPACES = re.compile(r"\s+")


def strip_marks(s):
    return _SPACES.sub(" ", _MARKS.sub("", s)).strip()


def rasm(s):
    """هيكل تقريبي للحروف: بلا تشكيل، والألفات موحّدة، وهمزة القطع المفردة محذوفة.

    هاي أداة بحث، مش «الرسم العثماني» بالمعنى العلمي الدقيق. مثلًا:
    الأمر -> الامر ، الروم -> الروم ، إرم -> ارم
    """
    s = strip_marks(s)
    for a in "ٱأإآ":
        s = s.replace(a, "ا")
    s = s.replace("ى", "ي").replace("ة", "ه")
    s = s.replace("ؤ", "و").replace("ئ", "ي").replace("ء", "")
    return s


def _load(path):
    verses = {}
    basmala = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n").lstrip("﻿")
            if not line or line.startswith("#"):
                continue
            s, a, text = line.split("|", 2)
            s, a = int(s), int(a)
            if (s, a) == (1, 1):
                basmala = strip_marks(text)
            removed = False
            if a == 1 and s not in (1, 9):
                # بنقارن بلا تشكيل: في سورتي التين والقدر بيحمل باء البسملة شدّة إدغام.
                head = text.split(" ", 4)
                if len(head) == 5 and strip_marks(" ".join(head[:4])) == basmala:
                    text = head[4]
                    removed = True
            verses[(s, a)] = {"text": text, "basmala_prefix_removed": removed}
    return verses


class Quran:
    def __init__(self):
        self.uthmani = _load(UTHMANI)
        self.simple = _load(SIMPLE)
        meta = json.load(open(SURAHS, encoding="utf-8"))
        self.surahs = {m["number"]: m for m in meta["surahs"]}
        for n, m in self.surahs.items():
            m["name_ar"] = strip_marks(m["name_ar_vocalized"])

    # -- الوصول المباشر --------------------------------------------------
    def verse(self, s, a):
        return self.uthmani[(s, a)]["text"]

    def verse_simple(self, s, a):
        return self.simple[(s, a)]["text"]

    def name(self, s):
        return self.surahs[s]["name_ar"]

    def ayah_count(self, s):
        return self.surahs[s]["ayahs"]

    def keys(self):
        return sorted(self.uthmani)

    # -- البحث -----------------------------------------------------------
    def find_rasm(self, phrase):
        """كل المواضع اللي بيظهر فيها هيكل العبارة (بعد التطبيع) جوّا آية.

        بنقارن على حدود كلمات كاملة، فـ«الامر» ما بتطابق «بالامر».
        """
        target = " " + rasm(phrase) + " "
        hits = []
        for k in self.keys():
            if target in " " + rasm(self.simple[k]["text"]) + " ":
                hits.append(k)
        return hits

    def words_rasm(self):
        """كل كلمة (هيكلها) مع موضعها: [(سورة، آية، ترتيب الكلمة، هيكل)]."""
        out = []
        for k in self.keys():
            for i, w in enumerate(rasm(self.simple[k]["text"]).split(" "), 1):
                if w:
                    out.append((k[0], k[1], i, w))
        return out


_Q = None


def load():
    global _Q
    if _Q is None:
        _Q = Quran()
    return _Q
